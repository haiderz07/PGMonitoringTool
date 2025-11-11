#!/usr/bin/env python3
"""
Simple Database Connection Wrapper
Automatically uses PostgreSQL in production (Render) and SQLite in development
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import DictCursor


class DatabaseConnection:
    """Simple wrapper that makes PostgreSQL behave like SQLite"""
    
    def __init__(self):
        database_url = os.environ.get('DATABASE_URL')
        
        # Production: Use PostgreSQL if DATABASE_URL is set
        if database_url and database_url.startswith('postgresql'):
            self.db_type = 'postgresql'
            self.conn = psycopg2.connect(database_url)
            print("✅ Connected to PostgreSQL (Production)")
        else:
            # Development: Use SQLite
            self.db_type = 'sqlite'
            self.conn = sqlite3.connect('web_users.db', check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            print("✅ Connected to SQLite (Development)")
    
    def cursor(self):
        """Return cursor that works for both databases"""
        if self.db_type == 'postgresql':
            return self.conn.cursor(cursor_factory=DictCursor)
        else:
            return self.conn.cursor()
    
    def commit(self):
        """Commit transaction"""
        self.conn.commit()
    
    def close(self):
        """Close connection"""
        self.conn.close()
    
    def execute(self, query, params=None):
        """
        Execute query with automatic ? to %s conversion for PostgreSQL
        Returns cursor for chaining
        """
        cursor = self.cursor()
        
        # Convert SQLite ? placeholders to PostgreSQL %s
        if self.db_type == 'postgresql' and params:
            query = query.replace('?', '%s')
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        return cursor


def get_db():
    """Get database connection (auto-detects PostgreSQL vs SQLite)"""
    return DatabaseConnection()


def init_database():
    """
    Initialize database tables
    Uses EXACT same schema for both SQLite and PostgreSQL
    """
    db = get_db()
    cursor = db.cursor()
    
    if db.db_type == 'postgresql':
        # PostgreSQL schema (converted from SQLite)
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_tier VARCHAR(20) DEFAULT 'free',
                monthly_payment DECIMAL(10,2) DEFAULT 0.0,
                stripe_customer_id VARCHAR(100),
                stripe_subscription_id VARCHAR(100),
                subscription_status VARCHAR(20) DEFAULT 'active',
                max_connections INTEGER DEFAULT 2,
                last_payment_date TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS connections (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(100) NOT NULL,
                host VARCHAR(255) NOT NULL,
                port INTEGER NOT NULL,
                database VARCHAR(100) NOT NULL,
                username VARCHAR(100) NOT NULL,
                password VARCHAR(255) NOT NULL,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                activity_type VARCHAR(50) NOT NULL,
                description TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
    else:
        # SQLite schema (original)
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                subscription_tier TEXT DEFAULT 'free',
                monthly_payment REAL DEFAULT 0.0,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                subscription_status TEXT DEFAULT 'active',
                max_connections INTEGER DEFAULT 2,
                last_payment_date DATETIME
            )
            """,
            """
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
            """,
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                activity_type TEXT NOT NULL,
                description TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        ]
    
    # Execute all table creation queries
    for query in queries:
        cursor.execute(query)
    
    db.commit()
    db.close()
    
    print(f"✅ Database initialized ({db.db_type})")


if __name__ == '__main__':
    # Test the database connection
    print("Testing database connection...")
    init_database()
    db = get_db()
    print(f"✅ Successfully connected to {db.db_type}")
    db.close()
