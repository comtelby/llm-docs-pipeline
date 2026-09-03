
from pydantic import BaseModel


class DeviceInfo(BaseModel):
    file: str
    hostname: str = ""
    model: str = ""
    ip_mgmt: str = ""
    ip_addresses: list = []
    interfaces: list = []
    vlans: list = []
    routes: list = []
    aaa: list = []
    acl: list = []
    ntp: list = []
    snmp: list = []
    spanning_tree: list = []
    ospf: dict = {}
    vrrp: list = []
    stp_region: str = ""
    stp_instances: list = []
    tacacs_servers: list = []
    syslog_servers: list = []
    dhcp_snooping: bool = False
    port_security: bool = False
    bpdu_protection: bool = False
    ntp_servers: list = []
    eol_info: dict = {}
    full_length: int = 0


class ServerInfo(BaseModel):
    file: str
    hostname: str = ""
    model: str = ""
    ip_mgmt: str = ""
    cpu_model: str = ""
    cpu_count: int = 0
    cpu_cores: int = 0
    ram_total_gb: float = 0.0
    os_version: str = ""
    bios_version: str = ""
    ilo_version: str = ""
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0
    disk_free_pct: float = 0.0
    raid_level: str = ""
    raid_status: str = ""
    uptime: str = ""
    installed_services: list = []
    hosted_is: list = []
    eol_info: dict = {}
    source_type: str = ""


class VirtualizationInfo(BaseModel):
    file: str
    hypervisor_type: str = ""
    hypervisor_version: str = ""
    cluster_name: str = ""
    cluster_type: str = ""
    hosts_count: int = 0
    vm_count: int = 0
    host_details: list = []
    vm_details: list = []
    evc_mode: str = ""
    ha_enabled: bool = False
    ft_enabled: bool = False
    snapshots: list = []
    eol_info: dict = {}
    source_type: str = ""


class StorageInfo(BaseModel):
    file: str
    device_type: str = ""
    model: str = ""
    total_capacity_gb: float = 0.0
    used_capacity_gb: float = 0.0
    free_pct: float = 0.0
    raid_level: str = ""
    disk_count: int = 0
    hot_spare: int = 0
    status: str = ""
    controllers: list = []
    connected_servers: list = []
    replication_type: str = ""
    thin_provisioning: bool = False
    subscribed_pct: float = 0.0
    nas_model: str = ""
    nas_shares: list = []
    eol_info: dict = {}
    source_type: str = ""


class DatabaseInfo(BaseModel):
    file: str
    dbms_type: str = ""
    version: str = ""
    server_name: str = ""
    auth_mode: str = ""
    encryption: bool = False
    ha_enabled: bool = False
    ha_type: str = ""
    backup_config: str = ""
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0
    disk_free_pct: float = 0.0
    eol_info: dict = {}
    source_type: str = ""


class BackupInfo(BaseModel):
    file: str
    product: str = ""
    version: str = ""
    schedule_compliant: bool = False
    total_backup_gb: float = 0.0
    used_backup_gb: float = 0.0
    free_backup_pct: float = 0.0
    repo_type: str = ""
    repo_filesystem: str = ""
    repo_connection: str = ""
    tasks: list = []
    errors: list = []
    retention_days: int = 0
    protected_systems: list = []
    eol_info: dict = {}
    source_type: str = ""


class AntivirusInfo(BaseModel):
    file: str
    product: str = ""
    version: str = ""
    central_management: bool = False
    total_licenses: int = 0
    installed_agents: int = 0
    unprotected_count: int = 0
    mail_protection: bool = False
    device_control: bool = False
    update_schedule: str = ""
    scan_schedule: str = ""
    password_protection: bool = False
    eol_info: dict = {}
    source_type: str = ""


class NetworkSecurityInfo(BaseModel):
    file: str
    firewall_model: str = ""
    firewall_version: str = ""
    remote_access: bool = False
    vpn_type: str = ""
    vpn_auth_method: str = ""
    mfa_enabled: bool = False
    encryption_type: str = ""
    access_logging: bool = False
    eol_info: dict = {}
    source_type: str = ""


class ChecklistItem(BaseModel):
    number: str
    stage: str
    action: str
    result: str = ""
    faq: str = ""
    completed: bool = False
    data_added: bool = False
    issues: str = ""
    data_files: list = []
    normalized_data: dict = {}


class AuditProgress(BaseModel):
    total_items: int = 0
    completed_items: int = 0
    data_added_items: int = 0
    issues_count: int = 0
    sections_progress: dict = {}
    missing_data: list = []


class ScreenshotData(BaseModel):
    file: str
    text: str


class ChatRequest(BaseModel):
    prompt: str
    model: str = "qwen2.5-coder:7b"


class ChatResponse(BaseModel):
    response: str
    prompt_saved: bool = True


class FileInfo(BaseModel):
    name: str
    size_bytes: int
    modified: str


class ReportResult(BaseModel):
    status: str
    report_file: str
    path: str
    content_preview: str
    devices: int = 0
    eol_critical: int = 0
    eol_warning: int = 0
    issues_found: int = 0


class EOLRecord(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_key: str
    eol: str | None = None
    status: str = "Требуется проверка"
    note: str = ""
    vendor: str = ""
    category: str = ""


class InventoryRecord(BaseModel):
    id: int | None = None
    model: str
    vendor: str = ""
    category: str = "network"
    eol: str | None = None
    eol_status: str = "Требуется проверка"
    specs: str = ""
    source_url: str = ""
    created_at: str | None = None
