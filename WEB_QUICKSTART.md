# 🌐 Web Interface - Quick Start

## ✅ What's New?

PG-Monitor ab ek **web-based interface** ke saath aa gaya hai! Ab aap command line ke bajaye browser mein directly apne PostgreSQL database ko monitor kar sakte hain.

## 🚀 Start Karne Ka Tarika

### 1. Dependencies Install Karein

```powershell
pip install -r requirements.txt
```

### 2. Web Server Chalayein

```powershell
python web_app.py
```

### 3. Browser Mein Kholein

```
http://localhost:5000
```

## 📝 Setup Steps

### Pehli Baar (First Time):

1. **Register** karo - Username, email, password dalein
2. **Login** karo
3. **Setup Wizard** follow karein:
   - **Step 1**: SQL commands copy karke apne PostgreSQL mein run karein (monitoring user banane ke liye)
   - **Step 2**: Connection details bharein (host, port, database, username, password)
   - **Step 3**: Test karke save karein

### Bas! Dashboard Ready! 🎉

## 🎯 Features

✅ **Real-time Metrics** - Auto-refresh har 30 seconds
✅ **CPU Hog Queries** - Konse queries zyada CPU use kar rahe hain
✅ **Table Bloat** - Kaunse tables mein extra space waste ho raha hai
✅ **Table Statistics Health** - Missing/stale statistics ki warning
✅ **Transaction Performance** - TPS, rollback rate, deadlocks
✅ **System Metrics** - Active connections, cache hit ratio

## 📊 Dashboard Dekhne Ka Tarika

1. **Connection Select Karein** - Top pe dropdown se
2. **Metrics Dekho** - Automatically load ho jayegi
3. **Refresh** - Manual refresh ke liye button click karein
4. **Add More Connections** - "Add Connection" button se naye database add karein

## 🔧 Common Commands

### Web Server Port Change Karni Ho:

`web_app.py` mein edit karein:
```python
app.run(debug=True, port=8080)  # 5000 se 8080 pe change kiya
```

### Network Se Access Karni Ho:

```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## ❓ Troubleshooting

### "Connection Refused"
- PostgreSQL chal raha hai? Check karein
- Host/Port sahi hai? Verify karein

### "Permission Denied"
- Setup Wizard Step 1 ke SQL commands dobara run karein

### "Module Not Found"
```powershell
pip install flask flask-login psycopg2-binary
```

## 📚 Detailed Guide

Zyada details ke liye **WEB_INTERFACE_GUIDE.md** dekhein.

---

**Bilkul simple!** Install karo, run karo, monitor karo! 🚀
