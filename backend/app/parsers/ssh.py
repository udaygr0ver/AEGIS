import re
from datetime import datetime
from typing import Optional
from app.parsers.base import BaseParser
from app.schemas import LogCreate

class SSHParser(BaseParser):
    # Regex patterns for SSH auth.log and sudo commands
    FAILED_PWD = re.compile(
        r'Failed password for (invalid user )?(?P<user>\S+) from (?P<src_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) port (?P<src_port>\d+)'
    )
    ACCEPTED_PWD = re.compile(
        r'Accepted password for (?P<user>\S+) from (?P<src_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) port (?P<src_port>\d+)'
    )
    INVALID_USER = re.compile(
        r'Invalid user (?P<user>\S+) from (?P<src_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) port (?P<src_port>\d+)'
    )
    SUDO_CMD = re.compile(
        r'sudo:\s+(?P<user>\S+)\s+:\s+TTY=\S+\s+;\s+PWD=\S+\s+;\s+USER=(?P<target_user>\S+)\s+;\s+COMMAND=(?P<cmd>.+)'
    )

    def parse(self, raw_message: str, source_host: Optional[str] = "localhost") -> Optional[LogCreate]:
        # Check failed password
        m = self.FAILED_PWD.search(raw_message)
        if m:
            return LogCreate(
                timestamp=datetime.utcnow(),
                source_host=source_host,
                source_type="ssh",
                event_type="login_failed",
                src_ip=m.group("src_ip"),
                dest_ip="127.0.0.1",
                src_port=int(m.group("src_port")),
                dest_port=22,
                user=m.group("user"),
                message_raw=raw_message,
                severity="medium",
                tags=["auth", "ssh", "failure"]
            )

        # Check accepted password
        m = self.ACCEPTED_PWD.search(raw_message)
        if m:
            return LogCreate(
                timestamp=datetime.utcnow(),
                source_host=source_host,
                source_type="ssh",
                event_type="login_success",
                src_ip=m.group("src_ip"),
                dest_ip="127.0.0.1",
                src_port=int(m.group("src_port")),
                dest_port=22,
                user=m.group("user"),
                message_raw=raw_message,
                severity="low",
                tags=["auth", "ssh", "success"]
            )

        # Check invalid user
        m = self.INVALID_USER.search(raw_message)
        if m:
            return LogCreate(
                timestamp=datetime.utcnow(),
                source_host=source_host,
                source_type="ssh",
                event_type="login_failed",
                src_ip=m.group("src_ip"),
                dest_ip="127.0.0.1",
                src_port=int(m.group("src_port")),
                dest_port=22,
                user=m.group("user"),
                message_raw=raw_message,
                severity="medium",
                tags=["auth", "ssh", "invalid_user"]
            )

        # Check sudo privilege escalation
        m = self.SUDO_CMD.search(raw_message)
        if m:
            return LogCreate(
                timestamp=datetime.utcnow(),
                source_host=source_host,
                source_type="ssh",
                event_type="privilege_change",
                src_ip="127.0.0.1",
                dest_ip="127.0.0.1",
                user=m.group("user"),
                message_raw=raw_message,
                severity="high",
                tags=["sudo", "privilege_escalation", m.group("target_user")]
            )

        return None
