import asyncio
import logging
import re
from datetime import datetime, timezone

import aiofiles

from src.config import (
    CONFIGS_DIR,
    INVENTORY_DIR,
    OUTPUT_DIR,
    SAMPLES_DIR,
    SCREENSHOTS_DIR,
)
from src.database import find_inventory_by_model, save_audit_history
from src.eol import batch_upsert_from_audit
from src.llm import query_ollama
from src.models import (
    AntivirusInfo,
    BackupInfo,
    DatabaseInfo,
    DeviceInfo,
    NetworkSecurityInfo,
    ServerInfo,
    StorageInfo,
    VirtualizationInfo,
)
from src.normalizer import build_aggregated_summary
from src.parser import (
    classify_and_parse,
    extract_text_from_file,
    extract_text_from_image,
)

logger = logging.getLogger(__name__)


def _classify_devices(devices: list[DeviceInfo]) -> dict:
    core = [d for d in devices if any(k in d.hostname.lower() for k in ["core", "5510", "s6730"])]
    dist = [d for d in devices if any(k in d.hostname.lower() for k in ["hp5412", "hp3500"])]
    access = [d for d in devices if any(k in d.hostname.lower() for k in ["2530", "2620", "5120", "5731"])]
    edge = [d for d in devices if any(k in d.hostname.lower() for k in ["c4331", "h6121", "asa"])]
    return {"core": core, "dist": dist, "access": access, "edge": edge}


def _auto_add_eol(model: str, hostname: str, category: str) -> None:
    """Автоматически добавляет обнаруженное оборудование в EOL-базу."""
    if not model or model == "Неизвестно":
        return
    try:
        batch_upsert_from_audit([{
            "model": model,
            "vendor": model.split()[0] if model.split() else "",
            "category": category,
            "note": "Обнаружено во время аудита",
        }])
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Auto EOL add error: {e}")


def _extract_template_sections(text: str) -> list[dict]:
    """Извлекает структуру разделов из шаблона отчёта.
    Поддерживает markdown-заголовки (# ## ###), а также заголовки РУССКИМИ буквами (ВВЕДЕНИЕ, 1. РАЗДЕЛ).
    """
    sections = []
    lines = text.split('\n')
    current_section = None
    current_content = []

    header_patterns = [
        re.compile(r'^(#{1,3})\s+(.+)$'),                                         # # Заголовок
        re.compile(r'^(\d+)\.\s*([А-ЯA-Z][А-ЯA-Za-z0-9\s\-]+)$'),               # 1. ЗАГОЛОВОК
        re.compile(r'^([А-ЯA-Z][А-ЯA-Z\s\-]{3,})$'),                              # ЗАГОЛОВОК (только заглавные)
    ]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_content.append(line)
            continue

        matched = False
        for pattern in header_patterns:
            m = pattern.match(stripped)
            if m:
                if current_section:
                    current_section["content"] = '\n'.join(current_content).strip()
                    sections.append(current_section)

                if m.lastindex == 2:
                    level = 2 if m.group(1).isdigit() else 1
                    title = m.group(2).strip()
                elif m.lastindex == 1:
                    level = 1
                    title = m.group(1).strip()
                else:
                    level = len(m.group(1))
                    title = m.group(2).strip()

                current_section = {"level": level, "title": title, "content": ""}
                current_content = []
                matched = True
                break

        if not matched:
            current_content.append(line)

    if current_section:
        current_section["content"] = '\n'.join(current_content).strip()
        sections.append(current_section)

    return sections


def _read_template() -> str:
    """Читает шаблон из SAMPLES_DIR (.doc, .docx, .rtf, .md, .txt)."""
    if not SAMPLES_DIR.exists():
        return ""
    for f in SAMPLES_DIR.iterdir():
        if not f.is_file():
            continue
        try:
            text = extract_text_from_file(f)
            if text and len(text) > 100:
                return text[:50000]
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Ошибка чтения шаблона {f.name}: {e}")
    return ""


def _read_inventory_text() -> str:
    """Читает inventory из INVENTORY_DIR (все форматы)."""
    if not INVENTORY_DIR.exists():
        return ""
    sources = []
    for f in INVENTORY_DIR.iterdir():
        if not f.is_file():
            continue
        try:
            text = extract_text_from_file(f)
            if text and len(text) > 50:
                sources.append(f"--- {f.name} ---\n{text[:10000]}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Ошибка чтения inventory {f.name}: {e}")
    return "\n\n".join(sources)


def _read_screenshots_text() -> str:
    """OCR всех скриншотов, возвращает объединённый текст."""
    if not SCREENSHOTS_DIR.exists():
        return ""
    image_exts = {".png", ".jpg", ".jpeg", ".gif"}
    parts = []
    for f in SCREENSHOTS_DIR.iterdir():
        if not f.is_file() or f.suffix.lower() not in image_exts:
            continue
        try:
            ocr = extract_text_from_image(f)
            if ocr and len(ocr) > 20:
                parts.append(f"--- {f.name} ---\n{ocr[:3000]}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"OCR ошибка {f.name}: {e}")
    return "\n\n".join(parts)


def _build_device_markdown_table(devices: list[DeviceInfo]) -> str:
    lines = ["| Hostname | Модель | IP Mgmt | EOL Статус | VLAN | AAA | NTP | ACL |"]
    lines.append("|----------|--------|---------|------------|------|-----|-----|-----|")
    for d in devices:
        status = d.eol_info.get("status", "Неизвестно")
        eol_icon = "🔴" if status == "EOSL" else ("🟡" if status == "End-of-Sale" else "🟢")
        lines.append(
            f"| {d.hostname} | {d.model} | {d.ip_mgmt} | {eol_icon} {status} | "
            f"{len(d.vlans)} | {'✅' if d.aaa else '❌'} | "
            f"{'✅' if d.ntp_servers else '❌'} | {'✅' if d.acl else '❌'} |"
        )
    return '\n'.join(lines)


def _build_device_detail_text(devices: list[DeviceInfo]) -> str:
    lines = []
    for d in devices[:15]:
        ospf_str = 'Не настроен'
        if d.ospf and d.ospf.get('process_id'):
            ospf_str = f"Process {d.ospf.get('process_id', '?')}, Router ID {d.ospf.get('router_id', '?')}, Area {d.ospf.get('area', '?')}"
        lines.append(f"""
### {d.hostname} ({d.model})
- **IP управления:** {d.ip_mgmt}
- **EOL статус:** {d.eol_info.get('status', '?')} (срок: {d.eol_info.get('eol', '?')})
- **Интерфейсы:** {len(d.interfaces)} шт.
- **VLAN:** {', '.join(f"{v['id']}({v['ip']})" for v in d.vlans[:10]) if d.vlans else 'Нет'}
- **Маршруты:** {len(d.routes)} шт.
- **AAA:** {'Настроен' if d.aaa else '❌ Не настроен'}
- **NTP:** {'Настроен' if d.ntp_servers else '❌ Не настроен'}
- **ACL:** {'Настроены' if d.acl else '❌ Не настроены'}
- **OSPF:** {ospf_str}
- **DHCP Snooping:** {'✅' if d.dhcp_snooping else '❌'}
- **Port Security:** {'✅' if d.port_security else '❌'}
- **BPDU Protection:** {'✅' if d.bpdu_protection else '❌'}
""")
    return '\n'.join(lines)


async def generate_report(prompt: str) -> dict:
    logger.info("=== НАЧАЛО ГЕНЕРАЦИИ ОТЧЁТА ===")

    devices: list[DeviceInfo] = []
    servers: list[ServerInfo] = []
    vm_info: list[VirtualizationInfo] = []
    storage_list: list[StorageInfo] = []
    databases: list[DatabaseInfo] = []
    backups_list: list[BackupInfo] = []
    antivirus_list: list[AntivirusInfo] = []
    firewalls_list: list[NetworkSecurityInfo] = []
    raw_texts: list[tuple[str, str, str]] = []

    if CONFIGS_DIR.exists():
        for f in CONFIGS_DIR.iterdir():
            if not f.is_file():
                continue
            text = extract_text_from_file(f)
            if text and len(text) > 50:
                result, file_type = classify_and_parse(text, f.name)
                if result is None:
                    logger.info(f"  Неопознанный файл: {f.name} ({len(text)} chars)")
                    raw_texts.append((f.name, file_type, text[:3000]))
                    continue

                if isinstance(result, DeviceInfo) and result.hostname:
                    inv = await asyncio.to_thread(find_inventory_by_model, result.model)
                    if inv:
                        result.eol_info = {"eol": inv["eol"], "status": inv["eol_status"], "note": inv.get("specs", "")}
                    devices.append(result)
                    logger.info(f"  Сеть: {result.hostname} ({result.model}) [{file_type}]")
                elif isinstance(result, ServerInfo):
                    servers.append(result)
                    _auto_add_eol(result.model, result.hostname, "server")
                    logger.info(f"  Сервер: {result.hostname} [{file_type}]")
                elif isinstance(result, VirtualizationInfo):
                    vm_info.append(result)
                    _auto_add_eol(result.hypervisor_version, "", "virtualization")
                    logger.info(f"  Виртуализация: {result.hypervisor_type} {result.hypervisor_version} [{file_type}]")
                elif isinstance(result, StorageInfo):
                    storage_list.append(result)
                    _auto_add_eol(result.model, "", "storage")
                    logger.info(f"  СХД/NAS: {result.model} [{file_type}]")
                elif isinstance(result, DatabaseInfo):
                    databases.append(result)
                    _auto_add_eol(result.version, "", "database")
                    logger.info(f"  СУБД: {result.dbms_type} {result.version} [{file_type}]")
                elif isinstance(result, BackupInfo):
                    backups_list.append(result)
                    _auto_add_eol(result.product, "", "backup")
                    logger.info(f"  СРК: {result.product} [{file_type}]")
                elif isinstance(result, AntivirusInfo):
                    antivirus_list.append(result)
                    _auto_add_eol(result.product, "", "antivirus")
                    logger.info(f"  АВ: {result.product} [{file_type}]")
                elif isinstance(result, NetworkSecurityInfo):
                    firewalls_list.append(result)
                    _auto_add_eol(result.firewall_model, "", "firewall")
                    logger.info(f"  МСЭ/VPN: {result.firewall_model} [{file_type}]")
                else:
                    raw_texts.append((f.name, file_type, text[:3000]))
                    logger.info(f"  Прочее: {f.name} [{file_type}]")

    template_text = await asyncio.to_thread(_read_template)
    inventory_text = await asyncio.to_thread(_read_inventory_text)
    screenshots_text = await asyncio.to_thread(_read_screenshots_text)

    template_sections = _extract_template_sections(template_text) if template_text else []

    logger.info(
        f"Итого - Сеть: {len(devices)}, Серверы: {len(servers)}, ВМ: {len(vm_info)}, "
        f"СХД: {len(storage_list)}, СУБД: {len(databases)}, СРК: {len(backups_list)}, "
        f"АВ: {len(antivirus_list)}, МСЭ: {len(firewalls_list)}, "
        f"Скриншотов OCR: {len(screenshots_text)} chars, Шаблон: {len(template_text)} chars"
    )

    # === АНАЛИТИКА ===
    _classify_devices(devices)
    eol_critical = [d for d in devices if d.eol_info.get("status") == "EOSL"]
    eol_warning = [d for d in devices if d.eol_info.get("status") == "End-of-Sale"]
    eol_ok = [d for d in devices if d.eol_info.get("status") == "Актуальное"]
    no_aaa = [d for d in devices if not d.aaa]
    no_ntp = [d for d in devices if not d.ntp_servers]
    no_acl = [d for d in devices if not d.acl]

    aggregated = build_aggregated_summary(devices, servers, vm_info, storage_list, databases, backups_list, antivirus_list, firewalls_list)

    report_sections = []

    # Если есть шаблон — используем LLM для генерации по структуре шаблона
    if template_sections:
        template_structure = "\n".join(
            f"{'#' * s['level']} {s['title']}" for s in template_sections
        )
        device_table = _build_device_markdown_table(devices)
        device_details = _build_device_detail_text(devices)

        issues_list = []
        if no_aaa:
            issues_list.append(f"- **Отсутствует AAA:** {len(no_aaa)} устройств: {', '.join(d.hostname for d in no_aaa)}")
        if no_ntp:
            issues_list.append(f"- **Отсутствует NTP:** {len(no_ntp)} устройств: {', '.join(d.hostname for d in no_ntp)}")
        if no_acl:
            issues_list.append(f"- **Отсутствуют ACL:** {len(no_acl)} устройств: {', '.join(d.hostname for d in no_acl)}")
        if eol_critical:
            issues_list.append(f"- **EOSL:** {len(eol_critical)} устройств с прекращённой поддержкой")
        issues_str = '\n'.join(issues_list) if issues_list else "Критических проблем не выявлено."

        llm_report_prompt = f"""Ты — инженер по аудиту ИТ-инфраструктуры. Сформируй отчёт на русском языке строго по указанной структуре разделов.

СТРУКТУРА ОТЧЁТА (должна быть соблюдена):
{template_structure}

ДАННЫЕ ДЛЯ ЗАПОЛНЕНИЯ:

1. Сетевое оборудование (таблица):
{device_table}

2. Детальная информация по сетевым устройствам:
{device_details}

3. Серверное оборудование ({len(servers)} серверов):
{"".join(f"- {s.hostname}: {s.cpu_model} / RAM {s.ram_total_gb}GB / Диски {s.disk_total_gb}GB ({s.disk_free_pct}% свободно) / RAID {s.raid_level} [{s.raid_status}] / EOL: {s.eol_info.get('status', '?')}" + chr(10) for s in servers[:20]) if servers else "Нет данных" + chr(10)}

4. Виртуализация ({sum(v.vm_count for v in vm_info)} ВМ на {sum(v.hosts_count for v in vm_info)} хостах):
{"".join(f"- {v.hypervisor_type} {v.hypervisor_version}: {v.hosts_count} хостов, {v.vm_count} ВМ, кластер: {v.cluster_name or 'нет'}" + chr(10) for v in vm_info[:10]) if vm_info else "Нет данных" + chr(10)}

5. Системы хранения ({len(storage_list)} устройств, {round(sum(s.total_capacity_gb for s in storage_list)/1024, 1)} TB суммарно):
{"".join(f"- {s.model}: {s.device_type} / {s.total_capacity_gb}GB / RAID {s.raid_level} / Статус: {s.status}" + chr(10) for s in storage_list[:10]) if storage_list else "Нет данных" + chr(10)}

6. СУБД ({len(databases)}):
{"".join(f"- {d.dbms_type} {d.version} на {d.server_name}: Auth={d.auth_mode}, TDE={d.encryption}, HA={d.ha_enabled}" + chr(10) for d in databases[:10]) if databases else "Нет данных" + chr(10)}

7. Система резервного копирования ({len(backups_list)} продуктов):
{"".join(f"- {b.product} {b.version}: репозиторий={b.repo_type}, ошибок={len(b.errors)}, retention={b.retention_days}дн" + chr(10) for b in backups_list[:10]) if backups_list else "Нет данных" + chr(10)}

8. Антивирусная защита ({len(antivirus_list)}):
{"".join(f"- {a.product} {a.version}: централизован={a.central_management}, лицензий={a.total_licenses}, агентов={a.installed_agents}" + chr(10) for a in antivirus_list[:10]) if antivirus_list else "Нет данных" + chr(10)}

9. МСЭ/VPN ({len(firewalls_list)}):
{"".join(f"- {f.firewall_model} {f.firewall_version}: VPN={f.remote_access}, MFA={f.mfa_enabled}, шифрование={f.encryption_type}" + chr(10) for f in firewalls_list[:10]) if firewalls_list else "Нет данных" + chr(10)}

10. EOL-анализ:
- Актуальных: {len(eol_ok)}
- End-of-Sale: {', '.join(d.hostname for d in eol_warning) if eol_warning else 'нет'}
- EOSL: {', '.join(d.hostname for d in eol_critical) if eol_critical else 'нет'}

11. Проблемы безопасности:
{issues_str}

12. Данные со скриншотов:
{screenshots_text[:5000] if screenshots_text else 'Нет данных со скриншотов'}

13. Инвентаризационные данные:
{inventory_text[:5000] if inventory_text else 'Нет данных инвентаризации'}

14. Прочие данные (не классифицированные):
{"".join(f"--- {name} ({ftype}) ---" + chr(10) + txt[:1000] + chr(10) for name, ftype, txt in raw_texts[:5]) if raw_texts else 'Нет'}

15. Исходный запрос оператора:
{prompt[:500]}

ВАЖНЫЕ ТРЕБОВАНИЯ:
- Отчёт должен быть на русском языке, в деловом стиле.
- Строго соблюдай структуру разделов из шаблона.
- Если раздел шаблона подразумевает таблицу — сделай таблицу.
- Используй ВСЕ данные: серверы, виртуализацию, СХД, СУБД, СРК, АВ, МСЭ — для заполнения соответствующих разделов.
- Данные со скриншотов используй для разделов, которые не покрыты конфигами.
- Инвентаризационные данные используй для обогащения характеристик оборудования.
- Каждый раздел начинай с заголовка соответствующего уровня.
- Не добавляй разделов, которых нет в структуре.
- Если данных для какого-то раздела недостаточно — напиши "Нет данных" или "Требуется дополнительный сбор информации".
"""
        try:
            llm_result = await asyncio.to_thread(
                query_ollama, llm_report_prompt,
                temperature=0.3, num_predict=8000, timeout=600
            )
            report_sections.append(llm_result)
            logger.info("LLM-генерация по шаблону выполнена")
        except RuntimeError as e:
            logger.error(f"LLM ошибка: {e}")
            report_sections.append(f"*Ошибка LLM-генерации: {e}*\n")
            # Fallback на стандартную структуру
            template_sections = []

    # Если шаблона нет или LLM упал — стандартная структура
    if not template_sections:
        report_sections.append(f"""# ОТЧЁТ ПО АУДИТУ ИТ-ИНФРАСТРУКТУРЫ

**Дата:** {datetime.now(timezone.utc).strftime('%d.%m.%Y')}
**Основание:** {prompt[:200]}

---

## 1. ОБЩИЕ СВЕДЕНИЯ

| Параметр | Значение |
|----------|----------|
| Сетевых устройств | {len(devices)} |
| Серверов | {len(servers)} |
| Хостов виртуализации | {sum(v.hosts_count for v in vm_info)} |
| Виртуальных машин | {sum(v.vm_count for v in vm_info)} |
| Устройств хранения | {len(storage_list)} |
| СУБД | {len(databases)} |
| Продуктов СРК | {len(backups_list)} |
| Антивирусных решений | {len(antivirus_list)} |
| МСЭ/VPN | {len(firewalls_list)} |
| Актуальное оборудование | {len(eol_ok)} |
| End-of-Sale | {len(eol_warning)} |
| EOSL (критическое) | {len(eol_critical)} |

""")

        report_sections.append("## 2. СОСТАВ СЕТЕВОГО ОБОРУДОВАНИЯ\n\n")
        report_sections.append(_build_device_markdown_table(devices) + "\n\n")

        report_sections.append("\n## 3. СЕРВЕРНОЕ ОБОРУДОВАНИЕ\n\n")
        if servers:
            report_sections.append("| Сервер | CPU | RAM (GB) | Диски (GB) | RAID | Свободно (%) | EOL |\n")
            report_sections.append("|--------|-----|----------|------------|------|-------------|-----|\n")
            for s in servers[:20]:
                report_sections.append(
                    f"| {s.hostname} | {s.cpu_model[:30]} | {s.ram_total_gb} | {s.disk_total_gb} | "
                    f"{s.raid_level} | {s.disk_free_pct}% | {s.eol_info.get('status', '?')} |\n"
                )
        else:
            report_sections.append("Данные о серверах не загружены.\n")

        report_sections.append("\n## 4. ВИРТУАЛИЗАЦИЯ\n\n")
        if vm_info:
            for v in vm_info[:10]:
                report_sections.append(f"### {v.hypervisor_type} {v.hypervisor_version}\n")
                report_sections.append(f"- Хостов: {v.hosts_count}\n")
                report_sections.append(f"- ВМ: {v.vm_count}\n")
                report_sections.append(f"- Кластер: {v.cluster_name or 'не настроен'}\n")
                report_sections.append(f"- HA: {'включён' if v.ha_enabled else 'не настроен'}\n\n")
        else:
            report_sections.append("Данные о виртуализации не загружены.\n")

        report_sections.append("\n## 5. СИСТЕМЫ ХРАНЕНИЯ ДАННЫХ\n\n")
        if storage_list:
            report_sections.append("| Модель | Тип | Ёмкость (GB) | Использовано | RAID | Статус |\n")
            report_sections.append("|--------|-----|-------------|-------------|------|--------|\n")
            for s in storage_list[:15]:
                report_sections.append(
                    f"| {s.model[:30]} | {s.device_type} | {s.total_capacity_gb} | {s.used_capacity_gb} | "
                    f"{s.raid_level} | {s.status} |\n"
                )
        else:
            report_sections.append("Данные о системах хранения не загружены.\n")

        report_sections.append("\n## 6. АНАЛИЗ ЖИЗНЕННОГО ЦИКЛА\n\n")
        if eol_critical:
            table = "### Критическое (EOSL)\n| Устройство | Модель | EOL | Риск |\n|---|---|---|---|\n"
            for d in eol_critical:
                table += f"| {d.hostname} | {d.model} | {d.eol_info.get('eol', '?')} | {d.eol_info.get('note', '')} |\n"
            report_sections.append(table)
        if eol_warning:
            table = "### End-of-Sale\n| Устройство | Модель | EOL |\n|---|---|---|\n"
            for d in eol_warning:
                table += f"| {d.hostname} | {d.model} | {d.eol_info.get('eol', '?')} |\n"
            report_sections.append(table)
        if not eol_critical and not eol_warning:
            report_sections.append("Актуальное оборудование, критических позиций EOL не выявлено.\n")

        report_sections.append("\n## 7. ПРОБЛЕМЫ БЕЗОПАСНОСТИ\n\n")
        if no_aaa:
            report_sections.append(f"- Отсутствует AAA: {len(no_aaa)} устройств\n")
        if no_ntp:
            report_sections.append(f"- Отсутствует NTP: {len(no_ntp)} устройств\n")
        if no_acl:
            report_sections.append(f"- Отсутствуют ACL: {len(no_acl)} устройств\n")
        if aggregated["critical_issues"]:
            for issue in aggregated["critical_issues"]:
                report_sections.append(f"- {issue}\n")
        if not no_aaa and not no_ntp and not no_acl and not aggregated["critical_issues"]:
            report_sections.append("Критических проблем не выявлено.\n")

        report_sections.append("\n## 8. ИНФРАСТРУКТУРНЫЕ СЕРВИСЫ\n\n")
        report_sections.append(f"### СУБД ({len(databases)})\n")
        if databases:
            for d in databases[:10]:
                report_sections.append(f"- {d.dbms_type} {d.version} на {d.server_name}: Auth={d.auth_mode}, TDE={d.encryption}, HA={d.ha_enabled}\n")
        else:
            report_sections.append("Данные о СУБД не загружены.\n")

        report_sections.append(f"\n### Система резервного копирования ({len(backups_list)})\n")
        if backups_list:
            for b in backups_list[:10]:
                report_sections.append(f"- {b.product} {b.version}: репозиторий={b.repo_type}, ошибок={len(b.errors)}\n")
        else:
            report_sections.append("Данные о СРК не загружены.\n")

        report_sections.append(f"\n### Антивирусная защита ({len(antivirus_list)})\n")
        if antivirus_list:
            for a in antivirus_list[:10]:
                report_sections.append(f"- {a.product} {a.version}: централизован={a.central_management}, лицензий={a.total_licenses}\n")
        else:
            report_sections.append("Данные об антивирусной защите не загружены.\n")

        report_sections.append(f"\n### МСЭ/VPN ({len(firewalls_list)})\n")
        if firewalls_list:
            for f in firewalls_list[:10]:
                report_sections.append(f"- {f.firewall_model} {f.firewall_version}: VPN={f.remote_access}, MFA={f.mfa_enabled}\n")
        else:
            report_sections.append("Данные о МСЭ/VPN не загружены.\n")

        if screenshots_text:
            report_sections.append("\n## 9. ДАННЫЕ СИСТЕМЫ СЛУЖБЫ КАТАЛОГОВ (ADDS)\n\n")
            try:
                adds_prompt = (
                    f"Проанализируй данные со скриншотов систем Active Directory (ADDS), DHCP, DNS, "
                    f"безопасности Windows и производительности. Составь связный аналитический обзор "
                    f"на русском языке (3-5 абзацев) с выводами и рекомендациями.\n\n"
                    f"Данные OCR:\n{screenshots_text[:8000]}"
                )
                adds_analysis = await asyncio.to_thread(
                    query_ollama, adds_prompt,
                    temperature=0.3, num_predict=2000, timeout=300
                )
                report_sections.append(adds_analysis + "\n\n")
                logger.info("ADDS-анализ по OCR выполнен")
            except RuntimeError as e:
                logger.warning(f"ADDS-анализ не выполнен: {e}")
                report_sections.append("На основе OCR-распознавания скриншотов:\n\n")
                report_sections.append(f"```\n{screenshots_text[:10000]}\n```\n\n")

        if inventory_text:
            report_sections.append("\n## 10. ИНВЕНТАРИЗАЦИОННЫЕ ДАННЫЕ\n\n")
            report_sections.append(f"```\n{inventory_text[:5000]}\n```\n\n")

        try:
            conclusion_parts = [
                (f"Всего сетевых устройств: {len(devices)}, серверов: {len(servers)}, "
                f"хостов виртуализации: {sum(v.hosts_count for v in vm_info)}, ВМ: {sum(v.vm_count for v in vm_info)}, "
                f"устройств хранения: {len(storage_list)}, СУБД: {len(databases)}. "
                f"EOSL: {len(eol_critical)}, End-of-Sale: {len(eol_warning)}. "
                f"Без AAA: {len(no_aaa)}, без NTP: {len(no_ntp)}, без ACL: {len(no_acl)}.")
            ]
            if aggregated["critical_issues"]:
                conclusion_parts.append(f"Критические проблемы: {'; '.join(aggregated['critical_issues'])}.")
            conclusion_prompt = "Напиши итоговое заключение по аудиту ИТ-инфраструктуры (5-8 предложений на русском): " + " ".join(conclusion_parts)
            if screenshots_text and len(screenshots_text) > 100:
                conclusion_prompt += ". Также проанализированы скриншоты ADDS, DHCP, DNS, безопасности."
            conclusion = await asyncio.to_thread(
                query_ollama, conclusion_prompt,
                temperature=0.3, num_predict=1000, timeout=120
            )
            report_sections.append("\n## 11. ЗАКЛЮЧЕНИЕ\n\n" + conclusion + "\n")
        except RuntimeError:
            report_sections.append("\n## 11. ЗАКЛЮЧЕНИЕ\n\n*Не сгенерировано*\n")

        report_sections.append(f"\n---\n*Отчёт сгенерирован {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M:%S')}*\n")

    # === СОХРАНЕНИЕ ===
    full_report = "\n".join(report_sections)
    filename = f"audit_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
    path = OUTPUT_DIR / filename
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(full_report)

    await asyncio.to_thread(save_audit_history,
        filename, prompt,
        len(devices) + len(servers) + len(vm_info), len(eol_critical),
        len(eol_warning), len(aggregated["critical_issues"])
    )

    logger.info(f"ОТЧЁТ СОХРАНЁН: {path} ({len(full_report)} chars)")

    return {
        "status": "success",
        "report_file": filename,
        "path": str(path),
        "content_preview": full_report[:500] + "...",
        "devices": len(devices),
        "servers": len(servers),
        "virtual_hosts": sum(v.hosts_count for v in vm_info),
        "vms": sum(v.vm_count for v in vm_info),
        "storage": len(storage_list),
        "databases": len(databases),
        "backups": len(backups_list),
        "antivirus": len(antivirus_list),
        "firewalls": len(firewalls_list),
        "eol_critical": len(eol_critical),
        "eol_warning": len(eol_warning),
        "issues_found": len(aggregated["critical_issues"]),
    }
