# Отчёт по аудиту раздела: SIEM (Security Information and Event Management)

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

## 2. ОБЩАЯ ХАРАКТЕРИСТИКА SIEM

### 2.1 Развёрнутое решение
{{SIEM_PRODUCT_TABLE}}

### 2.2 Архитектура развёртывания
{{SIEM_ARCHITECTURE}}

### 2.3 Лицензирование и пропускная способность
{{SIEM_LICENSING_THROUGHPUT}}

---

## 3. ИСТОЧНИКИ ДАННЫХ (LOG SOURCES)

### 3.1 Подключённые источники
{{SIEM_LOG_SOURCES_TABLE}}

### 3.2 Парсеры и нормализация
{{SIEM_PARSERS_NORMALIZATION}}

### 3.3 Объём событий (EPS/GB в день)
{{SIEM_VOLUME_STATS}}

### 3.4 Полнота покрытия MITRE ATT&CK
{{SIEM_MITRE_COVERAGE}}

---

## 4. ПРАВИЛА КОРРЕЛЯЦИИ И ДЕТЕКТИРОВАНИЕ

### 4.1 Встроенные правила (Out-of-the-box)
{{SIEM_BUILTIN_RULES}}

### 4.2 Пользовательские правила (Custom)
{{SIEM_CUSTOM_RULES}}

### 4.3 Пороговые значения и подавление ложных срабатываний
{{SIEM_THRESHOLDS_SUPPRESSION}}

### 4.4 Использование Threat Intelligence
{{SIEM_THREAT_INTEL}}

### 4.5 Покрытие MITRE ATT&K тактик/техник
{{SIEM_MITRE_RULES_COVERAGE}}

---

## 5. ИНЦИДЕНТ-МЕНЕДЖМЕНТ И РАССЛЕДОВАНИЕ

### 5.1 Процесс триажа алертов
{{SIEM_TRIAGE_PROCESS}}

### 5.2 Кейсы и расследования
{{SIEM_CASES_INVESTIGATIONS}}

### 5.3 Интеграция с ITSM / SOAR
{{SIEM_ITSM_SOAR_INTEGRATION}}

### 5.4 SLA по обработке инцидентов
{{SIEM_SLA}}

---

## 6. ДАШБОРДЫ И ОТЧЁТНОСТЬ

### 6.1 Операционные дашборды (SOC)
{{SIEM_OPERATIONAL_DASHBOARDS}}

### 6.2 Управленческие отчёты
{{SIEM_MANAGEMENT_REPORTS}}

### 6.3 Комплаенс-отчёты
{{SIEM_COMPLIANCE_REPORTS}}

---

## 7. УПРАВЛЕНИЕ И ЭКСПЛУАТАЦИЯ

### 7.1 Роли и права доступа к SIEM
{{SIEM_RBAC}}

### 7.2 Журналирование действий администраторов SIEM
{{SIEM_ADMIN_AUDIT}}

### 7.3 Резервное копирование конфигурации SIEM
{{SIEM_CONFIG_BACKUP}}

### 7.4 Обновления контента (правил, парсеров, TI)
{{SIEM_CONTENT_UPDATES}}

### 7.5 Мониторинг здоровья SIEM
{{SIEM_HEALTH_MONITORING}}

---

## 8. ХРАНЕНИЕ ДАННЫХ

### 8.1 Горячее / тёплое / холодное хранение
{{SIEM_STORAGE_TIERS}}

### 8.2 Ретенция (сроки хранения)
{{SIEM_RETENTION}}

### 8.3 Соответствие регуляторным требованиям (152-ФЗ, ГОСТ и др.)
{{SIEM_REGULATORY_COMPLIANCE}}

---

## 9. ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ И НЕСООТВЕТСТВИЯ

### 9.1 Критические проблемы
{{SIEM_CRITICAL_ISSUES}}

### 9.2 Значительные проблемы
{{SIEM_MAJOR_ISSUES}}

### 9.3 Рекомендации по улучшению
{{SIEM_IMPROVEMENT_RECS}}

---

## 10. ЗАКЛЮЧЕНИЕ ПО РАЗДЕЛУ

{{SIEM_CONCLUSION}}

---

*Раздел отчёта сгенерирован автоматически системой iqData Bot*