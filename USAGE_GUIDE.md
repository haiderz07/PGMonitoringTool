# Usage Guide - Load Generator + Monitoring

## 🚀 Quick Start Options

### Option 1: One-Shot Mode (Single Run)

**Load Generator:**
```powershell
python heavy_load_generator.py
# Choose: 1 (One-shot mode)
```
- Loads 100K customers + 1M orders
- Runs operations once and exits
- Good for: Testing, benchmarking

**Monitor:**
```powershell
python pg_monitor_enhanced.py --all
# Choose: 1 (One-shot mode)
```
- Shows snapshot of current state
- Exits after displaying results

---

### Option 2: Continuous Mode (16 Minutes)

**Terminal 1 - Load Generator:**
```powershell
python heavy_load_generator.py
# Choose: 2 (Continuous mode)
```
- Loads initial data (100K customers + 1M orders)
- Runs **8 cycles** over **16 minutes** (2-min intervals)
- Each cycle: Updates → Queries → Deletes → Inserts
- Auto-stops after 16 minutes (or press Ctrl+C to stop early)

**Terminal 2 - Monitor:**
```powershell
python pg_monitor_enhanced.py --all
# Choose: 2 (Continuous mode)
```
- Refreshes **8 times** over **16 minutes** (2-min intervals)
- Shows real-time metrics synchronized with load
- Auto-stops after 16 minutes (or press Ctrl+C to stop early)

**Terminal 2 - Monitor (Custom interval):**
```powershell
python pg_monitor_enhanced.py --all --watch 10
```
- Refreshes every 10 seconds continuously
- Runs until you press Ctrl+C
- Good for: Real-time debugging

---

## 📊 What You'll See

### Load Generator Output:
```
Choose mode:
  1. One-shot - Load data once and exit
  2. Continuous - Run for 16 minutes (8 cycles × 2 min intervals)

✅ Continuous mode selected - Will run 8 cycles (16 minutes total)

🚀 Starting bulk insert of 1,000,000 orders...
   Progress: 50.0% | Inserted: 500,000 | Rate: 14,964 rows/sec

🔄 CYCLE 1/8 - Continuous Load Operations
   Updates: 10,000 | Rate: 454 updates/sec

✅ Cycle 1/8 complete! Next cycle in 2 minutes...
   Remaining: 7 cycles (14 minutes)

...

✅ ALL CYCLES COMPLETE! (8 cycles, 16 minutes)
```

### Monitor Output:
```
Choose monitoring mode:
  1. One-shot - Check metrics once and exit
  2. Continuous - Monitor for 16 minutes (8 refreshes × 2 min)

✅ Continuous mode - Will refresh 8 times (16 minutes total)

==================================================
Refresh 1/8
==================================================

CONNECTION POOL HEALTH
Total: 859 | Used: 25 (2.91%) | Available: 834

⏳ Next refresh in 120s...

...

==================================================
✅ Monitoring complete! (8 refreshes, 16 minutes)
==================================================
```

---

## 🎯 Specific Monitoring Commands

### Connection Pool Only:
```powershell
python pg_monitor_enhanced.py --connections
```

### Query Performance:
```powershell
python pg_monitor_enhanced.py --query-latency
```

### Table Bloat:
```powershell
python pg_monitor_enhanced.py --table-bloat
```

### Everything:
```powershell
python pg_monitor_enhanced.py --all
```

---

## 💡 Pro Tips

1. **Start monitoring FIRST**, then load generator
2. **Continuous mode** = Synchronized 16-min run (8 cycles × 2 min)
3. **Watch mode** = Custom intervals, runs until Ctrl+C
4. **One-shot mode** = Quick snapshot, instant results
5. Use `--no-history` to skip SQLite storage for faster results

---

## 🛑 How to Stop

- **Continuous mode**: Auto-stops after 16 minutes
- **Anytime**: Press **Ctrl+C** to stop early
- **Watch mode**: Only stops with Ctrl+C

---

## ⏱️ Timeline

| Mode | Duration | Intervals |
|------|----------|-----------|
| One-shot | ~2 minutes | 1 run |
| Continuous | 16 minutes | 8 × 2 min |
| Watch (custom) | Until Ctrl+C | User defined |

---

## 📈 Expected Performance

| Operation | Rate |
|-----------|------|
| Insert customers | ~11,700 rows/sec |
| Insert orders | ~14,700 rows/sec |
| Updates | ~450 updates/sec |
| Complex queries | ~1 query/sec |

---

## 🔍 What Gets Monitored

✅ Connection pool usage (% of max)
✅ Buffer cache hit ratio
✅ Query latency (pg_stat_statements)
✅ Table bloat (dead tuples %)
✅ Lock contention (blocking queries)
✅ Index usage (unused indexes)
✅ WAL growth rate
✅ Checkpoint statistics
✅ Autovacuum lag
✅ Replication health

---

## 🗂️ Files Created

- `load_test_customers` - 100K records
- `load_test_orders` - 1M records (maintained during continuous mode)
- `pg_monitor_history.db` - SQLite historical data
