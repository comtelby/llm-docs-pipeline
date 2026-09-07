# Отчёт по аудиту раздела: Инфраструктурные сервисы AD и Почта

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

## 2. ACTIVE DIRECTORY DOMAIN SERVICES (AD DS)

### 2.1 Топология леса и доменов
{{AD_TOPOLOGY}}

### 2.2 Контроллеры домена
{{AD_DC_TABLE}}

### 2.3 Функциональные уровни
{{AD_FUNCTIONAL_LEVELS}}

### 2.4 Сайты и репликация
{{AD_SITES_REPLICATION}}

### 2.5 FSMO роли
{{AD_FSMO_ROLES}}

### 2.6 DNS зоны
{{AD_DNS_ZONES}}

### 2.7 DHCP
{{AD_DHCP_ANALYSIS}}

---

## 3. ПОЛИТИКИ БЕЗОПАСНОСТИ AD

### 3.1 Политика паролей
{{AD_PASSWORD_POLICY}}

### 3.2 Политика блокировки учётных записей
{{AD_LOCKOUT_POLICY}}

### 3.3 Политика аудита
{{AD_AUDIT_POLICY}}

### 3.4 Тонкая политика паролей (PSO)
{{AD_PSO}}

---

## 4. УПРАВЛЕНИЕ ОБЪЕКТАМИ AD

### 4.1 Учётные записи пользователей
{{AD_USER_ACCOUNTS_ANALYSIS}}

### 4.2 Учётные записи компьютеров
{{AD_COMPUTER_ACCOUNTS_ANALYSIS}}

### 4.3 Группы и вложенность
{{AD_GROUPS_ANALYSIS}}

### 4.4 Групповые политики (GPO)
{{AD_GPO_ANALYSIS}}

### 4.5 Привилегированные учётные записи
{{AD_PRIVILEGED_ACCOUNTS}}

### 4.6 Сервисные учётные записи
{{AD_SERVICE_ACCOUNTS}}

---

## 5. ПОЧТОВЫЕ СЕРВИСЫ

### 5.1 Архитектура почтовой системы
{{MAIL_ARCHITECTURE}}

### 5.2 Почтовые серверы / Сервисы
{{MAIL_SERVERS_TABLE}}

### 5.3 Домены и почтовые ящики
{{MAIL_DOMAINS_MAILBOXES}}

### 5.4 Антиспам / Антивирус почты
{{MAIL_ANTISPAM_AV}}

### 5.5 Правила транспорта и DLP
{{MAIL_TRANSPORT_RULES}}

### 5.6 Архивация и eDiscovery
{{MAIL_ARCHIVING}}

### 5.7 Клиентский доступ (OWA, ActiveSync, MAPI)
{{MAIL_CLIENT_ACCESS}}

### 5.8 Резервное копирование почты
{{MAIL_BACKUP}}

---

## 6. СИНХРОНИЗАЦИЯ ВРЕМЕНИ (NTP)

### 6.1 Источник времени PDC
{{AD_NTP_SOURCE}}

### 6.2 Настройки клиентов
{{AD_NTP_CLIENTS}}

---

## 7. WSUS / УПРАВЛЕНИЕ ОБНОВЛЕНИЯМИ

### 7.1 Наличие WSUS
{{WSUS_PRESENCE}}

### 7.2 Настройки обновлений
{{WSUS_SETTINGS}}

### 7.3 Статус обновлений парка
{{WSUS_COMPLIANCE}}

---

## 8. ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ И НЕСООТВЕТСТВИЯ

### 8.1 Критические проблемы (AD)
{{AD_CRITICAL_ISSUES}}

### 8.2 Критические проблемы (Почта)
{{MAIL_CRITICAL_ISSUES}}

### 8.3 Значительные проблемы
{{AD_MAIL_MAJOR_ISSUES}}

### 8.4 Рекомендации по улучшению
{{AD_MAIL_IMPROVEMENT_RECS}}

---

## 9. ЗАКЛЮЧЕНИЕ ПО РАЗДЕЛУ

{{AD_MAIL_CONCLUSION}}

---

*Раздел отчёта сгенерирован автоматически системой iqData Bot*