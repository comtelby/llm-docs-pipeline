import logging
import re
import subprocess
from pathlib import Path

from src.eol import lookup_eol
from src.models import (
    AntivirusInfo,
    BackupInfo,
    DatabaseInfo,
    DeviceInfo,
    NetworkSecurityInfo,
    ServerInfo,
    StorageInfo,
    VirtualizationInfo,
)

logger = logging.getLogger(__name__)

MODEL_MAP = {
    "hp5412": "HP 5412R 92GT PoE+",
    "hp-5412": "HP 5412R 92GT PoE+",
    "hp5510": "HPE 5510 24G SFP 4SFP+ HI",
    "5510_m1": "HPE 5510 24G SFP 4SFP+ HI",
    "s6730": "Huawei S6730-H24X6C",
    "h6121": "Huawei AR6121E",
    "c4331": "Cisco ISR4331-K9",
    "asa5516": "Cisco ASA 5516-X",
    "2530-48": "HP Aruba 2530 48 PoE+",
    "2530": "HP Aruba 2530 24 PoE+",
    "hpe5120": "HPE 5120 16G",
    "5120-02": "HPE 5120 16G",
    "hp3500": "HP ProCurve 3500-24-PoE",
    "hp2620": "HP 2620-24 PoE+",
    "5731": "Huawei 5731-H48P4XC",
    "ac6508": "Huawei AC6508",
    "hwlc01": "Huawei AC6508",
    "by_core": "Cisco ISR4331/K9",
}


def parse_device_config(text: str, filename: str) -> DeviceInfo:
    device = DeviceInfo(file=filename, full_length=len(text))

    hostname_match = re.search(r'(?:hostname|sysname)\s+["\']?([^"\'\n\r]+)["\']?', text, re.IGNORECASE)
    if hostname_match:
        device.hostname = hostname_match.group(1).strip()

    hostname_lower = device.hostname.lower()
    for key, model_name in MODEL_MAP.items():
        if key in hostname_lower:
            device.model = model_name
            break

    device.eol_info = lookup_eol(device.hostname, device.model)

    mgmt_match = re.search(r'ip\s+address\s+([\d.]+)\s+([\d.]+)', text, re.IGNORECASE)
    if mgmt_match:
        device.ip_mgmt = mgmt_match.group(1)

    device.ip_addresses = re.findall(r'ip\s+address\s+([\d.]+)\s+([\d.]+)', text, re.IGNORECASE)[:50]

    interface_blocks = re.findall(
        r'^interface\s+(.+?)$(.*?)(?=^interface\s|\Z)',
        text, re.MULTILINE | re.DOTALL | re.IGNORECASE
    )
    for iface_name, iface_config in interface_blocks[:30]:
        iface_ip = re.search(r'ip\s+address\s+([\d.]+)\s+([\d.]+)', iface_config, re.IGNORECASE)
        device.interfaces.append({
            "name": iface_name.strip(),
            "ip": f"{iface_ip.group(1)}/{iface_ip.group(2)}" if iface_ip else "Нет IP"
        })

    vlan_blocks = re.findall(r'^vlan\s+(\d+).*$(.*?)(?=^vlan|\Z)', text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    for vlan_id, vlan_config in vlan_blocks[:30]:
        vlan_ip = re.search(r'ip\s+address\s+([\d.]+)\s+([\d.]+)', vlan_config, re.IGNORECASE)
        device.vlans.append({
            "id": vlan_id,
            "ip": f"{vlan_ip.group(1)}/{vlan_ip.group(2)}" if vlan_ip else "L2"
        })

    ospf_process = re.search(r"ospf\s+(\d+)", text, re.IGNORECASE)
    ospf_router_id = re.search(r"router-id\s+([\d.]+)", text, re.IGNORECASE)
    ospf_area = re.search(r"area\s+([\d.]+)", text, re.IGNORECASE)
    if ospf_process or ospf_router_id:
        device.ospf = {
            "process_id": ospf_process.group(1) if ospf_process else "?",
            "router_id": ospf_router_id.group(1) if ospf_router_id else "?",
            "area": ospf_area.group(1) if ospf_area else "?"
        }

    vrrp_blocks = re.findall(r'vrrp\s+(\d+)\s+.*?virtual-ip\s+([\d.]+)', text, re.IGNORECASE)
    device.vrrp = [{"group": g, "vip": vip} for g, vip in vrrp_blocks[:10]]

    stp_region = re.search(r'region-name\s+(\S+)', text, re.IGNORECASE)
    if stp_region:
        device.stp_region = stp_region.group(1)
    device.stp_instances = re.findall(r'instance\s+(\d+)\s+vlan\s+(.+)', text, re.IGNORECASE)[:10]

    device.tacacs_servers = re.findall(r'tacacs-server\s+host\s+([\d.]+)', text, re.IGNORECASE)[:5]
    device.syslog_servers = re.findall(r'syslog.*?([\d.]+)', text, re.IGNORECASE)[:5]
    device.ntp_servers = re.findall(r'ntp\s+(?:server|source)\s+([\d.]+)', text, re.IGNORECASE)[:5]

    device.dhcp_snooping = bool(re.search(r'dhcp-snooping', text, re.IGNORECASE))
    device.port_security = bool(re.search(r'port-security', text, re.IGNORECASE))
    device.bpdu_protection = bool(re.search(r'bpdu-protection', text, re.IGNORECASE))

    device.acl = re.findall(r'^(?:access-list|acl)\s+.+$', text, re.MULTILINE | re.IGNORECASE)[:20]
    device.aaa = re.findall(r'^(?:aaa|radius|tacacs)\s+.+$', text, re.MULTILINE | re.IGNORECASE)[:20]
    device.snmp = re.findall(r'^(?:snmp-server|snmp-agent)\s+.+$', text, re.MULTILINE | re.IGNORECASE)[:10]
    device.routes = re.findall(r'^ip\s+route\s+(.+)$', text, re.MULTILINE | re.IGNORECASE)[:30]

    return device


def detect_file_type(text: str, filename: str) -> str:
    """Определяет тип данных по содержимому и имени файла."""
    fn_lower = filename.lower()
    text_lower = text[:2000].lower()

    if any(k in text_lower for k in ["hostname", "sysname", "interface", "vlan", "router ospf"]):
        return "network_config"
    if any(k in text_lower for k in ["system information", "systeminfo", "host name", "processor", "total physical memory"]):
        return "windows_server"
    if any(k in text_lower for k in ["linux", "lscpu", "cpu(s):", "mem:", "disk"]):
        return "linux_server"
    if any(k in text_lower for k in ["esxcli", "vmware esxi", "vmkernel", "vcenter", "esxi"]):
        return "vmware_esxi"
    if any(k in text_lower for k in ["hyper-v", "get-vmhost", "get-vm", "vmguestservice"]):
        return "hyper_v"
    if any(k in text_lower for k in ["proxmox", "pve", "qm list", "pvesh"]):
        return "proxmox"
    if any(k in text_lower for k in ["storage-pool", "raid", "disk", "controller", "iops"]):
        return "storage"
    if any(k in text_lower for k in ["nas", "share", "smb", "cifs", "nfs"]):
        return "nas"
    if any(k in text_lower for k in ["sql server", "postgresql", "mysql", "oracle", "select @@version"]):
        return "database"
    if any(k in text_lower for k in ["backup", "veeam", "acronis", "wbadmin", "backup job"]):
        return "backup"
    if any(k in text_lower for k in ["kaspersky", "ksc", "antivirus", "антивирус", "threat"]):
        return "antivirus"
    if any(k in text_lower for k in ["firewall", "mсэ", "vpn", "ipsec", "openvpn", "nat"]):
        return "firewall_vpn"
    if any(k in text_lower for k in ["active directory", "admanager", "domain", "gpo", "dns"]):
        return "active_directory"
    if any(k in text_lower for k in ["monitoring", "zabbix", "prtg", "nagios", "sensor"]):
        return "monitoring"
    if any(k in text_lower for k in ["asterisk", "3cx", "sip", "voip", "pbx"]):
        return "telephony"
    if any(k in text_lower for k in ["skud", "access control", "доступ", "turniket"]):
        return "access_control"
    if ".docx" in fn_lower or ".doc" in fn_lower:
        return "document"
    if ".xlsx" in fn_lower or ".xls" in fn_lower or ".csv" in fn_lower:
        return "spreadsheet"
    return "unknown"


def parse_server_config(text: str, filename: str) -> ServerInfo:
    """Парсинг данных сервера (Windows systeminfo / Linux lscpu / iLO/iDRAC вывод)."""
    server = ServerInfo(file=filename)

    hostname_match = re.search(r'(?:Host\s*Name|hostname|Hostname):\s*(.+)', text, re.IGNORECASE)
    if hostname_match:
        server.hostname = hostname_match.group(1).strip()

    os_match = re.search(r'(?:OS\s*Name|Operating System|PRETTY_NAME)[=:]\s*(.+)', text, re.IGNORECASE)
    if os_match:
        server.os_version = os_match.group(1).strip()

    cpu_match = re.search(r'(?:Processor\(s\)|CPU\(s\)|model name)[=:]\s*(.+)', text, re.IGNORECASE)
    if cpu_match:
        server.cpu_model = cpu_match.group(1).strip()

    cpu_count_match = re.search(r'(?:Number of Processor|Socket\(s\)|CPU\(s\)):\s*(\d+)', text, re.IGNORECASE)
    if cpu_count_match:
        server.cpu_count = int(cpu_count_match.group(1))

    cpu_core_match = re.search(r'(?:Core\(s\)\s*per\s*Socket|cores per socket):\s*(\d+)', text, re.IGNORECASE)
    if cpu_core_match:
        server.cpu_cores = int(cpu_core_match.group(1))
    elif server.cpu_count > 0:
        server.cpu_cores = server.cpu_count

    ram_match = re.search(r'(?:Total Physical Memory|MemTotal)[:\s]+([\d,\.]+)\s*(GB|MB|KiB|MiB)', text, re.IGNORECASE)
    if ram_match:
        val = float(ram_match.group(1).replace(",", ""))
        unit = ram_match.group(2).upper()
        if unit in ("MB", "MIB"):
            server.ram_total_gb = round(val / 1024, 1)
        elif unit in ("KI", "KIB"):
            server.ram_total_gb = round(val / 1048576, 1)
        else:
            server.ram_total_gb = round(val, 1)

    bios_match = re.search(r'(?:BIOS Version|Firmware|BIOS)[=:]\s*(.+)', text, re.IGNORECASE)
    if bios_match:
        server.bios_version = bios_match.group(1).strip()[:100]

    ilo_match = re.search(r'(?:iLO|iDRAC|IPMI)\s*(?:Version|firmware)[=:]\s*(.+)', text, re.IGNORECASE)
    if ilo_match:
        server.ilo_version = ilo_match.group(1).strip()[:100]

    disk_total_match = re.search(r'(?:Total\s+Size|Size|Capacity)[:\s]+([\d,\.]+)\s*(GB|TB|MB)', text, re.IGNORECASE)
    if disk_total_match:
        val = float(disk_total_match.group(1).replace(",", ""))
        unit = disk_total_match.group(2).upper()
        if unit == "TB":
            server.disk_total_gb = round(val * 1024, 1)
        elif unit == "MB":
            server.disk_total_gb = round(val / 1024, 1)
        else:
            server.disk_total_gb = round(val, 1)

    disk_free_match = re.search(r'(?:Free Space|Free|Available)[:\s]+([\d,\.]+)\s*(GB|TB|MB)', text, re.IGNORECASE)
    if disk_free_match:
        val = float(disk_free_match.group(1).replace(",", ""))
        unit = disk_free_match.group(2).upper()
        free_gb = val * 1024 if unit == "TB" else (val / 1024 if unit == "MB" else val)
        if server.disk_total_gb > 0:
            server.disk_used_gb = round(server.disk_total_gb - free_gb, 1)
            server.disk_free_pct = round((free_gb / server.disk_total_gb) * 100, 1)

    raid_match = re.search(r'(?:RAID\s*Level|RAID)[=:]\s*(\S+)', text, re.IGNORECASE)
    if raid_match:
        server.raid_level = raid_match.group(1).strip()

    raid_status_match = re.search(r'(?:RAID\s*Status|Array\s*Status|State)[=:]\s*(\S+)', text, re.IGNORECASE)
    if raid_status_match:
        server.raid_status = raid_status_match.group(1).strip()

    uptime_match = re.search(r'(?:System\s*Up\s*Time|Uptime|up\s*time)[=:]\s*(.+)', text, re.IGNORECASE)
    if uptime_match:
        server.uptime = uptime_match.group(1).strip()[:100]

    services = re.findall(r'(?:Service|ServiceName)\s+(\S+)', text, re.IGNORECASE)[:30]
    server.installed_services = services

    server.model = f"{server.cpu_model[:50]} / {server.os_version[:50]}".strip()
    server.eol_info = lookup_eol(server.hostname, server.model)
    server.source_type = "systeminfo" if "system" in text[:500].lower() else "lscpu"
    return server


def parse_vmware_esxi(text: str, filename: str) -> VirtualizationInfo:
    """Парсинг данных VMware ESXi (esxcli, vim-cmd, vCenter export)."""
    vinfo = VirtualizationInfo(file=filename, hypervisor_type="VMware ESXi")

    version_match = re.search(r'(?:VMware ESXi|ESXi)\s+([\d\.]+)', text, re.IGNORECASE)
    if version_match:
        vinfo.hypervisor_version = f"ESXi {version_match.group(1)}"

    cluster_match = re.search(r'(?:Cluster|cluster)[- ]?(?:Name|name)[:\s]+(.+)', text, re.IGNORECASE)
    if cluster_match:
        vinfo.cluster_name = cluster_match.group(1).strip()

    hosts_match = re.search(r'(?:Hosts?|hosts?)[:\s]+(\d+)', text, re.IGNORECASE)
    if hosts_match:
        vinfo.hosts_count = int(hosts_match.group(1))

    vm_match = re.search(r'(?:Virtual Machines?|VMs?|virtual machines?)[:\s]+(\d+)', text, re.IGNORECASE)
    if vm_match:
        vinfo.vm_count = int(vm_match.group(1))

    evc_match = re.search(r'(?:EVC|Enhanced vMotion Compatibility)[:\s]+(\S+)', text, re.IGNORECASE)
    if evc_match:
        vinfo.evc_mode = evc_match.group(1).strip()

    vinfo.ha_enabled = bool(re.search(r'(?:vSphere\s+HA|HA\s*Enabled|HA\s*status)[:\s]*(?:enabled|on|yes)', text, re.IGNORECASE))
    vinfo.ft_enabled = bool(re.search(r'(?:Fault\s*Tolerance|FT)[:\s]*(?:enabled|on|yes)', text, re.IGNORECASE))

    vm_names = re.findall(r'(?:^|\s)(\S+)\s+(linux|windows|otherlinux|centos|ubuntu|debian|red\s*hat|suse|windows\s*\d+)', text, re.IGNORECASE)[:50]
    vinfo.vm_details = [{"name": m[0], "os": m[1]} for m in vm_names]

    host_cpus = re.findall(r'(?:CPU|Processor)[:\s]+([\d]+\s*(?:GHz|MHz|cores?))', text, re.IGNORECASE)[:20]
    host_rams = re.findall(r'(?:Memory|RAM)[:\s]+([\d]+\s*(?:GB|MB|TB))', text, re.IGNORECASE)[:20]
    for i in range(max(len(host_cpus), len(host_rams))):
        vinfo.host_details.append({
            "cpu": host_cpus[i] if i < len(host_cpus) else "?",
            "ram": host_rams[i] if i < len(host_rams) else "?",
        })

    vinfo.eol_info = lookup_eol("", vinfo.hypervisor_version)
    vinfo.source_type = "esxcli"
    return vinfo


def parse_hyper_v(text: str, filename: str) -> VirtualizationInfo:
    """Парсинг данных Hyper-V (PowerShell Get-VMHost, Get-VM)."""
    vinfo = VirtualizationInfo(file=filename, hypervisor_type="Hyper-V")

    version_match = re.search(r'(?:Hyper-V|Microsoft Hyper-V)\s+([\d\.]+)', text, re.IGNORECASE)
    if version_match:
        vinfo.hypervisor_version = f"Hyper-V {version_match.group(1)}"

    hosts_match = re.search(r'(?: hosts? |HostCount)[:\s]+(\d+)', text, re.IGNORECASE)
    if hosts_match:
        vinfo.hosts_count = int(hosts_match.group(1))

    vm_lines = re.findall(r'(\S+)\s+(\S+)\s+(Running|Stopped|Paused|Saved)', text, re.IGNORECASE)[:50]
    vinfo.vm_details = [{"name": m[0], "os": m[1], "state": m[2]} for m in vm_lines]
    vinfo.vm_count = len(vinfo.vm_details)

    vinfo.ha_enabled = bool(re.search(r'(?:Failover\s*Cluster|Cluster\s*Node|cluster)', text, re.IGNORECASE))

    vinfo.eol_info = lookup_eol("", vinfo.hypervisor_version)
    vinfo.source_type = "powershell"
    return vinfo


def parse_storage_config(text: str, filename: str) -> StorageInfo:
    """Парсинг данных СХД/NAS (CLI-вывод, web-интерфейс экспорт)."""
    sinfo = StorageInfo(file=filename)

    if any(k in text.lower() for k in ["nas", "share", "smb", "cifs", "nfs", "synology", "qnap"]):
        sinfo.device_type = "NAS"
    else:
        sinfo.device_type = "SAN"

    model_match = re.search(r'(?:Model|model|Модель)[:\s]+(.+)', text, re.IGNORECASE)
    if model_match:
        sinfo.model = model_match.group(1).strip()[:100]

    total_match = re.search(r'(?:Total\s*Capacity|Total|Общий объём|Ёмкость)[:\s]+([\d,\.]+)\s*(GB|TB|MB|PB)', text, re.IGNORECASE)
    if total_match:
        val = float(total_match.group(1).replace(",", ""))
        unit = total_match.group(2).upper()
        if unit == "TB":
            sinfo.total_capacity_gb = round(val * 1024, 1)
        elif unit == "PB":
            sinfo.total_capacity_gb = round(val * 1048576, 1)
        elif unit == "MB":
            sinfo.total_capacity_gb = round(val / 1024, 1)
        else:
            sinfo.total_capacity_gb = round(val, 1)

    used_match = re.search(r'(?:Used|Использовано|Занято)[:\s]+([\d,\.]+)\s*(GB|TB|MB)', text, re.IGNORECASE)
    if used_match:
        val = float(used_match.group(1).replace(",", ""))
        unit = used_match.group(2).upper()
        sinfo.used_capacity_gb = round(val * 1024 if unit == "TB" else (val / 1024 if unit == "MB" else val), 1)

    if sinfo.total_capacity_gb > 0 and sinfo.used_capacity_gb > 0:
        sinfo.free_pct = round(((sinfo.total_capacity_gb - sinfo.used_capacity_gb) / sinfo.total_capacity_gb) * 100, 1)

    raid_match = re.search(r'(?:RAID\s*Level|RAID)[:\s]+(\S+)', text, re.IGNORECASE)
    if raid_match:
        sinfo.raid_level = raid_match.group(1).strip()

    disk_count_match = re.search(r'(?:Disk\s*Count|Disks?|Дисков)[:\s]+(\d+)', text, re.IGNORECASE)
    if disk_count_match:
        sinfo.disk_count = int(disk_count_match.group(1))

    hot_spare_match = re.search(r'(?:Hot\s*Spare|Spare)[:\s]+(\d+)', text, re.IGNORECASE)
    if hot_spare_match:
        sinfo.hot_spare = int(hot_spare_match.group(1))

    status_match = re.search(r'(?:Status|State|Состояние)[:\s]+(Optimal|Normal|Degraded|Failed|Critical|Online|Offline)', text, re.IGNORECASE)
    if status_match:
        sinfo.status = status_match.group(1).strip()

    sinfo.thin_provisioning = bool(re.search(r'(?:Thin\s*Provisioning|thin)', text, re.IGNORECASE))

    subscribed_match = re.search(r'(?:Subscribed|Подписанная)[:\s]+([\d,\.]+)\s*%', text, re.IGNORECASE)
    if subscribed_match:
        sinfo.subscribed_pct = float(subscribed_match.group(1).replace(",", "."))

    replication_match = re.search(r'(?:Replication|HyperMetro|SnapMirror|Mirror)[:\s]+(\S+)', text, re.IGNORECASE)
    if replication_match:
        sinfo.replication_type = replication_match.group(1).strip()

    sinfo.eol_info = lookup_eol("", sinfo.model)
    sinfo.source_type = "cli"
    return sinfo


def parse_database_config(text: str, filename: str) -> DatabaseInfo:
    """Парсинг данных СУБД (SQL-запросы, pg_stat, конфиги)."""
    dbinfo = DatabaseInfo(file=filename)

    if re.search(r'Microsoft\s+SQL\s+Server', text, re.IGNORECASE):
        dbinfo.dbms_type = "Microsoft SQL Server"
        ver_match = re.search(r'(?:SQL Server|@@VERSION)\s+(\d{4})', text, re.IGNORECASE)
        if ver_match:
            dbinfo.version = f"SQL Server {ver_match.group(1)}"
    elif re.search(r'PostgreSQL', text, re.IGNORECASE):
        dbinfo.dbms_type = "PostgreSQL"
        ver_match = re.search(r'PostgreSQL\s+([\d\.]+)', text, re.IGNORECASE)
        if ver_match:
            dbinfo.version = f"PostgreSQL {ver_match.group(1)}"
    elif re.search(r'MySQL', text, re.IGNORECASE):
        dbinfo.dbms_type = "MySQL"
        ver_match = re.search(r'MySQL\s+v?([\d\.]+)', text, re.IGNORECASE)
        if ver_match:
            dbinfo.version = f"MySQL {ver_match.group(1)}"
    elif re.search(r'Oracle', text, re.IGNORECASE):
        dbinfo.dbms_type = "Oracle"
        ver_match = re.search(r'Oracle\s+(?:Database\s+)?(\d+[cR]?)', text, re.IGNORECASE)
        if ver_match:
            dbinfo.version = f"Oracle {ver_match.group(1)}"

    server_match = re.search(r'(?:Server|ServerName|HOSTNAME)[=:]\s*(\S+)', text, re.IGNORECASE)
    if server_match:
        dbinfo.server_name = server_match.group(1).strip()

    if re.search(r'(?:Windows\s+Authentication|integrated|AD)', text, re.IGNORECASE):
        dbinfo.auth_mode = "Windows AD"
    elif re.search(r'(?:SQL\s+Authentication|mixed)', text, re.IGNORECASE):
        dbinfo.auth_mode = "SQL/Mixed"
    else:
        dbinfo.auth_mode = "PostgreSQL/pg_hba"

    dbinfo.encryption = bool(re.search(r'(?:TDE|SSL|encrypt|шифр)', text, re.IGNORECASE))

    dbinfo.ha_enabled = bool(re.search(r'(?:Always\s*On|replication|clustering|HA)', text, re.IGNORECASE))
    ha_type_match = re.search(r'(?:Always\s*On|replication|clustering)[\s:]+(\S+)', text, re.IGNORECASE)
    if ha_type_match:
        dbinfo.ha_type = ha_type_match.group(1).strip()

    dbinfo.eol_info = lookup_eol("", dbinfo.version)
    dbinfo.source_type = "sql_output"
    return dbinfo


def parse_backup_config(text: str, filename: str) -> BackupInfo:
    """Парсинг данных СРК (Veeam, Acronis, Windows Backup)."""
    binfo = BackupInfo(file=filename)

    if re.search(r'Veeam', text, re.IGNORECASE):
        binfo.product = "Veeam Backup & Replication"
        ver_match = re.search(r'Veeam\s+(?:Backup\s+)?(?:&\s+Replication\s+)?(\d+[\.\d]*)', text, re.IGNORECASE)
        if ver_match:
            binfo.version = f"Veeam {ver_match.group(1)}"
    elif re.search(r'Acronis', text, re.IGNORECASE):
        binfo.product = "Acronis Cyber Protect"
        ver_match = re.search(r'Acronis\s+(?:Cyber\s+Protect\s+)?(\d+[\.\d]*)', text, re.IGNORECASE)
        if ver_match:
            binfo.version = f"Acronis {ver_match.group(1)}"
    elif re.search(r'wbadmin|Windows\s*Backup', text, re.IGNORECASE):
        binfo.product = "Windows Server Backup"

    binfo.schedule_compliant = not bool(re.search(r'(?:error|failed|ошибка|сбой)', text, re.IGNORECASE))

    repo_match = re.search(r'(?:Repository|Репозиторий|Location)[:\s]+(.+)', text, re.IGNORECASE)
    if repo_match:
        binfo.repo_type = repo_match.group(1).strip()[:100]

    fs_match = re.search(r'(?:File\s*System|ФС)[:\s]+(NTFS|ext4|ZFS|XFS|BTRFS)', text, re.IGNORECASE)
    if fs_match:
        binfo.repo_filesystem = fs_match.group(1).strip()

    conn_match = re.search(r'(?:Connection|Подключение)[:\s]+(SMB|CIFS|local|LUN|iSCSI)', text, re.IGNORECASE)
    if conn_match:
        binfo.repo_connection = conn_match.group(1).strip()

    retention_match = re.search(r'(?:Retention|retention\s*policy)[:\s]+(\d+)\s*(?:days?|дн)', text, re.IGNORECASE)
    if retention_match:
        binfo.retention_days = int(retention_match.group(1))

    binfo.errors = re.findall(r'(?:error|failed|ошибка|сбой)[:\s]*(.+)', text, re.IGNORECASE)[:20]

    binfo.eol_info = lookup_eol("", binfo.product)
    binfo.source_type = "backup_logs"
    return binfo


def parse_antivirus_config(text: str, filename: str) -> AntivirusInfo:
    """Парсинг данных антивирусного ПО (KSC, управление)."""
    ainfo = AntivirusInfo(file=filename)

    if re.search(r'Kaspersky|KSC', text, re.IGNORECASE):
        ainfo.product = "Kaspersky Security Center"
    elif re.search(r'Windows\s*Defender', text, re.IGNORECASE):
        ainfo.product = "Windows Defender"
    elif re.search(r'ESET', text, re.IGNORECASE):
        ainfo.product = "ESET"

    ver_match = re.search(r'(?:Version|Версия)[:\s]+([\d\.]+)', text, re.IGNORECASE)
    if ver_match:
        ainfo.version = ver_match.group(1).strip()

    ainfo.central_management = bool(re.search(r'(?:KSC|Console|AdminServer|управляющий сервер)', text, re.IGNORECASE))

    license_match = re.search(r'(?:License|Лицензи)[яйи]?:?\s*(\d+)', text, re.IGNORECASE)
    if license_match:
        ainfo.total_licenses = int(license_match.group(1))

    agent_match = re.search(r'(?:Agents?|Агенты)[:\s]+(\d+)', text, re.IGNORECASE)
    if agent_match:
        ainfo.installed_agents = int(agent_match.group(1))

    ainfo.mail_protection = bool(re.search(r'(?:Mail\s*Threat|почтов|mail\s*protect)', text, re.IGNORECASE))
    ainfo.device_control = bool(re.search(r'(?:Device\s*Control|съёмн|removable)', text, re.IGNORECASE))
    ainfo.password_protection = bool(re.search(r'(?:Password\s*protect|пароль)', text, re.IGNORECASE))

    update_match = re.search(r'(?:Update\s*Schedule|Обновление)[:\s]+(.+)', text, re.IGNORECASE)
    if update_match:
        ainfo.update_schedule = update_match.group(1).strip()[:100]

    ainfo.eol_info = lookup_eol("", ainfo.product)
    ainfo.source_type = "ksc_console"
    return ainfo


def parse_firewall_vpn(text: str, filename: str) -> NetworkSecurityInfo:
    """Парсинг данных МСЭ/VPN (Cisco ASA, UserGate, pfSense, OpenVPN)."""
    nsinfo = NetworkSecurityInfo(file=filename)

    fw_match = re.search(r'(?:Firewall|МСЭ|ASA|UserGate|pfSense|FortiGate)[\s:]+(.+)', text, re.IGNORECASE)
    if fw_match:
        nsinfo.firewall_model = fw_match.group(1).strip()[:100]

    ver_match = re.search(r'(?:Version|Версия|Software\s*Version)[:\s]+([\d\.]+)', text, re.IGNORECASE)
    if ver_match:
        nsinfo.firewall_version = ver_match.group(1).strip()

    nsinfo.remote_access = bool(re.search(r'(?:VPN|remote\s*access|удалённый)', text, re.IGNORECASE))

    vpn_match = re.search(r'(?:VPN\s*Type|Protocol|Протокол)[:\s]+(IPsec|OpenVPN|WireGuard|SSL\s*VPN|L2TP|PPTP)', text, re.IGNORECASE)
    if vpn_match:
        nsinfo.vpn_type = vpn_match.group(1).strip()

    nsinfo.mfa_enabled = bool(re.search(r'(?:MFA|multi.factor|двухфакторн)', text, re.IGNORECASE))

    enc_match = re.search(r'(?:Encryption|Шифрование|cipher)[:\s]+(AES-\d+|ChaCha)', text, re.IGNORECASE)
    if enc_match:
        nsinfo.encryption_type = enc_match.group(1).strip()

    nsinfo.access_logging = bool(re.search(r'(?:log|journal|аудит|logging)', text, re.IGNORECASE))

    nsinfo.eol_info = lookup_eol("", nsinfo.firewall_model)
    nsinfo.source_type = "firewall_config"
    return nsinfo


def classify_and_parse(text: str, filename: str):
    """Автоопределение типа данных и вызов нужного парсера. Возвращает объект_info + тип."""
    file_type = detect_file_type(text, filename)

    parsers = {
        "network_config": lambda: parse_device_config(text, filename),
        "windows_server": lambda: parse_server_config(text, filename),
        "linux_server": lambda: parse_server_config(text, filename),
        "vmware_esxi": lambda: parse_vmware_esxi(text, filename),
        "hyper_v": lambda: parse_hyper_v(text, filename),
        "storage": lambda: parse_storage_config(text, filename),
        "nas": lambda: parse_storage_config(text, filename),
        "database": lambda: parse_database_config(text, filename),
        "backup": lambda: parse_backup_config(text, filename),
        "antivirus": lambda: parse_antivirus_config(text, filename),
        "firewall_vpn": lambda: parse_firewall_vpn(text, filename),
    }

    parser = parsers.get(file_type)
    if parser:
        result = parser()
        return result, file_type
    return None, file_type


def extract_text_from_image(image_path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='rus+eng')
        if text.strip():
            logger.info(f"OCR OK: {image_path.name} ({len(text)} chars)")
            return text.strip()
        logger.warning(f"OCR пустой результат: {image_path.name}")
        return ""
    except ImportError as e:
        logger.error(f"OCR: нет библиотеки: {e}")
        return ""
    except Exception as e:  # noqa: BLE001
        logger.error(f"OCR ошибка {image_path.name}: {e}")
        return ""


def extract_text_from_docx(docx_path: Path) -> str:
    try:
        from docx import Document
        doc = Document(str(docx_path))
        paragraphs = []
        for p in doc.paragraphs:
            if p.text.strip():
                paragraphs.append(p.text)
        for table in doc.tables:
            for row in table.rows:
                row_text = ' | '.join([cell.text for cell in row.cells])
                if row_text.strip():
                    paragraphs.append(row_text)
        result = '\n'.join(paragraphs)
        logger.info(f"DOCX: {docx_path.name} ({len(result)} chars)")
        return result
    except ImportError:
        logger.error("DOCX: python-docx не установлен")
        return ""
    except Exception as e:  # noqa: BLE001
        logger.error(f"DOCX ошибка {docx_path.name}: {e}")
        return ""


def extract_text_from_doc(doc_path: Path) -> str:
    """Извлечение текста из старого .doc (Word 97-2003)."""
    # Попытка 1: antiword
    try:
        result = subprocess.run(
            ["antiword", "-m", "UTF-8", str(doc_path)],
            capture_output=True, text=True, timeout=30, check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            logger.info(f"DOC(antiword): {doc_path.name} ({len(result.stdout)} chars)")
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    except Exception as e:  # noqa: BLE001
        logger.warning(f"DOC antiword error {doc_path.name}: {e}")

    # Попытка 2: catdoc
    try:
        result = subprocess.run(
            ["catdoc", str(doc_path)],
            capture_output=True, text=True, timeout=30, check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            logger.info(f"DOC(catdoc): {doc_path.name} ({len(result.stdout)} chars)")
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    except Exception as e:  # noqa: BLE001
        logger.warning(f"DOC catdoc error {doc_path.name}: {e}")

    # Попытка 3: raw text через olefile
    try:
        import olefile
        ole = olefile.OleFileIO(str(doc_path))
        if ole.exists('WordDocument'):
            stream = ole.openstream('WordDocument')
            raw = stream.read()
            text = raw.decode('utf-8', errors='ignore')
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 100:
                logger.info(f"DOC(olefile): {doc_path.name} ({len(text)} chars)")
                return text[:50000]
    except ImportError:
        pass
    except Exception as e:  # noqa: BLE001
        logger.warning(f"DOC olefile error {doc_path.name}: {e}")

    logger.warning(f"DOC: не удалось извлечь текст из {doc_path.name}")
    return ""


def _detect_rtf_codepage(raw_bytes: bytes) -> int:
    """Определяет кодовую страницу RTF по \\ansicpgN или \\fcharsetN."""
    try:
        header = raw_bytes[:500].decode('latin-1', errors='replace')
        m = re.search(r'\\ansicpg(\d+)', header)
        if m:
            return int(m.group(1))
        m = re.search(r'\\fcharset(\d+)', header)
        if m:
            charset = int(m.group(1))
            charset_to_cp = {204: 1251, 238: 1251, 177: 1251, 162: 1251}
            if charset in charset_to_cp:
                return charset_to_cp[charset]
        if re.search(r"\\'([cdef][0-9a-f]|e[0-9a-f])", header, re.IGNORECASE):
            return 1251
    except Exception:  # noqa: BLE001, S110
        pass
    return 1251


def _decode_rtf_escapes(raw_text: str, encoding: str) -> str:
    """Заменяет \\'xx на реальные символы в указанной кодировке."""
    def replace_escape(m):
        hex_val = m.group(1)
        return bytes.fromhex(hex_val).decode(encoding, errors='replace')
    return re.sub(r"\\'([0-9a-fA-F]{2})", replace_escape, raw_text)


def extract_text_from_rtf(rtf_path: Path) -> str:
    try:
        raw_bytes = rtf_path.read_bytes()
        cp = _detect_rtf_codepage(raw_bytes)
        encoding = f'cp{cp}'

        raw_text = raw_bytes.decode('latin-1', errors='replace')
        decoded_text = _decode_rtf_escapes(raw_text, encoding)

        try:
            from striprtf.striprtf import rtf_to_text
            result = rtf_to_text(decoded_text)
            if len(result.strip()) > 100:
                logger.info(f"RTF(striprtf): {rtf_path.name} ({len(result)} chars)")
                return result.strip()
        except ImportError:
            pass
        except Exception as e:  # noqa: BLE001
            logger.warning(f"RTF striprtf error {rtf_path.name}: {e}")

        content = decoded_text
        content = re.sub(r'\\[a-z]+\d*', '', content)
        content = re.sub(r'[\\{};]', '', content)
        content = content.replace('\\par', '\n')
        lines = [line.strip() for line in content.split('\n') if line.strip() and len(line.strip()) > 3]
        result = '\n'.join(lines)
        logger.info(f"RTF(fallback): {rtf_path.name} ({len(result)} chars)")
        return result
    except Exception as e:  # noqa: BLE001
        logger.error(f"RTF ошибка {rtf_path.name}: {e}")
        return ""


def extract_text_from_xlsx(xlsx_path: Path) -> str:
    try:
        from openpyxl import load_workbook
        wb = load_workbook(xlsx_path, read_only=True, data_only=True)
        parts = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows_text = []
            for row in ws.iter_rows(values_only=True):
                row_str = ' | '.join(str(c) if c is not None else '' for c in row)
                if row_str.strip():
                    rows_text.append(row_str)
            if rows_text:
                parts.append(f"=== {sheet_name} ===\n" + '\n'.join(rows_text))
        result = '\n\n'.join(parts)
        logger.info(f"XLSX: {xlsx_path.name} ({len(result)} chars)")
        return result
    except ImportError:
        logger.error("XLSX: openpyxl не установлен")
        return ""
    except Exception as e:  # noqa: BLE001
        logger.error(f"XLSX ошибка {xlsx_path.name}: {e}")
        return ""


def extract_text_from_xls(xls_path: Path) -> str:
    try:
        import xlrd
        wb = xlrd.open_workbook(str(xls_path))
        parts = []
        for sheet_name in wb.sheet_names():
            ws = wb.sheet_by_name(sheet_name)
            rows_text = []
            for row_idx in range(ws.nrows):
                row_str = ' | '.join(str(ws.cell_value(row_idx, c)) for c in range(ws.ncols))
                if row_str.strip():
                    rows_text.append(row_str)
            if rows_text:
                parts.append(f"=== {sheet_name} ===\n" + '\n'.join(rows_text))
        result = '\n\n'.join(parts)
        logger.info(f"XLS: {xls_path.name} ({len(result)} chars)")
        return result
    except ImportError:
        logger.error("XLS: xlrd не установлен, пробую pandas")
        try:
            import pandas as pd
            dfs = pd.read_excel(xls_path, sheet_name=None)
            parts = []
            for sheet_name, df in dfs.items():
                rows_text = df.astype(str).to_csv(sep=' | ', index=False)
                if rows_text.strip():
                    parts.append(f"=== {sheet_name} ===\n{rows_text}")
            result = '\n\n'.join(parts)
            logger.info(f"XLS(pandas): {xls_path.name} ({len(result)} chars)")
            return result
        except ImportError:
            logger.error("XLS: ни xlrd, ни pandas недоступны")
            return ""
        except Exception as e:  # noqa: BLE001
            logger.error(f"XLS pandas ошибка {xls_path.name}: {e}")
            return ""
    except Exception as e:  # noqa: BLE001
        logger.error(f"XLS ошибка {xls_path.name}: {e}")
        return ""


def extract_text_from_file(file_path: Path) -> str:
    """Универсальное извлечение текста из файла любого поддерживаемого формата."""
    suffix = file_path.suffix.lower()
    try:
        if suffix == '.docx':
            return extract_text_from_docx(file_path)
        elif suffix == '.doc':
            return extract_text_from_doc(file_path)
        elif suffix == '.xlsx':
            return extract_text_from_xlsx(file_path)
        elif suffix == '.xls':
            return extract_text_from_xls(file_path)
        elif suffix == '.rtf':
            return extract_text_from_rtf(file_path)
        elif suffix in {'.txt', '.md', '.cfg', '.conf'} or suffix == '.csv':
            return read_text_file(file_path)
        else:
            logger.debug(f"extract_text_from_file: неподдерживаемый формат {suffix} для {file_path.name}")
            return ""
    except Exception as e:  # noqa: BLE001
        logger.warning(f"extract_text_from_file ошибка {file_path.name}: {e}")
        return ""


def read_text_file(file_path: Path) -> str:
    for encoding in ['utf-8', 'cp1251', 'latin-1', 'ascii']:
        try:
            return file_path.read_text(encoding=encoding)
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    return ""


def parse_inventory_rows(file_path: Path) -> list[dict]:
    """Парсит файл инвентаризации (xlsx/xls/csv/txt) и возвращает список записей."""
    suffix = file_path.suffix.lower()
    rows = []

    try:
        if suffix == '.xlsx':
            from openpyxl import load_workbook
            wb = load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active
            headers = [str(c.value).strip().lower() if c.value else '' for c in next(ws.iter_rows(min_row=1, max_row=1))]
            col_map = _map_inventory_columns(headers)
            for row in ws.iter_rows(min_row=2, values_only=True):
                rec = _build_inventory_record(row, col_map)
                if rec.get('model'):
                    rows.append(rec)

        elif suffix == '.xls':
            import xlrd
            wb = xlrd.open_workbook(str(file_path))
            ws = wb.sheet_by_index(0)
            headers = [str(ws.cell_value(0, c)).strip().lower() for c in range(ws.ncols)]
            col_map = _map_inventory_columns(headers)
            for r in range(1, ws.nrows):
                row = [ws.cell_value(r, c) for c in range(ws.ncols)]
                rec = _build_inventory_record(row, col_map)
                if rec.get('model'):
                    rows.append(rec)

        elif suffix == '.csv':
            import csv
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                col_map = _map_inventory_columns(headers)
                for row in reader:
                    rec = _build_inventory_record(row, col_map)
                    if rec.get('model'):
                        rows.append(rec)

        else:
            text = read_text_file(file_path)
            if text:
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                if lines:
                    sep = '\t' if '\t' in lines[0] else '|' if '|' in lines[0] else ','
                    headers = [h.strip().lower() for h in lines[0].split(sep)]
                    col_map = _map_inventory_columns(headers)
                    for line in lines[1:]:
                        vals = [v.strip() for v in line.split(sep)]
                        rec = _build_inventory_record(vals, col_map)
                        if rec.get('model'):
                            rows.append(rec)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"parse_inventory_rows error {file_path.name}: {e}")

    return rows


def _map_inventory_columns(headers: list[str]) -> dict:
    col_map = {}
    for i, h in enumerate(headers):
        h = h.lower().replace(' ', '_')
        if h in ('model', 'модель', 'device', 'наименование', 'name', 'equipment'):
            col_map['model'] = i
        elif h in ('vendor', 'manufacturer', 'производитель', 'вендор'):
            col_map['vendor'] = i
        elif h in ('category', 'тип', 'type', 'категория'):
            col_map['category'] = i
        elif h in ('eol', 'eosl', 'end_of_life', 'end_of_sale', 'срок_поддержки'):
            col_map['eol'] = i
        elif h in ('eol_status', 'status', 'статус', 'lifecycle'):
            col_map['eol_status'] = i
        elif h in ('specs', 'specification', 'description', 'описание', 'характеристики', 'spec'):
            col_map['specs'] = i
    return col_map


def _build_inventory_record(row: tuple | list, col_map: dict) -> dict:
    return {
        'model': str(row[col_map['model']]).strip() if 'model' in col_map and col_map['model'] < len(row) else '',
        'vendor': str(row[col_map['vendor']]).strip() if 'vendor' in col_map and col_map['vendor'] < len(row) else '',
        'category': str(row[col_map['category']]).strip() if 'category' in col_map and col_map['category'] < len(row) else 'network',
        'eol': str(row[col_map['eol']]).strip() if 'eol' in col_map and col_map['eol'] < len(row) else '',
        'eol_status': str(row[col_map['eol_status']]).strip() if 'eol_status' in col_map and col_map['eol_status'] < len(row) else 'Требуется проверка',
        'specs': str(row[col_map['specs']]).strip() if 'specs' in col_map and col_map['specs'] < len(row) else '',
    }
