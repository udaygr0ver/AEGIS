import re
from datetime import datetime
from typing import Optional
from app.parsers.base import BaseParser
from app.schemas import LogCreate

class SyslogParser(BaseParser):
    SYSLOG_REGEX = re.compile(
        r'^(<(?P<pri>\d+)>)?(?P<timestamp>[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<tag>[a-zA-Z0-9_\-\[\.\/\\]+):\s+(?P<msg>.+)$'
    )
    # Firewall / Port probe pattern
    CONN_LOG = re.compile(
        r'CONNECT src=(?P<src_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(?P<src_port>\d+)\s+dst=(?P<dest_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(?P<dest_port>\d+)'
    )

    def parse(self, raw_message: str, source_host: Optional[str] = "localhost") -> Optional[LogCreate]:
        conn_match = self.CONN_LOG.search(raw_message)
        if conn_match:
            return LogCreate(
                timestamp=datetime.utcnow(),
                source_host=source_host,
                source_type="syslog",
                event_type="connection_attempt",
                src_ip=conn_match.group("src_ip"),
                dest_ip=conn_match.group("dest_ip"),
                src_port=int(conn_match.group("src_port")),
                dest_port=int(conn_match.group("dest_port")),
                message_raw=raw_message,
                severity="low",
                tags=["network", "firewall", "syslog"]
            )

        syslog_match = self.SYSLOG_REGEX.search(raw_message)
        if syslog_match:
            msg = syslog_match.group("msg")
            host = syslog_match.group("host") or source_host
            tag = syslog_match.group("tag")
            return LogCreate(
                timestamp=datetime.utcnow(),
                source_host=host,
                source_type="syslog",
                event_type="generic",
                message_raw=raw_message,
                severity="low",
                tags=["syslog", tag]
            )
        return None
