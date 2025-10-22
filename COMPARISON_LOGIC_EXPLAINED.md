# 📊 Historical Comparison Logic - Complete Explanation

## 🎯 Overview
Yeh system **time-series data** store karta hai aur **statistical analysis** karta hai past performance ke saath compare karne ke liye.

---

## 🔄 Complete Flow (Step by Step)

### **Step 1: Data Collection** 
Har monitoring run pe metrics save hote hain SQLite database mein:

```python
# Transaction performance data save karna
def get_transaction_performance(self):
    # ... metrics calculate karte hain ...
    
    # Historical storage mein save
    if self.storage and db_stats:
        stats = db_stats[0]
        self.storage.save_metric('transaction', 'commit_count', stats.get('committed_txns', 0))
        self.storage.save_metric('transaction', 'rollback_count', stats.get('rolled_back_txns', 0))
        self.storage.save_metric('performance', 'tps', result['tps_data']['tps'])
```

**Database Structure:**
```sql
CREATE TABLE metrics_history (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,           -- Kab save hua (ISO format)
    metric_type TEXT,         -- 'performance', 'transaction', 'table_size'
    metric_name TEXT,         -- 'tps', 'commit_count', 'customers'
    metric_value REAL,        -- Actual value (1755.18)
    metadata TEXT             -- Extra info (JSON)
)
```

**Example Data:**
```
timestamp                | metric_type  | metric_name | metric_value
-------------------------|--------------|-------------|-------------
2025-10-21 17:00:00     | performance  | tps         | 1755.18
2025-10-21 17:02:00     | performance  | tps         | 1768.42
2025-10-21 17:04:00     | performance  | tps         | 1742.90
2025-10-21 18:00:00     | performance  | tps         | 1692.53
2025-10-21 18:06:00     | performance  | tps         | 1621.45  ← Current
```

---

### **Step 2: Historical Query**
Jab comparison chahiye, toh past X hours ka data fetch hota hai:

```python
def get_metric_comparison(self, metric_type: str, metric_name: str, hours: int = 24):
    """
    Past X hours ka data fetch karke statistics calculate karta hai
    
    Args:
        metric_type: 'performance', 'transaction', etc.
        metric_name: 'tps', 'commit_count', etc.
        hours: Kitne hours peeche jana hai (24 = last 24 hours)
    
    Returns:
        {
            'avg': Average value,
            'min': Minimum value,
            'max': Maximum value,
            'samples': Kitne data points the
        }
    """
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # Calculate time threshold
    since = datetime.now() - timedelta(hours=hours)
    
    # SQL Query - Statistical aggregation
    cursor.execute("""
        SELECT 
            AVG(metric_value) as avg_value,    -- Average nikalo
            MIN(metric_value) as min_value,     -- Minimum nikalo
            MAX(metric_value) as max_value,     -- Maximum nikalo
            COUNT(*) as samples                 -- Kitne samples the
        FROM metrics_history
        WHERE metric_type = ? 
          AND metric_name = ? 
          AND timestamp > ?                    -- Only last X hours
    """, (metric_type, metric_name, since.isoformat()))
    
    row = cursor.fetchone()
    conn.close()
    
    return {
        'avg': round(row[0], 2),
        'min': round(row[1], 2),
        'max': round(row[2], 2),
        'samples': row[3]
    }
```

**Example Query Result (24h TPS data):**
```python
{
    'avg': 1692.53,    # Average TPS in last 24 hours
    'min': 1621.45,    # Lowest TPS in last 24 hours
    'max': 1777.32,    # Highest TPS in last 24 hours
    'samples': 42      # 42 data points collected
}
```

---

### **Step 3: Comparison Calculation**
Current value ko historical average se compare karo:

```python
# Display section mein
if txn_data.get('tps_data'):
    current_tps = float(tps_info.get('tps', 0))  # Current: 1621.45
    
    # Get 24h historical data
    tps_trend_24h = monitor.storage.get_metric_comparison('performance', 'tps', 24)
    
    if tps_trend_24h and tps_trend_24h.get('avg'):
        avg_24h = float(tps_trend_24h['avg'])  # Historical avg: 1692.53
        
        # Percentage difference calculate karo
        diff_pct = ((current_tps - avg_24h) / avg_24h * 100)
        # = ((1621.45 - 1692.53) / 1692.53 * 100)
        # = (-71.08 / 1692.53) * 100
        # = -4.20%
        
        # Trend icon decide karo
        trend_icon = "📈" if diff_pct > 0 else "📉" if diff_pct < 0 else "➡️"
        # diff_pct is -4.20, so icon = "📉"
        
        # Display
        print(f"Avg TPS (24h): {avg_24h:.2f}")      # 1692.53
        print(f"{trend_icon} Change: {diff_pct:+.2f}%")  # 📉 -4.20%
```

---

## 📐 Mathematical Logic

### **Percentage Change Formula:**
```
Percentage Change = ((Current - Historical_Avg) / Historical_Avg) × 100

Examples:
• Current: 1621, Avg: 1692 → ((1621-1692)/1692)*100 = -4.20% 📉 (Decreased)
• Current: 1800, Avg: 1692 → ((1800-1692)/1692)*100 = +6.38% 📈 (Increased)
• Current: 1692, Avg: 1692 → ((1692-1692)/1692)*100 = 0.00% ➡️ (Same)
```

### **Trend Indicators:**
```python
if diff_pct > 0:
    trend = "📈"  # Improvement (TPS increased)
elif diff_pct < 0:
    trend = "📉"  # Decline (TPS decreased)
else:
    trend = "➡️"  # Stable (no change)
```

---

## 🕐 Time Windows Supported

### **24 Hour Comparison**
```python
tps_trend_24h = monitor.storage.get_metric_comparison('performance', 'tps', 24)
```
- **Purpose:** Short-term trend detection
- **Use Case:** Detect recent performance changes
- **Sample Rate:** Every 2 minutes = ~720 samples/day

### **7 Day Comparison**
```python
tps_trend_7d = monitor.storage.get_metric_comparison('performance', 'tps', 168)
```
- **Purpose:** Long-term performance baseline
- **Use Case:** Weekly patterns, capacity planning
- **Useful Metrics:**
  - `avg`: Normal operating TPS
  - `max`: Peak capacity
  - `min`: Lowest point (might indicate issues)

---

## 📊 Real Example Output

```
📊 Throughput Metrics:
   Database Uptime: 4794.18 sec (1.3 hours)
   Total Transactions: 7,835,695
   🚀 TPS (Transactions/Sec): 1621.45        ← CURRENT VALUE

   📊 24h Comparison:
      Avg TPS (24h): 1692.53                 ← HISTORICAL AVERAGE (24h)
      📉 Change: -4.20%                      ← CALCULATED DIFFERENCE

   📊 7d Comparison:
      Avg TPS (7d): 1698.20                  ← HISTORICAL AVERAGE (7 days)
      📉 Change: -4.51%                      ← CALCULATED DIFFERENCE
      Peak (7d): 1777.32                     ← HIGHEST in 7 days
      Low (7d): 1621.45                      ← LOWEST in 7 days
```

---

## 🎯 How to Read the Comparison

### **Scenario 1: Performance Degradation** 📉
```
Current TPS: 1621.45
Avg TPS (24h): 1692.53
Change: -4.20%
```
**Meaning:** System is **4.20% slower** than 24h average  
**Action:** Investigate if this is expected (lower traffic) or a problem

### **Scenario 2: Performance Improvement** 📈
```
Current TPS: 1850.00
Avg TPS (24h): 1692.53
Change: +9.30%
```
**Meaning:** System is **9.30% faster** than 24h average  
**Action:** Good! Maybe optimizations working or higher load handling

### **Scenario 3: Stable Performance** ➡️
```
Current TPS: 1692.53
Avg TPS (24h): 1692.53
Change: +0.00%
```
**Meaning:** Performance is **stable** and predictable  
**Action:** System is running normally

---

## 🔧 Code Integration Points

### **Where Data Gets Saved:**
```python
# In get_transaction_performance()
if self.storage and result.get('tps_data'):
    self.storage.save_metric('performance', 'tps', result['tps_data']['tps'])
    # ↑ Har run pe TPS save hota hai
```

### **Where Comparison Happens:**
```python
# In run_monitoring() display section
tps_trend_24h = monitor.storage.get_metric_comparison('performance', 'tps', 24)
tps_trend_7d = monitor.storage.get_metric_comparison('performance', 'tps', 168)
# ↑ Historical data fetch karke compare karte hain
```

---

## 💡 Key Benefits

1. **Trend Detection:** Jaldi se pata chal jata hai performance badh rahi hai ya gir rahi hai
2. **Baseline Establishment:** Normal operating range pata chal jati hai
3. **Anomaly Detection:** Unusual patterns detect kar sakte hain
4. **Capacity Planning:** Peak aur low values se planning kar sakte hain
5. **Historical Context:** Current metrics ko context mein dekh sakte hain

---

## 🎓 Summary

**3-Step Process:**
1. **Collect:** Har run pe metrics save karo SQLite mein
2. **Aggregate:** Past X hours ka AVG/MIN/MAX calculate karo
3. **Compare:** Current value ko historical average se compare karo

**Formula:**
```
% Change = ((Current - Historical_Avg) / Historical_Avg) × 100
```

**Result:**
- Positive % = Performance improved 📈
- Negative % = Performance declined 📉
- Zero % = Performance stable ➡️

---

## 🔍 Want More Details?

Check these files:
- `pg_monitor_enhanced.py` - Lines 230-260 (get_metric_comparison)
- `pg_monitor_enhanced.py` - Lines 1725-1747 (comparison display)
- `pg_monitor_history.db` - SQLite database (metrics_history table)

Run query to see your data:
```sql
SELECT * FROM metrics_history 
WHERE metric_type = 'performance' 
  AND metric_name = 'tps' 
ORDER BY timestamp DESC 
LIMIT 20;
```
