#!/usr/bin/env python3
"""
Heavy Load Generator - Millions of records insert/update/delete
Real-time monitoring ke liye design kiya gaya hai
"""

import psycopg2
import time
import random
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class HeavyLoadGenerator:
    """Generate heavy database load with millions of records"""
    
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('PG_HOST', 'localhost'),
            'port': int(os.getenv('PG_PORT', 5432)),
            'database': os.getenv('PG_DATABASE', 'postgres'),
            'user': os.getenv('PG_USER', 'postgres'),
            'password': os.getenv('PG_PASSWORD', '')
        }
        self.conn = None
    
    def connect(self):
        """Connect to database"""
        self.conn = psycopg2.connect(**self.conn_params)
        self.conn.autocommit = False  # Manual transaction control
    
    def setup_tables(self):
        """Create tables for heavy load testing"""
        print("📊 Setting up tables for heavy load...")
        cursor = self.conn.cursor()
        
        # Drop existing tables
        cursor.execute("DROP TABLE IF EXISTS load_test_orders CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS load_test_customers CASCADE;")
        
        # Create customers table
        cursor.execute("""
            CREATE TABLE load_test_customers (
                id SERIAL PRIMARY KEY,
                customer_name VARCHAR(100),
                email VARCHAR(100),
                phone VARCHAR(20),
                address TEXT,
                city VARCHAR(50),
                country VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                status VARCHAR(20) DEFAULT 'active'
            );
        """)
        
        # Create orders table
        cursor.execute("""
            CREATE TABLE load_test_orders (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER,
                order_date TIMESTAMP DEFAULT NOW(),
                total_amount DECIMAL(10,2),
                items_count INTEGER,
                status VARCHAR(20) DEFAULT 'pending',
                payment_method VARCHAR(20),
                shipping_address TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_customers_email ON load_test_customers(email);")
        cursor.execute("CREATE INDEX idx_customers_status ON load_test_customers(status);")
        cursor.execute("CREATE INDEX idx_orders_customer ON load_test_orders(customer_id);")
        cursor.execute("CREATE INDEX idx_orders_status ON load_test_orders(status);")
        cursor.execute("CREATE INDEX idx_orders_date ON load_test_orders(order_date);")
        
        self.conn.commit()
        cursor.close()
        print("✅ Tables created successfully!")
    
    def bulk_insert_customers(self, count=100000):
        """Bulk insert customers"""
        print(f"\n🚀 Starting bulk insert of {count:,} customers...")
        cursor = self.conn.cursor()
        
        batch_size = 5000
        total_batches = count // batch_size
        start_time = time.time()
        
        for batch in range(total_batches):
            values = []
            for i in range(batch_size):
                customer_id = batch * batch_size + i
                values.append(f"('Customer_{customer_id}', 'customer_{customer_id}@example.com', "
                            f"'+92-300-{random.randint(1000000, 9999999)}', "
                            f"'Address {customer_id}', 'City_{random.randint(1, 100)}', "
                            f"'Pakistan', NOW(), NOW(), "
                            f"'{random.choice(['active', 'inactive', 'suspended'])}')")
            
            query = f"""
                INSERT INTO load_test_customers 
                (customer_name, email, phone, address, city, country, created_at, updated_at, status)
                VALUES {','.join(values)}
            """
            
            cursor.execute(query)
            self.conn.commit()
            
            elapsed = time.time() - start_time
            progress = ((batch + 1) / total_batches) * 100
            rate = ((batch + 1) * batch_size) / elapsed
            
            print(f"   Progress: {progress:.1f}% | Inserted: {(batch + 1) * batch_size:,} | "
                  f"Rate: {rate:.0f} rows/sec | Elapsed: {elapsed:.1f}s")
        
        cursor.close()
        total_time = time.time() - start_time
        print(f"✅ Inserted {count:,} customers in {total_time:.2f} seconds ({count/total_time:.0f} rows/sec)")
    
    def bulk_insert_orders(self, count=1000000):
        """Bulk insert orders"""
        print(f"\n🚀 Starting bulk insert of {count:,} orders...")
        cursor = self.conn.cursor()
        
        # Get customer count
        cursor.execute("SELECT COUNT(*) FROM load_test_customers")
        customer_count = cursor.fetchone()[0]
        
        batch_size = 10000
        total_batches = count // batch_size
        start_time = time.time()
        
        for batch in range(total_batches):
            values = []
            for i in range(batch_size):
                customer_id = random.randint(1, customer_count)
                amount = random.uniform(100, 10000)
                items = random.randint(1, 20)
                status = random.choice(['pending', 'processing', 'shipped', 'delivered', 'cancelled'])
                payment = random.choice(['credit_card', 'debit_card', 'cash', 'bank_transfer'])
                
                values.append(f"({customer_id}, NOW() - INTERVAL '{random.randint(0, 365)} days', "
                            f"{amount:.2f}, {items}, '{status}', '{payment}', "
                            f"'Shipping Address {i}', NOW(), NOW())")
            
            query = f"""
                INSERT INTO load_test_orders 
                (customer_id, order_date, total_amount, items_count, status, 
                 payment_method, shipping_address, created_at, updated_at)
                VALUES {','.join(values)}
            """
            
            cursor.execute(query)
            self.conn.commit()
            
            elapsed = time.time() - start_time
            progress = ((batch + 1) / total_batches) * 100
            rate = ((batch + 1) * batch_size) / elapsed
            
            print(f"   Progress: {progress:.1f}% | Inserted: {(batch + 1) * batch_size:,} | "
                  f"Rate: {rate:.0f} rows/sec | Elapsed: {elapsed:.1f}s")
        
        cursor.close()
        total_time = time.time() - start_time
        print(f"✅ Inserted {count:,} orders in {total_time:.2f} seconds ({count/total_time:.0f} rows/sec)")
    
    def heavy_updates(self, count=50000, duration=60):
        """Continuous heavy updates"""
        print(f"\n🔄 Starting heavy updates ({count:,} updates over {duration}s)...")
        cursor = self.conn.cursor()
        
        start_time = time.time()
        updates_done = 0
        
        while time.time() - start_time < duration and updates_done < count:
            # Update customers
            cursor.execute("""
                UPDATE load_test_customers 
                SET updated_at = NOW(), 
                    status = CASE 
                        WHEN random() < 0.3 THEN 'active'
                        WHEN random() < 0.6 THEN 'inactive'
                        ELSE 'suspended'
                    END
                WHERE id IN (
                    SELECT id FROM load_test_customers 
                    ORDER BY random() 
                    LIMIT 100
                )
            """)
            
            # Update orders
            cursor.execute("""
                UPDATE load_test_orders 
                SET updated_at = NOW(),
                    status = CASE 
                        WHEN status = 'pending' THEN 'processing'
                        WHEN status = 'processing' THEN 'shipped'
                        WHEN status = 'shipped' THEN 'delivered'
                        ELSE status
                    END
                WHERE id IN (
                    SELECT id FROM load_test_orders 
                    WHERE status != 'delivered'
                    ORDER BY random() 
                    LIMIT 100
                )
            """)
            
            self.conn.commit()
            updates_done += 200
            
            if updates_done % 1000 == 0:
                elapsed = time.time() - start_time
                rate = updates_done / elapsed
                print(f"   Updates: {updates_done:,} | Rate: {rate:.0f} updates/sec | Elapsed: {elapsed:.1f}s")
            
            time.sleep(0.1)  # Small delay to create sustained load
        
        cursor.close()
        total_time = time.time() - start_time
        print(f"✅ Completed {updates_done:,} updates in {total_time:.2f} seconds")
    
    def heavy_deletes(self, count=10000):
        """Heavy deletes"""
        print(f"\n🗑️  Starting heavy deletes ({count:,} records)...")
        cursor = self.conn.cursor()
        
        start_time = time.time()
        
        # Delete old orders
        cursor.execute(f"""
            DELETE FROM load_test_orders 
            WHERE id IN (
                SELECT id FROM load_test_orders 
                WHERE status = 'cancelled' 
                ORDER BY random() 
                LIMIT {count}
            )
        """)
        deleted = cursor.rowcount
        self.conn.commit()
        
        cursor.close()
        total_time = time.time() - start_time
        print(f"✅ Deleted {deleted:,} orders in {total_time:.2f} seconds")
    
    def complex_queries(self, duration=30):
        """Run complex queries"""
        print(f"\n🔍 Running complex queries for {duration}s...")
        cursor = self.conn.cursor()
        
        start_time = time.time()
        query_count = 0
        
        while time.time() - start_time < duration:
            # Complex join query
            cursor.execute("""
                SELECT 
                    c.city,
                    COUNT(DISTINCT c.id) as customer_count,
                    COUNT(o.id) as order_count,
                    SUM(o.total_amount) as total_revenue,
                    AVG(o.items_count) as avg_items
                FROM load_test_customers c
                LEFT JOIN load_test_orders o ON c.id = o.customer_id
                WHERE o.order_date > NOW() - INTERVAL '180 days'
                GROUP BY c.city
                HAVING COUNT(o.id) > 10
                ORDER BY total_revenue DESC
                LIMIT 20
            """)
            cursor.fetchall()
            
            query_count += 1
            
            if query_count % 10 == 0:
                elapsed = time.time() - start_time
                rate = query_count / elapsed
                print(f"   Queries: {query_count} | Rate: {rate:.1f} queries/sec")
            
            time.sleep(1)
        
        cursor.close()
        print(f"✅ Completed {query_count} complex queries")
    
    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()


def main():
    """Run heavy load generator"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Heavy Load Generator - Millions of Records             ║")
    print("║   Monitor with: python pg_monitor_enhanced.py --all      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    # Ask user for mode
    print("Choose mode:")
    print("  1. One-shot - Load data once and exit")
    print("  2. Continuous - Run for 16 minutes (8 cycles × 2 min intervals)")
    print()
    
    # Validate input
    while True:
        mode_choice = input("Enter choice (1 or 2): ").strip()
        if mode_choice in ['1', '2']:
            break
        print("❌ Invalid choice. Please enter 1 or 2.\n")
    
    continuous_mode = mode_choice == "2"
    
    if continuous_mode:
        print("\n✅ Continuous mode selected - Will run 8 cycles (16 minutes total)")
        print("   Each cycle runs every 2 minutes")
        print("   Press Ctrl+C to stop early\n")
    else:
        print("\n✅ One-shot mode selected - Will load data and exit\n")
    
    generator = HeavyLoadGenerator()
    
    try:
        generator.connect()
        print("✅ Connected to database")
        
        # Phase 1: Setup
        generator.setup_tables()
        
        # Phase 2: Insert customers (100K)
        generator.bulk_insert_customers(count=100000)
        
        # Phase 3: Insert orders (1 Million)
        generator.bulk_insert_orders(count=1000000)
        
        if continuous_mode:
            print("\n" + "="*60)
            print("⏸️  Data loaded! Now starting continuous operations...")
            print("   Total duration: 16 minutes (8 cycles)")
            print("   Open another terminal and run:")
            print("   python pg_monitor_enhanced.py --all")
            print("="*60)
            
            time.sleep(5)
            
            # Continuous load loop - 8 cycles (16 minutes)
            max_cycles = 8
            cycle = 1
            while cycle <= max_cycles:
                print("\n" + "="*60)
                print(f"🔄 CYCLE {cycle} - Continuous Load Operations")
                print("="*60)
                
                # Phase 4: Heavy updates (60 seconds)
                generator.heavy_updates(count=50000, duration=60)
                
                # Phase 5: Complex queries (30 seconds)
                generator.complex_queries(duration=30)
                
                # Phase 6: Heavy deletes
                generator.heavy_deletes(count=10000)
                
                # Phase 7: More inserts to compensate deletes
                print(f"\n➕ Inserting more orders to compensate deletes...")
                cursor = generator.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM load_test_customers")
                customer_count = cursor.fetchone()[0]
                
                values = []
                for i in range(10000):
                    customer_id = random.randint(1, customer_count)
                    amount = random.uniform(100, 10000)
                    items = random.randint(1, 20)
                    status = random.choice(['pending', 'processing', 'shipped'])
                    payment = random.choice(['credit_card', 'debit_card', 'cash'])
                    values.append(f"({customer_id}, NOW(), {amount:.2f}, {items}, '{status}', '{payment}', 'New Address', NOW(), NOW())")
                
                query = f"""
                    INSERT INTO load_test_orders 
                    (customer_id, order_date, total_amount, items_count, status, payment_method, shipping_address, created_at, updated_at)
                    VALUES {','.join(values)}
                """
                cursor.execute(query)
                generator.conn.commit()
                cursor.close()
                print(f"   ✅ Inserted 10,000 new orders")
                
                if cycle < max_cycles:
                    print("\n" + "="*60)
                    print(f"✅ Cycle {cycle}/{max_cycles} complete! Next cycle in 2 minutes...")
                    print(f"   Remaining: {max_cycles - cycle} cycles ({(max_cycles - cycle) * 2} minutes)")
                    print("   Monitor shows:")
                    print("   - Connection pool usage")
                    print("   - Table bloat from updates/deletes")
                    print("   - Cache hit ratios")
                    print("   - Query latency")
                    print("="*60)
                    time.sleep(120)  # 2 minutes
                else:
                    print("\n" + "="*60)
                    print(f"✅ ALL CYCLES COMPLETE! ({max_cycles} cycles, 16 minutes)")
                    print("   Load generation finished.")
                    print("="*60)
                
                cycle += 1
        else:
            # One-shot mode
            print("\n" + "="*60)
            print("⏸️  Data loaded! Running one-shot operations...")
            print("="*60)
            
            time.sleep(2)
            
            # Single cycle operations
            generator.heavy_updates(count=50000, duration=60)
            generator.complex_queries(duration=30)
            generator.heavy_deletes(count=10000)
            
            print("\n" + "="*60)
            print("✅ One-shot load generation complete!")
            print("   Check monitoring to see the impact:")
            print("   python pg_monitor_enhanced.py --all")
            print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        generator.close()


if __name__ == '__main__':
    main()
