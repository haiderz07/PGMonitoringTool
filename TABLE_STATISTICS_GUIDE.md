# 📊 Table Statistics Health Monitoring

## Overview

This feature monitors PostgreSQL table statistics that directly impact the query planner's ability to generate optimal execution plans. Missing or stale statistics can cause severe performance degradation even when proper indexes exist.

## Why This Matters

PostgreSQL's query planner uses table statistics to:
- **Estimate row counts** for query operations
- **Choose optimal indexes** (index scan vs sequential scan)
- **Determine join strategies** (nested loop vs hash join vs merge join)
- **Allocate memory** for sorts and hash operations

When statistics are missing or stale, the planner makes poor decisions:
- ❌ Uses sequential scans instead of index scans
- ❌ Chooses nested loops instead of hash joins (or vice versa)
- ❌ Estimates 1 row when actually millions exist
- ❌ Allocates insufficient memory causing disk spills

## What Is Checked

### 1. Never Analyzed Tables
**Problem:** Tables that have NEVER been analyzed
**Impact:** Query planner has ZERO statistics - uses default estimates (100 rows)
**Severity:** 🔴 CRITICAL

### 2. Critical Staleness (>20% modifications)
**Problem:** More than 20% of rows modified since last ANALYZE
**Impact:** Statistics severely outdated - poor performance likely
**Severity:** 🔴 CRITICAL

### 3. Warning Staleness (10-20% modifications)
**Problem:** 10-20% of rows modified since last ANALYZE
**Impact:** Statistics becoming stale - suboptimal plans possible
**Severity:** 🟠 WARNING

### 4. Moderate Staleness (5-10% modifications)
**Problem:** 5-10% of rows modified since last ANALYZE
**Impact:** Monitor closely - may need ANALYZE soon
**Severity:** 🟡 MODERATE

### 5. Healthy (<5% modifications)
**Status:** Statistics are fresh and accurate
**Severity:** 🟢 HEALTHY

## Key Metrics

### n_mod_since_analyze
Number of rows modified (INSERT/UPDATE/DELETE) since the last ANALYZE operation.

### Staleness Percentage
```
staleness_pct = (n_mod_since_analyze / n_live_tup) × 100
```

High staleness means the query planner is making decisions based on outdated information.

### last_analyze / last_autoanalyze
Timestamps showing when statistics were last collected:
- **last_analyze**: Manual `ANALYZE` command
- **last_autoanalyze**: Automatic autovacuum analyze

## Usage

### Check All Tables
```bash
python pg_monitor_enhanced.py --table-statistics
```

### Include in Full Monitoring
```bash
python pg_monitor_enhanced.py --all
```

## Sample Output

```
📊 Table Statistics Health (Query Planner Impact)
──────────────────────────────────────────────────────────────────────

📖 What This Checks:
   • Missing statistics: Tables NEVER analyzed (planner has NO data)
   • Stale statistics: Too many modifications since last ANALYZE
   • Impact: Wrong indexes, bad row estimates, poor query plans
──────────────────────────────────────────────────────────────────────

📋 Summary:
   Status: 🟠 Warning - Statistics Need Refresh
   Total Tables Checked: 25
   🟢 Healthy: 18
   🟡 Moderate Stale: 3
   🟠 Warning Stale: 2
   🔴 Critical Stale: 1
   🔴 Never Analyzed: 1

⚠️  Problematic Tables:
┌────────────┬──────────────┬──────────┬────────────┬──────────────┬──────────┬─────────┐
│ schemaname │ tablename    │ live_    │ modific... │ staleness_pct│ status   │ table_  │
│            │              │ tuples   │            │              │          │ size    │
├────────────┼──────────────┼──────────┼────────────┼──────────────┼──────────┼─────────┤
│ public     │ orders       │ 500000   │ 125000     │ 25.00        │ 🔴 Crit..│ 120 MB  │
│ public     │ products     │ 50000    │ 7500       │ 15.00        │ 🟠 Warni │ 15 MB   │
│ public     │ new_table    │ 10000    │ 0          │ 0.00         │ 🔴 Never │ 8 MB    │
└────────────┴──────────────┴──────────┴────────────┴──────────────┴──────────┴─────────┘

💡 Actionable Recommendations:

   🔴 HIGH 1 table(s) have NEVER been analyzed
      Impact: Query planner has NO statistics - may choose worst possible plans
      Action: Run: ANALYZE public.new_table; (or ANALYZE; for all tables)
      Affected: 1 table(s)

   🔴 HIGH 1 table(s) have >20% modifications since ANALYZE
      Impact: Statistics severely outdated - poor query performance likely
      Action: Run: ANALYZE public.orders;
      Affected: 1 table(s)

   🟠 MEDIUM 2 table(s) have 10-20% modifications since ANALYZE
      Impact: Statistics becoming stale - query plans may be suboptimal
      Action: Consider running ANALYZE during maintenance window
      Affected: 2 table(s)

   💡 TIP Autovacuum may not be running frequently enough
      Impact: Tables accumulating too many modifications between auto-analyzes
      Action: Consider lowering autovacuum_analyze_scale_factor (default: 0.1) 
              or autovacuum_analyze_threshold
──────────────────────────────────────────────────────────────────────
```

## How to Fix Issues

### Manual ANALYZE
```sql
-- Analyze specific table
ANALYZE schema_name.table_name;

-- Analyze all tables in database
ANALYZE;

-- Analyze only specific table (verbose)
ANALYZE VERBOSE schema_name.table_name;
```

### Adjust Autovacuum Settings

If tables frequently have stale statistics, tune autovacuum:

```sql
-- View current settings
SHOW autovacuum_analyze_scale_factor;
SHOW autovacuum_analyze_threshold;

-- Database-level tuning (requires superuser)
ALTER DATABASE your_db SET autovacuum_analyze_scale_factor = 0.05;
ALTER DATABASE your_db SET autovacuum_analyze_threshold = 50;

-- Table-specific tuning
ALTER TABLE large_table SET (
    autovacuum_analyze_scale_factor = 0.02,
    autovacuum_analyze_threshold = 100
);
```

**Defaults:**
- `autovacuum_analyze_scale_factor`: 0.1 (10% of table)
- `autovacuum_analyze_threshold`: 50 rows

**Formula:**
```
ANALYZE triggers when: 
  n_mod_since_analyze > (threshold + scale_factor * n_live_tup)
```

### Schedule Regular ANALYZE

For very large or frequently modified tables:

```sql
-- Create cron job (requires pg_cron extension)
SELECT cron.schedule('analyze-orders', '0 2 * * *', 'ANALYZE public.orders');

-- Or use external scheduler (crontab)
0 2 * * * psql -d mydb -c "ANALYZE public.orders;"
```

## Alert Integration

### Console Alerts
When running `--all` or `--table-statistics`, critical issues are displayed immediately.

### Historical Tracking
Alerts are saved to `pg_monitor_history.db`:
- Alert type: `table_statistics`
- Severity: `critical`, `warning`, or `info`
- Details: table name, staleness %, modification count

### View Alert History
```bash
# Show all alerts from last 24 hours
python pg_monitor_enhanced.py --show-alerts

# Show alerts with trend analysis
python pg_monitor_enhanced.py --trend 24h
```

## Best Practices

### 1. Monitor Regularly
Run `--table-statistics` daily or include in `--all` monitoring.

### 2. Immediate Action Needed
- **Never analyzed tables**: Run ANALYZE immediately
- **>20% stale**: Run ANALYZE during next maintenance window
- **>10% stale**: Schedule ANALYZE within 24-48 hours

### 3. Tune Autovacuum
For tables that frequently become stale:
- Lower `autovacuum_analyze_scale_factor`
- Consider table-specific settings for large tables

### 4. After Bulk Operations
Always run ANALYZE after:
- Bulk INSERT/UPDATE/DELETE operations
- Data migrations
- Index creation/rebuilding

### 5. Large Tables
For tables >1GB, consider:
- More aggressive autovacuum settings
- Scheduled ANALYZE during off-peak hours
- Partitioning to reduce analyze overhead

## Performance Impact

### ANALYZE Cost
- **Small tables (<1000 rows)**: Milliseconds
- **Medium tables (1K-1M rows)**: Seconds
- **Large tables (>1M rows)**: Minutes

ANALYZE samples tables (default 300 rows per column), so it scales sub-linearly with table size.

### When to Run
- **Off-peak hours**: For very large tables
- **After data loads**: Always
- **Before critical queries**: If statistics are stale

### Locks
ANALYZE acquires `SHARE UPDATE EXCLUSIVE` lock:
- ✅ Allows concurrent SELECT/INSERT/UPDATE/DELETE
- ❌ Blocks DDL operations (ALTER TABLE, DROP TABLE)

## Troubleshooting

### Why is autovacuum not running?
```sql
-- Check if autovacuum is enabled
SHOW autovacuum;

-- Check autovacuum activity
SELECT * FROM pg_stat_activity WHERE query LIKE '%autovacuum%';

-- Check table-specific settings
SELECT relname, reloptions 
FROM pg_class 
WHERE relname = 'your_table';
```

### Force Immediate ANALYZE
```sql
-- If autovacuum is slow
ANALYZE your_table;

-- Verbose output to see what's happening
ANALYZE VERBOSE your_table;
```

### Check Current Statistics Age
```sql
SELECT 
    schemaname,
    relname,
    last_analyze,
    last_autoanalyze,
    NOW() - GREATEST(last_analyze, last_autoanalyze) as stats_age,
    n_mod_since_analyze
FROM pg_stat_user_tables
WHERE n_live_tup > 0
ORDER BY stats_age DESC NULLS FIRST;
```

## Related PostgreSQL Documentation

- [ANALYZE Command](https://www.postgresql.org/docs/current/sql-analyze.html)
- [Autovacuum Configuration](https://www.postgresql.org/docs/current/routine-vacuuming.html#AUTOVACUUM)
- [Query Planning](https://www.postgresql.org/docs/current/planner-stats.html)
- [pg_stat_user_tables](https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ALL-TABLES-VIEW)

## Summary

Missing or stale table statistics are a **hidden performance killer**. This feature:
- ✅ Automatically detects problematic tables
- ✅ Provides severity-based prioritization
- ✅ Gives actionable ANALYZE commands
- ✅ Tracks statistics health over time
- ✅ Integrates with alert system for continuous monitoring

Run regularly to ensure your query planner always has accurate data for optimal performance!
