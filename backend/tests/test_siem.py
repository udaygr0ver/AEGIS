import pytest
from app.parsers.ssh import SSHParser
from app.parsers.nginx import NginxParser
from app.parsers.syslog import SyslogParser
from app.parsers.manager import LogParserManager
from app.database import SessionLocal, engine, Base
from app.models import LogItem, AlertItem
from app.detection.rules import RuleEvaluator
from app.ml.anomaly_detector import anomaly_detector

def test_ssh_parser_failed_password():
    parser = SSHParser()
    raw = "Failed password for invalid user admin from 198.51.100.44 port 51515 ssh2"
    parsed = parser.parse(raw)
    assert parsed is not None
    assert parsed.source_type == "ssh"
    assert parsed.event_type == "login_failed"
    assert parsed.src_ip == "198.51.100.44"
    assert parsed.user == "admin"
    assert parsed.severity == "medium"

def test_ssh_parser_sudo_privilege():
    parser = SSHParser()
    raw = "sudo:   analyst : TTY=pts/0 ; PWD=/home/analyst ; USER=root ; COMMAND=/bin/bash"
    parsed = parser.parse(raw)
    assert parsed is not None
    assert parsed.event_type == "privilege_change"
    assert parsed.user == "analyst"
    assert parsed.severity == "high"

def test_nginx_parser_combined_log():
    parser = NginxParser()
    raw = '192.168.1.50 - admin [20/Jul/2026:10:30:00 +0000] "GET /api/v1/users HTTP/1.1" 200 1450 "-" "Mozilla/5.0"'
    parsed = parser.parse(raw)
    assert parsed is not None
    assert parsed.source_type == "nginx"
    assert parsed.event_type == "http_request"
    assert parsed.src_ip == "192.168.1.50"
    assert parsed.user == "admin"

def test_nginx_parser_sqli_detection():
    parser = NginxParser()
    raw = '192.168.1.50 - - [20/Jul/2026:10:30:00 +0000] "GET /products?id=1%20UNION%20SELECT%20password%20FROM%20users HTTP/1.1" 200 500 "-" "Mozilla/5.0"'
    parsed = parser.parse(raw)
    assert parsed is not None
    assert parsed.severity == "high"
    assert parsed.event_type == "web_attack"

def test_parser_manager_fallback():
    manager = LogParserManager()
    raw = "Random unformatted raw system log message with IP 10.0.0.99"
    parsed = manager.parse_log(raw)
    assert parsed is not None
    assert parsed.src_ip == "10.0.0.99"

def test_detection_rules_brute_force():
    Base.metadata.create_all(bind=engine, checkfirst=True)
    db = SessionLocal()
    try:
        # Insert 6 failed logins for IP 192.0.2.1
        for _ in range(6):
            log = LogItem(
                event_uuid=str(pytest.importorskip("uuid").uuid4()),
                source_type="ssh",
                event_type="login_failed",
                src_ip="192.0.2.1",
                dest_ip="127.0.0.1",
                message_raw="Failed password for root",
                severity="medium"
            )
            db.add(log)
        db.commit()

        evaluator = RuleEvaluator(db)
        evaluator.evaluate_brute_force(window_minutes=10, threshold=5)

        alert = db.query(AlertItem).filter(AlertItem.rule_name == "brute_force", AlertItem.src_ip == "192.0.2.1").first()
        assert alert is not None
        assert alert.severity in ("medium", "high")
    finally:
        db.close()
