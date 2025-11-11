#!/usr/bin/env python3
"""
Quick Render Database Setup
Run this once in Render Shell after deployment
"""

from simple_db import init_database, get_db

print("=" * 60)
print("RENDER DATABASE SETUP")
print("=" * 60)

# Initialize database
print("\nInitializing database...")
init_database()

# Verify
db = get_db()
cursor = db.cursor()

if db.db_type == 'postgresql':
    # Show tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n✅ PostgreSQL tables created: {', '.join(tables)}")
    
    # Show users count
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"✅ Users table ready (current count: {user_count})")
else:
    print("\n⚠️  Running on SQLite (development mode)")

db.close()

print("\n" + "=" * 60)
print("✅ SETUP COMPLETE!")
print("=" * 60)
print("\nYour app is ready! You can now:")
print("1. Open your Render URL")
print("2. Register a new user")
print("3. Add PostgreSQL database connections")
print("4. Start monitoring!")
