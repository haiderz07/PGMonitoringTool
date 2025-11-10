# 📊 Render.com Monitoring & User Tracking Guide

## How to View Logs and Track Users on Render

---

## 🔍 Viewing Logs on Render

### Method 1: Render Dashboard (Real-time)

1. **Go to Render Dashboard:**
   ```
   https://dashboard.render.com
   ```

2. **Select Your Service:**
   - Click on **"pg-monitoring-tool"** (or your service name)

3. **Click "Logs" Tab:**
   - Top navigation: **Logs**
   - Shows real-time output from your app

4. **What You'll See:**
   ```
   [STARTUP] PG Monitor starting on port 10000
   [STARTUP] Debug mode: False
   [STARTUP] Environment: production
   [ACTIVITY] User 1 | REGISTER | New user registered: haider (haider@email.com)
   [ACTIVITY] User 1 | LOGIN | User haider logged in successfully
   [ACTIVITY] User 1 | ADD_CONNECTION | Added connection: Production DB (pg-server.com)
   [SECURITY] Failed login attempt for username: admin from IP: 192.168.1.100
   ```

### Method 2: Render CLI (Advanced)

```bash
# Install Render CLI
npm install -g @render/cli

# Login
render login

# View logs
render logs --service pg-monitoring-tool --follow
```

---

## 👥 Tracking User Registrations

### In Application Logs (Console Output)

Every user action is logged to console with `print()` statements:

**Registration:**
```python
[ACTIVITY] User 5 | REGISTER | New user registered: john_doe (john@company.com)
```

**Login:**
```python
[ACTIVITY] User 5 | LOGIN | User john_doe logged in successfully
```

**Failed Login:**
```python
[SECURITY] Failed login attempt for username: john_doe from IP: 203.0.113.45
```

**Adding Database:**
```python
[ACTIVITY] User 5 | ADD_CONNECTION | Added connection: Production DB (prod-db.example.com)
```

### In Database (SQLite)

All activity is stored in `activity_log` table:

```sql
-- View all registrations
SELECT * FROM activity_log 
WHERE activity_type = 'REGISTER' 
ORDER BY created_at DESC;

-- View all logins today
SELECT u.username, a.ip_address, a.created_at 
FROM activity_log a
JOIN users u ON a.user_id = u.id
WHERE activity_type = 'LOGIN'
AND DATE(a.created_at) = DATE('now')
ORDER BY a.created_at DESC;

-- View user statistics
SELECT 
    COUNT(*) as total_users,
    SUM(CASE WHEN subscription_tier = 'paid' THEN 1 ELSE 0 END) as paid_users,
    SUM(monthly_payment) as monthly_revenue
FROM users;
```

### Via API Endpoint

Access user activity log:

```bash
# Get your activity (must be logged in)
curl https://pg-monitoring-tool.onrender.com/admin/activity-log \
  -H "Cookie: session=your-session-cookie"
```

Response:
```json
{
  "activities": [
    {
      "type": "LOGIN",
      "description": "User haider logged in successfully",
      "ip": "203.0.113.45",
      "timestamp": "2025-11-10 16:30:00"
    },
    {
      "type": "ADD_CONNECTION",
      "description": "Added connection: Prod DB (pg.example.com)",
      "ip": "203.0.113.45",
      "timestamp": "2025-11-10 16:31:15"
    }
  ]
}
```

---

## 📈 User Statistics Dashboard

### Real-time Stats Endpoint

**API:** `/api/user-stats`

```bash
curl https://pg-monitoring-tool.onrender.com/api/user-stats \
  -H "Cookie: session=your-session-cookie"
```

**Response:**
```json
{
  "subscription_tier": "free",
  "monthly_payment": 0.0,
  "max_connections": 2,
  "subscription_status": "active",
  "current_connections": 1,
  "connections_remaining": 1
}
```

---

## 💰 Monetization Implementation

### Current Setup

#### Free Tier:
- ✅ **2 database connections** maximum
- ✅ All monitoring features
- ✅ Community support

#### Paid Tier:
- ✅ **Unlimited database connections**
- ✅ All monitoring features
- ✅ Priority support
- ✅ **Minimum: $5/month**
- ✅ **Pay what you want** pricing model

### How It Works:

1. **User registers** → Free tier (2 connections)
2. **Tries to add 3rd connection** → Blocked with upgrade prompt
3. **Clicks "Upgrade"** → Redirected to `/pricing`
4. **Enters amount** (minimum $5) → Pay what you want
5. **Pays** → Unlimited connections unlocked

### Enforcement Logic:

```python
# In save_connection route:
if current_count >= current_user.max_connections:
    return jsonify({
        'success': False,
        'limit_reached': True,
        'message': '⚠️ Connection limit reached! Upgrade to add unlimited connections.'
    }), 403
```

---

## 🔐 Monitoring User Activity

### Render Dashboard Metrics

**Available Metrics:**
- Total requests/minute
- Response time
- Error rate
- Memory usage
- CPU usage

**Access:** Render Dashboard → Service → **Metrics** tab

### Custom Monitoring Queries

#### Total Users:
```sql
SELECT COUNT(*) FROM users;
```

#### Paid Users:
```sql
SELECT COUNT(*) FROM users WHERE subscription_tier = 'paid';
```

#### Monthly Revenue:
```sql
SELECT SUM(monthly_payment) as monthly_revenue FROM users WHERE subscription_tier = 'paid';
```

#### Most Active Users:
```sql
SELECT u.username, COUNT(a.id) as activity_count
FROM users u
LEFT JOIN activity_log a ON u.id = a.user_id
GROUP BY u.id
ORDER BY activity_count DESC
LIMIT 10;
```

#### Recent Upgrades:
```sql
SELECT username, monthly_payment, last_payment_date
FROM users
WHERE subscription_tier = 'paid'
ORDER BY last_payment_date DESC;
```

---

## 📧 Email Notifications (Future)

### Get Notified on New Registrations

Add to `register` route:

```python
# Send email notification
import smtplib
from email.message import EmailMessage

def notify_new_user(username, email):
    msg = EmailMessage()
    msg['Subject'] = f'New User Registered: {username}'
    msg['From'] = 'noreply@yourapp.com'
    msg['To'] = 'you@example.com'
    msg.set_content(f'New user: {username} ({email}) just registered!')
    
    # Send via SMTP (configure your email service)
    # smtp.send_message(msg)
```

---

## 🎯 Key Metrics to Track

### Daily:
- [ ] New user registrations
- [ ] Active users (logins)
- [ ] Failed login attempts (security)

### Weekly:
- [ ] Total users (free vs paid)
- [ ] Conversion rate (free → paid)
- [ ] Monthly recurring revenue (MRR)

### Monthly:
- [ ] User retention
- [ ] Average connections per user
- [ ] Customer lifetime value (CLV)

---

## 🚨 Important Log Patterns to Watch

### Security Alerts:
```
[SECURITY] Failed login attempt for username: admin from IP: 203.0.113.45
```
**Action:** If > 5 failed attempts from same IP → Block IP

### Upgrade Events:
```
[ACTIVITY] User 5 | UPGRADE | Upgraded to paid tier: $10/month
```
**Action:** Send thank you email, monitor for cancellations

### Connection Limits Hit:
```
[ACTIVITY] User 3 | LIMIT_REACHED | Tried to add 3rd connection (free tier)
```
**Action:** Good conversion opportunity → Send targeted email

---

## 📊 Sample Monitoring Dashboard

Create a simple admin dashboard to view:

1. **Total Users:** 150
2. **Paid Users:** 12 (8% conversion)
3. **Monthly Revenue:** $180
4. **Today's Registrations:** 5
5. **Active Now:** 23 users

**Implementation:**
```python
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    
    # Total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # Paid users
    cursor.execute("SELECT COUNT(*) FROM users WHERE subscription_tier = 'paid'")
    paid_users = cursor.fetchone()[0]
    
    # Monthly revenue
    cursor.execute("SELECT SUM(monthly_payment) FROM users WHERE subscription_tier = 'paid'")
    revenue = cursor.fetchone()[0] or 0
    
    # Today's registrations
    cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')")
    today_registrations = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_users': total_users,
        'paid_users': paid_users,
        'free_users': total_users - paid_users,
        'conversion_rate': round((paid_users / total_users * 100), 2) if total_users > 0 else 0,
        'monthly_revenue': revenue,
        'today_registrations': today_registrations
    })
```

---

## 🎉 Success Metrics

### Week 1:
- [ ] 10 free users registered
- [ ] 5 users added databases
- [ ] 1 upgrade ($10/month) ✅ First revenue!

### Month 1:
- [ ] 50 free users
- [ ] 5 paid users ($60 MRR)
- [ ] 10% conversion rate

### Month 3:
- [ ] 200 free users
- [ ] 20 paid users ($250 MRR)
- [ ] Profitable (revenue > hosting costs)

---

## 📞 Accessing Logs Remotely

### Via Render Dashboard:
1. Go to https://dashboard.render.com
2. Select service
3. Click "Logs" tab
4. See real-time logs

### Via Render API:
```bash
curl "https://api.render.com/v1/services/YOUR_SERVICE_ID/logs" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Download Database (for analysis):
```bash
# SSH into Render instance (if available)
render ssh pg-monitoring-tool

# Download web_users.db
scp user@render-instance:/path/to/web_users.db ./local_backup.db
```

---

## 🔔 Set Up Alerts

### Render Built-in Alerts:
- Go to Service → Settings → Notifications
- Add email for:
  - ✅ Deploy failures
  - ✅ Service crashes
  - ✅ High error rate

### Custom Alerts (via code):
```python
# Alert on high failed login attempts
failed_attempts = log_activity_count('FAILED_LOGIN', last_hour=True)
if failed_attempts > 10:
    send_alert('High failed login attempts detected!')
```

---

## ✅ Quick Checklist for Monitoring

Daily tasks:
- [ ] Check Render logs for errors
- [ ] Review new user registrations
- [ ] Check for upgrade events
- [ ] Monitor failed login attempts

Weekly tasks:
- [ ] Calculate conversion rate
- [ ] Review monthly revenue
- [ ] Check user retention
- [ ] Respond to support requests

Monthly tasks:
- [ ] Download database backup
- [ ] Analyze user behavior
- [ ] Plan feature improvements
- [ ] Review pricing strategy

---

**All logs are visible in Render dashboard in real-time!**

**Database tracks everything for analysis!**

**Monetization enforces 2-connection limit for free tier!**

**Minimum payment: $5/month with pay-what-you-want model!**
