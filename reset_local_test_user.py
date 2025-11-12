import sqlite3

# Connect to local SQLite database
conn = sqlite3.connect('web_users.db')
cursor = conn.cursor()

# Show all users
print("\n📊 Current Users in Local Database:")
print("=" * 100)
cursor.execute('''
    SELECT id, username, email, subscription_tier, monthly_payment, 
           max_connections, stripe_subscription_id, stripe_customer_id,
           subscription_status, created_at
    FROM users 
    ORDER BY id
''')
users = cursor.fetchall()

print(f"{'ID':<5} {'Username':<15} {'Email':<25} {'Tier':<8} {'$':<6} {'Conns':<7} {'Status':<10} {'Stripe Sub'}")
print("-" * 100)

for user in users:
    stripe_sub = (user[6][:20] + '...') if user[6] else 'None'
    email = user[2] if user[2] else 'N/A'
    status = user[8] if user[8] else 'N/A'
    print(f"{user[0]:<5} {user[1]:<15} {email:<25} {user[3]:<8} ${user[4]:<5} {user[5]:<7} {status:<10} {stripe_sub}")

print("\n")

# Ask which user to reset
user_input = input("Enter the ID of the test user to reset to FREE tier (or 'q' to quit): ")

if user_input.lower() != 'q':
    try:
        user_id = int(user_input)
        
        # Get user details
        cursor.execute('SELECT username, subscription_tier FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            print(f"❌ User ID {user_id} not found!")
        else:
            username, current_tier = user_data
            print(f"\n⚠️  About to reset user: {username} (currently {current_tier})")
            confirm = input("Are you sure? Type 'yes' to confirm: ")
            
            if confirm.lower() == 'yes':
                # Reset to free tier
                cursor.execute('''
                    UPDATE users 
                    SET subscription_tier = 'free',
                        monthly_payment = 0,
                        max_connections = 2,
                        stripe_subscription_id = NULL,
                        stripe_customer_id = NULL,
                        subscription_status = 'inactive'
                    WHERE id = ?
                ''', (user_id,))
                
                conn.commit()
                print(f"\n✅ Successfully reset user '{username}' to FREE tier!")
                print("   - Tier: free")
                print("   - Monthly Payment: $0")
                print("   - Max Connections: 2")
                print("   - Stripe IDs: Cleared")
                print("   - Status: inactive")
                
                # Also log this activity
                cursor.execute('''
                    INSERT INTO activity_log (user_id, action, details, timestamp)
                    VALUES (?, ?, ?, datetime('now'))
                ''', (user_id, 'ADMIN_RESET', f'Reset test user {username} to free tier (removed invalid paid status)'))
                conn.commit()
                
            else:
                print("❌ Reset cancelled.")
    except ValueError:
        print("❌ Invalid user ID!")
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()

cursor.close()
conn.close()
print("\n🔒 Database connection closed.")
