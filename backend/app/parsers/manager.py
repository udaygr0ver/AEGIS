from typing import Optional, List
from app.parsers.base import BaseParser
from app.parsers.ssh import SSHParser
from app.parsers.nginx import NginxParser
from app.parsers.syslog import SyslogParser
from app.parsers.fallback import FallbackParser
from app.schemas import LogCreate

class LogParserManager:
    def __init__(self):
        self.parsers: List[BaseParser] = [
            SSHParser(),
            NginxParser(),
            SyslogParser()
        ]
        self.fallback = FallbackParser()

    def parse_log(self, raw_message: str, source_type: Optional[str] = None, source_host: Optional[str] = "localhost") -> LogCreate:
        # If source_type hint is given, try matching specific parser first
        if source_type:
            st = source_type.lower()
            if st == "ssh":
                res = SSHParser().parse(raw_message, source_host)
                if res: return res
            elif st in ("nginx", "apache", "web"):
                res = NginxParser().parse(raw_message, source_host)
                if res: return res
            elif st == "syslog":
                res = SyslogParser().parse(raw_message, source_host)
                if res: return res

        # Try all specialized parsers sequentially
        for parser in self.parsers:
            res = parser.parse(raw_message, source_host)
            if res:
                return res

        # Default fallback parser so no log line is lost
        return self.fallback.parse(raw_message, source_host)

parser_manager = LogParserManager()
