import re
from datetime import datetime
from typing import Optional
from app.parsers.base import BaseParser
from app.schemas import LogCreate

class NginxParser(BaseParser):
    # Combined Log Format regex
    NGINX_LOG = re.compile(
        r'^(?P<src_ip>\S+)\s+\S+\s+(?P<user>\S+)\s+\[(?P<time>[^\]]+)\]\s+"(?P<method>\S+)\s+(?P<path>\S+)\s+HTTP/[0-9.]+"\s+(?P<status>\d{3})\s+(?P<bytes>\d+)'
    )

    def parse(self, raw_message: str, source_host: Optional[str] = "localhost") -> Optional[LogCreate]:
        m = self.NGINX_LOG.search(raw_message)
        if m:
            status_code = int(m.group("status"))
            user = m.group("user") if m.group("user") != "-" else None
            path = m.group("path")
            
            severity = "low"
            event_type = "http_request"
            tags = ["web", "http", m.group("method").lower()]

            if status_code in (401, 403):
                severity = "medium"
                tags.append("access_denied")
            elif status_code >= 500:
                severity = "medium"
                tags.append("server_error")

            # Check suspicious payload keywords (SQLi, XSS, Path Traversal)
            if any(sqli in path.lower() for sqli in ["union", "select", "'or'", "--", "drop", "<script>"]):
                severity = "high"
                event_type = "web_attack"
                tags.append("injection_attempt")

            return LogCreate(
                timestamp=datetime.utcnow(),
                source_host=source_host,
                source_type="nginx",
                event_type=event_type,
                src_ip=m.group("src_ip"),
                dest_ip="127.0.0.1",
                dest_port=80,
                user=user,
                message_raw=raw_message,
                severity=severity,
                tags=tags
            )
        return None
