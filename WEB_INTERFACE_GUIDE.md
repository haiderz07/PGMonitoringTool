# PG-Monitor Web Interface Guide

## 🌐 Overview

The PG-Monitor web interface provides a **user-friendly dashboard** for DBAs to monitor PostgreSQL databases without using the command line. Features include:

- 🔒 **User Authentication** - Secure login/registration system
- 🧙‍♂️ **Setup Wizard** - Guided 3-step process to add database connections
- 📊 **Real-time Dashboard** - Auto-refreshing metrics with charts and graphs
- 🚀 **Instant Insights** - No extra work, just connect and see performance data

---

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL 12 or higher (target database to monitor)
- Web browser (Chrome, Firefox, Edge, Safari)

---

## 🚀 Installation

### 1. Install Dependencies

First, make sure you have all required Python packages:

```powershell
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist or is incomplete, install manually:

```powershell
pip install flask flask-login psycopg2-binary click
```

### 2. Initialize the Database

The web application uses SQLite to store user accounts and connection details. On first run, it will automatically create the database.

---

## 🏃‍♂️ Running the Web Interface

### Start the Server

```powershell
python web_app.py
```

You should see:

```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Access the Dashboard

Open your web browser and go to:

```
http://localhost:5000
```

---

## 👤 First-Time Setup

### Step 1: Create an Account

1. Click **"Register"** on the login page
2. Enter your details:
   - Username
   - Email
   - Password
3. Click **"Register"** button

### Step 2: Login

1. Enter your username and password
2. Click **"Login"**

### Step 3: Add Database Connection (Setup Wizard)

After logging in, you'll be redirected to the **Setup Wizard**.

#### **Wizard Step 1: Create PostgreSQL User**

The wizard shows you SQL commands to create a monitoring user on your PostgreSQL database:

```sql
-- Connect to your PostgreSQL as superuser (e.g., postgres)
CREATE USER pg_monitor_user WITH PASSWORD 'your_secure_password';

-- Grant basic permissions
GRANT CONNECT ON DATABASE your_database_name TO pg_monitor_user;
GRANT USAGE ON SCHEMA public TO pg_monitor_user;

-- Grant SELECT on all tables (for reading statistics)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO pg_monitor_user;

-- Grant pg_monitor role (for system views)
GRANT pg_monitor TO pg_monitor_user;
```

**💡 Click the "Copy SQL" button** to copy these commands to clipboard, then run them in your PostgreSQL database.

#### **Wizard Step 2: Enter Connection Details**

Fill in the form:

- **Connection Name**: e.g., "Production DB", "Dev Server"
- **Host**: e.g., `localhost` or `192.168.1.100`
- **Port**: Default is `5432`
- **Database**: The database name to monitor
- **Username**: `pg_monitor_user` (from Step 1)
- **Password**: The password you set in Step 1

#### **Wizard Step 3: Test & Save**

1. Click **"Test Connection"**
   - You'll see a ✅ success or ❌ error message
2. If successful, click **"Save Connection"**
3. You'll be redirected to the **Dashboard**

---

## 📊 Using the Dashboard

### Overview

The dashboard displays real-time metrics for your selected PostgreSQL database:

1. **Summary Cards** (Top Row):
   - Database Size
   - TPS (Transactions Per Second)
   - Active Connections
   - Cache Hit Ratio

2. **Charts Section**:
   - **Top Slow Queries (CPU Hogs)**: Shows queries consuming most CPU time (`pct_total_time`)
   - **Table Bloat**: Displays tables with excessive dead space (`bloat_pct`)

3. **Transaction Performance**:
   - TPS (Transactions/Second)
   - Rollback Rate
   - Deadlocks

4. **Table Statistics Health** (NEW):
   - Shows tables with missing or stale statistics
   - Recommendations to run `ANALYZE`
   - Color-coded severity: 🟢 Healthy, 🟡 Moderate, 🟠 Warning, 🔴 Critical

5. **System Metrics**:
   - Active Backends
   - CPU Usage
   - Heap/Index Hit Ratios

### Auto-Refresh

The dashboard **automatically refreshes every 30 seconds** when a connection is selected.

You can also manually refresh by clicking the **"Refresh"** button.

### Switching Connections

Use the dropdown at the top to switch between saved connections.

### Adding More Connections

Click **"Add Connection"** to launch the setup wizard again.

---

## 🔧 Configuration

### Change Server Port

Edit `web_app.py` and modify the last line:

```python
# Change from default port 5000 to 8080
app.run(debug=True, port=8080)
```

### Enable External Access

⚠️ **Warning**: Only do this in secure networks

```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

This allows access from other machines on your network.

### Session Timeout

Default session lifetime is 24 hours. To change it, edit `web_app.py`:

```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)  # Change to 12 hours
```

---

## 🛠️ Troubleshooting

### "Connection Refused" Error

**Problem**: Cannot connect to PostgreSQL

**Solutions**:
1. Check if PostgreSQL is running: `pg_ctl status`
2. Verify host/port are correct
3. Check `pg_hba.conf` allows connections from web server
4. Ensure firewall allows port 5432

### "Permission Denied" Error

**Problem**: `pg_monitor_user` doesn't have required permissions

**Solution**: Run the GRANT commands from Setup Wizard Step 1 again

### "No Data Available"

**Problem**: Dashboard shows no metrics

**Solutions**:
1. Ensure `pg_stat_statements` extension is enabled:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
   ```
2. Check PostgreSQL logs for errors
3. Refresh the page

### "Module Not Found: flask"

**Problem**: Missing Python dependencies

**Solution**:
```powershell
pip install flask flask-login psycopg2-binary
```

---

## 📁 File Structure

```
MonitoringPGApp/
├── web_app.py              # Flask application (main web server)
├── pg_monitor_enhanced.py  # Core monitoring logic
├── templates/
│   ├── base.html           # Base template
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── setup_wizard.html   # 3-step setup wizard
│   └── dashboard.html      # Main dashboard
├── static/                 # CSS/JS assets (optional)
├── web_users.db            # User database (auto-created)
└── pg_monitor_history.db   # Metrics history (auto-created)
```

---

## 🔐 Security Best Practices

1. **Use Strong Passwords**: Both for web accounts and PostgreSQL users
2. **HTTPS**: In production, use HTTPS (not HTTP) with SSL certificates
3. **Firewall**: Restrict access to port 5000 (or your custom port)
4. **PostgreSQL User**: Grant only necessary permissions (SELECT, pg_monitor role)
5. **Regular Updates**: Keep Python packages updated

---

## 🚀 Production Deployment

For production use, replace Flask's built-in server with a production-grade WSGI server:

### Using Gunicorn (Recommended)

```powershell
pip install gunicorn

# Run with 4 worker processes
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

### Using Waitress (Windows-friendly)

```powershell
pip install waitress

# Run on port 8080
waitress-serve --port=8080 web_app:app
```

---

## 📚 Related Documentation

- **CLI Tool**: See `README.md` for command-line usage
- **Table Statistics**: See `TABLE_STATISTICS_GUIDE.md` for statistics health monitoring
- **Architecture**: See `ARCHITECTURE.md` for system design

---

## ❓ FAQ

### Q: Can I monitor multiple databases?
**A**: Yes! Add multiple connections via the Setup Wizard. Switch between them using the dropdown.

### Q: Does the web interface replace the CLI tool?
**A**: No, both work independently. Use the CLI for quick checks or automation scripts, and the web interface for real-time monitoring.

### Q: How often does the dashboard update?
**A**: Auto-refresh every 30 seconds. You can also manually refresh anytime.

### Q: Is my data secure?
**A**: Yes. User passwords are hashed using Werkzeug's secure hash functions. Database credentials are stored locally in SQLite.

### Q: Can I export metrics?
**A**: Currently, metrics are displayed in real-time. For historical analysis, use the CLI tool's export options.

---

## 📧 Support

For issues or questions, check:
- `TROUBLESHOOTING.md` (if available)
- PostgreSQL logs: `pg_log/`
- Flask debug output in terminal

**Happy Monitoring!** 🎉
