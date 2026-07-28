import os
import sys
import time
import random
import argparse
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("siem.simulator")

API_INGEST_URL = os.getenv("API_INGEST_URL", "http://localhost:8000/api/v1/logs/ingest")

USERNAMES = ["admin", "root", "ubuntu", "guest", "oracle", "postgres", "test", "deploy", "analyst", "developer"]
NORMAL_IPS = ["192.168.1.10", "192.168.1.15", "192.168.1.22", "10.0.0.12", "10.0.0.45", "172.16.0.8"]
ATTACK_IPS = {
    "brute_force": "198.51.100.44",
    "port_scan": "203.0.113.88",
    "ddos": "192.0.2.105",
    "privilege": "198.51.100.99"
}

HTTP_METHODS = ["GET", "POST", "PUT", "DELETE"]
HTTP_PATHS = ["/", "/index.html", "/api/v1/users", "/login", "/dashboard", "/assets/app.js", "/api/v1/health"]

def send_log(raw_msg: str, source_type: str = None):
    try:
        resp = requests.post(API_INGEST_URL, json={
            "raw_message": raw_msg,
            "source_type": source_type,
            "source_host": "simulated-server-01"
        }, timeout=3)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"Failed to post log to {API_INGEST_URL}: {e}")
        return False

def generate_normal_traffic(count: int = 10):
    logger.info(f"Generating {count} normal baseline log lines...")
    for _ in range(count):
        ip = random.choice(NORMAL_IPS)
        user = random.choice(USERNAMES)
        log_type = random.choice(["ssh_success", "nginx", "syslog"])
        
        if log_type == "ssh_success":
            port = random.randint(40000, 65000)
            msg = f"Accepted password for {user} from {ip} port {port} ssh2"
            send_log(msg, source_type="ssh")
        elif log_type == "nginx":
            method = random.choice(HTTP_METHODS)
            path = random.choice(HTTP_PATHS)
            status = random.choice([200, 200, 200, 304, 404])
            size = random.randint(200, 5000)
            msg = f'{ip} - {user} [20/Jul/2026:10:35:00 +0000] "{method} {path} HTTP/1.1" {status} {size} "-" "Mozilla/5.0"'
            send_log(msg, source_type="nginx")
        else:
            msg = f"Jul 20 10:35:00 server-01 systemd[1]: Started Periodic Background Cleanup Service."
            send_log(msg, source_type="syslog")
        time.sleep(0.05)

def simulate_brute_force(ip: str = None, attempts: int = 12):
    target_ip = ip or ATTACK_IPS["brute_force"]
    target_user = "admin"
    logger.info(f"⚡ SIMULATING BRUTE-FORCE ATTACK: {attempts} failed SSH logins from {target_ip}")
    for i in range(attempts):
        port = random.randint(50000, 60000)
        msg = f"Failed password for invalid user {target_user} from {target_ip} port {port} ssh2"
        send_log(msg, source_type="ssh")
        time.sleep(0.1)

def simulate_port_scan(ip: str = None, ports_count: int = 25):
    target_ip = ip or ATTACK_IPS["port_scan"]
    logger.info(f"⚡ SIMULATING PORT SCAN: Probing {ports_count} ports from {target_ip}")
    ports = random.sample(range(20, 1000), ports_count)
    for p in ports:
        src_port = random.randint(40000, 60000)
        msg = f"CONNECT src={target_ip}:{src_port} dst=10.0.0.1:{p}"
        send_log(msg, source_type="syslog")
        time.sleep(0.05)

def simulate_ddos(requests_count: int = 150):
    target_ip = ATTACK_IPS["ddos"]
    logger.info(f"⚡ SIMULATING DDoS SPIKE: {requests_count} request burst targeting 10.0.0.1")
    for i in range(requests_count):
        src_ip = f"192.0.2.{random.randint(1, 200)}"
        msg = f'{src_ip} - - [20/Jul/2026:10:36:00 +0000] "GET /api/v1/heavy-endpoint HTTP/1.1" 200 4500 "-" "DDoSBot/1.0"'
        send_log(msg, source_type="nginx")
        if i % 10 == 0:
            time.sleep(0.02)

def simulate_privilege_escalation():
    ip = ATTACK_IPS["privilege"]
    logger.info(f"⚡ SIMULATING PRIVILEGE ESCALATION EVENT from {ip}")
    msg = f"sudo:   analyst : TTY=pts/0 ; PWD=/home/analyst ; USER=root ; COMMAND=/bin/bash"
    send_log(msg, source_type="ssh")

def main():
    parser = argparse.ArgumentParser(description="SIEM Log & Attack Simulator")
    parser.add_argument("--scenario", choices=["normal", "brute_force", "port_scan", "ddos", "privilege", "all", "continuous"], default="all", help="Attack scenario to run")
    parser.add_argument("--interval", type=float, default=2.0, help="Continuous loop interval in seconds")
    args = parser.parse_args()

    if args.scenario == "normal":
        generate_normal_traffic(30)
    elif args.scenario == "brute_force":
        simulate_brute_force()
    elif args.scenario == "port_scan":
        simulate_port_scan()
    elif args.scenario == "ddos":
        simulate_ddos()
    elif args.scenario == "privilege":
        simulate_privilege_escalation()
    elif args.scenario == "all":
        generate_normal_traffic(15)
        simulate_brute_force()
        generate_normal_traffic(10)
        simulate_port_scan()
        generate_normal_traffic(10)
        simulate_ddos()
        simulate_privilege_escalation()
        logger.info("✅ Full attack simulation suite executed successfully.")
    elif args.scenario == "continuous":
        logger.info("🔁 Starting continuous log stream mode. Press Ctrl+C to stop.")
        try:
            step = 0
            while True:
                generate_normal_traffic(5)
                step += 1
                if step % 3 == 0:
                    simulate_brute_force(attempts=random.randint(6, 12))
                if step % 5 == 0:
                    simulate_port_scan(ports_count=random.randint(16, 30))
                if step % 8 == 0:
                    simulate_ddos(requests_count=120)
                if step % 10 == 0:
                    simulate_privilege_escalation()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("Stopped continuous log stream.")

if __name__ == "__main__":
    main()
