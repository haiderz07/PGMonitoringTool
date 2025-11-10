# 🚀 Deployment Guide - Render.com (FREE)

## Quick Deploy to Render.com

### Prerequisites
- GitHub account
- Render.com account (free)

---

## Step 1: Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - PostgreSQL Monitoring Tool"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/haiderz07/PGMonitoringTool.git

# Push to GitHub
git push -u origin main
```

---

## Step 2: Deploy to Render.com

### A. Create Render Account
1. Go to https://render.com
2. Sign up with GitHub account
3. Authorize Render to access your repositories

### B. Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your **PGMonitoringTool** repository
3. Configure settings:

```
Name: pg-monitoring-tool
Region: Oregon (US West) or closest to you
Branch: main
Root Directory: (leave empty)
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn web_app:app
```

### C. Environment Variables
Add these in Render dashboard:

```
SECRET_KEY = your-random-secret-key-here
FLASK_ENV = production
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### D. Instance Type
- **Free Tier** (select this for testing)
- Spins down after 15 min inactivity
- Wakes up in ~30 seconds

### E. Deploy!
- Click **"Create Web Service"**
- Wait 2-3 minutes for build
- Your app will be live at: `https://pg-monitoring-tool.onrender.com`

---

## Step 3: Initial Setup

1. Visit your Render URL
2. Click **"Register"**
3. Create admin account
4. Add PostgreSQL database connection
5. View dashboard!

---

## 🔧 Troubleshooting

### Build Fails?
```bash
# Check requirements.txt has all dependencies
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

### App Not Starting?
- Check Render logs: Dashboard → Logs tab
- Verify `Procfile` exists with: `web: gunicorn web_app:app`
- Ensure `PORT` environment variable is used

### Database Errors?
- SQLite database is created automatically on first run
- For production, upgrade to PostgreSQL (see below)

---

## 📊 Monitoring Deployment

### View Logs:
```
Render Dashboard → Your Service → Logs
```

### Health Check:
```
https://your-app.onrender.com/health
```

---

## 🎯 Next Steps

### 1. Custom Domain (Optional)
- Render Dashboard → Settings → Custom Domain
- Add: `monitor.yourdomain.com`
- Update DNS: CNAME to `pg-monitoring-tool.onrender.com`

### 2. Upgrade to PostgreSQL (Recommended)
```
Render Dashboard → New → PostgreSQL
Name: pg-monitor-users-db
Plan: Free (90 days)

# Get DATABASE_URL from PostgreSQL dashboard
# Add to web service environment variables
```

### 3. Enable Auto-Deploy
- Already enabled by default
- Every `git push` triggers new deployment

### 4. Add Monitoring
- Render provides basic metrics (free)
- CPU, Memory, Request count

---

## 💰 Upgrading to Paid (Remove Sleep)

### When to Upgrade?
- After getting 3-5 paying customers
- Revenue: $57-95/month
- Cost: $7/month (Starter plan)
- **Profit: $50-88/month** ✅

### How to Upgrade:
```
Render Dashboard → Your Service → Settings
Instance Type: Starter ($7/month)
Save Changes
```

**Benefits:**
- ✅ Always running (no sleep)
- ✅ 512MB RAM
- ✅ Better performance
- ✅ Professional image

---

## 🔐 Production Security Checklist

- [ ] Change `SECRET_KEY` from default
- [ ] Set `FLASK_ENV=production`
- [ ] Enable HTTPS (Render does this automatically)
- [ ] Encrypt database passwords (see WEB_DEPLOYMENT_MONETIZATION_GUIDE.md)
- [ ] Add rate limiting
- [ ] Set up backups (download `web_users.db` weekly)

---

## 📱 Testing Deployment

### 1. Access App
```
https://your-app.onrender.com
```

### 2. Register Account
```
Username: admin
Password: YourSecurePassword123!
Email: you@example.com
```

### 3. Add PostgreSQL Connection
```
Name: Test Database
Host: your-pg-server.com
Port: 5432
Database: your_db_name
Username: your_username
Password: your_password
```

### 4. View Dashboard
- Should load metrics
- Check slow queries
- Verify index analysis
- Test table statistics

---

## 🆘 Support

**Common Issues:**

1. **App crashes on startup:**
   - Check logs for missing dependencies
   - Verify Python version in `runtime.txt`

2. **Can't connect to PostgreSQL:**
   - Whitelist Render IPs in your firewall
   - Check connection credentials

3. **Slow performance:**
   - Free tier spins down (normal)
   - Upgrade to Starter for always-on

**Get Help:**
- Render Community Forum: https://community.render.com
- Check logs: Render Dashboard → Logs

---

## ✅ Deployment Complete!

Your PostgreSQL monitoring tool is now live! 🎉

**Share with:**
- DevOps teams
- Database administrators
- PostgreSQL communities

**Next:** Add payment integration (Stripe) to start monetizing!

See: `WEB_DEPLOYMENT_MONETIZATION_GUIDE.md` for details.
