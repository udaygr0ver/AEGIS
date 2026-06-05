# Security Information and Event Management (SIEM) Analytics System
## Full Technical Build Guide — Phases 2 to 5

---

## 0. Recommended Tech Stack (decide this first)

| Layer | Technology | Why |
|---|---|---|
| Log collection agents | Python (`watchdog`, `pygtail`) or Fluent Bit / Filebeat | Lightweight, cross-platform, easy to customize |
| Ingestion service | Python (FastAPI) or Node.js (Express) | Async, good for high-throughput log ingestion |
| Message buffer (optional but recommended) | Kafka or Redis Streams | Decouples collection from processing so bursts don't overwhelm MySQL |
| Parsing / normalization | Python (regex + `grok`-style parsers, or `pygrok`) | Converts raw logs (syslog, auth.log, Apache/Nginx, Windows Event Log via `evtx`) into one schema |
| Database | MySQL 8.x | As specified — use InnoDB, partitioned tables for log volume |
| Backend API | FastAPI (Python) or Express (Node.js) | REST/GraphQL endpoints for retrieval, filtering, pagination |
| Detection engine | Python rules engine (custom) + optional Sigma rules | Brute-force, port scan, DDoS, privilege escalation logic |
| ML anomaly detection | scikit-learn (Isolation Forest, LOF) | Standard, well-documented, easy to productionize |
| Frontend | React + Vite, Recharts or Chart.js, Tailwind CSS | Dashboards, charts, reports |
| Report generation | `pdfkit`/`reportlab` (Python) or `jsPDF` (frontend) | Downloadable PDF/CSV reports |
| Auth | JWT-based API auth | Protect log data endpoints |
| Containerization | Docker + Docker Compose | Reproducible dev/prod environments |

Set this up once, in a monorepo or multi-repo structure like:

```
siem-project/
├── collector/          # Phase 2 - log collector agents
├── ingestion-api/       # Phase 2 - FastAPI ingestion + retrieval endpoints
├── detection-engine/     # Phase 3 - rules + alerting
├── ml-engine/          # Phase 5 - anomaly detection models
├── dashboard/          # Phase 4 - React frontend
├── db/                # MySQL schema, migrations
└── docker-compose.yml
```

---

## PHASE 2 — Log Collector, Parsing, Storage, APIs

### 2.1 Build the Log Collector

**Goal:** Continuously read logs from sources (syslog, auth.log, web server logs, Windows Event Logs, firewall logs) and forward them for parsing.

Steps:
1. Pick your initial log sources for the MVP — start with 2–3:
   - Linux: `/var/log/auth.log` (SSH/login attempts), `/var/log/syslog`
   - Web server: Nginx/Apache access & error logs
   - Firewall/router logs (if simulating, use a tool like `iptables` logging)
2. Write a Python collector using `watchdog` to tail files in real time:
   - Detect new lines appended to log files
   - Forward each raw line + metadata (source host, file path, timestamp read) to the ingestion API via HTTP POST, or push to a Kafka/Redis queue
3. If you want to simulate a "real" SIEM feel, add a **syslog listener** (UDP/TCP port 514) using Python's `socketserver`, so any device that can send syslog can pump data into your collector.
4. Containerize the collector so it can be deployed on multiple hosts later.

**Deliverable:** A collector service that tails/receives logs and pushes raw log lines downstream.

### 2.2 Parse Logs into a Common Schema

**Goal:** Normalize wildly different log formats into one structure so detection/storage/API layers don't care about the source.

Define a common schema, e.g.:

```json
{
  "id": "uuid",
  "timestamp": "ISO8601",
  "source_host": "string",
  "source_type": "ssh|firewall|web|windows|custom",
  "event_type": "login_failed|login_success|port_scan|http_request|...",
  "src_ip": "string",
  "dest_ip": "string",
  "src_port": "int",
  "dest_port": "int",
  "user": "string",
  "message_raw": "string",
  "severity": "low|medium|high|critical",
  "tags": ["array of strings"]
}
```

Steps:
1. Write per-source-type parsers (a "parser plugin" pattern):
   - `parsers/ssh_parser.py` — regex to extract failed/successful login attempts, source IP, username from `auth.log` lines.
   - `parsers/nginx_parser.py` — parse Combined Log Format.
   - `parsers/syslog_parser.py` — generic syslog (RFC 3164/5424) parser.
2. Use `pygrok` or handwritten regex — for auth.log lines like:
   `Failed password for invalid user admin from 192.168.1.5 port 51515 ssh2`
   extract `user=admin`, `src_ip=192.168.1.5`, `event_type=login_failed`.
3. Each parser outputs a record matching the common schema above.
4. Add a fallback "raw" parser for unrecognized formats so nothing gets dropped.

**Deliverable:** A normalization module that turns any raw log line into a common JSON schema record.

### 2.3 Store Logs in MySQL

Steps:
1. Design the schema:

```sql
CREATE DATABASE siem_db;

CREATE TABLE logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  event_uuid CHAR(36) UNIQUE,
  timestamp DATETIME(3) NOT NULL,
  source_host VARCHAR(255),
  source_type VARCHAR(50),
  event_type VARCHAR(100),
  src_ip VARCHAR(45),
  dest_ip VARCHAR(45),
  src_port INT,
  dest_port INT,
  user VARCHAR(255),
  message_raw TEXT,
  severity ENUM('low','medium','high','critical') DEFAULT 'low',
  tags JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_timestamp (timestamp),
  INDEX idx_src_ip (src_ip),
  INDEX idx_event_type (event_type),
  INDEX idx_severity (severity)
) ENGINE=InnoDB;
```

2. For log volume at scale, consider **partitioning by date** (RANGE partitioning on `timestamp`) so old logs can be archived/dropped efficiently.
3. Use an ORM (SQLAlchemy for Python) or a connection pool (`mysql-connector-python` / `PyMySQL`) for writes — batch-insert parsed records rather than one-row-per-insert for performance.
4. Set up a separate `alerts` table now (you'll need it in Phase 3):

```sql
CREATE TABLE alerts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  rule_name VARCHAR(100),
  severity ENUM('low','medium','high','critical'),
  description TEXT,
  related_log_ids JSON,
  src_ip VARCHAR(45),
  triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status ENUM('open','acknowledged','resolved') DEFAULT 'open'
);
```

**Deliverable:** Running MySQL instance with `logs` and `alerts` tables, and a write path from parser → DB.

### 2.4 Create APIs to Retrieve Logs

Steps:
1. Stand up FastAPI (or Express) with endpoints:
   - `GET /logs` — paginated, filterable by `src_ip`, `event_type`, `severity`, `date_range`
   - `GET /logs/{id}` — single log detail
   - `GET /logs/stats` — counts grouped by severity/event_type (useful later for dashboard)
   - `POST /logs/ingest` — internal endpoint the collector posts parsed logs to
2. Add pagination (`limit`/`offset` or cursor-based) — log tables get big fast.
3. Add JWT auth middleware so only authenticated dashboard/API clients can query.
4. Document endpoints with OpenAPI/Swagger (FastAPI gives this for free at `/docs`).

**Deliverable:** A working REST API layer, testable via Swagger UI or Postman, backed by MySQL.

**Phase 2 exit criteria:** You can tail a real log file → see it appear as a normalized row in MySQL within seconds → query it back through `GET /logs`.

---

## PHASE 3 — Detection Rules & Alerting

### 3.1 Detection Engine Architecture

Run this as either:
- A **polling job** (every N seconds, query recent logs from MySQL and evaluate rules), or
- A **streaming consumer** (if you added Kafka/Redis in Phase 2, consume the log stream directly) — better for real-time detection.

Start with polling for simplicity; upgrade to streaming later if needed.

### 3.2 Implement Each Rule

**Brute-force login detection**
- Logic: count `event_type = 'login_failed'` grouped by `src_ip` (and optionally `user`) within a sliding window (e.g., last 5 minutes).
- Threshold: e.g., ≥5 failed logins from the same IP in 5 minutes → trigger alert.
- SQL sketch:
```sql
SELECT src_ip, COUNT(*) as attempts
FROM logs
WHERE event_type = 'login_failed' AND timestamp > NOW() - INTERVAL 5 MINUTE
GROUP BY src_ip
HAVING attempts >= 5;
```

**Port scan detection**
- Logic: count *distinct* `dest_port` values hit by a single `src_ip` within a short window.
- Threshold: e.g., ≥15 distinct ports from one IP in 1 minute → port scan.
- Requires firewall/connection logs (or simulate with a tool like `nmap` against a test host while logging connections).

**DDoS detection**
- Logic: count total requests/connections to a single `dest_ip` (or specific service) within a short window, from many distinct source IPs.
- Threshold: e.g., request volume exceeds a baseline (use a rolling average) by some multiple, or raw count > X requests/sec.
- This is where basic anomaly detection (Phase 5) will later improve on a fixed threshold.

**Privilege escalation alerts**
- Logic: watch for specific event types like `sudo` usage, `user added to admin group`, `account privilege changed`, or Windows Security Event IDs (4728, 4732, 4756 for group membership changes).
- Pattern match on `message_raw` or a dedicated `event_type = 'privilege_change'` if your parser tags it that way in Phase 2.

### 3.3 Severity Classification

Build a simple scoring function per alert type:
- Brute-force: severity scales with attempt count (5–10 = medium, 10–50 = high, 50+ = critical).
- Port scan: severity scales with number of ports scanned.
- DDoS: severity scales with request volume vs. baseline.
- Privilege escalation: typically high/critical by default since it's inherently sensitive.

Store this as a config table or JSON rules file so thresholds are tunable without code changes:

```json
{
  "brute_force": {"window_minutes": 5, "threshold": 5, "severity_bands": {"medium": 5, "high": 10, "critical": 50}},
  "port_scan": {"window_minutes": 1, "threshold": 15},
  "ddos": {"window_minutes": 1, "multiplier_over_baseline": 5}
}
```

### 3.4 Alert Generation

1. When a rule fires, insert a row into the `alerts` table (from Phase 2.3) with `rule_name`, `severity`, `related_log_ids`, `src_ip`.
2. Deduplicate — don't fire a new alert every polling cycle for the same ongoing attack; use a cooldown window per `(rule_name, src_ip)` pair.
3. Add `GET /alerts` and `GET /alerts/{id}` API endpoints (extend Phase 2.4's API layer).
4. Optional: add a notification hook (email/Slack webhook) for `high`/`critical` alerts.

**Phase 3 exit criteria:** Simulate a brute-force attack (e.g., script that fails SSH login 10 times) and see a corresponding alert appear in the `alerts` table and via `GET /alerts` within your polling interval.

---

## PHASE 4 — React Dashboard

### 4.1 Project Setup

```bash
npm create vite@latest dashboard -- --template react
cd dashboard
npm install axios recharts react-router-dom tailwindcss jspdf
```

### 4.2 Core Pages

- **Overview/Home** — summary cards (total logs today, open alerts, critical alerts, top attacking IP).
- **Logs Explorer** — filterable, paginated table hitting `GET /logs`.
- **Alerts Panel** — list of alerts with severity color-coding, status (open/acknowledged/resolved), hitting `GET /alerts`.
- **Analytics/Charts page** (see below).
- **Reports page** — generate/download reports.

### 4.3 Charts

Use Recharts (or Chart.js) fed by new aggregation endpoints you add to the backend (extend `GET /logs/stats`):
- **Attack trends over time** — line/area chart of alert counts per day/hour, filterable by rule type.
- **Severity distribution** — pie or donut chart of alert counts by severity.
- **Top attackers** — horizontal bar chart of `src_ip` ranked by alert count (add `GET /alerts/top-attackers`).

### 4.4 Downloadable Reports

- Client-side: use `jsPDF` + `html2canvas` to export the current dashboard view as a PDF.
- Server-side (more robust): add a `GET /reports/generate?range=7d` endpoint that queries alert/log summaries and renders a PDF server-side with `reportlab` (Python) — return as a file download.
- Also offer CSV export of raw filtered logs (`GET /logs/export.csv`).

**Phase 4 exit criteria:** A live dashboard showing real alert/log data with working charts, and a "Download Report" button producing a PDF or CSV.

---

## PHASE 5 — ML Anomaly Detection, Polish, Testing, Docs

### 5.1 Machine Learning Anomaly Detection

1. Feature engineering — for each time window (e.g., per minute per `src_ip`), compute features like:
   - Number of failed logins
   - Number of distinct ports touched
   - Number of distinct destination IPs
   - Request/connection rate
   - Time-of-day (encode cyclically)
2. Train unsupervised models on historical "normal" traffic:

```python
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
import pandas as pd

# X = feature matrix built from aggregated log windows
model = IsolationForest(contamination=0.02, random_state=42)
model.fit(X_train)
predictions = model.predict(X_new)  # -1 = anomaly, 1 = normal
```

   Use LOF as a comparison/ensemble model (`novelty=True` for scoring new data after fitting on training data).
3. Periodically (e.g., every N minutes) score recent windows and feed anomalies into the same `alerts` table with `rule_name = 'ml_anomaly'`, using the model's anomaly score to set severity.
4. Retrain periodically (e.g., nightly) as traffic patterns evolve — store the model with `joblib` and version it.

### 5.2 UI Polish & Performance

- Add loading states, error boundaries, dark mode, responsive layout in React.
- Backend: add DB indexes based on actual query patterns, cache expensive aggregation queries (Redis), add rate-limiting on APIs.
- Load-test the ingestion pipeline (e.g., with `locust` or a simple log-flooding script) to confirm it holds up under volume.

### 5.3 Testing with Simulated Attack Logs

Build a **log simulator** script that generates realistic synthetic logs:
- Normal baseline traffic (logins, web requests) at low volume.
- Injected attack patterns: brute-force bursts, port-scan sequences, DDoS spikes, privilege escalation events.
- Feed these through the full pipeline (collector → parser → MySQL → detection engine → dashboard) to validate end-to-end detection accuracy, and to generate demo data.

### 5.4 Documentation & Architecture Diagrams

- Write a `README.md` per service plus a root-level architecture doc covering: data flow (collector → parser → MySQL → detection/ML → API → dashboard), schema reference, rule configuration, and deployment instructions (Docker Compose).
- Draw an architecture diagram (I can generate one for you inline if useful — just ask).
- Prepare a demo script: start services via `docker-compose up`, run the log simulator with an attack scenario, walk through the dashboard showing the alert appear live.

**Phase 5 exit criteria:** ML-based alerts appear alongside rule-based ones, the system holds up under simulated load, and you have docs + a diagram + a repeatable demo.

---

## Suggested Order of Work (if starting today)

1. Docker Compose skeleton with MySQL running.
2. Phase 2.3 (DB schema) → 2.1 (collector) → 2.2 (parser) → 2.4 (API) — in that order, since schema drives everything else.
3. Phase 3 rules, tested with manually crafted fake log entries before building the simulator.
4. Phase 4 dashboard against real data from Phase 2/3.
5. Phase 5 last, since it needs historical data from the earlier phases to train on.

---

*Want me to generate the initial `docker-compose.yml`, the MySQL schema as a `.sql` file, or a starter FastAPI project structure to kick this off?*
