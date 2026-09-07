# Отчёт по аудиту раздела: Система Резервного Копирования (СРК)

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

## 2. ОБЩАЯ ХАРАКТЕРИСТИКА СРК

### 2.1 Развёрнутые продукты резервного копирования
{{BACKUP_PRODUCTS_TABLE}}

### 2.2 Защищаемые системы и объёмы
{{PROTECTED_SYSTEMS_VOLUMES}}

---

## 3. ДЕТАЛЬНЫЙ АНАЛИЗ ПО ПРОДУКТАМ СРК

### 3.1 {{BACKUP_PRODUCT_1}} {{BACKUP_VERSION_1}}
- **Тип репозитория:** {{BACKUP_REPO_TYPE_1}}
- **Файловая система репозитория:** {{BACKUP_REPO_FS_1}}
- **Тип подключения:** {{BACKUP_REPO_CONNECTION_1}}
- **Политика хранения:** {{BACKUP_RETENTION_1}} дней
- **Расписание бэкапов:** {{BACKUP_SCHEDULE_1}}
- **Типы бэкапов:** {{BACKUP_TYPES_1}} (full/incremental/differential/snapshot)
- **Шифрование:** {{BACKUP_ENCRYPTION_1}}
- **Сжатие:** {{BACKUP_COMPRESSION_1}}
- **Дедупликация:** {{BACKUP_DEDUP_1}}
- **Ошибки за период:** {{BACKUP_ERRORS_COUNT_1}}
- **Последний успешный бэкап:** {{BACKUP_LAST_SUCCESS_1}}
- **Тестирование восстановления:** {{BACKUP_RESTORE_TEST_1}}
- **EOL статус:** {{BACKUP_EOL_1}}

### 3.2 {{BACKUP_PRODUCT_2}}
*(аналогичная структура)*

---

## 4. АНАЛИЗ ЗАЩИЩАЕМЫХ СИСТЕМ

### 4.1 Серверы (физические/виртуальные)
{{BACKUP_SERVERS_COVERAGE}}

### 4.2 Базы данных
{{BACKUP_DATABASES_COVERAGE}}

### 4.3 Файловые серверы и NAS
{{BACKUP_FILES_NAS_COVERAGE}}

### 4.4 Виртуальные машины
{{BACKUP_VMS_COVERAGE}}

### 4.4 Контейнеры / Kubernetes
{{BACKUP_CONTAINERS_COVERAGE}}

---

## 5. ПРОВЕРКА ВОССТАНОВЛЕНИЯ И RTO/RPO

### 5.1 Документированные RTO/RPO
{{BACKUP_RTO_RPO}}

### 5.2 Результаты тестов восстановления
{{BACKUP_RESTORE_TEST_RESULTS}}

### 5.3 Соответствие регуляторным требованиям
{{BACKUP_COMPLIANCE}}

---

## 6. МОНИТОРИНГ И УПРАВЛЕНИЕ

### 6.1 Централизованная консоль
{{BACKUP_CENTRAL_CONSOLE}}

### 6.2 Алертинг и уведомления
{{BACKUP_ALERTING}}

### 6.3 Отчётность
{{BACKUP_REPORTING}}

---

## 7. ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ И НЕСООТВЕТСТВИЯ

### 7.1 Критические проблемы
{{BACKUP_CRITICAL_ISSUES}}

### 7.2 Значительные проблемы
{{BACKUP_MAJOR_ISSUES}}

### 7.3 Рекомендации по улучшению
{{BACKUP_IMPROVEMENT_RECS}}

---

## 8. ЗАКЛЮЧЕНИЕ ПО РАЗДЕЛУ

{{BACKUP_CONCLUSION}}

---

*Раздел отчёта сгенерирован автоматически системой iqData Bot*