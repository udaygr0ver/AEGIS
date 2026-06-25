import datetime
import uuid
import json
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Enum, JSON, Boolean
from app.database import Base

class LogItem(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.datetime.utcnow)
    source_host = Column(String(255), default="localhost")
    source_type = Column(String(50), nullable=False, index=True) # ssh, nginx, apache, syslog, windows, custom
    event_type = Column(String(100), nullable=False, index=True) # login_failed, login_success, port_scan, http_request, privilege_change, generic
    src_ip = Column(String(45), nullable=True, index=True)
    dest_ip = Column(String(45), nullable=True, index=True)
    src_port = Column(Integer, nullable=True)
    dest_port = Column(Integer, nullable=True)
    user = Column(String(255), nullable=True)
    message_raw = Column(Text, nullable=False)
    severity = Column(Enum('low', 'medium', 'high', 'critical', name='log_severity_enum'), default='low', index=True)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AlertItem(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    rule_name = Column(String(100), nullable=False)
    severity = Column(Enum('low', 'medium', 'high', 'critical', name='alert_severity_enum'), default='medium', index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    related_log_ids = Column(JSON, nullable=True)
    src_ip = Column(String(45), nullable=True, index=True)
    dest_ip = Column(String(45), nullable=True)
    triggered_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    status = Column(Enum('open', 'acknowledged', 'resolved', name='alert_status_enum'), default='open', index=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum('admin', 'analyst', 'viewer', name='user_role_enum'), default='analyst')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RuleConfig(Base):
    __tablename__ = "rule_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rule_name = Column(String(100), unique=True, nullable=False)
    enabled = Column(Boolean, default=True)
    window_minutes = Column(Integer, default=5)
    threshold = Column(Integer, default=5)
    severity = Column(Enum('low', 'medium', 'high', 'critical', name='rule_severity_enum'), default='high')
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
