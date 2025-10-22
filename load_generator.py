#!/usr/bin/env python3
"""
Load Generator for PostgreSQL - Creates realistic database activity for testing monitoring
"""

import psycopg2
import time
import random
import os
from dotenv import load_dotenv
from threading import Thread

load_dotenv()

class PGLoadGenerator:
    """Generate various types of database load"""
    
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('PG_HOST', 'localhost'),
            'port': int(os.getenv('PG_PORT', 5432)),
            'database': os.getenv('PG_DATABASE', 'postgres'),
            'user': os.getenv('PG_USER', 'postgres'),
            'password': os.getenv('PG_PASSWORD', '')
        }
    
    def setup_test_data(self):
        """Create test tables with data"""
        print("📊 Setting up test data...")
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute("""
            DROP TABLE IF EXISTS test_users CASCADE;
            CREATE TABLE test_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50),
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW(),
                last_login TIMESTAMP,
                status VARCHAR(20)
            );
        """)
        
        cursor.execute("""
            DROP TABLE IF EXISTS test_orders CASCADE;
            CREATE TABLE test_orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                order_date TIMESTAMP DEFAULT NOW(),
                amount DECIMAL(10,2),
                status VARCHAR(20)
            );
        """)
        
        # Insert sample data
        print("   Inserting sample data...")
        for i in range(1000):
            cursor.execute("""
                INSERT INTO test_users (username, email, last_login, status)
                VALUES (%s, %s, NOW() - INTERVAL '%s days', %s)
            """, (f'user_{i}', f'user_{i}@example.com', random.randint(1, 30), 
                  random.choice(['active', 'inactive', 'suspended'])))
        
        for i in range(5000):
            cursor.execute("""
                INSERT INTO test_orders (user_id, amount, status)
                VALUES (%s, %s, %s)
            """, (random.randint(1, 1000), random.uniform(10, 1000), 
                  random.choice(['pending', 'completed', 'cancelled'])))
        
        # Create some indexes (one will be unused)
        cursor.execute("CREATE INDEX idx_users_username ON test_users(username);")
        cursor.execute("CREATE INDEX idx_users_email ON test_users(email);")
        cursor.execute("CREATE INDEX idx_users_unused ON test_users(status, created_at);")  # Will be unused
        cursor.execute("CREATE INDEX idx_orders_user ON test_orders(user_id);")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Test data created!")
    
    def generate_slow_queries(self, duration=60):
        """Generate intentionally slow queries"""
        print(f"🐌 Generating slow queries for {duration}s...")
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()
        
        start = time.time()
        while time.time() - start < duration:
            # Slow query without index
            cursor.execute("""
                SELECT u.*, COUNT(o.id) as order_count
                FROM test_users u
                LEFT JOIN test_orders o ON o.user_id = u.id
                WHERE u.email LIKE '%example.com'
                GROUP BY u.id
                ORDER BY order_count DESC;
            """)
            cursor.fetchall()
            
            time.sleep(2)
        
        cursor.close()
        conn.close()
        print("✅ Slow queries completed")
    
    def generate_lock_contention(self, duration=60):
        """Create lock contention scenarios"""
        print(f"🔒 Generating lock contention for {duration}s...")
        
        def long_transaction():
            conn = psycopg2.connect(**self.conn_params)
            cursor = conn.cursor()
            cursor.execute("BEGIN;")
            cursor.execute("UPDATE test_users SET status = 'locked' WHERE id = 1;")
            time.sleep(15)  # Hold lock for 15 seconds
            cursor.execute("COMMIT;")
            cursor.close()
            conn.close()
        
        def blocked_transaction():
            time.sleep(2)  # Wait a bit before trying
            conn = psycopg2.connect(**self.conn_params)
            cursor = conn.cursor()
            try:
                cursor.execute("SET statement_timeout = '5000';")  # 5 second timeout
                cursor.execute("UPDATE test_users SET last_login = NOW() WHERE id = 1;")
                conn.commit()
            except:
                pass
            cursor.close()
            conn.close()
        
        start = time.time()
        while time.time() - start < duration:
            t1 = Thread(target=long_transaction)
            t2 = Thread(target=blocked_transaction)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            time.sleep(5)
        
        print("✅ Lock contention completed")
    
    def generate_connection_load(self, duration=60):
        """Create multiple connections"""
        print(f"🔌 Generating connection load for {duration}s...")
        connections = []
        
        # Open many connections
        for i in range(10):
            conn = psycopg2.connect(**self.conn_params)
            connections.append(conn)
            print(f"   Opened connection {i+1}/10")
        
        # Keep them alive
        time.sleep(duration)
        
        # Close them
        for conn in connections:
            conn.close()
        
        print("✅ Connection load completed")
    
    def generate_table_bloat(self):
        """Create table bloat by doing updates without vacuum"""
        print("💾 Generating table bloat...")
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()
        
        # Many updates create dead tuples
        for i in range(500):
            cursor.execute("""
                UPDATE test_users 
                SET last_login = NOW() 
                WHERE id = %s
            """, (random.randint(1, 1000),))
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Table bloat generated (dead tuples created)")
    
    def cleanup(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS test_users CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS test_orders CASCADE;")
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Cleanup completed")


def main():
    """Run load generation scenarios"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   PostgreSQL Load Generator - Testing Monitoring         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    generator = PGLoadGenerator()
    
    try:
        # Setup
        generator.setup_test_data()
        print()
        
        # Generate various loads (run in parallel for 60 seconds)
        print("🚀 Starting load generation (60 seconds)...")
        print("   This will create:")
        print("   - Slow queries (visible in query latency)")
        print("   - Lock contention (blocking scenarios)")
        print("   - Connection pool usage")
        print("   - Table bloat (dead tuples)")
        print()
        
        threads = [
            Thread(target=generator.generate_slow_queries, args=(60,)),
            Thread(target=generator.generate_lock_contention, args=(60,)),
            Thread(target=generator.generate_connection_load, args=(60,))
        ]
        
        for t in threads:
            t.start()
        
        # Generate bloat after 10 seconds
        time.sleep(10)
        generator.generate_table_bloat()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        print()
        print("✅ Load generation complete!")
        print()
        print("📊 Now run the monitoring tool to see the results:")
        print("   python pg_monitor_enhanced.py --all")
        print()
        print("🧹 To clean up test data later:")
        print("   python load_generator.py --cleanup")
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == '__main__':
    import sys
    if '--cleanup' in sys.argv:
        generator = PGLoadGenerator()
        generator.cleanup()
    else:
        main()
