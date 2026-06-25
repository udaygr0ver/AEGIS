from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime

# Common Normalized Log Schema (from Phase 2 requirement)
class LogCreate(BaseModel):
    timestamp: Optional[datetime] = None
    source_host: Optional[str] = "localhost"
    source_type: str = "custom" # ssh, nginx, apache, syslog, windows, custom
    event_type: str = "generic" # login_failed, login_success, port_scan, http_request, privilege_change, generic
    src_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    src_port: Optional[int] = None
    dest_port: Optional[int] = None
    user: Optional[str] = None
    message_raw: str
    severity: str = "low" # low, medium, high, critical
    tags: Optional[List[str]] = []

class RawLogIngest(BaseModel):
    raw_message: str
    source_type: Optional[str] = None # Optional override if known
    source_host: Optional[str] = "localhost"

class LogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_uuid: str
    timestamp: datetime
    source_host: Optional[str]
    source_type: str
    event_type: str
    src_ip: Optional[str]
    dest_ip: Optional[str]
    src_port: Optional[int]
    dest_port: Optional[int]
    user: Optional[str]
    message_raw: str
    severity: str
    tags: Optional[List[str]] = None
    created_at: datetime

class LogPaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[LogResponse]

# Alert Schemas
class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_uuid: str
    rule_name: str
    severity: str
    title: str
    description: str
    related_log_ids: Optional[List[int]] = None
    src_ip: Optional[str]
    dest_ip: Optional[str]
    triggered_at: datetime
    status: str

class AlertStatusUpdate(BaseModel):
    status: str # open, acknowledged, resolved

class AlertPaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[AlertResponse]

# Auth Schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "analyst"

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class LoginRequest(BaseModel):
    username: str
    password: str

# Stats Schemas
class TopAttacker(BaseModel):
    src_ip: str
    alert_count: int
    log_count: int
    highest_severity: str

class SeverityCounts(BaseModel):
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0

class DashboardStats(BaseModel):
    total_logs: int
    total_alerts: int
    open_alerts: int
    critical_alerts: int
    logs_by_severity: SeverityCounts
    alerts_by_severity: SeverityCounts
    top_attackers: List[TopAttacker]
