#!/usr/bin/env python3
"""
PG-Monitor Enhanced: PostgreSQL Monitoring CLI with Dashboard-Ready Features
Monitors critical metrics that are hard for engineers to track manually
"""

import psycopg2
import click
import json
import time
import sys
import sqlite3
from datetime import datetime, timedelta
from tabulate import tabulate
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class MetricsStorage:
    """SQLite storage for historical metrics (dashboard-ready)"""
    
    def __init__(self, db_path: str = "pg_monitor_history.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Metrics history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT NOT NULL,
                metric_name TEXT,
                metric_value REAL,
                metadata TEXT
            )
        """)
        
        # Alerts history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT NOT NULL,
                severity TEXT,
                message TEXT,
                details TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_metric(self, metric_type: str, metric_name: str, 
                   metric_value: float, metadata: Optional[Dict] = None):
        """Save a metric to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert to float to handle Decimal types from PostgreSQL
        metric_value_float = float(metric_value) if metric_value is not None else None
        
        cursor.execute("""
            INSERT INTO metrics_history (metric_type, metric_name, metric_value, metadata)
            VALUES (?, ?, ?, ?)
        """, (metric_type, metric_name, metric_value_float, json.dumps(metadata) if metadata else None))
        
        conn.commit()
        conn.close()
    
    def save_alert(self, alert_type: str, severity: str, message: str, details: Optional[Dict] = None):
        """Save an alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert any Decimal types in details to float for JSON serialization
        if details:
            details = {k: float(v) if hasattr(v, '__float__') and not isinstance(v, bool) else v 
                      for k, v in details.items()}
        
        cursor.execute("""
            INSERT INTO alerts_history (alert_type, severity, message, details)
            VALUES (?, ?, ?, ?)
        """, (alert_type, severity, message, json.dumps(details, default=str) if details else None))
        
        conn.commit()
        conn.close()
    
    def get_metric_trend(self, metric_type: str, hours: int = 24) -> List[Dict]:
        """Get metric trend for last N hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT timestamp, metric_name, metric_value, metadata
            FROM metrics_history
            WHERE metric_type = ? AND timestamp > ?
            ORDER BY timestamp DESC
        """, (metric_type, since.isoformat()))
        
        results = [
            {
                'timestamp': row[0],
                'metric_name': row[1],
                'metric_value': row[2],
                'metadata': json.loads(row[3]) if row[3] else {}
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return results
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT timestamp, alert_type, severity, message, details
            FROM alerts_history
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """, (since.isoformat(),))
        
        results = [
            {
                'timestamp': row[0],
                'alert_type': row[1],
                'severity': row[2],
                'message': row[3],
                'details': json.loads(row[4]) if row[4] else {}
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return results
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert summary with counts by severity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM alerts_history
            WHERE timestamp > ?
            GROUP BY severity
            ORDER BY 
                CASE severity 
                    WHEN 'critical' THEN 1
                    WHEN 'warning' THEN 2
                    WHEN 'info' THEN 3
                END
        """, (since.isoformat(),))
        
        summary = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get most recent critical alerts
        cursor.execute("""
            SELECT alert_type, message, timestamp
            FROM alerts_history
            WHERE timestamp > ? AND severity = 'critical'
            ORDER BY timestamp DESC
            LIMIT 5
        """, (since.isoformat(),))
        
        critical_alerts = [
            {'type': row[0], 'message': row[1], 'timestamp': row[2]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return {
            'summary': summary,
            'critical_alerts': critical_alerts,
            'total': sum(summary.values())
        }
    
    def get_table_growth_trend(self, hours: int = 168) -> List[Dict]:
        """Get table size growth trend (default 7 days)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT 
                metric_name as tablename,
                MIN(metric_value) as min_size,
                MAX(metric_value) as max_size,
                MAX(metric_value) - MIN(metric_value) as growth,
                COUNT(*) as samples
            FROM metrics_history
            WHERE metric_type = 'table_size' AND timestamp > ?
            GROUP BY metric_name
            HAVING COUNT(*) > 1
            ORDER BY growth DESC
            LIMIT 10
        """, (since.isoformat(),))
        
        results = [
            {
                'tablename': row[0],
                'min_size_mb': round(row[1], 2),
                'max_size_mb': round(row[2], 2),
                'growth_mb': round(row[3], 2),
                'samples': row[4]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return results
    
    def get_metric_comparison(self, metric_type: str, metric_name: str, hours: int = 24) -> Dict[str, Any]:
        """Compare current vs past average for a specific metric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT 
                AVG(metric_value) as avg_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value,
                COUNT(*) as samples
            FROM metrics_history
            WHERE metric_type = ? AND metric_name = ? AND timestamp > ?
        """, (metric_type, metric_name, since.isoformat()))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] is not None:
            return {
                'avg': round(row[0], 2),
                'min': round(row[1], 2),
                'max': round(row[2], 2),
                'samples': row[3]
            }
        return None


class PGMonitorEnhanced:
    """Enhanced PostgreSQL Monitor with dashboard-ready features"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str,
                 enable_history: bool = True):
        self.conn_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.conn = None
        self.storage = MetricsStorage() if enable_history else None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            return True
        except Exception as e:
            click.echo(f"❌ Connection failed: {e}", err=True)
            return False
    
    def cleanup_aborted_transactions(self, idle_seconds: int = 10) -> int:
        """Cleanup aborted transactions that are idle for too long"""
        query = f"""
        SELECT 
            pid,
            usename,
            datname,
            state,
            EXTRACT(EPOCH FROM (NOW() - state_change))::int as idle_seconds
        FROM pg_stat_activity
        WHERE state = 'idle in transaction (aborted)'
            AND state_change < NOW() - INTERVAL '{idle_seconds} seconds'
            AND pid != pg_backend_pid()
        """
        
        aborted = self.execute_query(query)
        terminated_count = 0
        
        if aborted:
            click.echo(f"⚠️  Found {len(aborted)} aborted transaction(s) idle >{idle_seconds}s")
            for txn in aborted:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute(f"SELECT pg_terminate_backend({txn['pid']})")
                    cursor.close()
                    self.conn.commit()
                    terminated_count += 1
                    click.echo(f"   ✓ Terminated PID {txn['pid']} ({txn['usename']}, idle {txn['idle_seconds']}s)")
                except Exception as e:
                    click.echo(f"   ✗ Failed to terminate PID {txn['pid']}: {e}")
        
        return terminated_count
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_database_metadata(self) -> Dict[str, Any]:
        """Get database metadata for report header"""
        query = """
        SELECT 
            current_database() as db_name,
            inet_server_addr() as host,
            inet_server_port() as port,
            version() as pg_version,
            pg_postmaster_start_time() as start_time,
            NOW() - pg_postmaster_start_time() as uptime,
            pg_database_size(current_database()) as db_size,
            (SELECT count(*) FROM pg_stat_activity WHERE pid != pg_backend_pid()) as active_connections
        """
        
        result = self.execute_query(query)
        if result:
            meta = result[0]
            # Format uptime in human-readable format
            if meta.get('uptime'):
                uptime_delta = meta['uptime']
                days = uptime_delta.days
                hours, remainder = divmod(uptime_delta.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                # Build readable string
                parts = []
                if days > 0:
                    parts.append(f"{days}d")
                if hours > 0 or days > 0:
                    parts.append(f"{hours}h")
                if minutes > 0 or (hours == 0 and days == 0):
                    parts.append(f"{minutes}m")
                
                uptime_str = " ".join(parts) if parts else "0m"
            else:
                uptime_str = 'Unknown'
            
            # Format size
            size_query = "SELECT pg_size_pretty(pg_database_size(current_database()))"
            size_result = self.execute_query(size_query)
            db_size_pretty = size_result[0]['pg_size_pretty'] if size_result else 'Unknown'
            
            # Detect deployment type (managed service vs on-premise)
            deployment_type, deployment_info = self.detect_deployment_type()
            
            # Format start time
            start_time_str = 'Unknown'
            if meta.get('start_time'):
                start_time_str = meta['start_time'].strftime('%Y-%m-%d %H:%M:%S %Z').strip()
            
            return {
                'db_name': meta.get('db_name', 'Unknown'),
                'host': meta.get('host', self.conn_params['host']),
                'port': meta.get('port', self.conn_params['port']),
                'pg_version': meta.get('pg_version', 'Unknown').split(' on ')[0],  # Short version
                'start_time': start_time_str,
                'uptime': uptime_str,
                'db_size': db_size_pretty,
                'active_connections': meta.get('active_connections', 0),
                'deployment_type': deployment_type,
                'deployment_info': deployment_info
            }
        return {}
    
    def detect_deployment_type(self) -> tuple:
        """Detect if PostgreSQL is managed service or on-premise"""
        # Check version string for cloud provider hints
        version_query = "SELECT version()"
        version_result = self.execute_query(version_query)
        
        if not version_result:
            return 'unknown', {}
        
        version_str = version_result[0].get('version', '').lower()
        connection_host = self.conn_params.get('host', '').lower()
        
        # Azure PostgreSQL detection (check both version string and hostname)
        if ('azure' in version_str or 'microsoft' in version_str or 
            'postgres.database.azure.com' in connection_host or
            'database.windows.net' in connection_host):
            return 'managed', {
                'provider': 'Azure PostgreSQL',
                'icon': '☁️ ',
                'limitations': [
                    'System metrics (CPU/Memory/IO) not accessible via SQL',
                    'Use Azure Monitor for system-level metrics',
                    'Limited access to pg_stat_statements configuration'
                ]
            }
        
        # AWS RDS detection
        elif 'rds' in version_str or '.rds.amazonaws.com' in connection_host:
            return 'managed', {
                'provider': 'AWS RDS',
                'icon': '☁️ ',
                'limitations': [
                    'System metrics available via CloudWatch only',
                    'No direct OS access',
                    'Enhanced Monitoring required for detailed metrics'
                ]
            }
        
        # Google Cloud SQL detection
        elif 'cloudsql' in connection_host or 'google' in version_str:
            return 'managed', {
                'provider': 'Google Cloud SQL',
                'icon': '☁️ ',
                'limitations': [
                    'System metrics available via Cloud Monitoring',
                    'No SSH access to underlying VM',
                    'Use gcloud monitoring for CPU/Memory/Disk'
                ]
            }
        
        # Heroku Postgres detection
        elif 'heroku' in connection_host:
            return 'managed', {
                'provider': 'Heroku Postgres',
                'icon': '☁️ ',
                'limitations': [
                    'Limited system metrics access',
                    'Use Heroku metrics for monitoring',
                    'pg_stat_statements available'
                ]
            }
        
        # On-premise or self-hosted
        else:
            # Try to detect if we can access system stats
            can_access_system = self.check_system_stats_access()
            
            if can_access_system:
                return 'on-premise', {
                    'provider': 'On-Premise / Self-Hosted',
                    'icon': '🏢 ',
                    'capabilities': [
                        'Full system metrics available',
                        'CPU, Memory, Disk I/O accessible',
                        'Direct OS-level monitoring possible'
                    ]
                }
            else:
                return 'self-hosted', {
                    'provider': 'Self-Hosted (Limited Access)',
                    'icon': '🖥️ ',
                    'limitations': [
                        'System metrics require superuser privileges',
                        'Install pg_stat_kcache extension for I/O stats',
                        'Consider prometheus_postgres_exporter'
                    ]
                }
    
    def check_system_stats_access(self) -> bool:
        """Check if we can access system-level statistics"""
        try:
            # Try to access pg_stat_bgwriter (basic system stats)
            query = "SELECT checkpoints_timed FROM pg_stat_bgwriter LIMIT 1"
            result = self.execute_query(query)
            
            # Check for pg_stat_kcache extension (I/O stats)
            ext_query = "SELECT * FROM pg_available_extensions WHERE name = 'pg_stat_kcache'"
            ext_result = self.execute_query(ext_query)
            
            return bool(result and ext_result)
        except:
            return False
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics (CPU, Memory, I/O) when available"""
        deployment_type, deployment_info = self.detect_deployment_type()
        
        if deployment_type == 'managed':
            return {
                'available': False,
                'reason': f"📍 Running on {deployment_info['provider']}",
                'message': f"System metrics not accessible via SQL for managed services.",
                'limitations': deployment_info.get('limitations', []),
                'recommendation': f"Use cloud provider's monitoring:\n" + 
                                 self._get_monitoring_recommendation(deployment_info['provider'])
            }
        
        # Try to get system stats for on-premise
        metrics = {
            'available': True,
            'deployment': deployment_info.get('provider', 'Unknown')
        }
        
        # CPU metrics (via pg_stat_activity)
        cpu_query = """
        SELECT 
            COUNT(*) FILTER (WHERE state = 'active') as active_backends,
            COUNT(*) as total_backends,
            ROUND(100.0 * COUNT(*) FILTER (WHERE state = 'active') / NULLIF(COUNT(*), 0), 2) as cpu_usage_pct
        FROM pg_stat_activity
        WHERE pid != pg_backend_pid()
        """
        cpu_result = self.execute_query(cpu_query)
        if cpu_result:
            metrics['cpu'] = cpu_result[0]
        
        # Memory metrics (via pg_stat_database)
        memory_query = """
        SELECT 
            pg_size_pretty(sum(temp_bytes)) as temp_space_used,
            sum(temp_files) as temp_files_created,
            pg_size_pretty(pg_database_size(current_database())) as db_memory_footprint
        FROM pg_stat_database
        WHERE datname = current_database()
        """
        memory_result = self.execute_query(memory_query)
        if memory_result:
            metrics['memory'] = memory_result[0]
        
        # I/O metrics (via pg_stat_bgwriter and pg_stat_database)
        io_query = """
        SELECT 
            buffers_checkpoint,
            buffers_clean,
            buffers_backend,
            buffers_backend_fsync,
            buffers_alloc,
            maxwritten_clean,
            ROUND(100.0 * buffers_checkpoint / NULLIF(buffers_checkpoint + buffers_clean + buffers_backend, 0), 2) as checkpoint_write_pct
        FROM pg_stat_bgwriter
        """
        io_result = self.execute_query(io_query)
        if io_result:
            metrics['io'] = io_result[0]
        
        # Disk I/O per table (reads/writes)
        table_io_query = """
        SELECT 
            SUM(heap_blks_read) as total_heap_reads,
            SUM(heap_blks_hit) as total_heap_hits,
            SUM(idx_blks_read) as total_idx_reads,
            SUM(idx_blks_hit) as total_idx_hits,
            ROUND(100.0 * SUM(heap_blks_hit) / NULLIF(SUM(heap_blks_hit + heap_blks_read), 0), 2) as heap_hit_ratio,
            ROUND(100.0 * SUM(idx_blks_hit) / NULLIF(SUM(idx_blks_hit + idx_blks_read), 0), 2) as idx_hit_ratio
        FROM pg_statio_user_tables
        """
        table_io_result = self.execute_query(table_io_query)
        if table_io_result:
            metrics['table_io'] = table_io_result[0]
        
        # Check for pg_stat_kcache (kernel cache stats for deeper I/O metrics)
        kcache_query = """
        SELECT 
            SUM(reads) as total_physical_reads,
            SUM(writes) as total_physical_writes,
            SUM(user_time) as total_cpu_user_time,
            SUM(system_time) as total_cpu_system_time
        FROM pg_stat_kcache
        LIMIT 1
        """
        kcache_result = self.execute_query(kcache_query)
        if kcache_result and kcache_result[0].get('total_physical_reads') is not None:
            metrics['kcache_available'] = True
            metrics['kcache'] = kcache_result[0]
        else:
            metrics['kcache_available'] = False
            metrics['kcache_recommendation'] = "Install pg_stat_kcache extension for detailed I/O stats"
        
        return metrics
    
    def _get_monitoring_recommendation(self, provider: str) -> str:
        """Get monitoring recommendation for cloud provider"""
        recommendations = {
            'Azure PostgreSQL': """
    - Azure Portal → Monitor → Metrics (CPU, Memory, Storage, IO)
    - Enable Query Performance Insight for query-level metrics
    - Use Azure Monitor Workbooks for dashboards
    - CLI: az postgres flexible-server show --resource-group <rg> --name <server>""",
            
            'AWS RDS': """
    - CloudWatch → RDS → Performance Insights
    - Enable Enhanced Monitoring for OS-level metrics
    - CLI: aws rds describe-db-instances --db-instance-identifier <id>
    - Consider RDS Performance Insights Dashboard""",
            
            'Google Cloud SQL': """
    - Cloud Console → SQL → <instance> → Monitoring
    - Use Cloud Monitoring for system metrics
    - CLI: gcloud sql instances describe <instance>
    - Query Insights for query-level performance""",
            
            'Heroku Postgres': """
    - Heroku CLI: heroku pg:info
    - Heroku Dashboard → Resources → Postgres → Metrics
    - Use Heroku Metrics for system-level monitoring"""
        }
        
        return recommendations.get(provider, "Check your cloud provider's documentation for monitoring options")
    
    def execute_query(self, query: str) -> List[Dict]:
        """Execute query and return results as list of dicts"""
        try:
            # Rollback any failed transaction before executing new query
            if self.conn:
                self.conn.rollback()
            
            cursor = self.conn.cursor()
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            cursor.close()
            return results
        except Exception as e:
            # Rollback on error
            if self.conn:
                self.conn.rollback()
            click.echo(f"⚠️  Query warning: {e}", err=True)
            return []
    
    def get_lock_contention(self) -> Dict[str, Any]:
        """Get detailed lock contention - WHO is blocking WHOM"""
        query = """
        WITH blocking_locks AS (
            SELECT 
                blocked_locks.pid AS blocked_pid,
                blocked_activity.usename AS blocked_user,
                blocking_locks.pid AS blocking_pid,
                blocking_activity.usename AS blocking_user,
                blocked_activity.query AS blocked_query,
                blocking_activity.query AS blocking_query,
                blocked_locks.mode AS blocked_mode,
                blocking_locks.mode AS blocking_mode,
                blocked_activity.application_name AS blocked_app
            FROM pg_catalog.pg_locks blocked_locks
            JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
            JOIN pg_catalog.pg_locks blocking_locks 
                ON blocking_locks.locktype = blocked_locks.locktype
                AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                AND blocking_locks.pid != blocked_locks.pid
            JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
            WHERE NOT blocked_locks.granted
        )
        SELECT 
            blocked_pid,
            blocked_user,
            LEFT(blocked_query, 80) as blocked_query_preview,
            blocking_pid,
            blocking_user,
            LEFT(blocking_query, 80) as blocking_query_preview,
            blocked_mode,
            blocking_mode
        FROM blocking_locks;
        """
        
        locks = self.execute_query(query)
        
        # Get lock counts by type
        lock_summary_query = """
        SELECT 
            mode,
            COUNT(*) as lock_count,
            COUNT(DISTINCT pid) as process_count
        FROM pg_locks
        WHERE NOT granted
        GROUP BY mode
        ORDER BY lock_count DESC;
        """
        
        lock_summary = self.execute_query(lock_summary_query)
        
        # Save metrics
        if self.storage and locks:
            self.storage.save_alert(
                'lock_contention',
                'warning' if len(locks) > 5 else 'info',
                f"{len(locks)} blocked queries detected",
                {'blocked_count': len(locks)}
            )
        
        return {
            'blocking_details': locks,
            'lock_summary': lock_summary,
            'total_blocked': len(locks)
        }
    
    def get_connection_pool_health(self) -> Dict[str, Any]:
        """Monitor connection pool status - are we running out?"""
        query = """
        SELECT 
            max_conn,
            used,
            res_for_super,
            max_conn - used - res_for_super AS available,
            ROUND(100.0 * used / max_conn, 2) AS pct_used
        FROM 
            (SELECT COUNT(*) used FROM pg_stat_activity) t1,
            (SELECT setting::int res_for_super FROM pg_settings WHERE name = 'superuser_reserved_connections') t2,
            (SELECT setting::int max_conn FROM pg_settings WHERE name = 'max_connections') t3;
        """
        
        pool_status = self.execute_query(query)
        
        # Connection states breakdown
        states_query = """
        SELECT 
            CASE 
                WHEN state IS NULL OR state = '' THEN 
                    CASE 
                        WHEN backend_type IN ('autovacuum launcher', 'logical replication launcher', 
                                             'background writer', 'checkpointer', 'walwriter', 
                                             'archiver', 'stats collector', 'autovacuum worker') 
                        THEN 'background process'
                        WHEN backend_type LIKE '%pg%' OR backend_type LIKE '%azure%' 
                        THEN 'system process'
                        ELSE 'background'
                    END
                ELSE state
            END as connection_state,
            COUNT(*) as count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct
        FROM pg_stat_activity
        WHERE pid != pg_backend_pid()
        GROUP BY connection_state
        ORDER BY count DESC;
        """
        
        states = self.execute_query(states_query)
        
        # Background process details
        background_query = """
        SELECT 
            backend_type,
            COUNT(*) as count,
            string_agg(DISTINCT usename, ', ') as users
        FROM pg_stat_activity
        WHERE (state IS NULL OR state = '')
            AND pid != pg_backend_pid()
        GROUP BY backend_type
        ORDER BY count DESC;
        """
        
        background_processes = self.execute_query(background_query)
        
        # Long-running idle connections
        idle_query = """
        SELECT 
            pid,
            usename,
            application_name,
            client_addr,
            state,
            EXTRACT(EPOCH FROM (NOW() - state_change)) as idle_seconds
        FROM pg_stat_activity
        WHERE state = 'idle'
            AND state_change < NOW() - INTERVAL '5 minutes'
        ORDER BY state_change
        LIMIT 10;
        """
        
        idle_connections = self.execute_query(idle_query)
        
        # Save metrics
        if self.storage and pool_status:
            pct_used = pool_status[0].get('pct_used', 0)
            self.storage.save_metric('connection_pool', 'pct_used', pct_used)
            
            if pct_used > 80:
                self.storage.save_alert(
                    'connection_pool',
                    'critical' if pct_used > 90 else 'warning',
                    f"Connection pool at {pct_used}% capacity",
                    pool_status[0]
                )
        
        return {
            'pool_status': pool_status,
            'connection_states': states,
            'background_processes': background_processes,
            'idle_connections': idle_connections
        }
    
    def get_index_usage_analysis(self) -> Dict[str, Any]:
        """Find unused indexes and missing index opportunities"""
        
        # Unused indexes (taking space, never used)
        unused_query = """
        SELECT 
            schemaname,
            relname as tablename,
            indexrelname as indexname,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
            idx_scan as scans
        FROM pg_stat_user_indexes
        WHERE idx_scan = 0
            AND indexrelname NOT LIKE 'pg_toast%'
        ORDER BY pg_relation_size(indexrelid) DESC
        LIMIT 20;
        """
        
        unused_indexes = self.execute_query(unused_query)
        
        # Low usage indexes
        low_usage_query = """
        SELECT 
            pui.schemaname,
            pui.relname as tablename,
            pui.indexrelname as indexname,
            pui.idx_scan,
            pg_size_pretty(pg_relation_size(pui.indexrelid)) as index_size,
            ROUND(100.0 * pui.idx_scan / NULLIF(put.seq_scan + pui.idx_scan, 0), 2) as index_usage_pct
        FROM pg_stat_user_indexes pui
        JOIN pg_stat_user_tables put ON pui.schemaname = put.schemaname AND pui.relname = put.relname
        WHERE (put.seq_scan + pui.idx_scan) > 100
            AND pui.idx_scan < 100
        ORDER BY pg_relation_size(pui.indexrelid) DESC
        LIMIT 20;
        """
        
        low_usage_indexes = self.execute_query(low_usage_query)
        
        # Tables with high sequential scans (might need indexes)
        missing_indexes_query = """
        SELECT 
            schemaname,
            relname as tablename,
            seq_scan,
            seq_tup_read,
            idx_scan,
            ROUND(100.0 * idx_scan / NULLIF(seq_scan + idx_scan, 0), 2) as index_usage_pct,
            n_live_tup,
            pg_size_pretty(pg_relation_size(schemaname||'.'||relname)) as table_size
        FROM pg_stat_user_tables
        WHERE seq_scan > 1000
            AND n_live_tup > 10000
            AND (idx_scan::float / NULLIF(seq_scan + idx_scan, 0)) < 0.5
        ORDER BY seq_scan DESC
        LIMIT 20;
        """
        
        missing_opportunities = self.execute_query(missing_indexes_query)
        
        # Save metrics
        if self.storage:
            self.storage.save_metric('indexes', 'unused_count', len(unused_indexes))
            if len(unused_indexes) > 10:
                self.storage.save_alert(
                    'index_usage',
                    'warning',
                    f"{len(unused_indexes)} unused indexes wasting space",
                    {'count': len(unused_indexes)}
                )
        
        return {
            'unused_indexes': unused_indexes,
            'low_usage_indexes': low_usage_indexes,
            'missing_index_opportunities': missing_opportunities
        }
    
    def get_replication_health(self) -> Dict[str, Any]:
        """Detailed replication health - lag, slots, conflicts"""
        
        # Replication status
        replication_query = """
        SELECT 
            client_addr,
            application_name,
            state,
            sync_state,
            pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) / 1024 / 1024 as send_lag_mb,
            pg_wal_lsn_diff(sent_lsn, write_lsn) / 1024 / 1024 as write_lag_mb,
            pg_wal_lsn_diff(write_lsn, flush_lsn) / 1024 / 1024 as flush_lag_mb,
            pg_wal_lsn_diff(flush_lsn, replay_lsn) / 1024 / 1024 as replay_lag_mb,
            EXTRACT(EPOCH FROM write_lag) as write_lag_sec,
            EXTRACT(EPOCH FROM flush_lag) as flush_lag_sec,
            EXTRACT(EPOCH FROM replay_lag) as replay_lag_sec
        FROM pg_stat_replication;
        """
        
        replication_status = self.execute_query(replication_query)
        
        # Replication slots
        slots_query = """
        SELECT 
            slot_name,
            slot_type,
            active,
            pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) / 1024 / 1024 as lag_mb,
            temporary
        FROM pg_replication_slots;
        """
        
        replication_slots = self.execute_query(slots_query)
        
        # Save metrics
        if self.storage and replication_status:
            for replica in replication_status:
                replay_lag = replica.get('replay_lag_mb', 0)
                if replay_lag and replay_lag > 100:
                    self.storage.save_alert(
                        'replication',
                        'warning',
                        f"Replica {replica.get('client_addr')} lagging {replay_lag:.1f} MB",
                        replica
                    )
        
        return {
            'replication_status': replication_status,
            'replication_slots': replication_slots
        }
    
    def get_buffer_cache_stats(self) -> Dict[str, Any]:
        """Buffer cache hit ratio - I/O efficiency"""
        query = """
        SELECT 
            ROUND(100.0 * sum(blks_hit) / NULLIF(sum(blks_hit + blks_read), 0), 2) as cache_hit_ratio,
            sum(blks_hit) as cache_hits,
            sum(blks_read) as disk_reads,
            sum(blks_hit + blks_read) as total_reads
        FROM pg_stat_database;
        """
        
        cache_stats = self.execute_query(query)
        
        # Per-table cache stats
        table_cache_query = """
        SELECT 
            schemaname,
            relname as tablename,
            heap_blks_read,
            heap_blks_hit,
            ROUND(100.0 * heap_blks_hit / NULLIF(heap_blks_hit + heap_blks_read, 0), 2) as cache_hit_ratio,
            idx_blks_read,
            idx_blks_hit
        FROM pg_statio_user_tables
        WHERE heap_blks_read + heap_blks_hit > 0
        ORDER BY heap_blks_read DESC
        LIMIT 20;
        """
        
        table_cache_stats = self.execute_query(table_cache_query)
        
        # Save metrics
        if self.storage and cache_stats:
            hit_ratio = cache_stats[0].get('cache_hit_ratio', 0)
            self.storage.save_metric('buffer_cache', 'hit_ratio', hit_ratio)
            
            if hit_ratio < 90:
                self.storage.save_alert(
                    'buffer_cache',
                    'warning',
                    f"Low cache hit ratio: {hit_ratio}%",
                    cache_stats[0]
                )
        
        return {
            'overall_stats': cache_stats,
            'table_stats': table_cache_stats
        }
    
    def get_checkpoint_stats(self) -> Dict[str, Any]:
        """Checkpoint and background writer stats"""
        query = """
        SELECT 
            checkpoints_timed,
            checkpoints_req,
            ROUND(100.0 * checkpoints_req / NULLIF(checkpoints_timed + checkpoints_req, 0), 2) as pct_req,
            checkpoint_write_time,
            checkpoint_sync_time,
            buffers_checkpoint,
            buffers_clean,
            buffers_backend,
            buffers_backend_fsync,
            ROUND(buffers_alloc / 1024.0 / 1024.0, 2) as buffers_alloc_mb
        FROM pg_stat_bgwriter;
        """
        
        return {'checkpoint_stats': self.execute_query(query)}
    
    def get_query_latency(self, threshold_ms: int = 100) -> List[Dict]:
        """
        Get query latency trends from pg_stat_statements
        
        Logic:
        1. Uses pg_stat_statements extension for accurate query statistics
        2. Filters queries with mean execution time > threshold_ms
        3. Calculates percentage of total execution time (identifies bottleneck queries)
        4. Orders by average execution time (slowest first)
        5. Falls back to pg_stat_activity if pg_stat_statements unavailable
        
        Key Metrics:
        - avg_time_ms: Average execution time across all calls
        - max_time_ms: Maximum execution time ever recorded
        - calls: How many times this query was executed
        - pct_total_time: % of total DB time spent on this query
        """
        query = f"""
        SELECT 
            COALESCE(datname, 'N/A') as database,
            COALESCE(usename, 'N/A') as user,
            LEFT(query, 80) as query_preview,
            calls,
            ROUND(mean_exec_time::numeric, 2) as avg_time_ms,
            ROUND(min_exec_time::numeric, 2) as min_time_ms,
            ROUND(max_exec_time::numeric, 2) as max_time_ms,
            ROUND(stddev_exec_time::numeric, 2) as stddev_time_ms,
            ROUND(total_exec_time::numeric, 2) as total_time_ms,
            ROUND((100 * total_exec_time / SUM(total_exec_time) OVER ())::numeric, 2) as pct_total_time,
            CASE 
                WHEN mean_exec_time > 10000 THEN '🔴 Critical (>10s)'
                WHEN mean_exec_time > 5000 THEN '🟠 High (>5s)'
                WHEN mean_exec_time > 1000 THEN '🟡 Medium (>1s)'
                ELSE '🟢 Low'
            END as severity
        FROM pg_stat_statements pss
        LEFT JOIN pg_database pd ON pss.dbid = pd.oid
        LEFT JOIN pg_user pu ON pss.userid = pu.usesysid
        WHERE mean_exec_time > {threshold_ms}
        ORDER BY mean_exec_time DESC
        LIMIT 20;
        """
        
        fallback_query = """
        SELECT 
            datname as database,
            usename as user,
            LEFT(query, 80) as query_preview,
            state,
            EXTRACT(EPOCH FROM (NOW() - query_start)) * 1000 as runtime_ms,
            '⚠️  Active' as severity
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
                results = self.execute_query(fallback_query)
            
            # Save metrics
            if self.storage and results:
                for query_stat in results[:5]:  # Top 5 slow queries
                    avg_time = query_stat.get('avg_time_ms', query_stat.get('runtime_ms', 0))
                    if avg_time:
                        self.storage.save_metric('query_latency', 'avg_ms', avg_time, query_stat)
                        
                        # Generate alert for very slow queries
                        if avg_time > 5000:  # > 5 seconds
                            self.storage.save_alert(
                                'slow_query',
                                'critical' if avg_time > 10000 else 'warning',
                                f"Query averaging {avg_time:.2f}ms detected",
                                query_stat
                            )
            
            return results
        except:
            return self.execute_query(fallback_query)
    
    def get_table_bloat(self, threshold_pct: int = 20) -> List[Dict]:
        """Calculate table bloat percentage"""
        # Simplified query that works across PostgreSQL versions including Azure
        query = f"""
        SELECT 
            schemaname,
            relname as tablename,
            ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as bloat_pct,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as table_size,
            pg_size_pretty((pg_total_relation_size(schemaname||'.'||relname)::bigint * 
                n_dead_tup::bigint / NULLIF(n_live_tup + n_dead_tup, 1))::bigint) as bloat_size,
            n_dead_tup as dead_tuples,
            n_live_tup as live_tuples
        FROM pg_stat_user_tables
        WHERE n_dead_tup > 0
        ORDER BY bloat_pct DESC NULLS LAST
        LIMIT 20;
        """
        
        results = self.execute_query(query)
        
        # Filter by threshold in Python (more flexible)
        if results and threshold_pct > 0:
            results = [r for r in results if r.get('bloat_pct', 0) and r['bloat_pct'] >= threshold_pct]
        
        # Save metrics
        if self.storage and results:
            for table_stat in results:
                bloat_pct = table_stat.get('bloat_pct', 0)
                self.storage.save_metric('table_bloat', table_stat['tablename'], bloat_pct)
        
        # Save alert for high bloat
        if self.storage and results:
            high_bloat = [r for r in results if r.get('bloat_pct', 0) > 30]
            if high_bloat:
                self.storage.save_alert(
                    'table_bloat',
                    'warning',
                    f"{len(high_bloat)} tables with >30% bloat",
                    {'tables': [r['tablename'] for r in high_bloat]}
                )
        
        return results
    
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
        
        results = self.execute_query(query)
        
        # Save metrics
        if self.storage and results:
            for table_stat in results:
                dead_pct = table_stat.get('dead_pct', 0)
                if dead_pct and dead_pct > 20:
                    self.storage.save_alert(
                        'autovacuum',
                        'warning',
                        f"Table {table_stat['tablename']} has {dead_pct}% dead tuples",
                        table_stat
                    )
        
        return results
    
    def get_wal_growth(self) -> Dict[str, Any]:
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
        
        wal_info = self.execute_query(query)
        
        # Save metrics
        if self.storage and wal_info:
            wal_bytes = wal_info[0].get('wal_bytes', 0)
            self.storage.save_metric('wal', 'bytes', wal_bytes / 1024 / 1024)  # MB
        
        return {'wal_status': wal_info}
    
    def get_transaction_performance(self) -> Dict[str, Any]:
        """Get transaction performance metrics and benchmarking data"""
        # Database-level transaction stats
        db_stats_query = """
        SELECT 
            datname,
            xact_commit as committed_txns,
            xact_rollback as rolled_back_txns,
            xact_commit + xact_rollback as total_txns,
            CASE WHEN (xact_commit + xact_rollback) > 0 
                THEN ROUND(100.0 * xact_rollback / (xact_commit + xact_rollback), 2)
                ELSE 0 
            END as rollback_pct,
            blks_read as disk_blocks_read,
            blks_hit as cache_blocks_hit,
            CASE WHEN (blks_read + blks_hit) > 0
                THEN ROUND(100.0 * blks_hit / (blks_read + blks_hit), 2)
                ELSE 0
            END as cache_hit_ratio,
            tup_returned as rows_returned,
            tup_fetched as rows_fetched,
            tup_inserted as rows_inserted,
            tup_updated as rows_updated,
            tup_deleted as rows_deleted,
            conflicts,
            temp_files as temp_files_created,
            temp_bytes as temp_bytes_written,
            deadlocks,
            blk_read_time as block_read_time_ms,
            blk_write_time as block_write_time_ms
        FROM pg_stat_database
        WHERE datname = current_database();
        """
        
        # TPS calculation (transactions per second since startup)
        tps_query = """
        SELECT 
            EXTRACT(EPOCH FROM (NOW() - pg_postmaster_start_time())) as uptime_seconds,
            (SELECT xact_commit + xact_rollback FROM pg_stat_database WHERE datname = current_database()) as total_txns
        """
        
        # Query performance from pg_stat_statements
        query_perf_query = """
        SELECT 
            COUNT(*) as total_queries,
            SUM(calls) as total_calls,
            ROUND(AVG(mean_exec_time)::numeric, 2) as avg_query_time_ms,
            ROUND(MIN(mean_exec_time)::numeric, 2) as min_query_time_ms,
            ROUND(MAX(mean_exec_time)::numeric, 2) as max_query_time_ms,
            ROUND(AVG(calls)::numeric, 2) as avg_calls_per_query,
            SUM(CASE WHEN mean_exec_time > 1000 THEN 1 ELSE 0 END) as slow_queries_count,
            ROUND(SUM(total_exec_time)::numeric / 1000, 2) as total_exec_time_sec
        FROM pg_stat_statements
        WHERE queryid IS NOT NULL;
        """
        
        db_stats = self.execute_query(db_stats_query)
        tps_data = self.execute_query(tps_query)
        query_perf = self.execute_query(query_perf_query)
        
        result = {
            'database_stats': db_stats[0] if db_stats else {},
            'tps_data': {},
            'query_performance': query_perf[0] if query_perf else {}
        }
        
        # Calculate TPS
        if tps_data and tps_data[0].get('uptime_seconds'):
            uptime = tps_data[0]['uptime_seconds']
            total_txns = tps_data[0]['total_txns']
            tps = round(total_txns / uptime, 2) if uptime > 0 else 0
            
            result['tps_data'] = {
                'uptime_seconds': round(uptime, 2),
                'total_transactions': total_txns,
                'tps': tps,
                'tpm': round(tps * 60, 2)  # Transactions per minute
            }
        
        # Calculate queries per transaction
        if db_stats and query_perf:
            total_txns = db_stats[0].get('total_txns', 0)
            total_calls = query_perf[0].get('total_calls')
            
            if total_txns > 0 and total_calls:
                queries_per_txn = round(total_calls / total_txns, 2)
                result['queries_per_transaction'] = queries_per_txn
        
        # Save metrics for trending
        if self.storage and db_stats:
            stats = db_stats[0]
            self.storage.save_metric('transaction', 'commit_count', stats.get('committed_txns', 0))
            self.storage.save_metric('transaction', 'rollback_count', stats.get('rolled_back_txns', 0))
            self.storage.save_metric('transaction', 'rollback_pct', stats.get('rollback_pct', 0))
            
            if result.get('tps_data'):
                self.storage.save_metric('performance', 'tps', result['tps_data']['tps'])
        
        return result
    
    def get_disk_usage(self) -> List[Dict]:
        """Get disk usage and table sizes"""
        query = """
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - 
                          pg_relation_size(schemaname||'.'||tablename)) as index_size
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY size_bytes DESC
        LIMIT 20;
        """
        
        results = self.execute_query(query)
        
        # Save metrics for trend analysis
        if self.storage and results:
            for table in results:
                size_mb = table.get('size_bytes', 0) / (1024 * 1024)
                self.storage.save_metric('table_size', table['tablename'], size_mb)
        
        return results
    
    def get_vacuum_health_score(self) -> Dict[str, Any]:
        """Calculate vacuum health score"""
        query = """
        SELECT 
            COUNT(*) as total_tables,
            COUNT(CASE WHEN last_vacuum IS NOT NULL OR last_autovacuum IS NOT NULL THEN 1 END) as vacuumed_tables,
            COUNT(CASE WHEN last_analyze IS NOT NULL OR last_autoanalyze IS NOT NULL THEN 1 END) as analyzed_tables,
            COUNT(CASE WHEN n_dead_tup > 1000 AND 
                       (100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0)) > 10 THEN 1 END) as bloated_tables,
            AVG(CASE WHEN last_autovacuum IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (NOW() - last_autovacuum)) / 3600 
                ELSE NULL END) as avg_hours_since_vacuum
        FROM pg_stat_user_tables
        WHERE n_live_tup > 0;
        """
        
        result = self.execute_query(query)
        if not result:
            return {}
        
        stats = result[0]
        total = stats.get('total_tables', 0)
        
        if total == 0:
            return {'score': 100, 'status': 'N/A', 'details': 'No user tables'}
        
        vacuumed_pct = (stats.get('vacuumed_tables', 0) / total) * 100
        analyzed_pct = (stats.get('analyzed_tables', 0) / total) * 100
        bloated_count = stats.get('bloated_tables', 0)
        
        # Calculate score (0-100)
        score = (vacuumed_pct * 0.4) + (analyzed_pct * 0.4) + ((total - bloated_count) / total * 100 * 0.2)
        
        if score >= 90:
            status = '🟢 Excellent'
        elif score >= 75:
            status = '🟡 Good'
        elif score >= 50:
            status = '🟠 Fair'
        else:
            status = '🔴 Poor'
        
        return {
            'score': round(score, 1),
            'status': status,
            'total_tables': total,
            'vacuumed_tables': stats.get('vacuumed_tables', 0),
            'analyzed_tables': stats.get('analyzed_tables', 0),
            'bloated_tables': bloated_count,
            'avg_hours_since_vacuum': round(stats.get('avg_hours_since_vacuum', 0), 1) if stats.get('avg_hours_since_vacuum') else 'N/A'
        }


def format_output(data: Any, format_type: str = 'table', colored: bool = True) -> str:
    """Format output as table or JSON with colors"""
    if format_type == 'json':
        return json.dumps(data, indent=2, default=str)
    
    if isinstance(data, dict):
        output = []
        for key, value in data.items():
            output.append(f"\n{'='*70}\n{key.upper()}\n{'='*70}")
            if value:
                if isinstance(value, list):
                    output.append(tabulate(value, headers='keys', tablefmt='grid'))
                else:
                    output.append(str(value))
            else:
                output.append("✓ No issues detected")
        return '\n'.join(output)
    elif isinstance(data, list) and data:
        return tabulate(data, headers='keys', tablefmt='grid')
    else:
        return "✓ No data available"


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
@click.option('--locks', is_flag=True, help='Monitor lock contention')
@click.option('--connections', is_flag=True, help='Monitor connection pool')
@click.option('--indexes', is_flag=True, help='Analyze index usage')
@click.option('--replication', is_flag=True, help='Monitor replication health')
@click.option('--cache', is_flag=True, help='Monitor buffer cache')
@click.option('--checkpoints', is_flag=True, help='Monitor checkpoints')
@click.option('--latency-threshold', default=100, help='Query latency threshold (ms)')
@click.option('--bloat-threshold', default=20, help='Table bloat threshold (%)')
@click.option('--output', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--watch', type=int, help='Custom monitoring interval (seconds)')
@click.option('--no-history', is_flag=True, help='Disable historical data storage')
@click.option('--show-trends', is_flag=True, help='Show historical trends')
@click.option('--show-alerts', is_flag=True, help='Show recent alerts')
@click.option('--trend', type=str, help='Show trend for period (24h, 7d, 30d)')
@click.option('--summary', is_flag=True, help='Show summary mode (alerts & key stats only)')
@click.option('--disk-usage', is_flag=True, help='Show disk usage and table sizes')
@click.option('--vacuum-health', is_flag=True, help='Show vacuum health score')
@click.option('--system-metrics', is_flag=True, help='Show CPU/Memory/IO metrics (on-premise only)')
@click.option('--transaction-perf', is_flag=True, help='Show transaction performance & benchmarking metrics')
def main(host, port, database, user, password, monitor_all, query_latency, 
         table_bloat, autovacuum, wal_growth, locks, connections, indexes,
         replication, cache, checkpoints, latency_threshold, bloat_threshold, 
         output, watch, no_history, show_trends, show_alerts, trend, summary,
         disk_usage, vacuum_health, system_metrics, transaction_perf):
    """PostgreSQL Enhanced Monitoring CLI - Dashboard Ready"""
    
    # Ask user for mode if no watch interval specified
    if watch is None and not any([show_trends, show_alerts]):
        click.echo("\n╔══════════════════════════════════════════════════════════╗")
        click.echo("║        PostgreSQL Enhanced Monitor                       ║")
        click.echo("╚══════════════════════════════════════════════════════════╝\n")
        click.echo("Choose monitoring mode:")
        click.echo("  1. One-shot - Check metrics once and exit")
        click.echo("  2. Continuous - Monitor for 16 minutes (8 refreshes × 2 min)\n")
        
        # Validate input
        while True:
            mode_choice = click.prompt("Enter choice (1 or 2)", type=str, default="1")
            if mode_choice.strip() in ['1', '2']:
                break
            click.echo("❌ Invalid choice. Please enter 1 or 2.\n")
        
        if mode_choice.strip() == "2":
            watch = 120  # 2 minutes
            continuous_mode = True
            max_iterations = 8  # 8 cycles = 16 minutes
            click.echo("\n✅ Continuous mode - Will refresh 8 times (16 minutes total)\n")
        else:
            watch = None
            continuous_mode = False
            max_iterations = 1
            click.echo("\n✅ One-shot mode - Will run once and exit\n")
    else:
        continuous_mode = bool(watch)
        max_iterations = 999999 if watch else 1  # Keep running if --watch specified
    
    # Initialize monitor
    monitor = PGMonitorEnhanced(host, port, database, user, password, 
                               enable_history=not no_history)
    
    if not monitor.connect():
        sys.exit(1)
    
    mode_info = ""
    if continuous_mode and max_iterations < 999999:
        mode_info = f" [Continuous: {max_iterations} refreshes × {watch}s = {max_iterations * watch // 60} min]"
    elif watch:
        mode_info = f" [Watch mode: refresh every {watch}s]"
    
    click.echo(f"✅ Connected to PostgreSQL: {user}@{host}:{port}/{database}{mode_info}")
    if not no_history:
        click.echo(f"📊 Historical data: {monitor.storage.db_path}\n")
    
    # Cleanup aborted transactions automatically
    terminated = monitor.cleanup_aborted_transactions(idle_seconds=10)
    if terminated > 0:
        click.echo(f"🧹 Cleaned up {terminated} aborted transaction(s)\n")
    
    # Get database metadata for report header
    metadata = monitor.get_database_metadata()
    
    # Handle --trend mode
    if trend and monitor.storage:
        hours_map = {'24h': 24, '7d': 168, '30d': 720}
        hours = hours_map.get(trend.lower(), 24)
        
        click.echo(f"\n📈 Trend Analysis - Last {trend}")
        click.echo("="*70)
        
        # Show table growth trend
        growth = monitor.storage.get_table_growth_trend(hours=hours)
        if growth:
            click.echo("\n📊 Table Size Growth:")
            click.echo(format_output(growth, output))
        else:
            click.echo("No table growth data available yet")
        
        # Show alert summary
        alert_summary = monitor.storage.get_alert_summary(hours=hours)
        if alert_summary and alert_summary.get('total', 0) > 0:
            click.echo(f"\n⚠️  Alerts Summary ({trend}):")
            click.echo(f"   Total: {alert_summary['total']}")
            for severity, count in alert_summary['summary'].items():
                emoji = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(severity, '⚪')
                click.echo(f"   {emoji} {severity.capitalize()}: {count}")
        
        return
    
    # Handle --summary mode
    if summary:
        click.echo("\n📋 MONITORING SUMMARY")
        click.echo("="*70)
        
        # Metadata
        click.echo(f"\n🗄️  Database: {metadata.get('db_name', 'Unknown')}")
        click.echo(f"🌍 Host: {metadata.get('host', 'Unknown')}")
        click.echo(f"⏱️  Uptime: {metadata.get('uptime', 'Unknown')}")
        click.echo(f"💾 Size: {metadata.get('db_size', 'Unknown')}")
        click.echo(f"🔗 Connections: {metadata.get('active_connections', 0)}")
        
        # Key stats
        pool = monitor.get_connection_pool_health()
        if pool and pool.get('pool_status'):
            ps = pool['pool_status'][0]
            click.echo(f"\n🔌 Connection Pool: {ps['used']}/{ps['max_conn']} ({ps['pct_used']}%)")
        
        cache = monitor.get_buffer_cache_stats()
        if cache and cache.get('overall_stats'):
            hit_ratio = cache['overall_stats'][0]['cache_hit_ratio']
            click.echo(f"💾 Cache Hit Ratio: {hit_ratio}%")
        
        # Vacuum health
        vacuum_health_data = monitor.get_vacuum_health_score()
        if vacuum_health_data:
            click.echo(f"\n🧹 Vacuum Health: {vacuum_health_data['status']} ({vacuum_health_data['score']}/100)")
        
        # Alerts
        if monitor.storage:
            alert_summary = monitor.storage.get_alert_summary(hours=24)
            if alert_summary and alert_summary.get('total', 0) > 0:
                click.echo(f"\n⚠️  Alerts (24h): {alert_summary['total']}")
                for severity, count in alert_summary['summary'].items():
                    emoji = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(severity, '⚪')
                    click.echo(f"   {emoji} {severity.capitalize()}: {count}")
                
                if alert_summary.get('critical_alerts'):
                    click.echo("\n🔴 Recent Critical Alerts:")
                    for alert in alert_summary['critical_alerts'][:3]:
                        click.echo(f"   • {alert['message']} ({alert['timestamp']})")
        
        return
    
    # Show trends if requested
    if show_trends and monitor.storage:
        click.echo("\n📈 Historical Trends (Last 24h)")
        click.echo("="*70)
        trends = monitor.storage.get_metric_trend('connection_pool', hours=24)
        if trends:
            click.echo(format_output(trends[:10], output))
        else:
            click.echo("No historical data available yet")
        return
    
    # Show alerts if requested
    if show_alerts and monitor.storage:
        click.echo("\n⚠️  Recent Alerts (Last 24h)")
        click.echo("="*70)
        alerts = monitor.storage.get_recent_alerts(hours=24)
        if alerts:
            click.echo(format_output(alerts, output))
        else:
            click.echo("✓ No alerts in the last 24 hours")
        return
    
    # Determine what to monitor
    if not any([monitor_all, query_latency, table_bloat, autovacuum, wal_growth,
                locks, connections, indexes, replication, cache, checkpoints]):
        monitor_all = True
    
    def run_monitoring():
        """Run monitoring checks"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        click.echo(f"\n{'='*70}")
        click.echo(f"📊 PG-Monitor Enhanced Report - {timestamp}")
        click.echo(f"{'='*70}")
        
        # Metadata Block
        if metadata:
            deployment_icon = metadata.get('deployment_info', {}).get('icon', '🖥️ ')
            deployment_provider = metadata.get('deployment_info', {}).get('provider', 'Unknown')
            
            click.echo(f"\n📋 ENVIRONMENT")
            click.echo(f"{'─'*70}")
            click.echo(f"📅 Report Date: {timestamp}")
            click.echo(f"🏷️  Database: {metadata.get('db_name', 'Unknown')}")
            click.echo(f"🌍 Host: {metadata.get('host', 'Unknown')}:{metadata.get('port', 'Unknown')}")
            click.echo(f"{deployment_icon}Deployment: {deployment_provider}")
            click.echo(f"🚀 Started: {metadata.get('start_time', 'Unknown')}")
            click.echo(f"⏱️  Uptime: {metadata.get('uptime', 'Unknown')}")
            click.echo(f"💾 DB Size: {metadata.get('db_size', 'Unknown')}")
            click.echo(f"🔗 Active Connections: {metadata.get('active_connections', 0)}")
            click.echo(f"{'─'*70}")
        
        # System Metrics (CPU, Memory, I/O)
        if monitor_all:
            system_metrics = monitor.get_system_metrics()
            
            if not system_metrics.get('available', False):
                # Managed service - show limitations
                click.echo(f"\n⚙️  SYSTEM METRICS (CPU / Memory / I/O)")
                click.echo(f"{'─'*70}")
                click.echo(f"{system_metrics.get('reason', 'Not Available')}")
                click.echo(f"\n⚠️  {system_metrics.get('message', '')}")
                
                if system_metrics.get('limitations'):
                    click.echo(f"\n📌 Limitations:")
                    for limitation in system_metrics['limitations']:
                        click.echo(f"   • {limitation}")
                
                if system_metrics.get('recommendation'):
                    click.echo(f"\n💡 How to Access System Metrics:")
                    click.echo(system_metrics['recommendation'])
                
                click.echo(f"{'─'*70}")
            else:
                # On-premise - show actual metrics
                click.echo(f"\n⚙️  SYSTEM METRICS (CPU / Memory / I/O)")
                click.echo(f"{'─'*70}")
                click.echo(f"🏢 Deployment: {system_metrics.get('deployment', 'On-Premise')}")
                
                if system_metrics.get('cpu'):
                    cpu = system_metrics['cpu']
                    click.echo(f"\n📊 CPU Usage (Active Backends):")
                    click.echo(f"   Active: {cpu['active_backends']} / {cpu['total_backends']} ({cpu['cpu_usage_pct']}%)")
                
                if system_metrics.get('memory'):
                    mem = system_metrics['memory']
                    click.echo(f"\n💾 Memory:")
                    click.echo(f"   Temp Space Used: {mem['temp_space_used']}")
                    click.echo(f"   Temp Files Created: {mem['temp_files_created']}")
                    click.echo(f"   DB Memory Footprint: {mem['db_memory_footprint']}")
                
                if system_metrics.get('io'):
                    io = system_metrics['io']
                    click.echo(f"\n💿 I/O Statistics:")
                    click.echo(f"   Checkpoint Writes: {io['buffers_checkpoint']}")
                    click.echo(f"   Backend Writes: {io['buffers_backend']}")
                    click.echo(f"   Checkpoint Write %: {io['checkpoint_write_pct']}%")
                
                if system_metrics.get('table_io'):
                    tio = system_metrics['table_io']
                    click.echo(f"\n📁 Table I/O:")
                    click.echo(f"   Heap Reads: {tio['total_heap_reads']:,} | Hits: {tio['total_heap_hits']:,} ({tio['heap_hit_ratio']}%)")
                    click.echo(f"   Index Reads: {tio['total_idx_reads']:,} | Hits: {tio['total_idx_hits']:,} ({tio['idx_hit_ratio']}%)")
                
                if system_metrics.get('kcache_available'):
                    kcache = system_metrics['kcache']
                    click.echo(f"\n🔬 Kernel Cache Stats (pg_stat_kcache):")
                    click.echo(f"   Physical Reads: {kcache['total_physical_reads']:,}")
                    click.echo(f"   Physical Writes: {kcache['total_physical_writes']:,}")
                    click.echo(f"   CPU User Time: {kcache['total_cpu_user_time']:.2f}s")
                    click.echo(f"   CPU System Time: {kcache['total_cpu_system_time']:.2f}s")
                else:
                    click.echo(f"\n💡 {system_metrics.get('kcache_recommendation', '')}")
                
                click.echo(f"{'─'*70}")
        
        # Alert Summary Block (if historical data exists)
        if monitor.storage and monitor_all:
            alert_summary = monitor.storage.get_alert_summary(hours=24)
            if alert_summary and alert_summary.get('total', 0) > 0:
                click.echo(f"\n🚨 ALERT SUMMARY (Last 24h)")
                click.echo(f"{'─'*70}")
                click.echo(f"Total Alerts: {alert_summary['total']}")
                for severity, count in alert_summary['summary'].items():
                    emoji = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(severity, '⚪')
                    click.echo(f"  {emoji} {severity.capitalize()}: {count}")
                
                if alert_summary.get('critical_alerts'):
                    click.echo(f"\n� Recent Critical:")
                    for alert in alert_summary['critical_alerts'][:2]:
                        click.echo(f"  • {alert['message']}")
                click.echo(f"{'─'*70}")
        
        # Vacuum Health Score
        if monitor_all or vacuum_health:
            click.echo("\n🧹 Vacuum Health Score")
            vacuum_data = monitor.get_vacuum_health_score()
            if vacuum_data:
                click.echo(f"  Score: {vacuum_data['score']}/100 {vacuum_data['status']}")
                click.echo(f"  Vacuumed Tables: {vacuum_data['vacuumed_tables']}/{vacuum_data['total_tables']}")
                click.echo(f"  Analyzed Tables: {vacuum_data['analyzed_tables']}/{vacuum_data['total_tables']}")
                click.echo(f"  Bloated Tables: {vacuum_data['bloated_tables']}")
                click.echo(f"  Avg Hours Since Vacuum: {vacuum_data['avg_hours_since_vacuum']}")
        
        # Disk Usage
        if monitor_all or disk_usage:
            click.echo("\n💽 Disk Usage / Table Sizes")
            disk_data = monitor.get_disk_usage()
            click.echo(format_output(disk_data, output))
        
        # Transaction Performance & Benchmarking
        if monitor_all or transaction_perf:
            click.echo("\n⚡ Transaction Performance & Benchmarking")
            click.echo(f"{'─'*70}")
            
            txn_data = monitor.get_transaction_performance()
            
            # TPS / TPM with Historical Comparison
            if txn_data.get('tps_data'):
                tps_info = txn_data['tps_data']
                current_tps = float(tps_info.get('tps', 0))
                
                click.echo(f"\n📊 Throughput Metrics:")
                click.echo(f"   Database Uptime: {tps_info.get('uptime_seconds', 0):.2f} sec ({tps_info.get('uptime_seconds', 0)/3600:.1f} hours)")
                click.echo(f"   Total Transactions: {tps_info.get('total_transactions', 0):,}")
                click.echo(f"   🚀 TPS (Transactions/Sec): {current_tps:.2f}")
                click.echo(f"   🚀 TPM (Transactions/Min): {tps_info.get('tpm', 0):.2f}")
                
                # Historical TPS Comparison
                if monitor.storage:
                    # Get 24h average TPS
                    tps_trend_24h = monitor.storage.get_metric_comparison('performance', 'tps', 24)
                    tps_trend_7d = monitor.storage.get_metric_comparison('performance', 'tps', 168)
                    
                    if tps_trend_24h and tps_trend_24h.get('avg'):
                        avg_24h = float(tps_trend_24h['avg'])
                        diff_pct = ((current_tps - avg_24h) / avg_24h * 100) if avg_24h > 0 else 0
                        trend_icon = "📈" if diff_pct > 0 else "📉" if diff_pct < 0 else "➡️"
                        click.echo(f"\n   � 24h Comparison:")
                        click.echo(f"      Avg TPS (24h): {avg_24h:.2f}")
                        click.echo(f"      {trend_icon} Change: {diff_pct:+.2f}%")
                    
                    if tps_trend_7d and tps_trend_7d.get('avg'):
                        avg_7d = float(tps_trend_7d['avg'])
                        diff_pct_7d = ((current_tps - avg_7d) / avg_7d * 100) if avg_7d > 0 else 0
                        trend_icon_7d = "📈" if diff_pct_7d > 0 else "📉" if diff_pct_7d < 0 else "➡️"
                        click.echo(f"   📊 7d Comparison:")
                        click.echo(f"      Avg TPS (7d): {avg_7d:.2f}")
                        click.echo(f"      {trend_icon_7d} Change: {diff_pct_7d:+.2f}%")
                        click.echo(f"      Peak (7d): {float(tps_trend_7d.get('max', 0)):.2f}")
                        click.echo(f"      Low (7d): {float(tps_trend_7d.get('min', 0)):.2f}")
            
            # Database stats with health indicators
            if txn_data.get('database_stats'):
                db_stats = txn_data['database_stats']
                rollback_pct = db_stats.get('rollback_pct', 0)
                
                # Health indicator for rollback rate
                if rollback_pct < 1:
                    rollback_status = "🟢 Excellent"
                elif rollback_pct < 5:
                    rollback_status = "🟡 Normal"
                elif rollback_pct < 10:
                    rollback_status = "🟠 Warning"
                else:
                    rollback_status = "🔴 Critical"
                
                click.echo(f"\n💾 Transaction Statistics:")
                click.echo(f"   ✅ Committed: {db_stats.get('committed_txns', 0):,}")
                click.echo(f"   ❌ Rolled Back: {db_stats.get('rolled_back_txns', 0):,}")
                click.echo(f"   📈 Rollback Rate: {rollback_pct}% {rollback_status}")
                
                deadlocks = db_stats.get('deadlocks', 0)
                if deadlocks > 0:
                    click.echo(f"   💀 Deadlocks: {deadlocks} ⚠️  NEEDS ATTENTION")
                else:
                    click.echo(f"   💀 Deadlocks: {deadlocks} 🟢 Good")
                
                conflicts = db_stats.get('conflicts', 0)
                if conflicts > 0:
                    click.echo(f"   ⚠️  Conflicts: {conflicts} ⚠️  Check replication")
                else:
                    click.echo(f"   ⚠️  Conflicts: {conflicts} 🟢 Good")
                
                click.echo(f"\n📝 Data Operations (Total since startup):")
                total_writes = db_stats.get('rows_inserted', 0) + db_stats.get('rows_updated', 0) + db_stats.get('rows_deleted', 0)
                total_reads = db_stats.get('rows_fetched', 0)
                read_write_ratio = total_reads / total_writes if total_writes > 0 else 0
                
                click.echo(f"   Rows Inserted: {db_stats.get('rows_inserted', 0):,}")
                click.echo(f"   Rows Updated: {db_stats.get('rows_updated', 0):,}")
                click.echo(f"   Rows Deleted: {db_stats.get('rows_deleted', 0):,}")
                click.echo(f"   Rows Fetched: {total_reads:,}")
                click.echo(f"   📊 Read/Write Ratio: {read_write_ratio:.2f}x (Higher = More reads)")
                
                cache_hit_ratio = db_stats.get('cache_hit_ratio', 0)
                if cache_hit_ratio >= 99:
                    cache_status = "🟢 Excellent"
                elif cache_hit_ratio >= 95:
                    cache_status = "🟡 Good"
                elif cache_hit_ratio >= 90:
                    cache_status = "🟠 Fair"
                else:
                    cache_status = "🔴 Poor - Increase shared_buffers"
                
                click.echo(f"\n💿 I/O Performance:")
                click.echo(f"   Cache Hit Ratio: {cache_hit_ratio}% {cache_status}")
                click.echo(f"   Disk Blocks Read: {db_stats.get('disk_blocks_read', 0):,}")
                click.echo(f"   Cache Blocks Hit: {db_stats.get('cache_blocks_hit', 0):,}")
                
                if db_stats.get('temp_files_created', 0) > 0:
                    temp_mb = db_stats.get('temp_bytes_written', 0) / (1024 * 1024)
                    click.echo(f"\n🗂️  Temp Files: ⚠️  Work Memory May Be Low")
                    click.echo(f"   Files Created: {db_stats.get('temp_files_created', 0):,}")
                    click.echo(f"   Bytes Written: {temp_mb:.2f} MB")
                    click.echo(f"   💡 Tip: Increase work_mem if temp file usage is high")
            
            # Query performance
            if txn_data.get('query_performance'):
                query_perf = txn_data['query_performance']
                total_queries = query_perf.get('total_queries') or 0
                total_calls = query_perf.get('total_calls') or 0
                avg_time = query_perf.get('avg_query_time_ms') or 0
                slow_count = query_perf.get('slow_queries_count') or 0
                
                if total_queries > 0:
                    click.echo(f"\n🔍 Query Performance Summary:")
                    click.echo(f"   Total Unique Queries: {total_queries:,}")
                    click.echo(f"   Total Query Calls: {total_calls:,}")
                    click.echo(f"   Avg Calls/Query: {total_calls/total_queries:.2f}")
                    
                    if avg_time < 10:
                        perf_status = "🟢 Excellent"
                    elif avg_time < 100:
                        perf_status = "🟡 Good"
                    elif avg_time < 500:
                        perf_status = "🟠 Needs Optimization"
                    else:
                        perf_status = "🔴 Critical - Optimize Now"
                    
                    click.echo(f"   Avg Query Time: {avg_time} ms {perf_status}")
                    click.echo(f"   Min Query Time: {query_perf.get('min_query_time_ms') or 0} ms")
                    click.echo(f"   Max Query Time: {query_perf.get('max_query_time_ms') or 0} ms")
                    
                    if slow_count > 0:
                        slow_pct = (slow_count / total_queries * 100) if total_queries > 0 else 0
                        click.echo(f"   🐌 Slow Queries (>1s): {slow_count} ({slow_pct:.1f}%) ⚠️  REVIEW REQUIRED")
                    else:
                        click.echo(f"   🐌 Slow Queries (>1s): 0 🟢 Good")
                    
                    click.echo(f"   Total Exec Time: {query_perf.get('total_exec_time_sec') or 0} sec")
                else:
                    click.echo(f"\n🔍 Query Performance:")
                    click.echo(f"   ℹ️  No pg_stat_statements data available")
                    click.echo(f"   💡 Enable: CREATE EXTENSION pg_stat_statements;")
            
            # Queries per transaction
            if txn_data.get('queries_per_transaction'):
                qpt = txn_data['queries_per_transaction']
                click.echo(f"\n📊 Efficiency Metrics:")
                click.echo(f"   Queries Per Transaction: {qpt:.2f}")
                
                if qpt < 5:
                    eff_status = "🟢 Efficient (Low query/txn ratio)"
                elif qpt < 20:
                    eff_status = "🟡 Normal"
                elif qpt < 50:
                    eff_status = "🟠 High - Consider batching"
                else:
                    eff_status = "🔴 Very High - Review transaction logic"
                
                click.echo(f"   Status: {eff_status}")
            
            # Performance Insights
            click.echo(f"\n💡 Performance Insights:")
            insights = []
            
            if txn_data.get('database_stats'):
                db_stats = txn_data['database_stats']
                
                if db_stats.get('rollback_pct', 0) > 5:
                    insights.append("   ⚠️  High rollback rate - check application error handling")
                
                if db_stats.get('deadlocks', 0) > 0:
                    insights.append("   ⚠️  Deadlocks detected - review transaction order and locking")
                
                if db_stats.get('cache_hit_ratio', 0) < 95:
                    insights.append("   ⚠️  Low cache hit ratio - consider increasing shared_buffers")
                
                if db_stats.get('temp_files_created', 0) > 100:
                    insights.append("   ⚠️  High temp file usage - increase work_mem")
            
            if txn_data.get('query_performance'):
                query_perf = txn_data['query_performance']
                if (query_perf.get('slow_queries_count') or 0) > 0:
                    insights.append("   ⚠️  Slow queries found - review and optimize (see details below)")
            
            if not insights:
                insights.append("   ✅ All metrics within normal range - system performing well!")
            
            for insight in insights:
                click.echo(insight)
            
            click.echo(f"{'─'*70}")
        
        # Core metrics
        if monitor_all or query_latency:
            click.echo("\n🔍 Top Slow Queries (threshold: {}ms)".format(latency_threshold))
            click.echo(f"{'─'*70}")
            click.echo("\n📖 Logic:")
            click.echo("   • Queries pg_stat_statements extension for aggregated statistics")
            click.echo("   • Filters queries where AVERAGE execution time > threshold")
            click.echo("   • Sorts by avg_time_ms (slowest first)")
            click.echo("   • Shows % of total DB time (identifies biggest bottlenecks)")
            click.echo("   • Severity: 🔴 >10s, 🟠 >5s, 🟡 >1s, 🟢 <1s")
            click.echo(f"{'─'*70}")
            
            data = monitor.get_query_latency(latency_threshold)
            
            if data:
                click.echo(format_output(data, output))
                
                # Summary insights
                total_slow = len(data)
                critical_count = sum(1 for q in data if q.get('avg_time_ms', 0) > 10000)
                high_count = sum(1 for q in data if 5000 < q.get('avg_time_ms', 0) <= 10000)
                
                click.echo(f"\n📊 Slow Query Summary:")
                click.echo(f"   Total Slow Queries: {total_slow}")
                if critical_count > 0:
                    click.echo(f"   🔴 Critical (>10s): {critical_count} queries")
                if high_count > 0:
                    click.echo(f"   🟠 High (>5s): {high_count} queries")
                
                # Top offender
                if data[0].get('avg_time_ms'):
                    top_query = data[0]
                    click.echo(f"\n🎯 Top Offender:")
                    click.echo(f"   Avg Time: {top_query.get('avg_time_ms', 0):.2f}ms")
                    click.echo(f"   Calls: {top_query.get('calls', 0):,}")
                    click.echo(f"   % Total Time: {top_query.get('pct_total_time', 0)}%")
                    click.echo(f"   Preview: {top_query.get('query_preview', 'N/A')}")
            else:
                click.echo("✓ No slow queries detected")
        
        if monitor_all or locks:
            click.echo("\n🔒 Lock Contention - Who's Blocking Whom")
            data = monitor.get_lock_contention()
            click.echo(format_output(data, output))
        
        if monitor_all or connections:
            click.echo("\n🔌 Connection Pool Health")
            data = monitor.get_connection_pool_health()
            click.echo(format_output(data, output))
        
        if monitor_all or indexes:
            click.echo("\n📊 Index Usage Analysis")
            data = monitor.get_index_usage_analysis()
            click.echo(format_output(data, output))
        
        if monitor_all or replication:
            click.echo("\n🔄 Replication Health")
            data = monitor.get_replication_health()
            click.echo(format_output(data, output))
        
        if monitor_all or cache:
            click.echo("\n💾 Buffer Cache Statistics")
            data = monitor.get_buffer_cache_stats()
            click.echo(format_output(data, output))
        
        if monitor_all or checkpoints:
            click.echo("\n⚡ Checkpoint Statistics")
            data = monitor.get_checkpoint_stats()
            click.echo(format_output(data, output))
        
        if monitor_all or table_bloat:
            click.echo("\n💽 Table Bloat (threshold: {}%)".format(bloat_threshold))
            data = monitor.get_table_bloat(bloat_threshold)
            click.echo(format_output(data, output))
        
        if monitor_all or autovacuum:
            click.echo("\n🧹 Autovacuum Lag")
            data = monitor.get_autovacuum_lag()
            click.echo(format_output(data, output))
        
        if monitor_all or wal_growth:
            click.echo("\n📝 WAL Growth Rate")
            data = monitor.get_wal_growth()
            click.echo(format_output(data, output))
    
    try:
        if watch:
            iteration = 1
            if max_iterations < 999999:
                click.echo(f"\n🔄 Continuous monitoring (8 refreshes × {watch}s, total 16 min)")
            else:
                click.echo(f"\n🔄 Watching (refresh every {watch}s, Ctrl+C to stop)")
            
            while iteration <= max_iterations:
                if max_iterations < 999999:
                    click.echo(f"\n{'='*70}")
                    click.echo(f"Refresh {iteration}/{max_iterations}")
                    click.echo(f"{'='*70}")
                
                run_monitoring()
                
                if iteration < max_iterations:
                    click.echo(f"\n⏳ Next refresh in {watch}s... (Ctrl+C to stop)")
                    time.sleep(watch)
                    if output == 'table':
                        click.clear()
                else:
                    if max_iterations < 999999:
                        click.echo(f"\n{'='*70}")
                        click.echo(f"✅ Monitoring complete! ({max_iterations} refreshes, {max_iterations * watch // 60} minutes)")
                        click.echo(f"{'='*70}")
                
                iteration += 1
        else:
            run_monitoring()
    
    except KeyboardInterrupt:
        click.echo("\n\n👋 Monitoring stopped")
    finally:
        monitor.close()


if __name__ == '__main__':
    main()
