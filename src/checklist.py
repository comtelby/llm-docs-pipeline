import csv
import logging
from pathlib import Path

from src.models import AuditProgress, ChecklistItem

logger = logging.getLogger(__name__)

SECTION_MAP = {
    "1": "Общие положения",
    "2": "Осмотр помещения серверной и сетевых устройств",
    "3": "Серверное оборудование",
    "4": "Виртуализация",
    "5": "Система резервного копирования (СРК)",
    "6": "Системы хранения данных (СХД), NAS и SAN-сети",
    "7": "Инфраструктурные сервисы и ADDS",
    "8": "Корпоративная сеть передачи данных (КСПД) и МСЭ",
    "9": "Антивирусная защита и СКЗИ",
    "10": "Отчётность и документация",
    "11": "Система мониторинга инфраструктуры",
    "12": "Система управления базами данных (СУБД)",
    "13": "Веб-серверы и веб-приложения",
    "14": "Система автоматизированного рабочего места (АРМ)",
    "15": "Телефония (VoIP, IP-PBX)",
    "16": "Документооборот (ЭДО, СЭД)",
    "17": "Система администрирования (привилегированный доступ)",
    "18": "Заключительный этап",
}

DATA_TYPE_HINTS = {
    "1.1": ["text"],
    "1.2": ["xlsx", "xls", "csv"],
    "1.3": ["docx", "doc", "pdf"],
    "2.1": ["png", "jpg", "jpeg"],
    "2.2": ["png", "jpg", "jpeg"],
    "2.3": ["txt", "csv"],
    "2.7": ["txt", "cfg", "conf"],
    "3.1": ["png", "jpg", "jpeg"],
    "3.2": ["txt", "cfg"],
    "3.3": ["txt", "cfg"],
    "3.6": ["txt", "cfg"],
    "4.1": ["txt", "cfg"],
    "4.4": ["xlsx", "csv", "txt"],
    "4.5": ["txt", "csv"],
    "5.1": ["docx", "doc", "txt"],
    "5.2": ["txt", "csv", "xlsx"],
    "5.5": ["txt", "csv"],
    "5.10": ["xlsx", "csv", "txt"],
    "6.1": ["txt", "cfg"],
    "6.3": ["txt", "csv"],
    "7.9": ["png", "jpg", "jpeg"],
    "7.10": ["xlsx", "pdf"],
    "7.11": ["xlsx", "pdf"],
    "7.22": ["txt", "cfg"],
    "8.1": ["txt", "cfg"],
    "8.4": ["txt", "cfg"],
    "8.6": ["txt", "cfg"],
    "8.12": ["txt", "cfg"],
    "9.1": ["txt", "cfg"],
    "9.10": ["txt", "csv"],
    "9.27": ["txt", "cfg"],
    "11.1": ["txt", "csv"],
    "12.1": ["txt", "cfg"],
    "12.5": ["txt"],
    "12.6": ["txt", "csv"],
    "13.1": ["txt", "cfg"],
    "14.1": ["xlsx", "csv"],
    "14.3": ["xlsx", "csv"],
}


def parse_checklist_csv(csv_path: Path) -> list[ChecklistItem]:
    """Парсит CSV-файл чеклиста аудита."""
    items = []
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                number = row.get("№", "").strip().rstrip(".")
                if not number or not any(c.isdigit() for c in number):
                    continue

                completed_raw = row.get("Отметка о выполнении", "").strip().upper()
                completed = completed_raw == "ИСТИНА"

                data_added_raw = row.get("Добавить данные", "").strip().upper()
                data_added = data_added_raw == "ИСТИНА"

                item = ChecklistItem(
                    number=number,
                    stage=row.get("Этап", "").strip(),
                    action=row.get("Действие", "").strip(),
                    result=row.get("Результат / Фиксация", "").strip(),
                    faq=row.get("FAQ", "").strip(),
                    completed=completed,
                    data_added=data_added,
                    issues=row.get("Замечания", "").strip(),
                )
                items.append(item)
    except (OSError, csv.Error) as e:
        logger.error(f"Checklist parse error: {e}")
    return items


def get_section_number(item_number: str) -> str:
    """Извлекает номер раздела из номера пункта (3.2 -> 3)."""
    parts = item_number.split(".")
    return parts[0] if parts else item_number


def get_expected_data_types(item_number: str) -> list[str]:
    """Возвращает ожидаемые типы данных для пункта чеклиста."""
    return DATA_TYPE_HINTS.get(item_number, [])


def calculate_progress(items: list[ChecklistItem]) -> AuditProgress:
    """Рассчитывает прогресс аудита по чеклисту."""
    total = len(items)
    completed = sum(1 for i in items if i.completed)
    data_added = sum(1 for i in items if i.data_added)
    issues = sum(1 for i in items if i.issues)

    sections = {}
    for item in items:
        sec = get_section_number(item.number)
        if sec not in sections:
            sections[sec] = {"total": 0, "completed": 0, "data_added": 0, "issues": 0}
        sections[sec]["total"] += 1
        if item.completed:
            sections[sec]["completed"] += 1
        if item.data_added:
            sections[sec]["data_added"] += 1
        if item.issues:
            sections[sec]["issues"] += 1

    missing = []
    for item in items:
        if not item.completed and not item.data_added:
            expected_types = get_expected_data_types(item.number)
            if expected_types:
                missing.append({
                    "number": item.number,
                    "action": item.action[:80],
                    "expected_types": expected_types,
                    "section": SECTION_MAP.get(get_section_number(item.number), "Неизвестный раздел"),
                })

    return AuditProgress(
        total_items=total,
        completed_items=completed,
        data_added_items=data_added,
        issues_count=issues,
        sections_progress=sections,
        missing_data=missing[:50],
    )


def match_files_to_checklist(items: list[ChecklistItem], file_list: list[str]) -> list[dict]:
    """Сопоставляет загруженные файлы с пунктами чеклиста на основе расширений и ключевых слов."""
    matches = []

    keyword_map = {
        "server": ["3.2", "3.3", "3.5", "3.6"],
        "esxi": ["4.1", "4.2", "4.5"],
        "vmware": ["4.1", "4.2", "4.5"],
        "hyper": ["4.1", "4.2", "4.5"],
        "storage": ["6.1", "6.3", "6.4"],
        "nas": ["6.10"],
        "backup": ["5.2", "5.10", "5.13"],
        "veeam": ["5.2", "5.10"],
        "acronis": ["5.2", "5.10"],
        "kaspersky": ["9.1", "9.4", "9.7"],
        "antivirus": ["9.1", "9.4"],
        "firewall": ["8.9", "8.10", "8.12"],
        "vpn": ["8.16", "8.20"],
        "database": ["12.1", "12.5", "12.6"],
        "sql": ["12.1", "12.5"],
        "postgresql": ["12.1", "12.5"],
        "active_directory": ["7.9", "7.10", "7.11"],
        "admanager": ["7.9", "7.10"],
        "monitoring": ["11.1", "11.8"],
        "zabbix": ["11.1"],
        "prtg": ["11.1"],
        "config": ["2.7", "8.1", "8.4", "8.6"],
        "screenshot": ["2.1", "2.2", "7.9", "11.8"],
        "inventory": ["1.2", "2.2"],
    }

    for filename in file_list:
        fn_lower = filename.lower()
        matched_items = set()

        for keyword, item_numbers in keyword_map.items():
            if keyword in fn_lower:
                for num in item_numbers:
                    matched_items.add(num)

        for item in items:
            if item.number in matched_items or any(
                kw in item.action.lower() and kw in fn_lower
                for kw in ["config", "backup", "server", "database"]
            ):
                matches.append({
                    "file": filename,
                    "checklist_item": item.number,
                    "section": SECTION_MAP.get(get_section_number(item.number), ""),
                    "action": item.action[:100],
                })

    return matches


def export_checklist_status(items: list[ChecklistItem]) -> str:
    """Экспортирует статус чеклиста в CSV-формат."""
    lines = ["№;Этап;Действие;Результат / Фиксация;Отметка о выполнении;Добавить данные;Замечания"]
    for item in items:
        status = "ИСТИНА" if item.completed else "ЛОЖЬ"
        data = "ИСТИНА" if item.data_added else "ЛОЖЬ"
        lines.append(
            f"{item.number};{item.stage};{item.action};{item.result};{status};{data};{item.issues}"
        )
    return "\n".join(lines)


def get_checklist_summary(items: list[ChecklistItem]) -> dict:
    """Возвращает краткую сводку по чеклисту."""
    progress = calculate_progress(items)

    sections_summary = []
    for sec_num in sorted(SECTION_MAP.keys(), key=lambda x: int(x)):
        sec_name = SECTION_MAP[sec_num]
        sec_data = progress.sections_progress.get(sec_num, {"total": 0, "completed": 0, "data_added": 0, "issues": 0})
        pct = round((sec_data["completed"] / sec_data["total"] * 100) if sec_data["total"] > 0 else 0, 1)
        sections_summary.append({
            "section": sec_num,
            "name": sec_name,
            "total": sec_data["total"],
            "completed": sec_data["completed"],
            "data_added": sec_data["data_added"],
            "issues": sec_data["issues"],
            "completion_pct": pct,
        })

    overall_pct = round((progress.completed_items / progress.total_items * 100) if progress.total_items > 0 else 0, 1)

    return {
        "total_items": progress.total_items,
        "completed_items": progress.completed_items,
        "data_added_items": progress.data_added_items,
        "issues_count": progress.issues_count,
        "overall_completion_pct": overall_pct,
        "sections": sections_summary,
        "missing_data_count": len(progress.missing_data),
        "missing_data_preview": progress.missing_data[:10],
    }
