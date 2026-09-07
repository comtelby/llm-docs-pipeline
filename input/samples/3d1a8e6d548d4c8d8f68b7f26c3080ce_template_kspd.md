# Отчёт по аудиту раздела: КСПД (Корпоративная Сеть Передачи Данных)

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

## 2. ОБЩАЯ ХАРАКТЕРИСТИКА КСПД

### 2.1 Топология корпоративной сети передачи данных
{{KSPD_TOPOLOGY}}

### 2.2 Сетевое оборудование КСПД (сводная таблица)
{{KSPD_NETWORK_DEVICES_TABLE}}

### 2.3 Сегментация сети (VLAN, зоны безопасности)
{{KSPD_SEGMENTATION}}

### 2.4 Каналы связи и протоколы маршрутизации
{{KSPD_ROUTING_PROTOCOLS}}

---

## 3. ДЕТАЛЬНЫЙ АНАЛИЗ СЕТЕВОГО ОБОРУДОВАНИЯ КСПД

### 3.1 Ядро сети (Core Layer)
{{KSPD_CORE_ANALYSIS}}

#### Устройства ядра:
| Hostname | Модель | Роль | IP Mgmt | EOL | OSPF/ISIS | BGP | VRRP/HSRP |
|----------|--------|------|---------|-----|-----------|-----|-----------|
{{KSPD_CORE_DEVICES_TABLE}}

### 3.2 Уровень агрегации / распределения (Distribution / Aggregation Layer)
{{KSPD_DISTRIBUTION_ANALYSIS}}

#### Устройства агрегации:
| Hostname | Модель | Роль | IP Mgmt | EOL | Uplink | VLANs | ACL |
|----------|--------|------|---------|-----|--------|-------|-----|
{{KSPD_DISTRIBUTION_DEVICES_TABLE}}

### 3.3 Уровень доступа (Access Layer)
{{KSPD_ACCESS_ANALYSIS}}

#### Коммутаторы доступа (сводка):
{{KSPD_ACCESS_DEVICES_SUMMARY}}

### 3.4 Периметр и WAN (Edge / Perimeter)
{{KSPD_EDGE_ANALYSIS}}

#### Маршрутизаторы / Firewall периметра:
| Hostname | Модель | Роль | IP Mgmt | EOL | BGP Peers | VPN Tunnels | ACL/Policy |
|----------|--------|------|---------|-----|-----------|-------------|------------|
{{KSPD_EDGE_DEVICES_TABLE}}

### 3.5 Беспроводная сеть (Wi-Fi) — при наличии
{{KSPD_WIFI_ANALYSIS}}

---

## 4. СЕТЕВЫЕ СЕРВИСЫ И ПРОТОКОЛЫ

### 4.1 Маршрутизация
- **Внутренние протоколы:** {{KSPD_IGP_PROTOCOLS}} (OSPF / IS-IS / RIP)
- **Внешние протоколы:** {{KSPD_EGP_PROTOCOLS}} (BGP / статика)
- **Policy-based routing:** {{KSPD_PBR}}
- **VRF / MPLS:** {{KSPD_VRF_MPLS}}

### 4.2 Резервирование и высокодоступность
- **VRRP / HSRP / GLBP:** {{KSPD_FHRP}}
- **Stacking / VSS / vPC / MC-LAG:** {{KSPD_STACKING}}
- **BFD / Fast Reroute:** {{KSPD_BFD_FR}}

### 4.3 Синхронизация времени (NTP)
- **Источник времени (стратег 1):** {{KSPD_NTP_SOURCE_1}} (рекомендуется БелГИМ: ntp1.belgim.by, ntp2.belgim.by)
- **Источник времени (стратег 2):** {{KSPD_NTP_SOURCE_2}}
- **Настроено на сетевом оборудовании:** {{KSPD_NTP_ON_NETWORK_DEVICES}} из {{KSPD_TOTAL_NETWORK_DEVICES}}
- **Разница времени (max offset):** {{KSPD_NTP_OFFSET_MAX}} мс

### 4.4 DHCP / IPAM
- **DHCP серверы в сети:** {{KSPD_DHCP_SERVERS}}
- **DHCP Relay / IP Helper:** {{KSPD_DHCP_RELAY}}
- **IPAM система:** {{KSPD_IPAM}}

### 4.5 DNS в сети КСПД
- **Внутренние DNS зоны:** {{KSPD_INTERNAL_DNS_ZONES}}
- **Forwarders:** {{KSPD_DNS_FORWARDERS}}
- **DNSSEC:** {{KSPD_DNSSEC}}

---

## 5. БЕЗОПАСНОСТЬ СЕТИ КСПД

### 5.1 Сетевая сегментация и межзонное экранирование
{{KSPD_INTERZONE_FIREWALLING}}

### 5.2 ACL на сетевом оборудовании
- **Настроено ACL:** {{KSPD_DEVICES_WITH_ACL}} из {{KSPD_TOTAL_NETWORK_DEVICES}}
- **Примеры правил:** {{KSPD_ACL_EXAMPLES}}

### 5.3 Защита плоскости управления (Control Plane Policing)
{{KSPD_CPP}}

### 5.4 Port Security / DHCP Snooping / DAI / BPDU Guard
{{KSPD_L2_SECURITY}}

### 5.5 VPN и удалённый доступ
- **Site-to-Site VPN:** {{KSPD_S2S_VPN_COUNT}} туннелей
- **Remote Access VPN:** {{KSPD_RA_VPN_USERS}} пользователей
- **Шифрование:** {{KSPD_VPN_ENCRYPTION}}
- **MFA:** {{KSPD_VPN_MFA}}

### 5.6 Журналирование (Syslog / NetFlow / sFlow)
- **Syslog серверы:** {{KSPD_SYSLOG_SERVERS}}
- **NetFlow / sFlow коллекторы:** {{KSPD_NETFLOW_COLLECTORS}}
- **Охват экспортера:** {{KSPD_NETFLOW_COVERAGE}}

---

## 6. ФАКТИЧЕСКОЕ НАЛИЧИЕ СЕРВЕРНОЙ И КЛИЕНТСКОЙ ИНФРАСТРУКТУРЫ В СЕТИ

### 6.1 Серверы, подключенные к КСПД
{{KSPD_CONNECTED_SERVERS_SUMMARY}}
*(Упоминаются только как факты подключения к портам доступа/агрегации)*

### 6.2 Количество хостов в сети (по VLAN / подсетям)
{{KSPD_HOSTS_COUNT_BY_VLAN}}

### 6.3 Виртуализация, затрагивающая сеть (VXLAN, EVPN, NSX и др.)
{{KSPD_NETWORK_VIRTUALIZATION}}

---

## 7. ЖИЗНЕННЫЙ ЦИКЛ СЕТЕВОГО ОБОРУДОВАНИЯ (EOL/EOSL)

### 7.1 Критическое оборудование (EOSL — поддержка прекращена)
{{KSPD_EOSL_TABLE}}

### 7.2 Оборудование End-of-Sale
{{KSPD_EOS_TABLE}}

### 7.3 План замены/модернизации сети
{{KSPD_REPLACEMENT_PLAN}}

---

## 8. ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ И НЕСООТВЕТСТВИЯ

### 8.1 Критические проблемы (сетевая доступность, безопасность)
{{KSPD_CRITICAL_ISSUES}}

### 8.2 Значительные проблемы (производительность, управление, резервирование)
{{KSPD_MAJOR_ISSUES}}

### 8.3 Рекомендации по развитию и улучшению КСПД
{{KSPD_IMPROVEMENT_RECS}}

---

## 9. ЗАКЛЮЧЕНИЕ ПО РАЗДЕЛУ

{{KSPD_CONCLUSION}}

---

*Раздел отчёта сгенерирован автоматически системой iqData Bot*