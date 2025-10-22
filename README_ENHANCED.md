# PG-Monitor Enhanced - PostgreSQL Monitoring CLI

A **production-ready**, lightweight PostgreSQL monitoring CLI with features that are **genuinely hard for engineers to track manually**. Built with dashboard conversion in mind.

## 🎯 Why This Tool?

Engineers struggle with:
- **"Who's blocking my query?"** - Lock contention visibility
- **"Are we running out of connections?"** - Connection pool health
- **"Which indexes are wasting space?"** - Unused index detection
- **"Is my replica falling behind?"** - Replication lag tracking
- **"Why is performance degrading?"** - Historical trend analysis
- **"What caused this issue yesterday?"** - Alert history

This tool solves these problems with **automatic alerts** and **historical tracking**.

## ✨ Enhanced Features

### Core Metrics (Original)
- ✅ Query latency trends with pg_stat_statements
- ✅ Table bloat detection
- ✅ Autovacuum lag monitoring
- ✅ WAL growth tracking

### New: Hard-to-Track Metrics
- 🔒 **Lock Contention** - Shows WHO is blocking WHOM (blocking PID → blocked PID)
- 🔌 **Connection Pool Health** - Connection usage %, states breakdown, idle connections
- 📊 **Index Usage Analysis** - Unused indexes, low-usage indexes, missing index opportunities
- 🔄 **Replication Health** - Replica lag (bytes + seconds), replication slots status
- 💾 **Buffer Cache Stats** - Cache hit ratio, per-table I/O efficiency
- ⚡ **Checkpoint Statistics** - Checkpoint frequency, I/O impact

### Dashboard-Ready Features
- 📈 **Historical Data Storage** - SQLite-based metrics history for trend analysis
- ⚠️ **Smart Alerts** - Automatic threshold-based alerting with severity levels
- 📊 **Trend Visualization** - View historical metrics over time
- 🔔 **Alert History** - Track when and why alerts fired

## 🚀 Quick Start

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure Connection
```powershell
copy .env.example .env
# Edit .env with your PostgreSQL credentials
```

Example `.env`:
```env
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=myapp_db
PG_USER=postgres
PG_PASSWORD=your_password
```

### 3. Run Monitoring

**Monitor everything:**
```powershell
python pg_monitor_enhanced.py --all
```

**Specific metrics (fast checks):**
```powershell
# Check who's blocking queries
python pg_monitor_enhanced.py --locks

# Connection pool status
python pg_monitor_enhanced.py --connections

# Find unused indexes wasting space
python pg_monitor_enhanced.py --indexes

# Replication health
python pg_monitor_enhanced.py --replication

# Cache performance
python pg_monitor_enhanced.py --cache
```

**Watch mode (continuous monitoring):**
```powershell
python pg_monitor_enhanced.py --all --watch 30
```

**View historical trends:**
```powershell
python pg_monitor_enhanced.py --show-trends
```

**View recent alerts:**
```powershell
python pg_monitor_enhanced.py --show-alerts
```

**Export to JSON (for automation):**
```powershell
python pg_monitor_enhanced.py --all --output json > metrics.json
```

## 📊 Example Output

### Lock Contention Detection
```
🔒 Lock Contention - Who's Blocking Whom
╒═══════════════╤═══════════════╤══════════════════════╕
│ blocked_pid   │ blocking_pid  │ blocked_query        │
╞═══════════════╪═══════════════╪══════════════════════╡
│ 12345         │ 12340         │ UPDATE orders SET... │
│ 12346         │ 12340         │ DELETE FROM logs...  │
╘═══════════════╧═══════════════╧══════════════════════╛
```

### Connection Pool Health
```
🔌 Connection Pool Health
╒═══════════╤═══════╤═══════════╤════════════╕
│ max_conn  │ used  │ available │ pct_used   │
╞═══════════╪═══════╪═══════════╪════════════╡
│ 100       │ 85    │ 12        │ 85.00      │
╘═══════════╧═══════╧═══════════╧════════════╛
⚠️ WARNING: Connection pool at 85% capacity!
```

### Unused Indexes
```
📊 Index Usage Analysis - Unused Indexes
╒════════════════╤═══════════════╤══════════════╕
│ indexname      │ index_size    │ scans        │
╞════════════════╪═══════════════╪══════════════╡
│ idx_old_email  │ 1.2 GB        │ 0            │
│ idx_temp_data  │ 890 MB        │ 0            │
╘════════════════╧═══════════════╧══════════════╛
💡 These indexes are wasting 2.09 GB of disk space!
```

## 🎛️ All Options

```powershell
# Core metrics
--query-latency          # Slow query analysis
--table-bloat            # Table bloat detection
--autovacuum            # Vacuum lag monitoring
--wal-growth            # WAL size tracking

# Enhanced metrics (hard to track manually)
--locks                 # Lock contention details
--connections           # Connection pool health
--indexes               # Index usage analysis
--replication           # Replication health
--cache                 # Buffer cache stats
--checkpoints           # Checkpoint statistics

# Configuration
--latency-threshold 100  # Query latency threshold (ms)
--bloat-threshold 20     # Table bloat threshold (%)
--output [table|json]    # Output format
--watch 30              # Continuous monitoring (seconds)

# Historical features
--no-history            # Disable data storage
--show-trends           # View historical metrics
--show-alerts           # View alert history
```

## 📁 Data Storage

Historical data is stored in `pg_monitor_history.db` (SQLite):
- **metrics_history**: Time-series metrics for trend analysis
- **alerts_history**: Alert logs with severity and details

This database is **dashboard-ready** and can be queried directly or connected to visualization tools.

## 🔄 Dashboard Conversion Path

The tool is designed for easy dashboard conversion:

1. **Historical Data**: Already stored in SQLite with timestamps
2. **JSON API**: `--output json` for programmatic access
3. **Alert System**: Severity levels (info, warning, critical)
4. **Metrics Structure**: Normalized data format for graphing
5. **Trend Analysis**: Built-in trend calculation functions

**Future Dashboard Features:**
- Real-time graphs (cache hit ratio, connection usage)
- Alert notifications (email, Slack, webhook)
- Custom threshold configuration UI
- Multi-database monitoring
- Comparative analysis (this week vs last week)

## 🎯 Value Proposition

### For Engineers:
- ❌ **Before**: "Why is this query slow? Let me dig through logs..."
- ✅ **After**: "Ah, PID 12340 is blocking it. Let me check that query."

- ❌ **Before**: "Are we near connection limit? Let me count manually..."
- ✅ **After**: "85% pool usage, need to scale soon."

- ❌ **Before**: "Which indexes should I drop? Complex queries needed..."
- ✅ **After**: "These 5 indexes have 0 scans, wasting 3GB."

### For Teams:
- 📊 Historical trends show performance degradation over time
- ⚠️ Proactive alerts before issues become critical
- 📈 Data-driven capacity planning
- 🔍 Root cause analysis with alert history

## 🚀 Production Deployment

### Option 1: Cron Job
```powershell
# Run every 5 minutes, save to JSON
*/5 * * * * python pg_monitor_enhanced.py --all --output json > /var/log/pg_monitor.json
```

### Option 2: Systemd Service
```ini
[Unit]
Description=PostgreSQL Monitor
After=postgresql.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/pg-monitor/pg_monitor_enhanced.py --all --watch 60
Restart=always

[Install]
WantedBy=multi-user.target
```

### Option 3: Container
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY pg_monitor_enhanced.py .
CMD ["python", "pg_monitor_enhanced.py", "--all", "--watch", "30"]
```

## 📦 Installation as Package

```powershell
pip install -e .
pg-monitor --all  # Available system-wide
```

## 🤝 Contributing

This is an open-source project (MIT License). Contributions welcome!

## 📝 License

MIT License - See LICENSE file for details.

---

**Built with ❤️ for PostgreSQL engineers who need better visibility into their databases.**
