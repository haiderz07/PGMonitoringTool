#!/usr/bin/env python3
"""
PG-Monitor Web Dashboard
Modern web interface with authentication and guided setup
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import json
import os
import re
from datetime import datetime, timedelta
from functools import wraps
import sqlite3
from pg_monitor_enhanced import PGMonitorEnhanced

app = Flask(__name__)
# Use environment variable for secret key in production, fallback to random for development
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# ============================================================================
# SECURITY: Data Sanitization Functions (DBA + Security Best Practices)
# ============================================================================

def sanitize_query_for_display(query_text):
    """
    Mask sensitive information in SQL queries for web display
    Security: Prevents exposure of passwords, API keys, sensitive data
    DBA Practice: Show query structure without compromising security
    """
    if not query_text:
        return query_text
    
    # Patterns to mask (case-insensitive)
    sensitive_patterns = [
        # Password patterns
        (r"password\s*=\s*['\"]([^'\"]+)['\"]", "password='***MASKED***'"),
        (r"pwd\s*=\s*['\"]([^'\"]+)['\"]", "pwd='***MASKED***'"),
        
        # Connection strings
        (r"postgres://[^:]+:([^@]+)@", "postgres://user:***@"),
        
        # API keys and tokens
        (r"(api[_-]?key|token|secret)\s*=\s*['\"]([^'\"]+)['\"]", r"\1='***MASKED***'"),
        
        # Credit card patterns (basic)
        (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "****-****-****-****"),
        
        # Email addresses (partial masking)
        (r"([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", r"***@\2"),
    ]
    
    masked_query = query_text
    for pattern, replacement in sensitive_patterns:
        masked_query = re.sub(pattern, replacement, masked_query, flags=re.IGNORECASE)
    
    return masked_query

def sanitize_metrics_data(metrics):
    """
    Sanitize all metrics data before sending to frontend
    Apply to: query texts, error messages, connection strings
    """
    if isinstance(metrics, dict):
        sanitized = {}
        for key, value in metrics.items():
            if key == 'query_latency' and isinstance(value, list):
                # Sanitize query preview in slow queries
                sanitized[key] = [
                    {**q, 'query_preview': sanitize_query_for_display(q.get('query_preview', ''))}
                    for q in value
                ]
            elif isinstance(value, (dict, list)):
                sanitized[key] = sanitize_metrics_data(value)
            else:
                sanitized[key] = value
        return sanitized
    elif isinstance(metrics, list):
        return [sanitize_metrics_data(item) for item in metrics]
    else:
        return metrics

def detect_server_sku_and_recommend(monitor):
    """
    Detect PostgreSQL server SKU (Azure, AWS, On-Prem) and provide 
    performance parameter recommendations
    
    DBA Best Practice: Optimize based on infrastructure tier
    """
    try:
        # Get server configuration - Focus on PERFORMANCE-CRITICAL parameters
        config_query = """
        SELECT 
            name, 
            setting, 
            unit, 
            category,
            short_desc,
            context
        FROM pg_settings 
        WHERE name IN (
            -- Memory Management (CRITICAL for performance)
            'shared_buffers', 'effective_cache_size', 'work_mem', 'maintenance_work_mem',
            -- Connection Management
            'max_connections', 'superuser_reserved_connections',
            -- Query Planner (affects query execution plans)
            'random_page_cost', 'seq_page_cost', 'effective_io_concurrency',
            'default_statistics_target', 'cpu_tuple_cost', 'cpu_index_tuple_cost',
            -- WAL & Checkpoints (write performance)
            'wal_buffers', 'max_wal_size', 'min_wal_size', 'checkpoint_completion_target',
            'checkpoint_timeout', 'wal_compression',
            -- Autovacuum (prevents bloat)
            'autovacuum', 'autovacuum_max_workers', 'autovacuum_naptime',
            'autovacuum_vacuum_threshold', 'autovacuum_analyze_threshold',
            'autovacuum_vacuum_scale_factor', 'autovacuum_analyze_scale_factor',
            -- Parallel Query Execution
            'max_parallel_workers_per_gather', 'max_parallel_workers', 'max_worker_processes',
            -- Logging (for monitoring)
            'log_min_duration_statement', 'log_statement', 'log_line_prefix'
        )
        ORDER BY category, name;
        """
        
        current_config = monitor.execute_query(config_query)
        
        # Detect SKU from connection string and server parameters
        version_query = "SELECT version();"
        version_info = monitor.execute_query(version_query)
        version_str = version_info[0]['version'] if version_info else ''
        
        # Get host from connection parameters
        host = monitor.conn_params.get('host', 'unknown')
        
        # Detect server type
        is_azure = 'azure' in version_str.lower() or 'azure' in host.lower()
        is_aws_rds = 'rds' in host.lower()
        is_aws_aurora = 'aurora' in version_str.lower()
        
        # Get server memory (estimate from shared_buffers)
        shared_buffers_config = next((c for c in current_config if c['name'] == 'shared_buffers'), None)
        shared_buffers_mb = 0
        if shared_buffers_config:
            val = int(shared_buffers_config['setting'])
            unit = shared_buffers_config.get('unit', '8kB')
            if unit == '8kB':
                shared_buffers_mb = (val * 8) // 1024
            elif unit == 'MB':
                shared_buffers_mb = val
        
        # Estimate total RAM (shared_buffers is typically 25% of RAM)
        estimated_ram_gb = (shared_buffers_mb * 4) // 1024 if shared_buffers_mb > 0 else 4
        
        # Determine SKU tier
        if is_azure:
            if estimated_ram_gb >= 32:
                sku_tier = "Azure Database for PostgreSQL - Business Critical / Memory Optimized"
                tier_code = "azure_premium"
            elif estimated_ram_gb >= 8:
                sku_tier = "Azure Database for PostgreSQL - General Purpose"
                tier_code = "azure_gp"
            else:
                sku_tier = "Azure Database for PostgreSQL - Burstable"
                tier_code = "azure_basic"
        elif is_aws_aurora:
            sku_tier = f"AWS Aurora PostgreSQL (~{estimated_ram_gb}GB RAM)"
            tier_code = "aws_aurora"
        elif is_aws_rds:
            sku_tier = f"AWS RDS PostgreSQL (~{estimated_ram_gb}GB RAM)"
            tier_code = "aws_rds"
        else:
            sku_tier = f"On-Premise / Self-Hosted (~{estimated_ram_gb}GB RAM)"
            tier_code = "onprem"
        
        # Generate educational guidance based on SKU
        guidance_data = generate_parameter_recommendations(
            tier_code, estimated_ram_gb, current_config
        )
        
        return {
            'detected_sku': sku_tier,
            'estimated_ram_gb': estimated_ram_gb,
            'tier_code': tier_code,
            'parameter_guidance': guidance_data['parameters'],
            'workload_education': guidance_data['workload_education'],
            'is_cloud': is_azure or is_aws_rds or is_aws_aurora
        }
    except Exception as e:
        print(f"SKU detection failed: {e}")
        return {
            'detected_sku': 'Unknown',
            'estimated_ram_gb': 0,
            'tier_code': 'unknown',
            'parameter_guidance': [],
            'workload_education': {},
            'is_cloud': False,
            'error': str(e)
        }

def generate_parameter_recommendations(tier_code, ram_gb, current_config):
    """
    Generate educational guidance on PostgreSQL parameters
    Focus: Explain current settings and how to tune based on workload type
    """
    guidance = []
    
    # Helper to get current value with proper unit conversion
    def get_current(param_name):
        param = next((c for c in current_config if c['name'] == param_name), None)
        if not param:
            return None
        val = int(param['setting'])
        unit = param.get('unit', '')
        
        # Convert to human-readable format
        if unit == '8kB' and val > 128:
            mb_val = (val * 8) // 1024
            return {'value': val, 'unit': unit, 'display': f"{mb_val}MB", 'mb': mb_val}
        return {'value': val, 'unit': unit, 'display': f"{val}{unit}", 'mb': val if unit == 'MB' else 0}
    
    # Industry standard baselines for reference
    baseline_shared_buffers = ram_gb * 1024 // 4  # 25% of RAM (industry standard)
    baseline_effective_cache = ram_gb * 1024 * 3 // 4  # 75% of RAM
    
    # 1. shared_buffers - Core memory parameter
    current_sb = get_current('shared_buffers')
    if current_sb:
        guidance.append({
            'parameter': 'shared_buffers',
            'current_value': current_sb['display'],
            'is_default': current_sb.get('mb', 0) < 256,  # Default is typically 128MB
            'category': 'Memory Management',
            'industry_baseline': f'{baseline_shared_buffers}MB (25% of RAM)',
            'oltp_guidance': 'OLTP workloads benefit from 25-40% of RAM. Higher values reduce disk I/O for frequently accessed data.',
            'olap_guidance': 'OLAP workloads can use 25-50% of RAM. Larger shared_buffers help with sequential scans and aggregations.',
            'measurement_tip': 'Monitor: pg_stat_bgwriter for buffer hits vs reads. Target >95% cache hit ratio.',
            'tuning_note': 'Requires PostgreSQL restart. Start conservative, monitor cache hit ratio over 1 week.',
            'reference': 'https://www.postgresql.org/docs/current/runtime-config-resource.html#GUC-SHARED-BUFFERS'
        })
    
    # 2. effective_cache_size - Query planner hint
    current_ecs = get_current('effective_cache_size')
    if current_ecs:
        guidance.append({
            'parameter': 'effective_cache_size',
            'current_value': current_ecs['display'],
            'is_default': current_ecs.get('mb', 0) < 4096,
            'category': 'Query Planning',
            'industry_baseline': f'{baseline_effective_cache}MB (75% of RAM)',
            'oltp_guidance': 'Set to 50-75% of RAM. Helps planner choose index scans over sequential scans for point queries.',
            'olap_guidance': 'Set to 75% of RAM. Planner will favor hash joins and in-memory operations for large analytical queries.',
            'measurement_tip': 'Monitor: pg_stat_statements for seq_scan vs idx_scan ratio. Compare execution plans before/after tuning.',
            'tuning_note': 'No restart required. This is a planner hint, not actual memory allocation. Safe to adjust dynamically.',
            'reference': 'https://www.postgresql.org/docs/current/runtime-config-query.html#GUC-EFFECTIVE-CACHE-SIZE'
        })
    
    # 3. work_mem - Per-operation memory
    current_wm = get_current('work_mem')
    if current_wm:
        guidance.append({
            'parameter': 'work_mem',
            'current_value': current_wm['display'],
            'is_default': current_wm.get('value', 0) == 4096,  # Default 4MB
            'category': 'Query Execution',
            'industry_baseline': f'{max(4, (ram_gb * 1024) // 200)}MB (depends on connection count)',
            'oltp_guidance': 'Keep low (4-16MB) for high-concurrency OLTP. Many small queries running simultaneously.',
            'olap_guidance': 'Increase (64-256MB) for complex analytical queries with large sorts and hash joins. Fewer concurrent queries.',
            'measurement_tip': 'Monitor logs for "temporary file" messages. If frequent, increase work_mem. Watch total memory: work_mem × max_connections.',
            'tuning_note': 'No restart needed. Can set per-session. Formula: (RAM × 0.25) / expected_concurrent_queries',
            'reference': 'https://www.postgresql.org/docs/current/runtime-config-resource.html#GUC-WORK-MEM'
        })
    
    # 4. maintenance_work_mem - Maintenance operations
    current_mwm = get_current('maintenance_work_mem')
    if current_mwm:
        guidance.append({
            'parameter': 'maintenance_work_mem',
            'current_value': current_mwm['display'],
            'is_default': current_mwm.get('value', 0) == 65536,  # Default 64MB
            'category': 'Maintenance Operations',
            'industry_baseline': f'{min(2048, ram_gb * 1024 // 16)}MB (RAM/16, max 2GB)',
            'oltp_guidance': 'Set to 256-512MB. Speeds up VACUUM, CREATE INDEX on transactional tables.',
            'olap_guidance': 'Set to 1-2GB. Large fact tables benefit from more memory during index creation and ANALYZE.',
            'measurement_tip': 'Monitor VACUUM/ANALYZE duration in logs. Measure CREATE INDEX time on large tables.',
            'tuning_note': 'No restart needed. Higher values speed up maintenance but use more memory during operations.',
            'reference': 'https://www.postgresql.org/docs/current/runtime-config-resource.html#GUC-MAINTENANCE-WORK-MEM'
        })
    
    # 5. max_connections - Connection limit
    current_mc = get_current('max_connections')
    if current_mc:
        guidance.append({
            'parameter': 'max_connections',
            'current_value': str(current_mc['value']),
            'is_default': current_mc['value'] == 100,
            'category': 'Connection Management',
            'industry_baseline': 'OLTP: 100-300, OLAP: 20-50 (use connection pooling)',
            'oltp_guidance': 'High-concurrency OLTP needs 100-500 connections. Use PgBouncer/connection pooling to reduce memory overhead.',
            'olap_guidance': 'Low-concurrency OLAP needs 20-50 connections. Analytical queries consume more resources per connection.',
            'measurement_tip': 'Monitor pg_stat_activity: current connections vs max. Track connection wait times in application.',
            'tuning_note': 'Requires restart. Each connection uses ~10MB RAM. Formula: max_connections = (RAM - shared_buffers) / 10MB',
            'reference': 'https://www.postgresql.org/docs/current/runtime-config-connection.html#GUC-MAX-CONNECTIONS'
        })
    
    # Add workload-specific educational notes
    workload_education = {
        'title': '🎓 Understanding Workload Types',
        'oltp_characteristics': [
            'Many concurrent short transactions',
            'Heavy INSERT/UPDATE/DELETE operations',
            'Point queries with indexes',
            'Low work_mem, high max_connections',
            'Example: E-commerce, banking applications'
        ],
        'olap_characteristics': [
            'Few concurrent complex queries',
            'Heavy SELECT with aggregations',
            'Sequential scans on large tables',
            'High work_mem, low max_connections',
            'Example: Data warehouses, reporting systems'
        ],
        'measurement_tools': [
            'pg_stat_statements: Track query patterns and execution frequency',
            'pg_stat_database: Monitor transaction rates (xact_commit/sec)',
            'pg_stat_user_tables: Check seq_scan vs idx_scan ratios',
            'Query duration logs: Identify long-running analytical queries'
        ],
        'tuning_methodology': [
            '1️⃣ Baseline: Record current metrics for 1 week',
            '2️⃣ Identify: Classify workload as OLTP/OLAP/Mixed',
            '3️⃣ Adjust: Change one parameter at a time',
            '4️⃣ Monitor: Track impact for 3-7 days',
            '5️⃣ Validate: Compare performance metrics vs baseline'
        ]
    }
    
    return {
        'parameters': guidance,
        'workload_education': workload_education
    }

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User database (SQLite)
USER_DB = 'web_users.db'

def init_user_db():
    """Initialize user database"""
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            database TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            is_default BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    conn.close()

init_user_db()

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

@app.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect(USER_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, email FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], user_data[1], user_data[3])
            login_user(user, remember=True)
            flash('✅ Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('❌ Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if len(password) < 6:
            flash('❌ Password must be at least 6 characters', 'error')
            return render_template('register.html')
        
        conn = sqlite3.connect(USER_DB)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            flash('❌ Username already exists', 'error')
            conn.close()
            return render_template('register.html')
        
        # Create user
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            (username, password_hash, email)
        )
        conn.commit()
        conn.close()
        
        flash('✅ Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    flash('👋 Logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    # Check if user has any connections
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM connections WHERE user_id = ?", (current_user.id,))
    connection_count = cursor.fetchone()[0]
    conn.close()
    
    if connection_count == 0:
        return redirect(url_for('setup_wizard'))
    
    return render_template('dashboard.html', username=current_user.username)

@app.route('/setup-wizard')
@login_required
def setup_wizard():
    """Guided setup wizard"""
    return render_template('setup_wizard.html')

@app.route('/api/test-connection', methods=['POST'])
@login_required
def test_connection():
    """Test PostgreSQL connection"""
    data = request.json
    
    try:
        conn = psycopg2.connect(
            host=data['host'],
            port=int(data['port']),
            database=data['database'],
            user=data['username'],
            password=data['password'],
            connect_timeout=5
        )
        
        # Test if user has SELECT permission
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT current_user, session_user;")
        user_info = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '✅ Connection successful!',
            'version': version.split(' on ')[0],
            'current_user': user_info[0]
        })
    
    except psycopg2.OperationalError as e:
        return jsonify({
            'success': False,
            'message': f'❌ Connection failed: {str(e)}'
        }), 400
    
    except psycopg2.Error as e:
        return jsonify({
            'success': False,
            'message': f'❌ Database error: {str(e)}'
        }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'❌ Error: {str(e)}'
        }), 400

@app.route('/api/save-connection', methods=['POST'])
@login_required
def save_connection():
    """Save connection to database"""
    data = request.json
    
    try:
        conn = sqlite3.connect(USER_DB)
        cursor = conn.cursor()
        
        # Check if this is the first connection (make it default)
        cursor.execute("SELECT COUNT(*) FROM connections WHERE user_id = ?", (current_user.id,))
        is_first = cursor.fetchone()[0] == 0
        
        cursor.execute("""
            INSERT INTO connections (user_id, name, host, port, database, username, password, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            current_user.id,
            data['name'],
            data['host'],
            int(data['port']),
            data['database'],
            data['username'],
            data['password'],
            is_first
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '✅ Connection saved successfully!',
            'redirect': url_for('dashboard')
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'❌ Error saving connection: {str(e)}'
        }), 400

@app.route('/api/connections')
@login_required
def get_connections():
    """Get user's connections"""
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, host, port, database, username, is_default, created_at
        FROM connections
        WHERE user_id = ?
        ORDER BY is_default DESC, created_at DESC
    """, (current_user.id,))
    
    connections = []
    for row in cursor.fetchall():
        connections.append({
            'id': row[0],
            'name': row[1],
            'host': row[2],
            'port': row[3],
            'database': row[4],
            'username': row[5],
            'is_default': bool(row[6]),
            'created_at': row[7]
        })
    
    conn.close()
    return jsonify(connections)

@app.route('/api/metrics/<int:connection_id>')
@login_required
def get_metrics(connection_id):
    """Get PostgreSQL metrics - optimized but COMPLETE like CLI"""
    # Get connection details
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT host, port, database, username, password
        FROM connections
        WHERE id = ? AND user_id = ?
    """, (connection_id, current_user.id))
    
    conn_data = cursor.fetchone()
    conn.close()
    
    if not conn_data:
        return jsonify({'error': 'Connection not found'}), 404
    
    try:
        # Initialize monitor - DISABLE HISTORY for speed
        monitor = PGMonitorEnhanced(
            host=conn_data[0],
            port=conn_data[1],
            database=conn_data[2],
            user=conn_data[3],
            password=conn_data[4],
            enable_history=False  # This saves 2-3 seconds!
        )
        
        if not monitor.connect():
            return jsonify({'error': 'Failed to connect to database'}), 500
        
        # Get ALL metrics like CLI - but optimized limits for web
        metrics = {
            'metadata': monitor.get_database_metadata(),
            'connections': monitor.get_connection_pool_health(),
            'transaction_perf': monitor.get_transaction_performance(),
            'query_latency': monitor.get_query_latency(50),  # Top 50 (CLI default: 100)
            'table_bloat': monitor.get_table_bloat(10),  # Top 10 (CLI default: 20)
            'table_stats_health': monitor.get_table_statistics_health(20),  # Top 20 (CLI default)
            'index_analysis': monitor.get_index_usage_analysis(),  # Index health (unused, missing, bloated)
            'system_metrics': monitor.get_system_metrics(),
            'timestamp': datetime.now().isoformat()
        }
        
        # DBA FEATURE: SKU-based parameter recommendations
        sku_info = detect_server_sku_and_recommend(monitor)
        metrics['server_sku'] = sku_info
        
        monitor.close()
        
        # SECURITY: Sanitize sensitive data before sending to frontend
        sanitized_metrics = sanitize_metrics_data(metrics)
        
        return jsonify(sanitized_metrics)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics-fast/<int:connection_id>')
@login_required
def get_metrics_fast(connection_id):
    """Get only fast metrics for quick overview"""
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT host, port, database, username, password
        FROM connections
        WHERE id = ? AND user_id = ?
    """, (connection_id, current_user.id))
    
    conn_data = cursor.fetchone()
    conn.close()
    
    if not conn_data:
        return jsonify({'error': 'Connection not found'}), 404
    
    try:
        monitor = PGMonitorEnhanced(
            host=conn_data[0],
            port=conn_data[1],
            database=conn_data[2],
            user=conn_data[3],
            password=conn_data[4],
            enable_history=False
        )
        
        if not monitor.connect():
            return jsonify({'error': 'Failed to connect to database'}), 500
        
        # Only fast queries
        metrics = {
            'metadata': monitor.get_database_metadata(),
            'connections': monitor.get_connection_pool_health(),
            'transaction_perf': monitor.get_transaction_performance(),
            'system_metrics': monitor.get_system_metrics(),
            'timestamp': datetime.now().isoformat()
        }
        
        monitor.close()
        
        # SECURITY: Sanitize even fast metrics
        sanitized_metrics = sanitize_metrics_data(metrics)
        return jsonify(sanitized_metrics)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-connection/<int:connection_id>', methods=['DELETE'])
@login_required
def delete_connection(connection_id):
    """Delete a connection"""
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM connections WHERE id = ? AND user_id = ?", (connection_id, current_user.id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '✅ Connection deleted'})

@app.route('/debug/connections')
@login_required
def debug_connections():
    """Debug: Show all connections for current user"""
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connections WHERE user_id = ?", (current_user.id,))
    rows = cursor.fetchall()
    
    cursor.execute("PRAGMA table_info(connections)")
    columns = [col[1] for col in cursor.fetchall()]
    
    conn.close()
    
    result = {
        'user_id': current_user.id,
        'username': current_user.username,
        'columns': columns,
        'connections': [dict(zip(columns, row)) for row in rows]
    }
    
    return jsonify(result)

@app.route('/test-page')
@login_required
def test_page():
    """Test page for debugging connections"""
    return render_template('test_connections.html')

if __name__ == '__main__':
    # Get port from environment variable (Render provides this)
    port = int(os.environ.get('PORT', 5000))
    # Disable debug in production
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
