import datetime
import uuid
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, distinct
from app.models import LogItem, AlertItem, RuleConfig

class RuleEvaluator:
    def __init__(self, db: Session):
        self.db = db

    def _is_in_cooldown(self, rule_name: str, src_ip: Optional[str], cooldown_minutes: int = 5) -> bool:
        if not src_ip:
            return False
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=cooldown_minutes)
        recent_alert = (
            self.db.query(AlertItem)
            .filter(
                AlertItem.rule_name == rule_name,
                AlertItem.src_ip == src_ip,
                AlertItem.triggered_at >= cutoff
            )
            .first()
        )
        return recent_alert is not None

    def evaluate_brute_force(self, window_minutes: int = 5, threshold: int = 5):
        """Rule 1: Brute-Force Login Detection"""
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=window_minutes)
        
        # Group failed logins by src_ip
        results = (
            self.db.query(
                LogItem.src_ip,
                func.count(LogItem.id).label('attempt_count')
            )
            .filter(
                LogItem.event_type == 'login_failed',
                LogItem.timestamp >= cutoff,
                LogItem.src_ip.isnot(None)
            )
            .group_by(LogItem.src_ip)
            .having(func.count(LogItem.id) >= threshold)
            .all()
        )

        for src_ip, attempts in results:
            if self._is_in_cooldown("brute_force", src_ip, cooldown_minutes=5):
                continue

            # Fetch matching log IDs
            matching_logs = (
                self.db.query(LogItem.id)
                .filter(
                    LogItem.event_type == 'login_failed',
                    LogItem.src_ip == src_ip,
                    LogItem.timestamp >= cutoff
                )
                .all()
            )
            log_ids = [l[0] for l in matching_logs]

            # Dynamic severity rating
            severity = "medium"
            if attempts >= 50:
                severity = "critical"
            elif attempts >= 15:
                severity = "high"

            alert = AlertItem(
                alert_uuid=str(uuid.uuid4()),
                rule_name="brute_force",
                severity=severity,
                title=f"SSH Brute-Force Attack Detected from {src_ip}",
                description=f"Detected {attempts} failed login attempts from IP {src_ip} within the last {window_minutes} minutes.",
                related_log_ids=log_ids[:100],
                src_ip=src_ip,
                dest_ip="127.0.0.1",
                triggered_at=datetime.datetime.utcnow(),
                status="open"
            )
            self.db.add(alert)

        self.db.commit()

    def evaluate_port_scan(self, window_minutes: int = 1, threshold: int = 15):
        """Rule 2: Port Scan Detection"""
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=window_minutes)

        # Count distinct destination ports touched per src_ip
        results = (
            self.db.query(
                LogItem.src_ip,
                func.count(distinct(LogItem.dest_port)).label('distinct_ports')
            )
            .filter(
                LogItem.timestamp >= cutoff,
                LogItem.src_ip.isnot(None),
                LogItem.dest_port.isnot(None)
            )
            .group_by(LogItem.src_ip)
            .having(func.count(distinct(LogItem.dest_port)) >= threshold)
            .all()
        )

        for src_ip, distinct_ports in results:
            if self._is_in_cooldown("port_scan", src_ip, cooldown_minutes=3):
                continue

            matching_logs = (
                self.db.query(LogItem.id)
                .filter(
                    LogItem.src_ip == src_ip,
                    LogItem.timestamp >= cutoff
                )
                .all()
            )
            log_ids = [l[0] for l in matching_logs]

            severity = "high" if distinct_ports >= 30 else "medium"

            alert = AlertItem(
                alert_uuid=str(uuid.uuid4()),
                rule_name="port_scan",
                severity=severity,
                title=f"Port Scan Activity Detected from {src_ip}",
                description=f"Detected probe across {distinct_ports} distinct destination ports from IP {src_ip} in under {window_minutes} minute(s).",
                related_log_ids=log_ids[:100],
                src_ip=src_ip,
                dest_ip="127.0.0.1",
                triggered_at=datetime.datetime.utcnow(),
                status="open"
            )
            self.db.add(alert)

        self.db.commit()

    def evaluate_ddos(self, window_minutes: int = 1, threshold: int = 100):
        """Rule 3: DDoS Spike Detection"""
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=window_minutes)

        results = (
            self.db.query(
                LogItem.dest_ip,
                func.count(LogItem.id).label('req_count'),
                func.count(distinct(LogItem.src_ip)).label('distinct_sources')
            )
            .filter(
                LogItem.timestamp >= cutoff,
                LogItem.dest_ip.isnot(None)
            )
            .group_by(LogItem.dest_ip)
            .having(func.count(LogItem.id) >= threshold)
            .all()
        )

        for dest_ip, req_count, distinct_sources in results:
            if self._is_in_cooldown("ddos_spike", dest_ip, cooldown_minutes=2):
                continue

            matching_logs = (
                self.db.query(LogItem.id)
                .filter(
                    LogItem.dest_ip == dest_ip,
                    LogItem.timestamp >= cutoff
                )
                .limit(100)
                .all()
            )
            log_ids = [l[0] for l in matching_logs]

            alert = AlertItem(
                alert_uuid=str(uuid.uuid4()),
                rule_name="ddos_spike",
                severity="critical",
                title=f"DDoS Request Spike Targetting {dest_ip}",
                description=f"High-volume HTTP/Network traffic flood ({req_count} requests from {distinct_sources} distinct IPs) detected targeting {dest_ip}.",
                related_log_ids=log_ids,
                src_ip=f"Multiple ({distinct_sources} IPs)",
                dest_ip=dest_ip,
                triggered_at=datetime.datetime.utcnow(),
                status="open"
            )
            self.db.add(alert)

        self.db.commit()

    def evaluate_privilege_escalation(self, window_minutes: int = 5):
        """Rule 4: Privilege Escalation Alerting"""
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=window_minutes)

        escalation_logs = (
            self.db.query(LogItem)
            .filter(
                LogItem.event_type == 'privilege_change',
                LogItem.timestamp >= cutoff
            )
            .all()
        )

        for log in escalation_logs:
            if self._is_in_cooldown("privilege_escalation", log.src_ip or log.user, cooldown_minutes=5):
                continue

            alert = AlertItem(
                alert_uuid=str(uuid.uuid4()),
                rule_name="privilege_escalation",
                severity="critical",
                title=f"Privilege Escalation Event by User '{log.user or 'unknown'}'",
                description=f"Sensitive administrative privilege action detected: {log.message_raw}",
                related_log_ids=[log.id],
                src_ip=log.src_ip or "127.0.0.1",
                dest_ip=log.dest_ip or "127.0.0.1",
                triggered_at=datetime.datetime.utcnow(),
                status="open"
            )
            self.db.add(alert)

        self.db.commit()
