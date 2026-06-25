import re
from datetime import datetime
from typing import Optional
from app.parsers.base import BaseParser
from app.schemas import LogCreate

class FallbackParser(BaseParser):
    IP_REGEX = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

    def parse(self, raw_message: str, source_host: Optional[str] = "localhost") -> LogCreate:
        # Extract IP address if present in raw string
        ip_matches = self.IP_REGEX.findall(raw_message)
        src_ip = ip_matches[0] if ip_matches else None
        dest_ip = ip_matches[1] if len(ip_matches) > 1 else None

        return LogCreate(
            timestamp=datetime.utcnow(),
            source_host=source_host,
            source_type="custom",
            event_type="generic",
            src_ip=src_ip,
            dest_ip=dest_ip,
            message_raw=raw_message,
            severity="low",
            tags=["unparsed", "raw"]
        )
