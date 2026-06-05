# Security Information and Event Management (SIEM) Analytics System
## Enterprise Technical Build — Phases 2 to 5

A production-grade, end-to-end Security Information and Event Management (SIEM) Analytics System featuring real-time log collection, multi-source log parsing & normalization, MySQL storage, configurable security detection rules, machine learning anomaly detection (`IsolationForest`), REST APIs, and a React SOC Security Dashboard.

---

## 🏛️ System Architecture

```
                               ┌────────────────────────────────┐
                               │     Log Sources & Agents       │
                               │ SSH auth.log / Nginx / Syslog  │
                               └──────────────┬─────────────────┘
                                              │
                                              ▼
                               ┌────────────────────────────────┐
                               │    Log Collector Agent         │
                               │ watchdog tailer & UDP:514      │
                               └──────────────┬─────────────────┘
                                              │ HTTP POST /ingest
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FastAPI Backend Engine                                 │
│                                                                                        │
│  ┌───────────────────────┐   ┌─────────────────────────┐   ┌────────────────────────┐  │
│  │ Log Normalization     │──►│ Detection Rules Engine  │──►│ ML Anomaly Engine      │  │
│  │ SSH / Nginx / Syslog  │   │ BruteForce / PortScan   │   │ IsolationForest        │  │
│  └───────────────────────┘   │ DDoS / PrivEscalation   │   └────────────────────────┘  │
│                                  └────────────┬────────────┘                            │
└───────────────────────────────────────────────┼────────────────────────────────────────┘
                                                │
                                                ▼
                               ┌────────────────────────────────┐
                               │       MySQL 8.x Database       │
                               │  logs, alerts, users, rules    │
                               └──────────────┬─────────────────┘
                                              │ REST API / JWT
                                              ▼
                               ┌────────────────────────────────┐
                               │   React SOC Dashboard          │
                               │  Recharts / Triage / PDF Export│
                               └────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### Option 1: Run via Docker Compose (Recommended)

To launch the complete containerized stack (MySQL, FastAPI Backend, Log Collector, and React Dashboard):

```bash
docker-compose up --build -d
```

Access services:
- **React Dashboard UI**: [http://localhost:3000](http://localhost:3000) *(Credentials: `admin` / `admin123`)*
- **FastAPI OpenAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Log Ingestion Endpoint**: `http://localhost:8000/api/v1/logs/ingest`

---

### Option 2: Run Locally (Standalone / Dev Mode)

#### 1. Setup Backend & Database
The backend supports automatic SQLite fallback if MySQL is not running locally.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

#### 2. Setup React Dashboard
```bash
cd dashboard
npm install
npm run dev
```

#### 3. Launch Log Collector Agent
```bash
cd collector
pip install -r requirements.txt
python log_collector.py
```

---

## ⚡ Attack Simulation & Verification

Run the included multi-scenario attack simulator script to push synthetic normal and malicious traffic through the entire pipeline:

```bash
python simulator/generate_logs.py --scenario all
```

Available simulation modes:
- `--scenario brute_force`: Simulates 12+ failed SSH login attempts from an attacker IP.
- `--scenario port_scan`: Simulates network connection probes across 25+ distinct ports.
- `--scenario ddos`: Simulates a 150+ request flood targeting a web destination.
- `--scenario privilege`: Simulates suspicious `sudo` privilege escalation commands.
- `--scenario continuous`: Generates a continuous stream of realistic mixed traffic for live dashboard demos.

---

## 📊 Core Features

1. **Multi-Source Log Normalization**: Converts raw `auth.log`, Nginx access logs, and Syslog packets into a unified JSON schema.
2. **Rule-Based Detection Engine**:
   - **Brute Force**: ≥5 login failures per IP within 5 minutes.
   - **Port Scanning**: Probes across ≥15 distinct destination ports per IP within 1 minute.
   - **DDoS Spikes**: Request bursts exceeding dynamic threshold targeting a destination IP.
   - **Privilege Escalation**: Detects sensitive `sudo` command execution.
3. **ML Anomaly Detection**: Unsupervised `IsolationForest` model extracting sliding-window features (login failures, unique ports, cyclic hour encoding) to identify novel behavioral anomalies.
4. **React SOC Security Dashboard**:
   - **Overview**: Real-time KPI counters, attack volume graphs, and recent alert feed.
   - **Logs Explorer**: Paginated, filterable table with search, severity filters, and raw JSON viewer.
   - **Alert Triage**: Incident management panel with status toggling (`open` -> `acknowledged` -> `resolved`).
   - **Analytics**: Threat intelligence charts powered by Recharts.
   - **Reports**: Downloadable Executive PDF and CSV audit exports.

---

## 🔐 Authentication & API Key
- **Default Username**: `admin`
- **Default Password**: `admin123`
- Authenticated via JWT Bearer Tokens (`/api/v1/auth/login`).
