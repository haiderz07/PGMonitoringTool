"""
Add metrics_history table for storing historical snapshots (paid users only)
"""
import sqlite3
import os

def add_metrics_history_table():
    db_path = 'web_users.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create metrics_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            connection_id INTEGER NOT NULL,
            snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            db_size TEXT,
            connections_count INTEGER,
            tps REAL,
            cache_hit_ratio REAL,
            rollback_rate REAL,
            deadlocks INTEGER,
            bloat_percentage REAL,
            index_usage REAL,
            slow_queries_count INTEGER,
            metrics_json TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (connection_id) REFERENCES connections (id)
        )
    """)
    
    # Create index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_metrics_history_lookup 
        ON metrics_history (user_id, connection_id, snapshot_time DESC)
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ metrics_history table created successfully!")

if __name__ == '__main__':
    add_metrics_history_table()
