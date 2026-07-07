# DefenSync — Multi-Server Behavioral Log Intelligence Platform

Enterprise-style behavioral threat detection: register multiple Linux servers via the web UI, collect logs over SSH, run Isolation Forest + Random Forest detection, and visualize per-server activity on a real-time dashboard.

## Architecture

```
User Login → Dashboard → Servers → Add Server (Test → Save)
                                        ↓
                    PostgreSQL (encrypted SSH credentials)
                                        ↓
              Background Scheduler (all active servers)
                                        ↓
         SSH Collect → Parse → Normalize → Risk Engine → Store
                                        ↓
              Isolation Forest + Random Forest → Alerts
                                        ↓
                    Dashboard (per-server metrics)
```

**SSH credentials are never read from `.env` in production.** Every Linux server is added through the DefenSync web interface.

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- One or more Linux VMs with SSH access (CentOS/RHEL/Ubuntu)

## Quick Start

### 1. Backend

```powershell
cd DefenSync
copy .env.example .env
# Set DB_* credentials and SECRET_KEY

.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python scripts\migrate_schema.py
python -m backend.database.init_db
python -m backend.main
```

API docs: http://localhost:8000/docs

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

UI: http://localhost:5173

### 3. Register Linux servers

1. Open http://localhost:5173 → **Register** / **Login**
2. Promote your user to admin:

```sql
UPDATE users SET role = 'admin' WHERE username = 'your_username';
```

3. Go to **Servers** → **Add Server**
4. Enter Server Name, Host/IP, Port, Username, Password or SSH Key
5. Click **Test Connection** — must succeed before **Save Server**
6. Click **Collect** or enable the background scheduler

### 4. Enable automatic collection

In `.env`:

```env
SCHEDULER_ENABLED=true
COLLECTION_INTERVAL_MINUTES=15
COLLECTION_TAIL_LINES=500
```

The scheduler connects to every **active** server, collects logs, runs preprocessing, and executes ML detection.

### 5. Run ML detection manually

**Detection** → **Run Detection** (requires ≥10 events in the database)

Use `python scripts\seed_demo_data.py 120` for demo data without live SSH.

## API Endpoints

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /health` | No | Health check |
| `POST /api/v1/auth/register` | No | Register user |
| `POST /api/v1/auth/token` | No | Login |
| `GET /api/v1/servers` | JWT | List servers |
| `POST /api/v1/servers/test-connection` | Admin | Test SSH before save |
| `POST /api/v1/servers` | Admin | Register server |
| `POST /api/v1/servers/{id}/test` | JWT | Test saved server |
| `POST /api/v1/servers/{id}/collect` | JWT | Collect logs |
| `POST /api/v1/collection/run` | Admin | Pipeline collection (requires `server_id`) |
| `GET /api/v1/events` | JWT | Query events (`server_id` filter) |
| `GET /api/v1/dashboard/summary` | JWT | Dashboard metrics |
| `POST /api/v1/detection/run` | JWT | Run ML detection |

## Project Structure

```
DefenSync/
├── backend/          # FastAPI, SSH collector, ML pipeline
├── frontend/         # React dashboard (Vite)
├── scripts/          # migrate_schema.py, seed_demo_data.py
└── .env              # DB, JWT, scheduler settings only
```

## ML Detection

Hybrid engine in `backend/services/detection_service.py`:

- **Rule Engine** — alerts for risk score ≥ 70
- **Isolation Forest** — unsupervised anomaly detection
- **Random Forest** — supervised suspicious/normal classification

Features include `server_id`, login time, session duration, failed login count, CPU/memory/disk usage, commands executed, and network connections.

## License

MCA Final Year Project — DefenSync Behavioral Log Intelligence System
