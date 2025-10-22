# 🐘 PG-Monitor Enhanced

**A lightweight, production-ready PostgreSQL monitoring CLI tool with intelligent insights and historical trend analysis.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PostgreSQL 12+](https://img.shields.io/badge/PostgreSQL-12%2B-blue.svg)](https://www.postgresql.org/)

## 🎯 Why This Tool?

Traditional monitoring tools either show too much or too little. **PG-Monitor Enhanced** focuses on metrics that are genuinely hard for engineers to track manually:

- 🔍 **Transaction Performance Benchmarking** - Real-time TPS/TPM with 24h/7d historical comparison
- 🔒 **Lock Contention Visibility** - See WHO is blocking WHOM instantly  
- 🐌 **Smart Slow Query Analysis** - Severity-based categorization with actionable insights
- 🔌 **Connection Pool Health** - Usage patterns and idle connection tracking
- 📊 **Index Efficiency Analysis** - Find unused indexes wasting disk space
- 🧹 **Vacuum Health Scoring** - 0-100 health score with automated recommendations
- ☁️ **Cloud-Aware Monitoring** - Auto-detects Azure, AWS, GCP, Heroku deployments
- 📈 **Historical Trend Analysis** - SQLite-based time-series storage with % change calculations

## ✨ Key Features

### 🚀 Transaction Performance & Benchmarking
```
📊 Throughput Metrics:
   🚀 TPS: 508.78
   🚀 TPM: 30,526.80
   
   📊 24h Comparison:
      Avg TPS (24h): 1,692.53
      📉 Change: -4.20%
   
   📊 7d Comparison:
      📉 Change: -4.51%
      Peak (7d): 1,777.32
      Low (7d): 1,621.45

💾 Transaction Statistics:
   📈 Rollback Rate: 0.01% 🟢 Excellent
   💀 Deadlocks: 0 🟢 Good
   💿 Cache Hit Ratio: 100.00% 🟢 Excellent
```

### 🔍 Slow Query Analysis with Logic Transparency
```
📖 Logic:
   • Uses pg_stat_statements for aggregated statistics
   • Filters queries where AVERAGE execution time > threshold
   • Shows % of total DB time (identifies bottlenecks)
   • Severity: 🔴 >10s, 🟠 >5s, 🟡 >1s, 🟢 <1s

Top Slow Queries:
   🟠 HIGH SEVERITY (5.2s avg, 1,234 calls, 15% of DB time)
   SELECT * FROM orders WHERE status = 'pending'...
```

### ☁️ Intelligent Cloud Detection
Automatically detects your deployment type:
- ✅ Azure PostgreSQL (Flexible Server)
- ✅ AWS RDS
- ✅ Google Cloud SQL
- ✅ Heroku Postgres
- ✅ On-Premise

Provides cloud-specific monitoring guidance when system metrics aren't accessible.

### 📊 Dashboard-Ready Historical Data
- SQLite-based time-series storage
- 24h/7d/30d trend analysis
- Percentage change calculations
- Peak/Low tracking
- Alert history with severity levels

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- PostgreSQL 12 or higher
- `pg_stat_statements` extension (recommended)

### Installation

#### Option 1: Clone from GitHub
```bash
git clone https://github.com/yourusername/pg-monitor-enhanced.git
cd pg-monitor-enhanced
pip install -r requirements.txt
```

#### Option 2: Direct Download
```bash
# Download the main script
curl -O https://raw.githubusercontent.com/yourusername/pg-monitor-enhanced/main/pg_monitor_enhanced.py

# Install dependencies
pip install psycopg2-binary click tabulate colorama python-dotenv
```

### Configuration

1. **Create `.env` file:**
```bash
cp .env.example .env
```

2. **Edit `.env` with your database credentials:**
```env
PG_HOST=your-postgres-host.com
PG_PORT=5432
PG_DATABASE=postgres
PG_USER=your_username
PG_PASSWORD=your_password
```

3. **Enable pg_stat_statements (recommended):**
```sql
-- Connect to your database and run:
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

**For managed services (Azure/AWS/GCP):**
- **Azure:** Go to Server Parameters → Set `pg_stat_statements.track` = `top`
- **AWS RDS:** Modify parameter group → Set `pg_stat_statements.track` = `top`
- **GCP:** Cloud SQL → Edit → Flags → Add `pg_stat_statements.track` = `top`

## 📖 Usage

### Basic Monitoring

**Check everything (recommended first run):**
```bash
python pg_monitor_enhanced.py --all
```

**Transaction performance with historical trends:**
```bash
python pg_monitor_enhanced.py --transaction-perf
```

**Slow query analysis:**
```bash
python pg_monitor_enhanced.py --query-latency
```

**Connection health:**
```bash
python pg_monitor_enhanced.py --connections
```

**Find unused indexes:**
```bash
python pg_monitor_enhanced.py --indexes
```

**Vacuum health score:**
```bash
python pg_monitor_enhanced.py --vacuum-health
```

### All Available Options

```bash
--all                  # Monitor all metrics (comprehensive report)
--summary              # Quick summary of key metrics
--query-latency        # Slow queries with severity analysis
--table-bloat          # Table bloat detection
--autovacuum           # Autovacuum lag monitoring
--wal-growth           # WAL growth tracking
--locks                # Lock contention (who's blocking whom)
--connections          # Connection pool health
--indexes              # Index usage analysis
--replication          # Replication health
--cache                # Buffer cache statistics
--checkpoints          # Checkpoint statistics
--disk-usage           # Disk usage by table
--vacuum-health        # Vacuum health score (0-100)
--system-metrics       # System metrics (CPU/Memory/I/O)
--transaction-perf     # Transaction performance benchmarking
```

### Continuous Monitoring

When you run the tool, you can choose:
- **Option 1:** One-shot mode - Check once and exit
- **Option 2:** Continuous mode - Monitor for 16 minutes (8 cycles × 2 min)

```bash
# Interactive mode
python pg_monitor_enhanced.py --all

# Choose: 2 (Continuous)
# The tool will refresh every 2 minutes for 16 minutes
```

## 🔧 Advanced Configuration

### Historical Data Storage

By default, metrics are stored in `pg_monitor_history.db` (SQLite). This enables:
- 24-hour trend comparison
- 7-day baseline tracking
- Peak/Low detection
- Alert history

**Location:** Same directory as the script

### Custom Thresholds

Edit these in `pg_monitor_enhanced.py`:
```python
# Slow query threshold (milliseconds)
threshold_ms = 100  # Default: 100ms

# Severity levels
CRITICAL = 10000  # 10 seconds
HIGH = 5000       # 5 seconds
MEDIUM = 1000     # 1 second
```

## 📊 Understanding the Output

### Health Indicators

| Indicator | Meaning |
|-----------|---------|
| 🟢 Excellent | Metric is in optimal range |
| 🟡 Normal/Good | Metric is acceptable |
| 🟠 Warning | Attention needed soon |
| 🔴 Critical | Immediate action required |

### Trend Icons

| Icon | Meaning |
|------|---------|
| 📈 | Increasing (positive/negative depending on metric) |
| 📉 | Decreasing (positive/negative depending on metric) |
| ➡️ | Stable (no significant change) |

### Severity Levels (Slow Queries)

| Icon | Severity | Threshold |
|------|----------|-----------|
| 🔴 | Critical | >10 seconds |
| 🟠 | High | >5 seconds |
| 🟡 | Medium | >1 second |
| 🟢 | Low | <1 second |

## 🎓 Examples

### Example 1: Find Performance Bottlenecks
```bash
python pg_monitor_enhanced.py --transaction-perf --query-latency
```

**What it shows:**
- Current TPS/TPM with 24h/7d comparison
- Rollback rate and deadlock count
- Cache hit ratio
- Top slow queries with severity
- Actionable performance insights

### Example 2: Diagnose Connection Issues
```bash
python pg_monitor_enhanced.py --connections --locks
```

**What it shows:**
- Connection pool usage %
- Connection states breakdown
- Idle connections
- Who's blocking whom

### Example 3: Database Maintenance Check
```bash
python pg_monitor_enhanced.py --vacuum-health --indexes --disk-usage
```

**What it shows:**
- Vacuum health score (0-100)
- Unused indexes wasting space
- Table sizes with trends
- Bloated tables

## 🌐 Cloud Provider Support

### Azure PostgreSQL Flexible Server
✅ Fully supported with automatic detection
- Detects Azure deployment automatically
- Provides Azure-specific monitoring guidance
- Shows limitations (system metrics via SQL)

**Enable pg_stat_statements:**
```bash
az postgres flexible-server parameter set \
  --resource-group <your-rg> \
  --server-name <server-name> \
  --name pg_stat_statements.track \
  --value top
```

### AWS RDS PostgreSQL
✅ Fully supported with automatic detection

**Enable pg_stat_statements:**
1. Create/modify parameter group
2. Set `pg_stat_statements.track = top`
3. Apply to instance (may require reboot)

### Google Cloud SQL
✅ Fully supported with automatic detection

**Enable pg_stat_statements:**
1. Cloud SQL → Edit instance
2. Flags → Add `pg_stat_statements.track = top`

### Heroku Postgres
✅ Fully supported with automatic detection

**pg_stat_statements usually pre-enabled on Heroku**

## 📋 Requirements

```txt
psycopg2-binary>=2.9.9
click>=8.1.7
tabulate>=0.9.0
colorama>=0.4.6
python-dotenv>=1.0.0
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Issue: "No pg_stat_statements data available"

**Solution:**
1. Check if extension is installed:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'pg_stat_statements';
   ```

2. If not installed:
   ```sql
   CREATE EXTENSION pg_stat_statements;
   ```

3. Check if tracking is enabled:
   ```sql
   SHOW pg_stat_statements.track;
   ```
   
   Should be `top` or `all`, not `none`.

4. For managed services, enable via console/CLI (see Cloud Provider Support section)

### Issue: Unicode encoding errors on Windows

**Solution:**
```powershell
$env:PYTHONIOENCODING='utf-8'
python pg_monitor_enhanced.py --all
```

### Issue: Connection refused

**Solution:**
- Check `.env` file has correct credentials
- Verify database is accessible from your network
- For cloud databases, check firewall rules

## 📚 Documentation

- [Usage Guide](USAGE_GUIDE.md) - Detailed usage instructions
- [Comparison Logic Explained](COMPARISON_LOGIC_EXPLAINED.md) - How historical comparison works
- [Architecture](ARCHITECTURE.md) - Technical architecture details
- [QA Test Report](QA_TEST_REPORT.md) - Quality assurance results

## 🎯 Roadmap

- [ ] Grafana/Prometheus export support
- [ ] JSON output format
- [ ] Email/Slack alerting
- [ ] Multi-database monitoring
- [ ] Web dashboard
- [ ] Docker container

## ⭐ Star History

If this tool helps you, please consider giving it a star! ⭐

## 👨‍💻 Author

Built with ❤️ for the PostgreSQL community

## 🙏 Acknowledgments

- PostgreSQL community for excellent documentation
- All contributors and testers

---

**Made with 🐘 PostgreSQL monitoring in mind**
