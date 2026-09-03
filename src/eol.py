import logging

from src.config import DB_PATH

logger = logging.getLogger(__name__)

EOL_DATABASE = {
    "avaya ip office 500v2": {"eol": "31.12.2020", "status": "EOSL", "note": "Поддержка прекращена", "vendor": "Avaya", "category": "telephony"},
    "hp 2620-24": {"eol": "2020", "status": "End-of-Sale", "note": "Обновлений нет", "vendor": "HP", "category": "network"},
    "hp procurve 3500-24": {"eol": "31.10.2019", "status": "EOSL", "note": "Производство прекращено", "vendor": "HP", "category": "network"},
    "hpe 5120 16g": {"eol": "2019", "status": "End-of-Sale", "note": "Заменён на серию 5130", "vendor": "HPE", "category": "network"},
    "hpe 5510": {"eol": "2021", "status": "End-of-Sale", "note": "Заменён на серию 5520", "vendor": "HPE", "category": "network"},
    "huawei 5731": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2029", "vendor": "Huawei", "category": "network"},
    "huawei s6730": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2031+", "vendor": "Huawei", "category": "network"},
    "huawei ac6508": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "Huawei", "category": "network"},
    "huawei ar6121e": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2030+", "vendor": "Huawei", "category": "network"},
    "huawei oceanstor dorado 2000": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "Huawei", "category": "storage"},
    "huawei oceanstor 5000": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2028+", "vendor": "Huawei", "category": "storage"},
    "huawei oceanstor 6000": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2030+", "vendor": "Huawei", "category": "storage"},
    "ibm system x3650 m5": {"eol": "2019", "status": "End-of-Sale", "note": "Поддержка прекращена (Lenovo)", "vendor": "IBM", "category": "server"},
    "ibm system x3630 m4": {"eol": "2019", "status": "EOSL", "note": "Полное прекращение поддержки", "vendor": "IBM", "category": "server"},
    "ibm ts3200": {"eol": "31.12.2023", "status": "EOSL", "note": "Поддержка прекращена", "vendor": "IBM", "category": "storage"},
    "synology rs814+": {"eol": "01.10.2024", "status": "EOSL", "note": "DSM 6.2, обновлений нет", "vendor": "Synology", "category": "storage"},
    "synology rs815+": {"eol": "01.10.2024", "status": "EOSL", "note": "DSM 6.2, обновлений нет", "vendor": "Synology", "category": "storage"},
    "synology rx415": {"eol": "01.10.2024", "status": "EOSL", "note": "Не поддерживает DSM 7.x", "vendor": "Synology", "category": "storage"},
    "synology rx1217": {"eol": "2023", "status": "End-of-Sale", "note": "Снят с производства", "vendor": "Synology", "category": "storage"},
    "synology rs3618xs": {"eol": "2022", "status": "End-of-Sale", "note": "Снят с продаж", "vendor": "Synology", "category": "storage"},
    "synology sa3200d": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "Synology", "category": "storage"},
    "cisco asa 5516": {"eol": "2022", "status": "End-of-Sale", "note": "Последний патч: август 2024", "vendor": "Cisco", "category": "firewall"},
    "cisco isr4331": {"eol": "2022", "status": "End-of-Sale", "note": "SW поддержка до 2026", "vendor": "Cisco", "category": "network"},
    "cisco air-ct-3504": {"eol": "2021", "status": "End-of-Sale", "note": "Заменён на 3504", "vendor": "Cisco", "category": "network"},
    "hp 5412r": {"eol": "2020", "status": "End-of-Sale", "note": "Поддержка ограничена", "vendor": "HP", "category": "network"},
    "hp aruba 2530": {"eol": "2021", "status": "End-of-Sale", "note": "Заменён на 2540", "vendor": "HP", "category": "network"},
    "lenovo b6505": {"eol": "2020", "status": "End-of-Sale", "note": "Снят с производства", "vendor": "Lenovo", "category": "storage"},
    "lenovo ds2200": {"eol": "2023", "status": "EOSL", "note": "Полное прекращение поддержки", "vendor": "Lenovo", "category": "storage"},
    "dell r230": {"eol": "31.03.2023", "status": "EOSL", "note": "iDRAC 8, обновлений нет", "vendor": "Dell", "category": "server"},
    "dell r640": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2027", "vendor": "Dell", "category": "server"},
    "dell r740": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2027", "vendor": "Dell", "category": "server"},
    "dell r750": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2030+", "vendor": "Dell", "category": "server"},
    "dell r650": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2032+", "vendor": "Dell", "category": "server"},
    "dell r750xs": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2030+", "vendor": "Dell", "category": "server"},
    "dell powerstore 500": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "Dell", "category": "storage"},
    "dell emc powerprotect dd": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "Dell", "category": "storage"},
    "hp proliant dl360 gen10": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2027", "vendor": "HPE", "category": "server"},
    "hp proliant dl380 gen10": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2027", "vendor": "HPE", "category": "server"},
    "hp proliant dl360 gen11": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2030+", "vendor": "HPE", "category": "server"},
    "hp proliant dl380 gen11": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2030+", "vendor": "HPE", "category": "server"},
    "hpe alletra 5000": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "HPE", "category": "storage"},
    "hpe nimble hf": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "HPE", "category": "storage"},
    "lenovo thinksystem sr650 v2": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2028+", "vendor": "Lenovo", "category": "server"},
    "lenovo thinksystem sr630 v2": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2028+", "vendor": "Lenovo", "category": "server"},
    "lenovo thinksystem dm5000h": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "Lenovo", "category": "storage"},
    "fortinet fortigate 60f": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2029+", "vendor": "Fortinet", "category": "firewall"},
    "fortinet fortigate 100f": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2029+", "vendor": "Fortinet", "category": "firewall"},
    "fortinet fortigate 200f": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2029+", "vendor": "Fortinet", "category": "firewall"},
    "vmware esxi 6.5": {"eol": "15.04.2023", "status": "EOSL", "note": "Полное прекращение поддержки", "vendor": "VMware", "category": "virtualization"},
    "vmware esxi 6.7": {"eol": "15.10.2024", "status": "End-of-Sale", "note": "Только критические патчи до 2025", "vendor": "VMware", "category": "virtualization"},
    "vmware esxi 7.0": {"eol": "02.04.2025", "status": "End-of-Sale", "note": "Приоритетная поддержка до 2025", "vendor": "VMware", "category": "virtualization"},
    "vmware esxi 8.0": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2027+", "vendor": "VMware", "category": "virtualization"},
    "microsoft hyper-v 2016": {"eol": "12.01.2027", "status": "Актуальное", "note": "Поддержка до 2027", "vendor": "Microsoft", "category": "virtualization"},
    "microsoft hyper-v 2019": {"eol": "09.01.2029", "status": "Актуальное", "note": "Поддержка до 2029", "vendor": "Microsoft", "category": "virtualization"},
    "microsoft hyper-v 2022": {"eol": "13.10.2031", "status": "Актуальное", "note": "Поддержка до 2031", "vendor": "Microsoft", "category": "virtualization"},
    "proxmox ve 7": {"eol": "01.07.2024", "status": "EOSL", "note": "Комьюнити-поддержка прекращена", "vendor": "Proxmox", "category": "virtualization"},
    "proxmox ve 8": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2027", "vendor": "Proxmox", "category": "virtualization"},
    "veeam backup & replication 11": {"eol": "28.02.2024", "status": "End-of-Sale", "note": "Только критические патчи", "vendor": "Veeam", "category": "backup"},
    "veeam backup & replication 12": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2027+", "vendor": "Veeam", "category": "backup"},
    "acronis cyber protect 15": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2026", "vendor": "Acronis", "category": "backup"},
    "kaspersky security center 14": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2027", "vendor": "Kaspersky", "category": "antivirus"},
    "kaspersky security center 15": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2029+", "vendor": "Kaspersky", "category": "antivirus"},
    "zabbix 6.0 lts": {"eol": "28.02.2025", "status": "End-of-Sale", "note": "Только критические патчи", "vendor": "Zabbix", "category": "monitoring"},
    "zabbix 6.4": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2025", "vendor": "Zabbix", "category": "monitoring"},
    "zabbix 7.0 lts": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2028", "vendor": "Zabbix", "category": "monitoring"},
    "p RTG (paessler)": {"eol": None, "status": "Актуальное", "note": "SaaS модель, поддержка активна", "vendor": "Paessler", "category": "monitoring"},
    "microsoft sql server 2016": {"eol": "13.07.2022", "status": "EOSL", "note": "Полное прекращение поддержки", "vendor": "Microsoft", "category": "database"},
    "microsoft sql server 2017": {"eol": "11.10.2027", "status": "Актуальное", "note": "Поддержка до 2027", "vendor": "Microsoft", "category": "database"},
    "microsoft sql server 2019": {"eol": "07.01.2030", "status": "Актуальное", "note": "Поддержка до 2030", "vendor": "Microsoft", "category": "database"},
    "microsoft sql server 2022": {"eol": "08.01.2033", "status": "Актуальное", "note": "Поддержка до 2033", "vendor": "Microsoft", "category": "database"},
    "postgresql 13": {"eol": "13.11.2025", "status": "End-of-Sale", "note": "Только исправления ошибок", "vendor": "PostgreSQL", "category": "database"},
    "postgresql 14": {"eol": "12.11.2026", "status": "Актуальное", "note": "Активная поддержка", "vendor": "PostgreSQL", "category": "database"},
    "postgresql 15": {"eol": "11.11.2027", "status": "Актуальное", "note": "Активная поддержка", "vendor": "PostgreSQL", "category": "database"},
    "postgresql 16": {"eol": "09.11.2028", "status": "Актуальное", "note": "Активная поддержка", "vendor": "PostgreSQL", "category": "database"},
    "mysql 8.0": {"eol": "30.04.2026", "status": "End-of-Sale", "note": "Extended Support до 2026", "vendor": "Oracle", "category": "database"},
    "mysql 8.4": {"eol": None, "status": "Актуальное", "note": "LTS поддержка", "vendor": "Oracle", "category": "database"},
    "oracle 19c": {"eol": None, "status": "Актуальное", "note": "Premier Support до 2024, Extended до 2027", "vendor": "Oracle", "category": "database"},
    "oracle 21c": {"eol": None, "status": "Актуальное", "note": "Premier Support до 2027", "vendor": "Oracle", "category": "database"},
    "apc smart-ups 2200": {"eol": "2022", "status": "EOSL", "note": "Снят с производства", "vendor": "APC", "category": "ups"},
    "apc smart-ups srt 5000": {"eol": None, "status": "Актуальное", "note": "В активной продаже", "vendor": "APC", "category": "ups"},
    "depo cs-3400": {"eol": "Неизвестно", "status": "End-of-Sale", "note": "Устаревшая модель", "vendor": "Depo", "category": "server"},
    "oring rgs-7168": {"eol": "2023", "status": "EOSL", "note": "Производство прекращено", "vendor": "ORing", "category": "network"},
    "hikvision ds-7600": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "Hikvision", "category": "surveillance"},
    "dahua nvr5xxx": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "Dahua", "category": "surveillance"},
    "axis p3245": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "Axis", "category": "surveillance"},
    "dlink dgs-1510-28": {"eol": "2023", "status": "End-of-Sale", "note": "Заменён на серию DGS-1520", "vendor": "D-Link", "category": "network"},
    "mikrotik rb3011": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "MikroTik", "category": "network"},
    "mikrotik ccr1036": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "MikroTik", "category": "network"},
    "zte zxr10 5960": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2028+", "vendor": "ZTE", "category": "network"},
    "dell powerscale 300": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "Dell", "category": "storage"},
    "netapp fas2700": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "NetApp", "category": "storage"},
    "netapp aff a-series": {"eol": None, "status": "Актуальное", "note": "Активная продажа", "vendor": "NetApp", "category": "storage"},
}

_SENTINEL = object()


def lookup_eol(hostname: str = "", model: str = "") -> dict:
    """Поиск EOL-информации по hostname или модели."""
    search_terms = []
    if hostname:
        search_terms.append(hostname.lower().strip())
    if model:
        search_terms.append(model.lower().strip())

    for term in search_terms:
        for key, value in EOL_DATABASE.items():
            if key in term or term in key:
                return dict(value)
    return {"eol": "Неизвестно", "status": "Требуется проверка", "note": "Нет в базе данных", "vendor": "", "category": ""}


def add_to_eol_database(model: str, vendor: str = "", category: str = "",
                        eol: str = "", status: str = "Требуется проверка",
                        note: str = "") -> bool:
    """Добавляет новую запись в EOL-базу (при обнаружении нового оборудования во время аудита)."""
    model_key = model.lower().strip()
    if model_key in EOL_DATABASE:
        existing = EOL_DATABASE[model_key]
        changed = False
        if vendor and not existing.get("vendor"):
            existing["vendor"] = vendor
            changed = True
        if eol and eol != "Неизвестно" and existing.get("eol") != eol:
            existing["eol"] = eol
            changed = True
        if status and status != "Требуется проверка" and existing.get("status") == "Требуется проверка":
            existing["status"] = status
            changed = True
        if note and not existing.get("note"):
            existing["note"] = note
            changed = True
        if changed:
            _sync_eol_to_db(model_key, existing)
            logger.info(f"EOL-база обновлена: {model_key}")
        return changed

    EOL_DATABASE[model_key] = {
        "eol": eol if eol else None,
        "status": status if status else "Требуется проверка",
        "note": note,
        "vendor": vendor,
        "category": category,
    }
    _sync_eol_to_db(model_key, EOL_DATABASE[model_key])
    logger.info(f"EOL-база пополнена: {model_key} ({vendor}, {category})")
    return True


def batch_upsert_from_audit(discovered_models: list[dict]) -> int:
    """Массовое добавление/обновление EOL-записей из результатов аудита.

    discovered_models: [{"model": "...", "vendor": "...", "category": "...", "eol": "...", "status": "...", "note": "..."}]
    Возвращает количество добавленных/обновлённых записей.
    """
    count = 0
    for item in discovered_models:
        model = item.get("model", "").strip()
        if not model:
            continue
        if add_to_eol_database(
            model=model,
            vendor=item.get("vendor", ""),
            category=item.get("category", ""),
            eol=item.get("eol", ""),
            status=item.get("status", "Требуется проверка"),
            note=item.get("note", ""),
        ):
            count += 1
    return count


def _sync_eol_to_db(model_key: str, info: dict) -> None:
    """Синхронизирует запись EOL с SQLite (если БД доступна)."""
    try:
        import sqlite3
        if not DB_PATH.exists():
            return
        conn = sqlite3.connect(str(DB_PATH))
        existing = conn.execute("SELECT id FROM inventories WHERE model = ?", (model_key,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE inventories SET vendor=?, category=?, eol=?, eol_status=?, specs=? WHERE model=?",
                (info.get("vendor", ""), info.get("category", ""),
                 info.get("eol", ""), info.get("status", "Требуется проверка"),
                 info.get("note", ""), model_key)
            )
        else:
            conn.execute(
                "INSERT INTO inventories (model, vendor, category, eol, eol_status, specs) VALUES (?, ?, ?, ?, ?, ?)",
                (model_key, info.get("vendor", ""), info.get("category", ""),
                 info.get("eol", ""), info.get("status", "Требуется проверка"),
                 info.get("note", ""))
            )
        conn.commit()
        conn.close()
    except (sqlite3.Error, OSError) as e:
        logger.warning(f"EOL sync to DB error: {e}")


def get_eol_stats() -> dict:
    """Статистика по EOL-базе."""
    total = len(EOL_DATABASE)
    by_status = {}
    by_category = {}
    by_vendor = {}
    for info in EOL_DATABASE.values():
        status = info.get("status", "Неизвестно")
        by_status[status] = by_status.get(status, 0) + 1
        category = info.get("category", "unknown")
        by_category[category] = by_category.get(category, 0) + 1
        vendor = info.get("vendor", "Unknown")
        by_vendor[vendor] = by_vendor.get(vendor, 0) + 1
    return {
        "total": total,
        "by_status": by_status,
        "by_category": by_category,
        "by_vendor": by_vendor,
    }
