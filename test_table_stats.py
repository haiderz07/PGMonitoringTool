#!/usr/bin/env python3
"""
Quick test script to verify table statistics monitoring feature
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Test connection
try:
    conn = psycopg2.connect(
        host=os.getenv('PG_HOST', 'localhost'),
        port=int(os.getenv('PG_PORT', 5432)),
        database=os.getenv('PG_DATABASE', 'postgres'),
        user=os.getenv('PG_USER', 'postgres'),
        password=os.getenv('PG_PASSWORD', '')
    )
    
    cursor = conn.cursor()
    
    # Test query for table statistics
    print("Testing table statistics query...")
    print("="*70)
    
    query = """
    SELECT 
        schemaname,
        relname as tablename,
        n_live_tup as live_tuples,
        n_mod_since_analyze as modifications_since_analyze,
        last_analyze,
        last_autoanalyze,
        CASE 
            WHEN n_live_tup > 0 THEN 
                ROUND(100.0 * n_mod_since_analyze / NULLIF(n_live_tup, 0), 2)
            ELSE 0
        END as staleness_pct
    FROM pg_stat_user_tables
    WHERE n_live_tup > 0
    ORDER BY n_mod_since_analyze DESC
    LIMIT 5;
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    if results:
        print(f"✅ Query successful! Found {len(results)} tables\n")
        print("Sample results:")
        for row in results:
            schema, table, live_tuples, mods, last_analyze, last_autoanalyze, staleness = row
            print(f"\n  Table: {schema}.{table}")
            print(f"    Live tuples: {live_tuples:,}")
            print(f"    Modifications since analyze: {mods:,}")
            print(f"    Staleness: {staleness}%")
            print(f"    Last analyze: {last_analyze or 'Never (manual)'}")
            print(f"    Last autoanalyze: {last_autoanalyze or 'Never (auto)'}")
    else:
        print("ℹ️  No user tables found with data")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*70)
    print("✅ Test completed successfully!")
    print("\nTo run the full feature:")
    print("  python pg_monitor_enhanced.py --table-statistics")
    print("\nOr include in full monitoring:")
    print("  python pg_monitor_enhanced.py --all")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure:")
    print("  1. PostgreSQL is running")
    print("  2. .env file has correct credentials")
    print("  3. You have access to pg_stat_user_tables view")
