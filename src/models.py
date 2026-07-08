from pydantic import BaseModel
from typing import Optional


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
    eol: Optional[str] = None
    status: str = "Требуется проверка"
    note: str = ""


class InventoryRecord(BaseModel):
    id: Optional[int] = None
    model: str
    vendor: str = ""
    category: str = "network"
    eol: Optional[str] = None
    eol_status: str = "Требуется проверка"
    specs: str = ""
    source_url: str = ""
    created_at: Optional[str] = None
