# 🚀 Quick Start Guide

Get PG-Monitor Enhanced running in 5 minutes!

## Step 1: Install Python Dependencies

```powershell
# From the project directory
pip install -r requirements.txt
```

**What gets installed:**
- `psycopg2-binary` - PostgreSQL database adapter
- `click` - CLI framework
- `tabulate` - Pretty table formatting
- `python-dotenv` - Environment variable management
- `colorama` - Colored terminal output

## Step 2: Configure Database Connection

```powershell
# Copy the example configuration
copy .env.example .env

# Edit .env with your database credentials
notepad .env
```

**Update these values:**
```env
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=your_database_name
PG_USER=your_username
PG_PASSWORD=your_password
```

## Step 3: Test Connection

```powershell
# Simple test - just check connections
python pg_monitor_enhanced.py --connections
```

**Expected output:**
```
✅ Connected to PostgreSQL: postgres@localhost:5432/mydb
📊 Historical data: pg_monitor_history.db

🔌 Connection Pool Health
╒═══════════╤═══════╤═══════════╤════════════╕
│ max_conn  │ used  │ available │ pct_used   │
╞═══════════╪═══════╪═══════════╪════════════╡
│ 100       │ 15    │ 82        │ 15.00      │
╘═══════════╧═══════╧═══════════╧════════════╛
```

## Step 4: Run Full Monitoring

```powershell
# Monitor everything once
python pg_monitor_enhanced.py --all
```

## Step 5: Enable Continuous Monitoring

```powershell
# Watch mode - refreshes every 30 seconds
python pg_monitor_enhanced.py --all --watch 30
```

Press `Ctrl+C` to stop.

## Common Commands

### Quick Health Checks (< 1 second each)

```powershell
# Who's blocking whom?
python pg_monitor_enhanced.py --locks

# Connection pool status
python pg_monitor_enhanced.py --connections

# Cache performance
python pg_monitor_enhanced.py --cache

# Slow queries
python pg_monitor_enhanced.py --query-latency --latency-threshold 100
```

### Deep Analysis

```powershell
# Find unused indexes (save disk space)
python pg_monitor_enhanced.py --indexes

# Check replication lag
python pg_monitor_enhanced.py --replication

# Identify bloated tables
python pg_monitor_enhanced.py --table-bloat --bloat-threshold 20
```

### Historical Analysis

```powershell
# View trends over last 24 hours
python pg_monitor_enhanced.py --show-trends

# View recent alerts
python pg_monitor_enhanced.py --show-alerts
```

### Automation / Integration

```powershell
# Export to JSON
python pg_monitor_enhanced.py --all --output json > metrics.json

# Export without saving history
python pg_monitor_enhanced.py --all --output json --no-history
```

## Troubleshooting

### "Connection failed"
- Check PostgreSQL is running: `pg_ctl status`
- Verify credentials in `.env` file
- Test connection: `psql -h localhost -U postgres`

### "pg_stat_statements not found"
- No problem! Tool automatically falls back to `pg_stat_activity`
- To enable (optional): 
  ```sql
  CREATE EXTENSION pg_stat_statements;
  ```

### "Permission denied"
- Some queries need superuser or `pg_monitor` role
- Grant access:
  ```sql
  GRANT pg_monitor TO your_username;
  ```

## Next Steps

1. **Set up scheduled monitoring** (cron/Task Scheduler)
2. **Review unused indexes** and consider dropping them
3. **Monitor trends** over a week to establish baselines
4. **Set up alerts** for critical thresholds
5. **Plan dashboard conversion** when you have enough historical data

## Need Help?

- Review `README_ENHANCED.md` for full documentation
- Check example outputs in the main README
- Report issues on GitHub

---

**You're now monitoring PostgreSQL like a pro! 🎉**
