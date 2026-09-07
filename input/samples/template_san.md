# Отчёт по аудиту раздела: Системы Хранения Данных (СХД / SAN / NAS)

**Дата формирования:** {{DATE}}  
**Объект аудита:** {{OBJECT_NAME}}  
**Период сбора данных:** {{DATA_PERIOD}}  

---

## 1. ВВЕДЕНИЕ

### 1.1 Цели и задачи аудита раздела
{{INTRO_GOALS}}

### 1.2 Объём проверки
{{INTRO_SCOPE}}

### 1.3 Используемые источники данных
{{INTRO_SOURCES}}

---

## 2. ОБЩАЯ ХАРАКТЕРИСТИКА СИСТЕМ ХРАНЕНИЯ

### 2.1 СХД (SAN / Блочные)
{{SAN_TABLE}}

### 2.2 NAS / Файловые хранилища
{{NAS_TABLE}}

### 2.3 Суммарные ресурсы
{{STORAGE_SUMMARY}}

---

## 3. ДЕТАЛЬНЫЙ АНАЛИЗ СХД (SAN)

### 3.1 {{SAN_MODEL_1}}
- **Тип:** {{SAN_TYPE_1}} (All-Flash / Hybrid / HDD)
- **Контроллеры:** {{SAN_CONTROLLERS_1}}
- **Кэш:** {{SAN_CACHE_1}} GB
- **Всего ёмкость:** {{SAN_TOTAL_CAPACITY_1}} TB
- **Использовано:** {{SAN_USED_CAPACITY_1}} TB ({{SAN_USED_PCT_1}}%)
- **RAID уровни:** {{SAN_RAID_LEVELS_1}}
- **Количество дисков:** {{SAN_DISK_COUNT_1}} (SSD: {{SAN_SSD_COUNT_1}}, HDD: {{SAN_HDD_COUNT_1}})
- **Горячие резервы:** {{SAN_HOT_SPARE_1}}
- **Тонкое выделение:** {{SAN_THIN_PROVISIONING_1}}
- **Репликация:** {{SAN_REPLICATION_1}}
- **Подключённые серверы:** {{SAN_CONNECTED_SERVERS_1}}
- **Статус:** {{SAN_STATUS_1}}
- **EOL статус:** {{SAN_EOL_1}}

#### Пулы и тома:
{{SAN_POOLS_VOLUMES_1}}

### 3.2 {{SAN_MODEL_2}}
*(аналогичная структура)*

---

## 4. ДЕТАЛЬНЫЙ АНАЛИЗ NAS

### 4.1 {{NAS_MODEL_1}}
- **Тип:** {{NAS_TYPE_1}}
- **Протоколы:** {{NAS_PROTOCOLS_1}} (SMB/CIFS, NFS, AFP, iSCSI)
- **Всего ёмкость:** {{NAS_TOTAL_CAPACITY_1}} TB
- **Использовано:** {{NAS_USED_CAPACITY_1}} TB ({{NAS_USED_PCT_1}}%)
- **RAID:** {{NAS_RAID_LEVEL_1}}
- **Снапшоты:** {{NAS_SNAPSHOTS_1}}
- **Репликация:** {{NAS_REPLICATION_1}}
- **Антивирус на NAS:** {{NAS_AV_1}}
- **Квоты:** {{NAS_QUOTAS_1}}
- **EOL статус:** {{NAS_EOL_1}}

#### Общие папки (Shares):
{{NAS_SHARES_1}}

### 4.2 {{NAS_MODEL_2}}
*(аналогичная структура)*

---

## 5. ПРОИЗВОДИТЕЛЬНОСТЬ И НАГРУЗКА

### 5.1 IOPS и пропускная способность
{{STORAGE_PERFORMANCE}}

### 5.2 Задержки (Latency)
{{STORAGE_LATENCY}}

### 5.3 Нагрузка по пулам/томам
{{STORAGE_LOAD_BY_POOL}}

---

## 6. ЗАЩИТА ДАННЫХ И БЕЗОПАСНОСТЬ

### 6.1 Шифрование в покое
{{STORAGE_ENCRYPTION_AT_REST}}

### 6.2 Контроль доступа к хранилищу
{{STORAGE_ACCESS_CONTROL}}

### 6.3 Резервное копирование СХД/NAS
{{STORAGE_BACKUP}}

### 6.4 Защита от вымогателей (Immutable snapshots, WORM)
{{STORAGE_RANSOMWARE_PROTECTION}}

---

## 7. ЖИЗНЕННЫЙ ЦИКЛ И ПЛАНИРОВАНИЕ

### 7.1 EOL/EOSL анализ
{{STORAGE_EOL_ANALYSIS}}

### 7.2 План расширения/замены
{{STORAGE_CAPACITY_PLAN}}

---

## 8. ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ И НЕСООТВЕТСТВИЯ

### 8.1 Критические проблемы
{{STORAGE_CRITICAL_ISSUES}}

### 8.2 Значительные проблемы
{{STORAGE_MAJOR_ISSUES}}

### 8.3 Рекомендации по улучшению
{{STORAGE_IMPROVEMENT_RECS}}

---

## 9. ЗАКЛЮЧЕНИЕ ПО РАЗДЕЛУ

{{STORAGE_CONCLUSION}}

---

*Раздел отчёта сгенерирован автоматически системой iqData Bot*