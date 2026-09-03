import logging
import re

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


def normalize_server_data(raw_output: str) -> dict:
    """Нормализует вывод systeminfo/lscpu в структурированный dict."""
    data = {
        "hostname": "",
        "os_version": "",
        "cpu_model": "",
        "cpu_count": 0,
        "cpu_cores": 0,
        "ram_gb": 0.0,
        "disk_total_gb": 0.0,
        "disk_used_gb": 0.0,
        "disk_free_pct": 0.0,
        "raid_level": "",
        "raid_status": "",
        "uptime": "",
        "network_adapters": [],
        "installed_roles": [],
        "running_services_count": 0,
    }

    hostname_m = re.search(r'(?:Host\s*Name|hostname|Hostname):\s*(.+)', raw_output, re.IGNORECASE)
    if hostname_m:
        data["hostname"] = hostname_m.group(1).strip()

    os_m = re.search(r'(?:OS\s*Name|Operating System|PRETTY_NAME)[=:]\s*(.+)', raw_output, re.IGNORECASE)
    if os_m:
        data["os_version"] = os_m.group(1).strip()

    cpu_m = re.search(r'(?:Processor\(s\)|CPU\(s\)|model name)[=:]\s*(.+)', raw_output, re.IGNORECASE)
    if cpu_m:
        data["cpu_model"] = cpu_m.group(1).strip()

    cpu_count_m = re.search(r'(?:Number of Processor|Socket\(s\)):\s*(\d+)', raw_output, re.IGNORECASE)
    if cpu_count_m:
        data["cpu_count"] = int(cpu_count_m.group(1))

    cpu_cores_m = re.search(r'(?:Core\(s\)\s*per\s*Socket|cores per socket):\s*(\d+)', raw_output, re.IGNORECASE)
    if cpu_cores_m:
        data["cpu_cores"] = int(cpu_cores_m.group(1))
    elif data["cpu_count"] > 0:
        data["cpu_cores"] = data["cpu_count"]

    ram_m = re.search(r'(?:Total Physical Memory|MemTotal)[:\s]+([\d,\.]+)\s*(GB|MB|KiB|MiB)', raw_output, re.IGNORECASE)
    if ram_m:
        val = float(ram_m.group(1).replace(",", ""))
        unit = ram_m.group(2).upper()
        if unit in ("MB", "MIB"):
            data["ram_gb"] = round(val / 1024, 1)
        elif unit in ("KI", "KIB"):
            data["ram_gb"] = round(val / 1048576, 1)
        else:
            data["ram_gb"] = round(val, 1)

    disk_lines = re.findall(r'(?:Drive\s+(\w:)|(\S+))\s*-\s*Total:\s*([\d\.]+)\s*GB.*?Free:\s*([\d\.]+)\s*GB.*?\(([\d\.]+)%\s*used\)', raw_output, re.IGNORECASE)
    if disk_lines:
        total = sum(float(d[2]) for d in disk_lines)
        free = sum(float(d[3]) for d in disk_lines)
        data["disk_total_gb"] = round(total, 1)
        data["disk_used_gb"] = round(total - free, 1)
        data["disk_free_pct"] = round((free / total * 100) if total > 0 else 0, 1)

    raid_m = re.search(r'(?:RAID\s*Level|RAID)[:\s]+(\S+)', raw_output, re.IGNORECASE)
    if raid_m:
        data["raid_level"] = raid_m.group(1).strip()

    raid_status_m = re.search(r'(?:RAID\s*Status|Array\s*Status|State)[:\s]+(Optimal|Degraded|Failed|Critical)', raw_output, re.IGNORECASE)
    if raid_status_m:
        data["raid_status"] = raid_status_m.group(1).strip()

    uptime_m = re.search(r'(?:up\s*time|uptime)[:\s]+(.+)', raw_output, re.IGNORECASE)
    if uptime_m:
        data["uptime"] = uptime_m.group(1).strip()[:100]

    services = re.findall(r'(?:ServiceName|Service)\s+(\S+)', raw_output, re.IGNORECASE)
    data["running_services_count"] = len(services)

    return data


def normalize_vm_data(raw_output: str) -> dict:
    """Нормализует данные виртуализации."""
    data = {
        "hypervisor_type": "",
        "hypervisor_version": "",
        "hosts_count": 0,
        "vm_count": 0,
        "cluster_name": "",
        "ha_enabled": False,
        "vms": [],
        "hosts": [],
    }

    if re.search(r'vmware|esxi', raw_output, re.IGNORECASE):
        data["hypervisor_type"] = "VMware ESXi"
    elif re.search(r'hyper-v|get-vmhost', raw_output, re.IGNORECASE):
        data["hypervisor_type"] = "Hyper-V"
    elif re.search(r'proxmox|pve', raw_output, re.IGNORECASE):
        data["hypervisor_type"] = "Proxmox VE"

    ver_m = re.search(r'(?:VMware ESXi|ESXi|Hyper-V|Proxmox)\s+([\d\.]+)', raw_output, re.IGNORECASE)
    if ver_m:
        data["hypervisor_version"] = ver_m.group(1)

    hosts_m = re.search(r'(?:Hosts?|hosts?)[:\s]+(\d+)', raw_output, re.IGNORECASE)
    if hosts_m:
        data["hosts_count"] = int(hosts_m.group(1))

    vm_m = re.search(r'(?:Virtual Machines?|VMs?)[:\s]+(\d+)', raw_output, re.IGNORECASE)
    if vm_m:
        data["vm_count"] = int(vm_m.group(1))

    cluster_m = re.search(r'(?:Cluster)[:\s]+(.+)', raw_output, re.IGNORECASE)
    if cluster_m:
        data["cluster_name"] = cluster_m.group(1).strip()

    data["ha_enabled"] = bool(re.search(r'(?:HA|Failover\s*Cluster|cluster)', raw_output, re.IGNORECASE))

    vm_lines = re.findall(r'(\S+)\s+(Running|Stopped|Paused|Saved)', raw_output, re.IGNORECASE)[:50]
    data["vms"] = [{"name": m[0], "state": m[1]} for m in vm_lines]
    data["vm_count"] = max(data["vm_count"], len(data["vms"]))

    return data


def normalize_storage_data(raw_output: str) -> dict:
    """Нормализует данные СХД/NAS."""
    data = {
        "device_type": "",
        "model": "",
        "total_gb": 0.0,
        "used_gb": 0.0,
        "free_pct": 0.0,
        "raid_level": "",
        "disk_count": 0,
        "hot_spare": 0,
        "status": "",
        "thin_provisioning": False,
        "replication": "",
    }

    if any(k in raw_output.lower() for k in ["nas", "share", "smb", "cifs", "nfs", "synology"]):
        data["device_type"] = "NAS"
    else:
        data["device_type"] = "SAN"

    model_m = re.search(r'(?:Model|Модель)[:\s]+(.+)', raw_output, re.IGNORECASE)
    if model_m:
        data["model"] = model_m.group(1).strip()[:100]

    total_m = re.search(r'(?:Total\s*Capacity|Total|Общий объём)[:\s]+([\d,\.]+)\s*(GB|TB|PB)', raw_output, re.IGNORECASE)
    if total_m:
        val = float(total_m.group(1).replace(",", ""))
        unit = total_m.group(2).upper()
        data["total_gb"] = round(val * 1024 if unit == "TB" else (val * 1048576 if unit == "PB" else val), 1)

    used_m = re.search(r'(?:Used|Использовано)[:\s]+([\d,\.]+)\s*(GB|TB)', raw_output, re.IGNORECASE)
    if used_m:
        val = float(used_m.group(1).replace(",", ""))
        unit = used_m.group(2).upper()
        data["used_gb"] = round(val * 1024 if unit == "TB" else val, 1)

    if data["total_gb"] > 0 and data["used_gb"] > 0:
        data["free_pct"] = round(((data["total_gb"] - data["used_gb"]) / data["total_gb"]) * 100, 1)

    raid_m = re.search(r'(?:RAID\s*Level|RAID)[:\s]+(\S+)', raw_output, re.IGNORECASE)
    if raid_m:
        data["raid_level"] = raid_m.group(1).strip()

    disk_count_m = re.search(r'(?:Disk\s*Count|Disks?|Дисков)[:\s]+(\d+)', raw_output, re.IGNORECASE)
    if disk_count_m:
        data["disk_count"] = int(disk_count_m.group(1))

    hot_spare_m = re.search(r'(?:Hot\s*Spare)[:\s]+(\d+)', raw_output, re.IGNORECASE)
    if hot_spare_m:
        data["hot_spare"] = int(hot_spare_m.group(1))

    status_m = re.search(r'(?:Status|State|Состояние)[:\s]+(Optimal|Normal|Degraded|Failed|Critical|Online|Offline)', raw_output, re.IGNORECASE)
    if status_m:
        data["status"] = status_m.group(1).strip()

    data["thin_provisioning"] = bool(re.search(r'(?:Thin\s*Provisioning|thin)', raw_output, re.IGNORECASE))

    repl_m = re.search(r'(?:Replication|HyperMetro|SnapMirror)[:\s]+(\S+)', raw_output, re.IGNORECASE)
    if repl_m:
        data["replication"] = repl_m.group(1).strip()

    return data


def normalize_database_data(raw_output: str) -> dict:
    """Нормализует данные СУБД."""
    data = {
        "dbms_type": "",
        "version": "",
        "server_name": "",
        "auth_mode": "",
        "encryption": False,
        "ha_enabled": False,
    }

    if re.search(r'Microsoft\s+SQL', raw_output, re.IGNORECASE):
        data["dbms_type"] = "Microsoft SQL Server"
    elif re.search(r'PostgreSQL', raw_output, re.IGNORECASE):
        data["dbms_type"] = "PostgreSQL"
    elif re.search(r'MySQL', raw_output, re.IGNORECASE):
        data["dbms_type"] = "MySQL"
    elif re.search(r'Oracle', raw_output, re.IGNORECASE):
        data["dbms_type"] = "Oracle"

    ver_m = re.search(r'(?:SQL Server|PostgreSQL|MySQL|Oracle)\s+(?:v)?([\d\.]+[cR]?)', raw_output, re.IGNORECASE)
    if ver_m:
        data["version"] = ver_m.group(1)

    server_m = re.search(r'(?:Server|HOSTNAME)[=:]\s*(\S+)', raw_output, re.IGNORECASE)
    if server_m:
        data["server_name"] = server_m.group(1).strip()

    if re.search(r'(?:Windows\s+Authentication|integrated|AD)', raw_output, re.IGNORECASE):
        data["auth_mode"] = "Windows AD"
    elif re.search(r'(?:SQL\s+Authentication|mixed)', raw_output, re.IGNORECASE):
        data["auth_mode"] = "SQL/Mixed"

    data["encryption"] = bool(re.search(r'(?:TDE|SSL|encrypt)', raw_output, re.IGNORECASE))
    data["ha_enabled"] = bool(re.search(r'(?:Always\s*On|replication|clustering)', raw_output, re.IGNORECASE))

    return data


def build_aggregated_summary(
    devices: list[DeviceInfo],
    servers: list[ServerInfo],
    vm_info: list[VirtualizationInfo],
    storage: list[StorageInfo],
    databases: list[DatabaseInfo],
    backups: list[BackupInfo],
    antivirus: list[AntivirusInfo],
    firewalls: list[NetworkSecurityInfo],
) -> dict:
    """Строит агрегированную сводку по всем собранным данным."""
    summary = {
        "network_devices": {
            "total": len(devices),
            "by_role": {"core": 0, "distribution": 0, "access": 0, "edge": 0},
            "eol_critical": sum(1 for d in devices if d.eol_info.get("status") == "EOSL"),
            "eol_warning": sum(1 for d in devices if d.eol_info.get("status") == "End-of-Sale"),
            "no_aaa": sum(1 for d in devices if not d.aaa),
            "no_ntp": sum(1 for d in devices if not d.ntp_servers),
            "no_acl": sum(1 for d in devices if not d.acl),
        },
        "servers": {
            "total": len(servers),
            "total_ram_tb": round(sum(s.ram_total_gb for s in servers) / 1024, 2),
            "total_disk_tb": round(sum(s.disk_total_gb for s in servers) / 1024, 2),
            "eol_critical": sum(1 for s in servers if s.eol_info.get("status") == "EOSL"),
        },
        "virtualization": {
            "total_hosts": sum(v.hosts_count for v in vm_info),
            "total_vms": sum(v.vm_count for v in vm_info),
            "hypervisors": list({v.hypervisor_type for v in vm_info if v.hypervisor_type}),
        },
        "storage": {
            "total_capacity_tb": round(sum(s.total_capacity_gb for s in storage) / 1024, 2),
            "total_used_tb": round(sum(s.used_capacity_gb for s in storage) / 1024, 2),
            "devices": len(storage),
        },
        "databases": {
            "total": len(databases),
            "types": list({d.dbms_type for d in databases if d.dbms_type}),
        },
        "backup": {
            "total": len(backups),
            "with_errors": sum(1 for b in backups if b.errors),
        },
        "antivirus": {
            "total": len(antivirus),
            "centralized": sum(1 for a in antivirus if a.central_management),
        },
        "firewalls": {
            "total": len(firewalls),
            "with_vpn": sum(1 for f in firewalls if f.remote_access),
            "with_mfa": sum(1 for f in firewalls if f.mfa_enabled),
        },
        "critical_issues": [],
    }

    if summary["network_devices"]["eol_critical"] > 0:
        summary["critical_issues"].append(
            f"{summary['network_devices']['eol_critical']} сетевых устройств с EOSL"
        )
    if summary["servers"]["eol_critical"] > 0:
        summary["critical_issues"].append(
            f"{summary['servers']['eol_critical']} серверов с EOSL"
        )
    if summary["network_devices"]["no_aaa"] > 0:
        summary["critical_issues"].append(
            f"{summary['network_devices']['no_aaa']} устройств без AAA"
        )

    return summary
