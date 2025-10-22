#!/usr/bin/env python3
"""
PG-Monitor: Lightweight PostgreSQL Monitoring CLI
Monitors: Query Latency, Table Bloat, Autovacuum Lag, WAL Growth
"""

import psycopg2
import click
import json
import time
import sys
from datetime import datetime
from tabulate import tabulate
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PGMonitor:
    """PostgreSQL Monitor Class"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.conn_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.conn = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            return True
        except Exception as e:
            click.echo(f"❌ Connection failed: {e}", err=True)
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def execute_query(self, query: str) -> List[Dict]:
        """Execute query and return results as list of dicts"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            cursor.close()
            return results
        except Exception as e:
            click.echo(f"❌ Query error: {e}", err=True)
            return []
    
    def get_query_latency(self, threshold_ms: int = 100) -> List[Dict]:
        """Get query latency trends from pg_stat_statements"""
        query = f"""
        SELECT 
            COALESCE(datname, 'N/A') as database,
            COALESCE(usename, 'N/A') as user,
            LEFT(query, 80) as query_preview,
            calls,
            ROUND(mean_exec_time::numeric, 2) as avg_time_ms,
            ROUND(max_exec_time::numeric, 2) as max_time_ms,
            ROUND(total_exec_time::numeric, 2) as total_time_ms,
            ROUND((100 * total_exec_time / SUM(total_exec_time) OVER ())::numeric, 2) as pct_total_time
        FROM pg_stat_statements pss
        LEFT JOIN pg_database pd ON pss.dbid = pd.oid
        LEFT JOIN pg_user pu ON pss.userid = pu.usesysid
        WHERE mean_exec_time > {threshold_ms}
        ORDER BY mean_exec_time DESC
        LIMIT 20;
        """
        
        # Fallback query if pg_stat_statements is not available
        fallback_query = """
        SELECT 
            datname as database,
            usename as user,
            LEFT(query, 80) as query_preview,
            state,
            EXTRACT(EPOCH FROM (NOW() - query_start)) * 1000 as runtime_ms
        FROM pg_stat_activity
        WHERE state != 'idle' 
            AND query NOT LIKE '%pg_stat_activity%'
            AND query_start IS NOT NULL
        ORDER BY query_start
        LIMIT 20;
        """
        
        try:
            results = self.execute_query(query)
            if not results:
                click.echo("ℹ️  pg_stat_statements extension not available, using pg_stat_activity")
                results = self.execute_query(fallback_query)
            return results
        except:
            return self.execute_query(fallback_query)
    
    def get_table_bloat(self, threshold_pct: int = 20) -> List[Dict]:
        """Calculate table bloat percentage"""
        query = f"""
        WITH constants AS (
            SELECT current_setting('block_size')::numeric AS bs, 23 AS hdr, 4 AS ma
        ),
        bloat_info AS (
            SELECT
                schemaname,
                tablename,
                bs * tblpages AS size_bytes,
                CASE 
                    WHEN tblpages - est_tblpages_ff > 0 
                    THEN (100 * (tblpages - est_tblpages_ff) / tblpages::float)::numeric
                    ELSE 0 
                END AS bloat_pct,
                (bs * (tblpages - est_tblpages_ff))::bigint AS bloat_bytes
            FROM (
                SELECT
                    schemaname, tablename, bs,
                    pg_total_relation_size(schemaname||'.'||tablename)::bigint / bs AS tblpages,
                    CEIL((reltuples * 
                        ((hdr + ma - 
                            CASE WHEN hdr % ma = 0 THEN ma ELSE hdr % ma END + 
                            CEIL((attlen_sum - nullhdr2 + ma - 
                                CASE WHEN nullhdr2 % ma = 0 THEN ma ELSE nullhdr2 % ma END
                            ) / ma::numeric) * ma
                        ) / (bs - 20))) AS est_tblpages_ff
                FROM (
                    SELECT
                        n.nspname AS schemaname,
                        c.relname AS tablename,
                        c.reltuples,
                        (SELECT bs FROM constants) AS bs,
                        (SELECT hdr FROM constants) AS hdr,
                        (SELECT ma FROM constants) AS ma,
                        SUM((1 - null_frac) * avg_width) AS attlen_sum,
                        MAX((1 - null_frac) * avg_width) AS nullhdr2
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    JOIN pg_stats s ON s.schemaname = n.nspname 
                        AND s.tablename = c.relname
                    WHERE c.relkind = 'r'
                        AND n.nspname NOT IN ('pg_catalog', 'information_schema')
                    GROUP BY n.nspname, c.relname, c.reltuples
                ) AS subq
            ) AS subq2
        )
        SELECT 
            schemaname,
            tablename,
            ROUND(bloat_pct, 2) as bloat_pct,
            pg_size_pretty(size_bytes) as table_size,
            pg_size_pretty(bloat_bytes) as bloat_size
        FROM bloat_info
        WHERE bloat_pct > {threshold_pct}
        ORDER BY bloat_pct DESC
        LIMIT 20;
        """
        return self.execute_query(query)
    
    def get_autovacuum_lag(self) -> List[Dict]:
        """Check tables that need autovacuum"""
        query = """
        SELECT 
            schemaname,
            relname as tablename,
            n_live_tup as live_tuples,
            n_dead_tup as dead_tuples,
            ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_pct,
            last_vacuum,
            last_autovacuum,
            CASE 
                WHEN last_autovacuum IS NULL THEN 'Never'
                ELSE EXTRACT(EPOCH FROM (NOW() - last_autovacuum))::int || ' seconds ago'
            END as autovacuum_ago
        FROM pg_stat_user_tables
        WHERE n_dead_tup > 100
        ORDER BY n_dead_tup DESC
        LIMIT 20;
        """
        return self.execute_query(query)
    
    def get_wal_growth(self) -> List[Dict]:
        """Monitor WAL growth rate"""
        query = """
        WITH wal_stats AS (
            SELECT 
                pg_current_wal_lsn() as current_lsn,
                pg_walfile_name(pg_current_wal_lsn()) as current_wal_file,
                pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0') as wal_bytes
        )
        SELECT 
            current_wal_file,
            pg_size_pretty(wal_bytes) as wal_size,
            wal_bytes,
            (SELECT count(*) FROM pg_ls_waldir()) as wal_file_count,
            pg_size_pretty((SELECT SUM(size) FROM pg_ls_waldir())) as total_wal_size
        FROM wal_stats;
        """
        
        # Additional WAL stats
        replication_query = """
        SELECT 
            client_addr,
            state,
            sync_state,
            pg_wal_lsn_diff(sent_lsn, write_lsn) as write_lag_bytes,
            pg_wal_lsn_diff(write_lsn, flush_lsn) as flush_lag_bytes,
            pg_wal_lsn_diff(flush_lsn, replay_lsn) as replay_lag_bytes
        FROM pg_stat_replication;
        """
        
        wal_info = self.execute_query(query)
        replication_info = self.execute_query(replication_query)
        
        return {
            'wal_status': wal_info,
            'replication_lag': replication_info
        }


def format_output(data: Any, format_type: str = 'table') -> str:
    """Format output as table or JSON"""
    if format_type == 'json':
        return json.dumps(data, indent=2, default=str)
    
    if isinstance(data, dict):
        output = []
        for key, value in data.items():
            output.append(f"\n{'='*60}\n{key.upper()}\n{'='*60}")
            if value:
                output.append(tabulate(value, headers='keys', tablefmt='grid'))
            else:
                output.append("No data available")
        return '\n'.join(output)
    elif isinstance(data, list) and data:
        return tabulate(data, headers='keys', tablefmt='grid')
    else:
        return "No data available"


@click.command()
@click.option('--host', default=lambda: os.getenv('PG_HOST', 'localhost'), help='PostgreSQL host')
@click.option('--port', default=lambda: int(os.getenv('PG_PORT', 5432)), help='PostgreSQL port')
@click.option('--database', default=lambda: os.getenv('PG_DATABASE', 'postgres'), help='Database name')
@click.option('--user', default=lambda: os.getenv('PG_USER', 'postgres'), help='Database user')
@click.option('--password', default=lambda: os.getenv('PG_PASSWORD', ''), help='Database password')
@click.option('--all', 'monitor_all', is_flag=True, help='Monitor all metrics')
@click.option('--query-latency', is_flag=True, help='Monitor query latency')
@click.option('--table-bloat', is_flag=True, help='Monitor table bloat')
@click.option('--autovacuum', is_flag=True, help='Monitor autovacuum lag')
@click.option('--wal-growth', is_flag=True, help='Monitor WAL growth')
@click.option('--latency-threshold', default=100, help='Query latency threshold (ms)')
@click.option('--bloat-threshold', default=20, help='Table bloat threshold (%)')
@click.option('--output', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--watch', type=int, help='Continuous monitoring interval (seconds)')
def main(host, port, database, user, password, monitor_all, query_latency, 
         table_bloat, autovacuum, wal_growth, latency_threshold, 
         bloat_threshold, output, watch):
    """PostgreSQL Lightweight Monitoring CLI"""
    
    # Initialize monitor
    monitor = PGMonitor(host, port, database, user, password)
    
    if not monitor.connect():
        sys.exit(1)
    
    click.echo(f"✅ Connected to PostgreSQL: {user}@{host}:{port}/{database}\n")
    
    # Determine what to monitor
    if not any([monitor_all, query_latency, table_bloat, autovacuum, wal_growth]):
        monitor_all = True
    
    def run_monitoring():
        """Run monitoring checks"""
        results = {}
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        click.echo(f"📊 Monitoring Report - {timestamp}")
        click.echo("="*60)
        
        if monitor_all or query_latency:
            click.echo("\n🔍 Query Latency Trends (threshold: {}ms)".format(latency_threshold))
            data = monitor.get_query_latency(latency_threshold)
            results['query_latency'] = data
            click.echo(format_output(data, output))
        
        if monitor_all or table_bloat:
            click.echo("\n💾 Table Bloat (threshold: {}%)".format(bloat_threshold))
            data = monitor.get_table_bloat(bloat_threshold)
            results['table_bloat'] = data
            click.echo(format_output(data, output))
        
        if monitor_all or autovacuum:
            click.echo("\n🧹 Autovacuum Lag")
            data = monitor.get_autovacuum_lag()
            results['autovacuum_lag'] = data
            click.echo(format_output(data, output))
        
        if monitor_all or wal_growth:
            click.echo("\n📝 WAL Growth Rate")
            data = monitor.get_wal_growth()
            results['wal_growth'] = data
            click.echo(format_output(data, output))
        
        return results
    
    try:
        if watch:
            # Continuous monitoring mode
            click.echo(f"\n🔄 Watching (refresh every {watch}s, Ctrl+C to stop)\n")
            while True:
                run_monitoring()
                time.sleep(watch)
                click.clear()
        else:
            # Single run
            run_monitoring()
    
    except KeyboardInterrupt:
        click.echo("\n\n👋 Monitoring stopped")
    finally:
        monitor.close()


if __name__ == '__main__':
    main()
