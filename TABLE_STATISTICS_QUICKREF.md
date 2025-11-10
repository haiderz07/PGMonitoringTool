# 📊 Table Statistics Health Feature - Quick Reference

## 🎯 Purpose
Detect missing/stale PostgreSQL table statistics that cause poor query planner decisions.

## 🚨 What Gets Detected

| Severity | Condition | Impact | Action |
|----------|-----------|--------|--------|
| 🔴 **Critical** | Never analyzed | No statistics = worst plans | `ANALYZE table;` immediately |
| 🔴 **Critical** | >20% stale | Severely outdated stats | `ANALYZE table;` soon |
| 🟠 **Warning** | 10-20% stale | Suboptimal plans likely | Schedule ANALYZE |
| 🟡 **Moderate** | 5-10% stale | Monitor closely | Plan maintenance |
| 🟢 **Healthy** | <5% stale | Statistics fresh | No action needed |

## 💻 Commands

```bash
# Run standalone check
python pg_monitor_enhanced.py --table-statistics

# Include in full monitoring (recommended)
python pg_monitor_enhanced.py --all

# View historical alerts
python pg_monitor_enhanced.py --show-alerts

# Test connectivity
python test_table_stats.py
```

## 📊 Sample Output

```
📊 Table Statistics Health (Query Planner Impact)
──────────────────────────────────────────────────────────────────────

📋 Summary:
   Status: 🟠 Warning - Statistics Need Refresh
   Total Tables Checked: 25
   🟢 Healthy: 18
   🔴 Critical Stale: 2
   🔴 Never Analyzed: 1

⚠️  Problematic Tables:
   • orders: 25% stale (125,000 modifications)
   • products: 15% stale (7,500 modifications)
   • new_table: Never analyzed

💡 Actionable Recommendations:
   🔴 HIGH: Run: ANALYZE public.orders;
   🔴 HIGH: Run: ANALYZE public.new_table;
   💡 TIP: Lower autovacuum_analyze_scale_factor for frequent updates
──────────────────────────────────────────────────────────────────────
```

## 🔧 Quick Fixes

### Analyze Specific Table
```sql
ANALYZE schema_name.table_name;
```

### Analyze All Tables
```sql
ANALYZE;
```

### Tune Autovacuum (if tables frequently stale)
```sql
-- Database level
ALTER DATABASE your_db SET autovacuum_analyze_scale_factor = 0.05;

-- Table level (large tables)
ALTER TABLE large_table SET (autovacuum_analyze_scale_factor = 0.02);
```

## 🎯 When to Use

### ✅ Always Run After:
- Bulk INSERT/UPDATE/DELETE operations
- Data migrations or imports
- Index creation/rebuilding
- Partition management

### ✅ Regular Monitoring:
- Daily checks with `--all`
- After deployment
- When queries suddenly slow down

### ✅ Troubleshooting:
- Unexpected sequential scans
- Wrong join strategies
- "Rows estimated: 1, actual: 1000000" in EXPLAIN

## 🔗 Integration

### Alert System
- **Console**: Immediate warnings during execution
- **SQLite DB**: Historical tracking in `pg_monitor_history.db`
- **Trends**: View with `--show-alerts` or `--trend 24h`

### Complements Other Features
- **Slow Queries**: Explains why queries are slow (bad stats)
- **Index Usage**: Unused indexes may be due to stale stats
- **Vacuum Health**: Focuses on ANALYZE vs VACUUM

## 📈 Metrics Tracked

| Metric | Description | Source |
|--------|-------------|--------|
| `n_mod_since_analyze` | Modifications since ANALYZE | `pg_stat_user_tables` |
| `n_live_tup` | Current row count | `pg_stat_user_tables` |
| `staleness_pct` | `(mods / rows) × 100` | Calculated |
| `last_analyze` | Manual ANALYZE timestamp | `pg_stat_user_tables` |
| `last_autoanalyze` | Auto ANALYZE timestamp | `pg_stat_user_tables` |

## 🎓 Learn More

- **Full Guide**: See `TABLE_STATISTICS_GUIDE.md`
- **Feature Details**: See `FEATURE_TABLE_STATISTICS.md`
- **PostgreSQL Docs**: [ANALYZE Command](https://www.postgresql.org/docs/current/sql-analyze.html)

## 💡 Pro Tips

1. **Run regularly**: Include in daily monitoring with `--all`
2. **Act fast**: Never-analyzed tables = immediate ANALYZE needed
3. **Tune autovacuum**: Adjust thresholds for frequently modified tables
4. **Monitor trends**: Use `--show-alerts` to see if issues are recurring
5. **After bulk ops**: Always ANALYZE after large data changes

## ⚡ Performance

- **Query Speed**: <1 second for 100+ tables
- **Lock Impact**: None (read-only monitoring)
- **ANALYZE Cost**: Seconds for most tables (samples data, doesn't read all rows)

---

**Bottom Line**: This feature catches the hidden performance killer that other tools miss - stale statistics that make your query planner make terrible decisions! 🎯
