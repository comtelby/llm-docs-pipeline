EOL_DATABASE = {
    "avaya ip office 500v2": {"eol": "31.12.2020", "status": "EOSL", "note": "Поддержка прекращена"},
    "hp 2620-24": {"eol": "2020", "status": "End-of-Sale", "note": "Обновлений нет"},
    "hp procurve 3500-24": {"eol": "31.10.2019", "status": "EOSL", "note": "Производство прекращено"},
    "hpe 5120 16g": {"eol": "2019", "status": "End-of-Sale", "note": "Заменён на серию 5130"},
    "hpe 5510": {"eol": "2021", "status": "End-of-Sale", "note": "Заменён на серию 5520"},
    "huawei 5731": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2029"},
    "huawei s6730": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2031+"},
    "huawei ac6508": {"eol": None, "status": "Актуальное", "note": "Активная продажа"},
    "huawei ar6121e": {"eol": None, "status": "Актуальное", "note": "Поддержка до 2030+"},
    "huawei oceanstor dorado 2000": {"eol": None, "status": "Актуальное", "note": "Активная продажа"},
    "ibm system x3650 m5": {"eol": "2019", "status": "End-of-Sale", "note": "Поддержка прекращена (Lenovo)"},
    "ibm system x3630 m4": {"eol": "2019", "status": "EOSL", "note": "Полное прекращение поддержки"},
    "synology rs814+": {"eol": "01.10.2024", "status": "EOSL", "note": "DSM 6.2, обновлений нет"},
    "synology rs815+": {"eol": "01.10.2024", "status": "EOSL", "note": "DSM 6.2, обновлений нет"},
    "synology rx415": {"eol": "01.10.2024", "status": "EOSL", "note": "Не поддерживает DSM 7.x"},
    "synology rx1217": {"eol": "2023", "status": "End-of-Sale", "note": "Снят с производства"},
    "synology rs3618xs": {"eol": "2022", "status": "End-of-Sale", "note": "Снят с продаж"},
    "synology sa3200d": {"eol": None, "status": "Актуальное", "note": "Активная продажа"},
    "cisco asa 5516": {"eol": "2022", "status": "End-of-Sale", "note": "Последний патч: август 2024"},
    "cisco isr4331": {"eol": "2022", "status": "End-of-Sale", "note": "SW поддержка до 2026"},
    "cisco air-ct-3504": {"eol": "2021", "status": "End-of-Sale", "note": "Заменён на 3504"},
    "hp 5412r": {"eol": "2020", "status": "End-of-Sale", "note": "Поддержка ограничена"},
    "hp aruba 2530": {"eol": "2021", "status": "End-of-Sale", "note": "Заменён на 2540"},
    "lenovo b6505": {"eol": "2020", "status": "End-of-Sale", "note": "Снят с производства"},
    "lenovo ds2200": {"eol": "2023", "status": "EOSL", "note": "Полное прекращение поддержки"},
    "dell r230": {"eol": "31.03.2023", "status": "EOSL", "note": "iDRAC 8, обновлений нет"},
    "ibm ts3200": {"eol": "31.12.2023", "status": "EOSL", "note": "Поддержка прекращена"},
    "oring rgs-7168": {"eol": "2023", "status": "EOSL", "note": "Производство прекращено"},
    "apc smart-ups 2200": {"eol": "2022", "status": "EOSL", "note": "Снят с производства"},
    "apc smart-ups srt 5000": {"eol": None, "status": "Актуальное", "note": "В активной продаже"},
    "depo cs-3400": {"eol": "Неизвестно", "status": "End-of-Sale", "note": "Устаревшая модель"},
}


def lookup_eol(hostname: str = "", model: str = "") -> dict:
    search_terms = []
    if hostname:
        search_terms.append(hostname.lower())
    if model:
        search_terms.append(model.lower())

    for term in search_terms:
        for key, value in EOL_DATABASE.items():
            if key in term or term in key:
                return value

    return {"eol": "Неизвестно", "status": "Требуется проверка", "note": "Нет в базе данных"}
