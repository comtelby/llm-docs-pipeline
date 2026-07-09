import asyncio
import re
import logging
from datetime import datetime


import aiofiles

from src.config import CONFIGS_DIR, SCREENSHOTS_DIR, SAMPLES_DIR, INVENTORY_DIR, OUTPUT_DIR
from src.parser import (
    parse_device_config, extract_text_from_image,
    extract_text_from_file
)
from src.llm import query_ollama
from src.database import save_audit_history, find_inventory_by_model
from src.models import DeviceInfo

logger = logging.getLogger(__name__)


def _classify_devices(devices: list[DeviceInfo]) -> dict:
    core = [d for d in devices if any(k in d.hostname.lower() for k in ["core", "5510", "s6730"])]
    dist = [d for d in devices if any(k in d.hostname.lower() for k in ["hp5412", "hp3500"])]
    access = [d for d in devices if any(k in d.hostname.lower() for k in ["2530", "2620", "5120", "5731"])]
    edge = [d for d in devices if any(k in d.hostname.lower() for k in ["c4331", "h6121", "asa"])]
    return {"core": core, "dist": dist, "access": access, "edge": edge}


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
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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

    # === ЧТЕНИЕ ВСЕХ ДАННЫХ ===
    devices: list[DeviceInfo] = []

    # Парсинг конфигов (все поддерживаемые форматы)
    if CONFIGS_DIR.exists():
        for f in CONFIGS_DIR.iterdir():
            if not f.is_file():
                continue
            text = extract_text_from_file(f)
            if text and len(text) > 100:
                device = parse_device_config(text, f.name)
                if device.hostname:
                    inv = await asyncio.to_thread(find_inventory_by_model, device.model)
                    if inv:
                        device.eol_info = {"eol": inv["eol"], "status": inv["eol_status"], "note": inv.get("specs", "")}
                    devices.append(device)
                    logger.info(f"  Устройство: {device.hostname} ({device.model}) из {f.name}")
                else:
                    logger.info(f"  Inventory/документ (не конфиг): {f.name} ({len(text)} chars)")

    # Чтение данных
    template_text = await asyncio.to_thread(_read_template)
    inventory_text = await asyncio.to_thread(_read_inventory_text)
    screenshots_text = await asyncio.to_thread(_read_screenshots_text)

    # Извлечение структуры шаблона
    template_sections = _extract_template_sections(template_text) if template_text else []

    logger.info(f"Устройств: {len(devices)}, Инвентаризации: {len(inventory_text)} chars, "
                f"Скриншотов OCR: {len(screenshots_text)} chars, Шаблон: {len(template_text)} chars, "
                f"Разделов шаблона: {len(template_sections)}")

    # === АНАЛИТИКА ===
    groups = _classify_devices(devices)
    eol_critical = [d for d in devices if d.eol_info.get("status") == "EOSL"]
    eol_warning = [d for d in devices if d.eol_info.get("status") == "End-of-Sale"]
    eol_ok = [d for d in devices if d.eol_info.get("status") == "Актуальное"]
    no_aaa = [d for d in devices if not d.aaa]
    no_ntp = [d for d in devices if not d.ntp_servers]
    no_acl = [d for d in devices if not d.acl]

    # === ФОРМИРОВАНИЕ ОТЧЁТА ===
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

1. Список устройств (таблица):
{device_table}

2. Детальная информация по устройствам:
{device_details}

3. EOL-анализ:
- Актуальных: {len(eol_ok)}
- End-of-Sale: {', '.join(d.hostname for d in eol_warning) if eol_warning else 'нет'}
- EOSL: {', '.join(d.hostname for d in eol_critical) if eol_critical else 'нет'}

4. Проблемы безопасности:
{issues_str}

5. Данные со скриншотов:
{screenshots_text[:5000] if screenshots_text else 'Нет данных со скриншотов'}

6. Инвентаризационные данные:
{inventory_text[:5000] if inventory_text else 'Нет данных инвентаризации'}

7. Исходный запрос оператора:
{prompt[:500]}

ВАЖНЫЕ ТРЕБОВАНИЯ:
- Отчёт должен быть на русском языке, в деловом стиле.
- Строго соблюдай структуру разделов из шаблона.
- Если раздел шаблона подразумевает таблицу — сделай таблицу.
- Данные со скриншотов используй для разделов, которые не покрыты конфигами (например, Active Directory, серверы, информационные системы).
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

**Дата:** {datetime.now().strftime('%d.%m.%Y')}
**Основание:** {prompt[:200]}

---

## 1. ОБЩИЕ СВЕДЕНИЯ

| Параметр | Значение |
|----------|----------|
| Всего устройств | {len(devices)} |
| Ядро/агрегация | {len(groups['core'])} |
| Распределение | {len(groups['dist'])} |
| Доступ | {len(groups['access'])} |
| Периметр/WAN | {len(groups['edge'])} |
| Актуальное оборудование | {len(eol_ok)} |
| End-of-Sale | {len(eol_warning)} |
| EOSL (критическое) | {len(eol_critical)} |
| Скриншотов обработано | {len(screenshots_text)} |

""")

        report_sections.append("## 2. СОСТАВ СЕТЕВОГО ОБОРУДОВАНИЯ\n\n")
        report_sections.append(_build_device_markdown_table(devices) + "\n\n")

        report_sections.append("\n## 3. ДЕТАЛЬНЫЙ АНАЛИЗ УСТРОЙСТВ\n\n")
        detail_text = _build_device_detail_text(devices)

        try:
            llm_analysis = await asyncio.to_thread(
                query_ollama,
                f"Проанализируй сетевые устройства и напиши краткое описание каждого (2-3 предложения на русском):\n\n{detail_text}\n\nДля каждого укажи роль в сети.",
                temperature=0.3, num_predict=3000, timeout=300
            )
            report_sections.append(llm_analysis)
        except RuntimeError as e:
            report_sections.append(f"*Анализ не выполнен: {e}*\n")

        report_sections.append("\n## 4. АНАЛИЗ ЖИЗНЕННОГО ЦИКЛА\n\n")
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

        report_sections.append("\n## 5. ПРОБЛЕМЫ БЕЗОПАСНОСТИ\n\n")
        if no_aaa:
            report_sections.append(f"- Отсутствует AAA: {len(no_aaa)} устройств\n")
        if no_ntp:
            report_sections.append(f"- Отсутствует NTP: {len(no_ntp)} устройств\n")
        if no_acl:
            report_sections.append(f"- Отсутствуют ACL: {len(no_acl)} устройств\n")
        if not no_aaa and not no_ntp and not no_acl:
            report_sections.append("Критических проблем не выявлено.\n")

        # Раздел: данные со скриншотов (ADDS, серверы, ИС)
        if screenshots_text:
            report_sections.append("\n## 6. ДАННЫЕ СИСТЕМЫ СЛУЖБЫ КАТАЛОГОВ (ADDS)\n\n")
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

        # Раздел: инвентаризационные данные
        if inventory_text:
            report_sections.append("\n## 7. ИНВЕНТАРИЗАЦИОННЫЕ ДАННЫЕ\n\n")
            report_sections.append(f"```\n{inventory_text[:5000]}\n```\n\n")

        try:
            conclusion_prompt = "Напиши итоговое заключение по аудиту ИТ-инфраструктуры (3-5 предложений на русском):"
            conclusion_prompt += f" всего устройств {len(devices)}, EOSL {len(eol_critical)}, End-of-Sale {len(eol_warning)}, "
            conclusion_prompt += f"устройства без AAA: {len(no_aaa)}, без NTP: {len(no_ntp)}, без ACL: {len(no_acl)}, "
            conclusion_prompt += f"ключевые: {', '.join(d.hostname for d in devices[:5])}"
            if screenshots_text and len(screenshots_text) > 100:
                conclusion_prompt += ". Также проанализированы скриншоты ADDS, DHCP, DNS, безопасности"
            if inventory_text and len(inventory_text) > 100:
                conclusion_prompt += ". Использованы справочные данные inventory"
            conclusion = await asyncio.to_thread(
                query_ollama, conclusion_prompt,
                temperature=0.3, num_predict=1000, timeout=120
            )
            report_sections.append("\n## 8. ЗАКЛЮЧЕНИЕ\n\n" + conclusion + "\n")
        except RuntimeError:
            report_sections.append("\n## 8. ЗАКЛЮЧЕНИЕ\n\n*Не сгенерировано*\n")

        report_sections.append(f"\n---\n*Отчёт сгенерирован {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*\n")

    # === СОХРАНЕНИЕ ===
    full_report = "\n".join(report_sections)
    filename = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    path = OUTPUT_DIR / filename
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(full_report)

    await asyncio.to_thread(save_audit_history,
        filename, prompt,
        len(devices), len(eol_critical),
        len(eol_warning), len([i for i in [no_aaa, no_ntp, no_acl, eol_critical] if i])
    )

    logger.info(f"ОТЧЁТ СОХРАНЁН: {path} ({len(full_report)} chars)")

    return {
        "status": "success",
        "report_file": filename,
        "path": str(path),
        "content_preview": full_report[:500] + "...",
        "devices": len(devices),
        "eol_critical": len(eol_critical),
        "eol_warning": len(eol_warning),
        "issues_found": len([i for i in [no_aaa, no_ntp, no_acl, eol_critical] if i])
    }
