# Comprehensive QA Test Plan - PostgreSQL Monitoring Tool
## Test Engineer: Senior QA | Date: November 10, 2025

---

## 🎯 Executive Summary
This document provides a comprehensive test strategy for the PostgreSQL Monitoring Web Application, covering functional, performance, security, usability, and compatibility testing.

---

## 📋 Test Scope

### In Scope:
- ✅ User authentication & authorization
- ✅ Database connection management
- ✅ Dashboard metrics accuracy
- ✅ Index health analysis
- ✅ Server configuration recommendations
- ✅ Slow query analysis
- ✅ Table bloat detection
- ✅ Table statistics health
- ✅ UI/UX responsiveness
- ✅ Data sanitization & security
- ✅ Performance benchmarks

### Out of Scope:
- ❌ PostgreSQL server installation
- ❌ Network infrastructure testing
- ❌ Browser plugin compatibility
- ❌ Mobile app testing (web-only)

---

## 🧪 Test Categories

### 1. FUNCTIONAL TESTING

#### 1.1 Authentication Module
**Test Case ID: AUTH-001**
- **Scenario**: User Registration
- **Steps**:
  1. Navigate to `/register`
  2. Enter username: `qatest_user1`
  3. Enter email: `qa@testdomain.com`
  4. Enter password: `SecureP@ss123`
  5. Confirm password: `SecureP@ss123`
  6. Click Register
- **Expected**: User created, redirected to login
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: AUTH-002**
- **Scenario**: Login with Valid Credentials
- **Steps**:
  1. Navigate to `/login`
  2. Enter registered username
  3. Enter correct password
  4. Click Login
- **Expected**: Redirected to `/dashboard`, session created
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: AUTH-003**
- **Scenario**: Login with Invalid Credentials
- **Steps**:
  1. Navigate to `/login`
  2. Enter username: `invalid_user`
  3. Enter password: `wrongpassword`
  4. Click Login
- **Expected**: Error message displayed, stay on login page
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: AUTH-004**
- **Scenario**: Session Persistence
- **Steps**:
  1. Login successfully
  2. Close browser tab
  3. Reopen application URL
- **Expected**: User still logged in (session persists)
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: AUTH-005**
- **Scenario**: Logout Functionality
- **Steps**:
  1. Login successfully
  2. Click Logout button
- **Expected**: Session destroyed, redirected to login page
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: AUTH-006**
- **Scenario**: Password Security (Hashing)
- **Steps**:
  1. Register new user
  2. Check database: `SELECT password FROM users WHERE username = 'qatest_user1'`
- **Expected**: Password is hashed (not plaintext)
- **Priority**: CRITICAL
- **Status**: [ ] PASS [ ] FAIL

---

#### 1.2 Database Connection Management

**Test Case ID: CONN-001**
- **Scenario**: Add New PostgreSQL Connection
- **Steps**:
  1. Navigate to Setup Wizard
  2. Enter connection details:
     - Host: `localhost`
     - Port: `5432`
     - Database: `testdb`
     - Username: `testuser`
     - Password: `testpass`
  3. Click "Test Connection"
- **Expected**: Green success message, connection saved
- **Priority**: CRITICAL
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: CONN-002**
- **Scenario**: Test Invalid Connection
- **Steps**:
  1. Enter wrong port: `9999`
  2. Click "Test Connection"
- **Expected**: Red error message, connection NOT saved
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: CONN-003**
- **Scenario**: Delete Existing Connection
- **Steps**:
  1. Navigate to dashboard
  2. Select a connection
  3. Click delete icon
  4. Confirm deletion
- **Expected**: Connection removed, dropdown updated
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: CONN-004**
- **Scenario**: Switch Between Multiple Connections
- **Steps**:
  1. Add 3 different database connections
  2. Switch between them using dropdown
- **Expected**: Metrics update for each database
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: CONN-005**
- **Scenario**: Connection String Sanitization
- **Steps**:
  1. Add connection with password containing special characters: `P@ss$123!`
  2. Save and retrieve connection
- **Expected**: Password stored/retrieved correctly
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

---

#### 1.3 Dashboard Metrics Accuracy

**Test Case ID: DASH-001**
- **Scenario**: Health Score Calculation
- **Steps**:
  1. Connect to a healthy database (>95% cache hit, no bloat)
  2. Check health score
- **Expected**: Score ≥ 75/100 (Green status)
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: DASH-002**
- **Scenario**: Cache Hit Ratio Display
- **Steps**:
  1. Query backend: `SELECT blks_hit, blks_read FROM pg_stat_database WHERE datname = current_database()`
  2. Calculate: `(blks_hit / (blks_hit + blks_read)) * 100`
  3. Compare with dashboard value
- **Expected**: Values match within 0.1% margin
- **Priority**: CRITICAL
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: DASH-003**
- **Scenario**: Active Connections Count
- **Steps**:
  1. Run SQL: `SELECT count(*) FROM pg_stat_activity WHERE state = 'active'`
  2. Compare with dashboard "Active Connections"
- **Expected**: Values match exactly
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: DASH-004**
- **Scenario**: Transaction Per Second (TPS)
- **Steps**:
  1. Note `xact_commit` at T0
  2. Wait 60 seconds
  3. Note `xact_commit` at T1
  4. Calculate: `(T1 - T0) / 60`
  5. Compare with dashboard TPS
- **Expected**: Values match within 10% margin
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

---

#### 1.4 Slow Query Analysis

**Test Case ID: SLOW-001**
- **Scenario**: Slow Query Detection (pg_stat_statements Required)
- **Pre-requisite**: `CREATE EXTENSION pg_stat_statements;`
- **Steps**:
  1. Run slow query: `SELECT pg_sleep(3);`
  2. Refresh dashboard
- **Expected**: Query appears in "Top Slow Queries" section
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: SLOW-002**
- **Scenario**: Query Sanitization (Security)
- **Steps**:
  1. Run query with sensitive data: `SELECT * FROM users WHERE email = 'test@example.com'`
  2. Check dashboard display
- **Expected**: Email is masked or query is sanitized
- **Priority**: CRITICAL
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: SLOW-003**
- **Scenario**: Expand/Collapse All Queries
- **Steps**:
  1. Load dashboard with 5+ slow queries
  2. Click "Collapse All" button
  3. Click "Expand All" button
- **Expected**: All queries collapse/expand smoothly
- **Priority**: LOW
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: SLOW-004**
- **Scenario**: Copy Query to Clipboard
- **Steps**:
  1. Click "Copy" button on a slow query
  2. Paste into text editor
- **Expected**: Full query text copied successfully
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: SLOW-005**
- **Scenario**: Severity Badge Accuracy
- **Steps**:
  1. Create query with avg_time > 5000ms
  2. Refresh dashboard
- **Expected**: Red "Critical" badge displayed
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: SLOW-006**
- **Scenario**: No pg_stat_statements Extension
- **Steps**:
  1. Connect to DB without `pg_stat_statements`
  2. Check slow queries section
- **Expected**: Educational message displayed with setup instructions
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

---

#### 1.5 Index Health Analysis

**Test Case ID: INDEX-001**
- **Scenario**: Unused Index Detection
- **Steps**:
  1. Create index: `CREATE INDEX test_unused_idx ON test_table(column1);`
  2. Don't use the index (no queries)
  3. Refresh dashboard
- **Expected**: Index appears in "Unused Indexes" section with 0 scans
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: INDEX-002**
- **Scenario**: Missing Index Opportunities
- **Steps**:
  1. Create table with 100k rows
  2. Run 1000+ sequential scans without index
  3. Refresh dashboard
- **Expected**: Table appears in "Missing Index Opportunities"
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: INDEX-003**
- **Scenario**: Copy DROP INDEX SQL
- **Steps**:
  1. Click "Drop SQL" button on unused index
  2. Paste into text editor
- **Expected**: Correct `DROP INDEX schema.index_name;` command with warning comments
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: INDEX-004**
- **Scenario**: Index Size Display
- **Steps**:
  1. Check unused index size on dashboard
  2. Verify: `SELECT pg_size_pretty(pg_relation_size('index_name'))`
- **Expected**: Sizes match
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

---

#### 1.6 Table Statistics Health

**Test Case ID: STATS-001**
- **Scenario**: Show ALL Tables (Not Just Critical)
- **Steps**:
  1. Check "All Tables Statistics" section
  2. Count tables displayed
  3. Compare with: `SELECT count(*) FROM pg_stat_user_tables`
- **Expected**: All user tables displayed (healthy + critical)
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: STATS-002**
- **Scenario**: Staleness Percentage Accuracy
- **Steps**:
  1. Get table with stale stats
  2. Calculate: `(n_dead_tup::float / NULLIF(n_live_tup + n_dead_tup, 0)) * 100`
  3. Compare with dashboard value
- **Expected**: Values match within 0.1%
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: STATS-003**
- **Scenario**: Color Coding by Health Status
- **Steps**:
  1. Check table with staleness < 5%
  2. Check table with staleness 10-20%
  3. Check table with staleness > 20%
- **Expected**: 
  - <5%: Green row
  - 10-20%: Orange row
  - >20%: Red row
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: STATS-004**
- **Scenario**: Copy ANALYZE Command
- **Steps**:
  1. Click "Analyze" button on critical table
  2. Paste command
- **Expected**: `ANALYZE schema.tablename;` copied
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: STATS-005**
- **Scenario**: Bulk ANALYZE Command
- **Steps**:
  1. Check bulk ANALYZE section (if 2+ critical tables)
  2. Click "Copy All SQL"
- **Expected**: Multiple `ANALYZE` commands copied (one per critical table)
- **Priority**: LOW
- **Status**: [ ] PASS [ ] FAIL

---

#### 1.7 Table Bloat Detection

**Test Case ID: BLOAT-001**
- **Scenario**: Bloat Percentage Accuracy
- **Steps**:
  1. Create heavily updated table (generate bloat)
  2. Check bloat percentage on dashboard
  3. Verify with manual calculation
- **Expected**: Bloat % within acceptable range (±5%)
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: BLOAT-002**
- **Scenario**: No Bloat Scenario
- **Steps**:
  1. Connect to fresh database
  2. Check table bloat section
- **Expected**: Green success message "No significant table bloat!"
- **Priority**: LOW
- **Status**: [ ] PASS [ ] FAIL

---

#### 1.8 Server Configuration Recommendations

**Test Case ID: CONFIG-001**
- **Scenario**: Parameter Detection
- **Steps**:
  1. Check "Current PostgreSQL Parameters" section
  2. Verify parameters displayed:
     - shared_buffers
     - effective_cache_size
     - work_mem
     - maintenance_work_mem
- **Expected**: All critical parameters shown with current values
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: CONFIG-002**
- **Scenario**: Current Value Accuracy
- **Steps**:
  1. Check dashboard value for `shared_buffers`
  2. Run SQL: `SHOW shared_buffers;`
- **Expected**: Values match exactly
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: CONFIG-003**
- **Scenario**: OLTP vs OLAP Guidance
- **Steps**:
  1. Expand any parameter card
  2. Check for OLTP and OLAP sections
- **Expected**: Both guidance sections displayed with different recommendations
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: CONFIG-004**
- **Scenario**: Documentation Links
- **Steps**:
  1. Click "Official PostgreSQL Documentation" link
- **Expected**: Opens official PostgreSQL docs in new tab
- **Priority**: LOW
- **Status**: [ ] PASS [ ] FAIL

---

### 2. SECURITY TESTING

**Test Case ID: SEC-001**
- **Scenario**: SQL Injection Prevention (Connection Form)
- **Steps**:
  1. Enter malicious input: `admin' OR '1'='1`
  2. Try to save connection
- **Expected**: Input sanitized, no SQL injection
- **Priority**: CRITICAL
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: SEC-002**
- **Scenario**: XSS Prevention (Query Display)
- **Steps**:
  1. Run query: `SELECT '<script>alert("XSS")</script>'`
  2. Check dashboard display
- **Expected**: Script tags escaped, not executed
- **Priority**: CRITICAL
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: SEC-003**
- **Scenario**: Password Storage Encryption
- **Steps**:
  1. Add new connection with password
  2. Check SQLite database: `SELECT password FROM connections`
- **Expected**: Password is hashed/encrypted
- **Priority**: CRITICAL
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: SEC-004**
- **Scenario**: Session Hijacking Prevention
- **Steps**:
  1. Login, capture session cookie
  2. Logout
  3. Try to reuse old session cookie
- **Expected**: Session invalid, redirected to login
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: SEC-005**
- **Scenario**: Sensitive Data Masking
- **Steps**:
  1. Run query with email/phone: `SELECT email, phone FROM users`
  2. Check query display on dashboard
- **Expected**: Email/phone masked (e.g., ***@domain.com)
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

---

### 3. PERFORMANCE TESTING

**Test Case ID: PERF-001**
- **Scenario**: Dashboard Load Time (Initial)
- **Steps**:
  1. Clear browser cache
  2. Navigate to `/dashboard`
  3. Measure time to "All metrics rendered successfully!"
- **Expected**: < 5 seconds for moderate database (100 tables, 1000 queries)
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL
- **Result**: ______ seconds

**Test Case ID: PERF-002**
- **Scenario**: Metrics Refresh Performance
- **Steps**:
  1. Load dashboard
  2. Switch to different connection
  3. Measure refresh time
- **Expected**: < 3 seconds
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL
- **Result**: ______ seconds

**Test Case ID: PERF-003**
- **Scenario**: Large Dataset Handling (Slow Queries)
- **Steps**:
  1. Database with 500+ slow queries
  2. Load dashboard
- **Expected**: Top 10 displayed, no UI freeze, load time < 10 seconds
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: PERF-004**
- **Scenario**: Concurrent User Load
- **Steps**:
  1. Simulate 10 users accessing dashboard simultaneously
- **Expected**: All users get response within 10 seconds
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: PERF-005**
- **Scenario**: Memory Leak Check
- **Steps**:
  1. Open dashboard
  2. Switch connections 20 times
  3. Check browser memory usage
- **Expected**: No significant memory increase (< 500MB total)
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

---

### 4. USABILITY TESTING

**Test Case ID: UI-001**
- **Scenario**: Responsive Design (Mobile)
- **Steps**:
  1. Open dashboard on mobile device (375px width)
  2. Check layout
- **Expected**: All sections stack vertically, no horizontal scroll
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: UI-002**
- **Scenario**: Responsive Design (Tablet)
- **Steps**:
  1. Open dashboard on tablet (768px width)
  2. Check grid layouts
- **Expected**: 2-column grids display properly
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: UI-003**
- **Scenario**: Color Accessibility (Contrast Ratio)
- **Steps**:
  1. Use browser accessibility tools
  2. Check color contrast for text
- **Expected**: WCAG AA compliant (4.5:1 for normal text)
- **Priority**: LOW
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: UI-004**
- **Scenario**: Tooltip/Hover States
- **Steps**:
  1. Hover over metric cards
  2. Hover over buttons
- **Expected**: Visual feedback (color change, cursor change)
- **Priority**: LOW
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: UI-005**
- **Scenario**: Loading States
- **Steps**:
  1. Select connection
  2. Observe loading process
- **Expected**: Loading spinner/progress bar displayed, no blank screens
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

---

### 5. COMPATIBILITY TESTING

**Test Case ID: COMPAT-001**
- **Scenario**: Browser - Chrome (Latest)
- **Steps**: Test all features on Chrome
- **Expected**: Full functionality
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: COMPAT-002**
- **Scenario**: Browser - Firefox (Latest)
- **Steps**: Test all features on Firefox
- **Expected**: Full functionality
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: COMPAT-003**
- **Scenario**: Browser - Edge (Latest)
- **Steps**: Test all features on Edge
- **Expected**: Full functionality
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: COMPAT-004**
- **Scenario**: PostgreSQL Version 12
- **Steps**: Connect to PG 12 database
- **Expected**: All metrics work (some features may be limited)
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: COMPAT-005**
- **Scenario**: PostgreSQL Version 15+
- **Steps**: Connect to PG 15 database
- **Expected**: Full functionality
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

---

### 6. ERROR HANDLING TESTING

**Test Case ID: ERROR-001**
- **Scenario**: Database Connection Lost During Metrics Fetch
- **Steps**:
  1. Start loading metrics
  2. Kill database connection mid-fetch
- **Expected**: Error message displayed, no crash
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: ERROR-002**
- **Scenario**: Missing pg_stat_statements Extension
- **Steps**:
  1. Connect to DB without extension
  2. Check slow queries section
- **Expected**: Helpful setup instructions displayed
- **Priority**: HIGH
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: ERROR-003**
- **Scenario**: Insufficient Permissions
- **Steps**:
  1. Connect with user without SELECT on `pg_stat_database`
  2. Try to load metrics
- **Expected**: Clear permission error message
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

**Test Case ID: ERROR-004**
- **Scenario**: Network Timeout
- **Steps**:
  1. Set very slow network
  2. Try to load dashboard
- **Expected**: Timeout error after 30 seconds, retry option
- **Priority**: MEDIUM
- **Status**: [ ] PASS [ ] FAIL

---

## 🐛 Defect Severity Levels

| Level | Description | Example |
|-------|-------------|---------|
| **CRITICAL** | Blocker - Core functionality broken | Cannot login, database connection fails |
| **HIGH** | Major impact - Feature not working | Wrong metrics displayed, security vulnerability |
| **MEDIUM** | Moderate impact - Workaround exists | UI glitch, slow performance |
| **LOW** | Minor issue - Cosmetic | Typo, slight color mismatch |

---

## 📊 Test Metrics

### Pass/Fail Criteria
- **CRITICAL**: 100% pass required
- **HIGH**: ≥ 95% pass required
- **MEDIUM**: ≥ 90% pass required
- **LOW**: ≥ 80% pass required

### Tracking
```
Total Test Cases: 60+
Executed: ___
Passed: ___
Failed: ___
Blocked: ___
Pass Rate: ____%
```

---

## 🔍 Exploratory Testing Checklist

### Session 1: Dashboard Navigation (30 min)
- [ ] Click all buttons, check for broken links
- [ ] Try to break the UI with rapid clicks
- [ ] Check console for JavaScript errors
- [ ] Test keyboard navigation (Tab, Enter, Esc)
- [ ] Test with JavaScript disabled

### Session 2: Edge Cases (30 min)
- [ ] Empty database (no tables, no queries)
- [ ] Database with 10,000+ tables
- [ ] Query with 10MB result set
- [ ] Connection name with special characters
- [ ] Zero active connections

### Session 3: Data Validation (30 min)
- [ ] Cross-verify metrics with direct SQL queries
- [ ] Check for off-by-one errors in counts
- [ ] Validate percentage calculations
- [ ] Check rounding consistency

---

## 🚨 Known Issues to Verify

### From Previous QA Report:
1. **MAJOR-1**: Table Bloat Detection - Check if fixed
2. **MINOR-2**: Unused Index Clutter - 9 unused indexes consuming ~10MB
3. **Slow Query Display**: Shows only 1 aborted query instead of actual slow queries

---

## 📝 Test Execution Notes

### Environment Setup:
```
OS: Windows 11
Python: 3.x
PostgreSQL: 14.x
Browser: Chrome 120+
Database Size: [Small/Medium/Large]
Test Data: [Generated/Production-like]
```

### Pre-requisites:
1. Install required extensions:
   ```sql
   CREATE EXTENSION pg_stat_statements;
   CREATE EXTENSION pg_trgm;
   ```
2. Grant permissions:
   ```sql
   GRANT pg_monitor TO monitoring_user;
   ```

---

## ✅ Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| QA Lead | __________ | __________ | ______ |
| Developer | __________ | __________ | ______ |
| Product Owner | __________ | __________ | ______ |

---

## 📚 References
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Flask Security Best Practices: https://flask.palletsprojects.com/en/2.3.x/security/
- OWASP Testing Guide: https://owasp.org/www-project-web-security-testing-guide/

---

**END OF TEST PLAN**
