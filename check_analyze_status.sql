-- ============================================================
-- PostgreSQL Table Statistics / ANALYZE Status Review Query
-- ============================================================
-- This query shows detailed information about table statistics
-- and helps identify tables that need ANALYZE
-- ============================================================

SELECT 
    schemaname,
    relname as tablename,
    
    -- Table size
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as table_size,
    
    -- Row counts
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    
    -- Statistics freshness
    n_mod_since_analyze as modifications_since_analyze,
    
    -- Calculate staleness percentage
    CASE 
        WHEN n_live_tup > 0 THEN 
            ROUND(100.0 * n_mod_since_analyze / NULLIF(n_live_tup, 0), 2)
        ELSE 0
    END as staleness_pct,
    
    -- Last ANALYZE timestamps
    last_analyze as last_manual_analyze,
    last_autoanalyze as last_auto_analyze,
    
    -- Most recent ANALYZE (manual or auto)
    GREATEST(last_analyze, last_autoanalyze) as most_recent_analyze,
    
    -- Time since last ANALYZE
    CASE 
        WHEN last_analyze IS NULL AND last_autoanalyze IS NULL THEN 'Never'
        ELSE 
            EXTRACT(EPOCH FROM (NOW() - GREATEST(last_analyze, last_autoanalyze)))::int || ' seconds ago'
    END as time_since_analyze,
    
    -- Human readable time
    CASE 
        WHEN last_analyze IS NULL AND last_autoanalyze IS NULL THEN 'Never'
        WHEN EXTRACT(EPOCH FROM (NOW() - GREATEST(last_analyze, last_autoanalyze))) < 3600 THEN
            ROUND(EXTRACT(EPOCH FROM (NOW() - GREATEST(last_analyze, last_autoanalyze))) / 60) || ' minutes ago'
        WHEN EXTRACT(EPOCH FROM (NOW() - GREATEST(last_analyze, last_autoanalyze))) < 86400 THEN
            ROUND(EXTRACT(EPOCH FROM (NOW() - GREATEST(last_analyze, last_autoanalyze))) / 3600) || ' hours ago'
        ELSE
            ROUND(EXTRACT(EPOCH FROM (NOW() - GREATEST(last_analyze, last_autoanalyze))) / 86400) || ' days ago'
    END as time_since_analyze_readable,
    
    -- Status indicator
    CASE
        WHEN last_analyze IS NULL AND last_autoanalyze IS NULL THEN '🔴 Never Analyzed'
        WHEN n_mod_since_analyze > n_live_tup * 0.2 THEN '🔴 Critical (>20% stale)'
        WHEN n_mod_since_analyze > n_live_tup * 0.1 THEN '🟠 Warning (10-20% stale)'
        WHEN n_mod_since_analyze > n_live_tup * 0.05 THEN '🟡 Moderate (5-10% stale)'
        ELSE '🟢 Healthy'
    END as status,
    
    -- Vacuum info (related)
    last_vacuum as last_manual_vacuum,
    last_autovacuum as last_auto_vacuum,
    
    -- Dead tuple percentage
    CASE 
        WHEN (n_live_tup + n_dead_tup) > 0 THEN
            ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2)
        ELSE 0
    END as dead_tuple_pct

FROM pg_stat_user_tables

-- Filter: Only tables with some data
WHERE n_live_tup > 0

-- Sort: Most problematic first
ORDER BY 
    -- Never analyzed first
    CASE 
        WHEN last_analyze IS NULL AND last_autoanalyze IS NULL THEN 1
        ELSE 0
    END DESC,
    -- Then by staleness percentage
    CASE 
        WHEN n_live_tup > 0 THEN 
            ROUND(100.0 * n_mod_since_analyze / NULLIF(n_live_tup, 0), 2)
        ELSE 0
    END DESC,
    -- Then by modifications count
    n_mod_since_analyze DESC;


-- ============================================================
-- ALTERNATIVE: Simplified version (essential columns only)
-- ============================================================
/*
SELECT 
    schemaname || '.' || relname as table_name,
    n_live_tup as rows,
    n_mod_since_analyze as modifications,
    ROUND(100.0 * n_mod_since_analyze / NULLIF(n_live_tup, 0), 2) as staleness_pct,
    GREATEST(last_analyze, last_autoanalyze) as last_analyzed,
    CASE
        WHEN last_analyze IS NULL AND last_autoanalyze IS NULL THEN '🔴 Never'
        WHEN n_mod_since_analyze > n_live_tup * 0.2 THEN '🔴 Critical'
        WHEN n_mod_since_analyze > n_live_tup * 0.1 THEN '🟠 Warning'
        WHEN n_mod_since_analyze > n_live_tup * 0.05 THEN '🟡 Moderate'
        ELSE '🟢 Healthy'
    END as status
FROM pg_stat_user_tables
WHERE n_live_tup > 0
ORDER BY staleness_pct DESC NULLS FIRST;
*/


-- ============================================================
-- SUMMARY: Count by status
-- ============================================================
/*
SELECT 
    CASE
        WHEN last_analyze IS NULL AND last_autoanalyze IS NULL THEN '🔴 Never Analyzed'
        WHEN n_mod_since_analyze > n_live_tup * 0.2 THEN '🔴 Critical'
        WHEN n_mod_since_analyze > n_live_tup * 0.1 THEN '🟠 Warning'
        WHEN n_mod_since_analyze > n_live_tup * 0.05 THEN '🟡 Moderate'
        ELSE '🟢 Healthy'
    END as status,
    COUNT(*) as table_count
FROM pg_stat_user_tables
WHERE n_live_tup > 0
GROUP BY status
ORDER BY 
    CASE 
        WHEN status LIKE '🔴%' THEN 1
        WHEN status LIKE '🟠%' THEN 2
        WHEN status LIKE '🟡%' THEN 3
        ELSE 4
    END;
*/


-- ============================================================
-- GENERATE ANALYZE COMMANDS for problematic tables
-- ============================================================
/*
SELECT 
    'ANALYZE ' || schemaname || '.' || relname || ';' as analyze_command,
    ROUND(100.0 * n_mod_since_analyze / NULLIF(n_live_tup, 0), 2) as staleness_pct
FROM pg_stat_user_tables
WHERE n_live_tup > 0
  AND (
      (last_analyze IS NULL AND last_autoanalyze IS NULL)  -- Never analyzed
      OR n_mod_since_analyze > n_live_tup * 0.1             -- >10% stale
  )
ORDER BY n_mod_since_analyze DESC;
*/
