# 🔐 Authentication & Pricing Model

## 📊 Data Storage Architecture

### 1. **User Authentication Data** (Local SQLite Database)

All login and registration data is saved in **`web_users.db`** - a local SQLite database file.

#### **Database Schema:**

```sql
-- Users Table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,      -- Hashed with Werkzeug (SHA256)
    email TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Connections Table (per user)
CREATE TABLE connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,               -- e.g., "Production DB", "Dev Server"
    host TEXT NOT NULL,                -- PostgreSQL host
    port INTEGER NOT NULL,             -- Default: 5432
    database TEXT NOT NULL,            -- Database name
    username TEXT NOT NULL,            -- PostgreSQL username
    password TEXT NOT NULL,            -- Encrypted/stored securely
    is_default BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### **Security Features:**

✅ **Password Hashing**: Uses `werkzeug.security.generate_password_hash()`
   - Algorithm: PBKDF2 with SHA256
   - Salt: Automatically generated
   - Iterations: 260,000 (industry standard)

✅ **Session Management**: 
   - Flask-Login for secure session handling
   - Session cookies with 24-hour lifetime
   - Automatic logout after timeout

✅ **SQL Injection Protection**: 
   - Parameterized queries (no string concatenation)
   - SQLite escaping built-in

❌ **Current Limitations** (Can be improved for production):
   - Database credentials stored in plaintext in SQLite
   - No encryption at rest for connection passwords
   - No 2FA/MFA support

---

## 💰 Monetization Models

### **Option 1: Free + Open Source** (Current State)
**Price**: Free  
**Model**: MIT License / Open Source  
**Revenue**: $0 (Community support, GitHub stars)

**Use Case**:
- Individual DBAs
- Small teams
- Learning/Education
- Community contribution

---

### **Option 2: Freemium Model** (Recommended)

#### **Free Tier**
- ✅ Up to 3 database connections
- ✅ Basic monitoring (CPU, bloat, stats)
- ✅ Manual refresh (no auto-refresh)
- ✅ 7 days data retention
- ✅ Community support

#### **Pro Tier** - $19/month per user
- ✅ **Unlimited database connections**
- ✅ **Auto-refresh** (real-time monitoring)
- ✅ **30 days data retention + historical charts**
- ✅ **Slack/Email alerts** (when issues detected)
- ✅ **Export reports** (PDF, CSV)
- ✅ **Priority email support**

#### **Enterprise Tier** - $99/month per team (5+ users)
- ✅ **Everything in Pro**
- ✅ **90 days data retention**
- ✅ **Multi-tenant isolation**
- ✅ **SSO/SAML integration**
- ✅ **Custom branding**
- ✅ **API access** (for automation)
- ✅ **Dedicated support + SLA**

---

### **Option 3: One-Time License** (Self-Hosted)

#### **Standard License** - $299 (one-time)
- ✅ Self-hosted deployment
- ✅ Unlimited users in your organization
- ✅ 1 year of updates
- ✅ Email support

#### **Enterprise License** - $999 (one-time)
- ✅ Everything in Standard
- ✅ Lifetime updates
- ✅ White-label branding
- ✅ Custom feature development (20 hours)
- ✅ Priority support

---

### **Option 4: Usage-Based Pricing** (SaaS Model)

**Pricing Structure:**
- **$0.10 per database per day**
- Billed monthly based on active connections
- Example: Monitor 10 databases → $30/month

**Advantages**:
- Pay only for what you use
- Scales with business growth
- No upfront commitment

---

### **Option 5: Managed Service** (Fully Hosted)

**PG-Monitor Cloud** - Starting at $49/month
- ✅ Fully hosted (no installation needed)
- ✅ Monitor up to 10 databases
- ✅ 99.9% uptime SLA
- ✅ Automatic updates
- ✅ Built-in backups
- ✅ 24/7 monitoring

**Add-ons:**
- +$10/month for each additional 5 databases
- +$20/month for advanced alerting (PagerDuty, Opsgenie)
- +$30/month for compliance reports (SOC2, HIPAA)

---

## 🔒 Data Security & Privacy

### **Current Implementation:**
1. **User Passwords**: Hashed with PBKDF2-SHA256
2. **Database Credentials**: Stored in local SQLite (plaintext)
3. **Session Tokens**: HTTP-only cookies
4. **Storage Location**: Local filesystem (`web_users.db`)

### **Production-Ready Improvements:**

#### **For Paid Tiers:**

✅ **Encrypt Database Credentials**:
```python
from cryptography.fernet import Fernet

# Generate encryption key (store in environment variable)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt before saving
encrypted_password = cipher.encrypt(password.encode())

# Decrypt when connecting
decrypted_password = cipher.decrypt(encrypted_password).decode()
```

✅ **Use PostgreSQL for User Data** (instead of SQLite):
- Better concurrency
- Row-level security
- Audit logging
- Replication support

✅ **Add 2FA/MFA**:
```python
pip install pyotp qrcode
# Generate TOTP tokens for two-factor authentication
```

✅ **SSL/TLS Encryption**:
```python
# Force HTTPS
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

---

## 💳 Payment Integration (For Paid Tiers)

### **Recommended Payment Processors:**

#### **1. Stripe** (Most Popular)
```python
pip install stripe

import stripe
stripe.api_key = 'your_secret_key'

# Create subscription
subscription = stripe.Subscription.create(
    customer=customer_id,
    items=[{'price': 'price_pro_tier'}],
)
```

**Integration Steps:**
1. Add `stripe` dependency
2. Create pricing plans in Stripe dashboard
3. Add `/api/create-subscription` endpoint
4. Store `stripe_customer_id` in `users` table
5. Add webhook handler for payment events

#### **2. Paddle** (Good for SaaS)
- Handles VAT/tax automatically
- Merchant of record
- Global payments

#### **3. LemonSqueezy** (Developer-friendly)
- Simple API
- No merchant account needed
- Handles EU VAT

---

## 📈 Implementation Roadmap

### **Phase 1: Free Version** (Current)
- ✅ Basic authentication
- ✅ Local SQLite storage
- ✅ Core monitoring features

### **Phase 2: Freemium MVP** (2-4 weeks)
- Add connection limit check (3 for free tier)
- Implement "Upgrade to Pro" prompts
- Add Stripe integration
- Create pricing page

### **Phase 3: Pro Features** (1-2 months)
- Auto-refresh toggle
- Historical data storage (PostgreSQL)
- Email alerts (SendGrid/Mailgun)
- Export functionality

### **Phase 4: Enterprise** (3-6 months)
- SSO/SAML integration
- Multi-tenancy
- API endpoints
- Custom branding

---

## 🔐 Database Location & Access

### **Current Setup:**

**File Location:**
```
MonitoringPGApp/
├── web_users.db          ← Authentication data (created on first run)
├── pg_monitor_history.db ← Metrics history (optional, for caching)
└── web_app.py
```

**Access Control:**
- **File Permissions**: Only the user running `web_app.py` can access
- **Network Access**: Only accessible from `localhost:5000` by default
- **No External Database**: Everything is local (no cloud dependency)

### **For Production:**

**Move to PostgreSQL:**
```python
# Instead of SQLite, use PostgreSQL for user data
DATABASE_URL = "postgresql://user:pass@host:5432/pgmonitor_users"

# Benefits:
# - Better security with role-based access
# - Encrypted connections (SSL/TLS)
# - Audit logging
# - Replication/backups
```

---

## 🎯 Recommended Approach

### **Start with Freemium Model:**

1. **Free Tier** (Get users hooked)
   - Limit to 3 connections
   - No historical data
   - Community support

2. **Pro Tier** ($19/month)
   - Unlimited connections
   - Auto-refresh
   - 30-day history
   - Email alerts

3. **Payment Flow:**
   - User clicks "Upgrade to Pro"
   - Redirects to Stripe checkout
   - After payment, set `subscription_tier = 'pro'` in database
   - Unlock Pro features

### **Estimated Monthly Revenue** (Example):
- 1,000 free users
- 100 Pro users × $19 = **$1,900/month**
- 10 Enterprise users × $99 = **$990/month**
- **Total: ~$3,000/month**

---

## 🔧 Quick Implementation: Add Subscription Tiers

### **Step 1: Update Database Schema**

```sql
ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT 'free';
ALTER TABLE users ADD COLUMN stripe_customer_id TEXT;
ALTER TABLE users ADD COLUMN subscription_expires_at DATETIME;
```

### **Step 2: Add Connection Limit Check**

```python
@app.route('/setup-wizard')
@login_required
def setup_wizard():
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    
    # Get current tier
    cursor.execute("SELECT subscription_tier FROM users WHERE id = ?", (current_user.id,))
    tier = cursor.fetchone()[0] or 'free'
    
    # Count connections
    cursor.execute("SELECT COUNT(*) FROM connections WHERE user_id = ?", (current_user.id,))
    connection_count = cursor.fetchone()[0]
    conn.close()
    
    # Free tier limit: 3 connections
    if tier == 'free' and connection_count >= 3:
        flash('❌ Free tier limited to 3 connections. Upgrade to Pro for unlimited!', 'error')
        return redirect(url_for('pricing'))
    
    return render_template('setup_wizard.html')
```

### **Step 3: Create Pricing Page**

```html
<!-- templates/pricing.html -->
<div class="pricing-card">
  <h3>Pro Tier</h3>
  <p>$19/month</p>
  <ul>
    <li>✅ Unlimited connections</li>
    <li>✅ Auto-refresh</li>
    <li>✅ 30-day history</li>
  </ul>
  <button onclick="location.href='/checkout/pro'">Upgrade Now</button>
</div>
```

---

## 📧 Contact & Support

For production deployment and monetization consulting:
- Email: your-email@example.com
- Discord: Your community server
- GitHub: Sponsorship tiers

**License Options:**
- MIT (Free, open-source)
- Commercial License (Paid, proprietary features)
- Dual License (Open-source core + paid plugins)

---

## ✅ Summary

**Data Storage:**
- ✅ Local SQLite file (`web_users.db`)
- ✅ Passwords hashed with PBKDF2-SHA256
- ✅ No external database required
- ⚠️ Database credentials NOT encrypted (can be improved)

**Monetization:**
- 🎯 **Recommended**: Freemium model ($0 → $19/month → $99/month)
- 💰 Estimated revenue: $1,000-$5,000/month with 100-200 paid users
- 🚀 Easy to implement with Stripe (1-2 weeks)

**Next Steps:**
1. Decide on pricing model
2. Implement Stripe integration
3. Add subscription tier checks
4. Launch with free tier first
5. Gather feedback, iterate

🎉 **Your tool is ready to monetize!**
