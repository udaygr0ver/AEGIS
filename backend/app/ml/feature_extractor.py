import math
import datetime
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.models import LogItem

class FeatureExtractor:
    def __init__(self, db: Session):
        self.db = db

    def extract_ip_features(self, window_minutes: int = 5) -> Tuple[List[str], np.ndarray, List[List[int]]]:
        """
        Extract windowed behavioral features per source IP.
        Features returned per IP:
        0: total_events
        1: failed_logins
        2: distinct_ports
        3: distinct_dest_ips
        4: high_severity_events
        5: sin_hour
        6: cos_hour
        """
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=window_minutes)
        now = datetime.datetime.utcnow()
        hour = now.hour
        sin_hour = math.sin(2 * math.pi * hour / 24.0)
        cos_hour = math.cos(2 * math.pi * hour / 24.0)

        logs = self.db.query(LogItem).filter(LogItem.timestamp >= cutoff, LogItem.src_ip.isnot(None)).all()
        if not logs:
            return [], np.array([]), []

        # Group by IP in memory
        ip_data: Dict[str, Dict[str, Any]] = {}
        for l in logs:
            ip = l.src_ip
            if ip not in ip_data:
                ip_data[ip] = {
                    "total_events": 0,
                    "failed_logins": 0,
                    "distinct_ports": set(),
                    "distinct_dest_ips": set(),
                    "high_sev": 0,
                    "log_ids": []
                }
            
            ip_data[ip]["total_events"] += 1
            if l.event_type == "login_failed":
                ip_data[ip]["failed_logins"] += 1
            if l.dest_port is not None:
                ip_data[ip]["distinct_ports"].add(l.dest_port)
            if l.dest_ip is not None:
                ip_data[ip]["distinct_dest_ips"].add(l.dest_ip)
            if l.severity in ("high", "critical"):
                ip_data[ip]["high_sev"] += 1
            ip_data[ip]["log_ids"].append(l.id)

        ip_list = []
        feature_rows = []
        log_ids_list = []

        for ip, stats in ip_data.items():
            ip_list.append(ip)
            row = [
                float(stats["total_events"]),
                float(stats["failed_logins"]),
                float(len(stats["distinct_ports"])),
                float(len(stats["distinct_dest_ips"])),
                float(stats["high_sev"]),
                sin_hour,
                cos_hour
            ]
            feature_rows.append(row)
            log_ids_list.append(stats["log_ids"])

        return ip_list, np.array(feature_rows), log_ids_list
