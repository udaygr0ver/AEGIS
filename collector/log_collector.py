import sys
import os
import time
import socketserver
import threading
import argparse
import logging
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("siem.collector")

INGEST_URL = os.getenv("INGEST_URL", "http://localhost:8000/api/v1/logs/ingest")
HOST_NAME = os.getenv("HOST_NAME", "collector-host-01")

def forward_log(raw_line: str, source_type: str = None):
    line = raw_line.strip()
    if not line:
        return
    try:
        payload = {
            "raw_message": line,
            "source_type": source_type,
            "source_host": HOST_NAME
        }
        resp = requests.post(INGEST_URL, json=payload, timeout=3)
        if resp.status_code != 200:
            logger.warning(f"Ingestion API returned status {resp.status_code}")
    except Exception as e:
        logger.error(f"Error posting log to ingestion API: {e}")

class FileTailHandler(FileSystemEventHandler):
    def __init__(self, filepath, source_type=None):
        self.filepath = os.path.abspath(filepath)
        self.source_type = source_type
        self.file_pos = 0
        if os.path.exists(self.filepath):
            self.file_pos = os.path.getsize(self.filepath)

    def on_modified(self, event):
        if os.path.abspath(event.src_path) == self.filepath:
            try:
                with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.file_pos)
                    lines = f.readlines()
                    self.file_pos = f.tell()
                    for line in lines:
                        forward_log(line, self.source_type)
            except Exception as e:
                logger.error(f"Error reading file {self.filepath}: {e}")

class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        raw_msg = data.decode('utf-8', errors='ignore')
        logger.info(f"Received syslog packet: {raw_msg[:60]}...")
        forward_log(raw_msg, source_type="syslog")

def start_syslog_server(port=514):
    try:
        server = socketserver.UDPServer(("0.0.0.0", port), SyslogUDPHandler)
        logger.info(f"Syslog UDP Listener running on port {port}...")
        server.serve_forever()
    except PermissionError:
        logger.warning(f"Permission denied for port {port}. Trying port 5140...")
        server = socketserver.UDPServer(("0.0.0.0", 5140), SyslogUDPHandler)
        logger.info(f"Syslog UDP Listener running on port 5140...")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Syslog server error: {e}")

def main():
    parser = argparse.ArgumentParser(description="SIEM Log Collector Agent")
    parser.add_argument("--watch-file", action="append", help="File to tail (e.g. /var/log/auth.log)")
    parser.add_argument("--source-type", default="custom", help="Source type hint")
    parser.add_argument("--syslog-port", type=int, default=514, help="Syslog UDP port")
    args = parser.parse_args()

    # Start Syslog Listener thread
    syslog_thread = threading.Thread(target=start_syslog_server, args=(args.syslog_port,), daemon=True)
    syslog_thread.start()

    # Start Watchdog Observer for tailed files
    observer = Observer()
    if args.watch_file:
        for fpath in args.watch_file:
            if os.path.exists(fpath):
                folder = os.path.dirname(os.path.abspath(fpath))
                handler = FileTailHandler(fpath, source_type=args.source_type)
                observer.schedule(handler, path=folder, recursive=False)
                logger.info(f"Tailing log file: {fpath}")
            else:
                logger.warning(f"Log file not found: {fpath}")

    observer.start()
    logger.info(f"Log Collector active. Ingestion URL: {INGEST_URL}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
