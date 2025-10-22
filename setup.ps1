# 🚀 Deployment & Setup Script for PG-Monitor Enhanced

Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   PG-Monitor Enhanced - PostgreSQL Monitoring CLI       ║" -ForegroundColor Cyan
Write-Host "║   Quick Setup & Deployment                              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "🔍 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.8+ from python.org" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
$venvPath = ".\venv"
if (Test-Path $venvPath) {
    Write-Host "📦 Virtual environment already exists" -ForegroundColor Green
} else {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip | Out-Null
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Setup configuration
Write-Host ""
Write-Host "⚙️  Setting up configuration..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "ℹ️  .env file already exists" -ForegroundColor Blue
    $overwrite = Read-Host "Do you want to reconfigure? (y/N)"
    if ($overwrite -ne "y") {
        Write-Host "✅ Using existing configuration" -ForegroundColor Green
        $setupConfig = $false
    } else {
        $setupConfig = $true
    }
} else {
    $setupConfig = $true
}

if ($setupConfig) {
    Write-Host ""
    Write-Host "📝 PostgreSQL Connection Setup" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    $pgHost = Read-Host "PostgreSQL Host [localhost]"
    if ([string]::IsNullOrWhiteSpace($pgHost)) { $pgHost = "localhost" }
    
    $pgPort = Read-Host "PostgreSQL Port [5432]"
    if ([string]::IsNullOrWhiteSpace($pgPort)) { $pgPort = "5432" }
    
    $pgDatabase = Read-Host "Database Name [postgres]"
    if ([string]::IsNullOrWhiteSpace($pgDatabase)) { $pgDatabase = "postgres" }
    
    $pgUser = Read-Host "Database User [postgres]"
    if ([string]::IsNullOrWhiteSpace($pgUser)) { $pgUser = "postgres" }
    
    $pgPassword = Read-Host "Database Password" -AsSecureString
    $pgPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($pgPassword))
    
    # Create .env file
    $envContent = @"
PG_HOST=$pgHost
PG_PORT=$pgPort
PG_DATABASE=$pgDatabase
PG_USER=$pgUser
PG_PASSWORD=$pgPasswordPlain
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Configuration saved to .env" -ForegroundColor Green
}

# Test connection
Write-Host ""
Write-Host "🔌 Testing database connection..." -ForegroundColor Yellow
$testResult = python pg_monitor_enhanced.py --connections 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Connection successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host "🎉 Setup Complete! Ready to monitor PostgreSQL" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""
    Write-Host "📚 Quick Commands:" -ForegroundColor Cyan
    Write-Host "  python pg_monitor_enhanced.py --all              # Full report"
    Write-Host "  python pg_monitor_enhanced.py --locks            # Check locks"
    Write-Host "  python pg_monitor_enhanced.py --connections      # Pool status"
    Write-Host "  python pg_monitor_enhanced.py --indexes          # Index analysis"
    Write-Host "  python pg_monitor_enhanced.py --all --watch 30   # Live monitoring"
    Write-Host ""
    Write-Host "📖 See QUICKSTART.md for more examples" -ForegroundColor Blue
} else {
    Write-Host "❌ Connection failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Verify PostgreSQL is running" -ForegroundColor White
    Write-Host "2. Check credentials in .env file" -ForegroundColor White
    Write-Host "3. Ensure user has proper permissions" -ForegroundColor White
    Write-Host ""
    Write-Host "Error details:" -ForegroundColor Yellow
    Write-Host $testResult -ForegroundColor Red
}

Write-Host ""
