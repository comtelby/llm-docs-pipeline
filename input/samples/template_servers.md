# Отчёт по аудиту раздела: Серверное оборудование

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

## 2. ОБЩАЯ ХАРАКТЕРИСТИКА СЕРВЕРНОЙ ИНФРАСТРУКТУРЫ

### 2.1 Физические серверы
{{PHYSICAL_SERVERS_TABLE}}

### 2.2 Виртуальные машины (если выделены отдельно)
{{VMS_SUMMARY}}

### 2.3 Распределение по ролям
{{SERVERS_BY_ROLE}}

---

## 3. ДЕТАЛЬНЫЙ АНАЛИЗ ФИЗИЧЕСКИХ СЕРВЕРОВ

### 3.1 {{SERVER_HOSTNAME_1}}
- **Модель:** {{SERVER_MODEL_1}}
- **CPU:** {{SERVER_CPU_1}} ({{SERVER_CPU_COUNT_1}} сокетов, {{SERVER_CPU_CORES_1}} ядер)
- **RAM:** {{SERVER_RAM_1}} GB
- **Диски:** {{SERVER_DISKS_1}} (RAID {{SERVER_RAID_LEVEL_1}}, {{SERVER_RAID_STATUS_1}})
- **Свободное место:** {{SERVER_DISK_FREE_1}}%
- **ОС:** {{SERVER_OS_1}}
- **BIOS/Фирмвара:** {{SERVER_BIOS_1}}
- **iLO/iDRAC/IPMI:** {{SERVER_ILO_1}}
- **Uptime:** {{SERVER_UPTIME_1}}
- **EOL статус:** {{SERVER_EOL_1}}

### 3.2 {{SERVER_HOSTNAME_2}}
*(аналогичная структура для каждого сервера)*

---

## 4. АНАЛИЗ ЖИЗНЕННОГО ЦИКЛА (EOL/EOSL)

### 4.1 Критическое оборудование (EOSL)
{{SERVER_EOSL_TABLE}}

### 4.2 Оборудование End-of-Sale
{{SERVER_EOS_TABLE}}

### 4.3 Актуальное оборудование
{{SERVER_CURRENT_TABLE}}

### 4.4 План замены
{{SERVER_REPLACEMENT_PLAN}}

---

## 5. АНАЛИЗ КОНФИГУРАЦИИ И БЕЗОПАСНОСТИ

### 5.1 Настройки BIOS/UEFI
{{SERVER_BIOS_SETTINGS}}

### 5.2 RAID конфигурация
{{SERVER_RAID_ANALYSIS}}

### 5.3 Управление (iLO/iDRAC/IPMI)
{{SERVER_MGMT_ANALYSIS}}

### 5.4 Установленные роли и службы
{{SERVER_ROLES_SERVICES}}

### 5.5 Сетевая конфигурация
{{SERVER_NETWORK_ANALYSIS}}

---

## 6. ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ И НЕСООТВЕТСТВИЯ

### 6.1 Критические проблемы
{{SERVER_CRITICAL_ISSUES}}

### 6.2 Значительные проблемы
{{SERVER_MAJOR_ISSUES}}

### 6.3 Рекомендации по улучшению
{{SERVER_IMPROVEMENT_RECS}}

---

## 7. ЗАКЛЮЧЕНИЕ ПО РАЗДЕЛУ

{{SERVER_CONCLUSION}}

---

*Раздел отчёта сгенерирован автоматически системой iqData Bot*