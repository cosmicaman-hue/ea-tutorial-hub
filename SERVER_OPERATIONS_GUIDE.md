# 24x7 Server Operations & Maintenance Guide

This guide covers daily operations, monitoring, and maintenance for your EA Tutorial Hub running on a server PC.

---

## 🚀 Quick Start (Server PC)

### Start the Server

**Option 1: Easiest Way**
1. Navigate to your project folder
2. Double-click `run_server.bat`
3. A window will open showing the application is running
4. Keep this window open

**Option 2: PowerShell**
```powershell
cd "C:\Users\[YourUsername]\Desktop\Project EA"
.\.venv\Scripts\Activate.ps1
python run.py
```

**Option 3: Auto-start on Boot**
See "Scheduled Start" section below

---

## 📊 Daily Monitoring

### Check Server Status from Any PC

**Quick Check:**
1. Open web browser on any networked PC
2. Go to: `http://[SERVER_IP]:5000`
3. Should see login page

**Get Server IP on Server PC:**
```powershell
ipconfig
```
Look for "IPv4 Address" under your WiFi adapter (e.g., `192.168.0.163`)

### Application Health Checks

| Check | What to Look For | Action if Failed |
|-------|-----------------|-----------------|
| **Login Page** | Loads without errors | Check terminal for error messages |
| **Admin Dashboard** | Displays without delays | May be normal during peak usage |
| **Database** | Page loads after login | Check `instance/ea_tutorial.db` exists |
| **File Upload** | Notes upload successfully | Check `app/static/uploads/` permissions |

---

## ⚙️ Server Terminal Messages

### Normal Messages ✅

```
* Running on http://0.0.0.0:5000
* Debugger is active!
* Debugger PIN: 123-456-789
WARNING: This is a development server. Do not use in production.
```

**What it means:** Server is running correctly

### Warning Messages ⚠️

```
WARNING: Debugger is active!
WARNING: This is a development server.
```

**What it means:** Normal in development mode, not a problem

### Error Messages ❌

| Error | Cause | Solution |
|-------|-------|----------|
| `Address already in use` | Port 5000 occupied | Change port in `run.py` or kill process |
| `No such table: user` | Database corrupted | Delete `instance/ea_tutorial.db`, restart |
| `ModuleNotFoundError` | Missing dependency | Run `pip install -r requirements.txt` |
| `Permission denied` | File access issue | Run as Administrator |

---

## 🔄 Server Maintenance

### Daily (Recommended)

- [ ] Check login page loads: `http://[SERVER_IP]:5000`
- [ ] Verify no error messages in terminal
- [ ] Check at least one user can login

### Weekly

- [ ] Monitor database size (should grow slowly)
  ```powershell
  ls -la "instance\ea_tutorial.db"
  ```
- [ ] Review activity logs in admin dashboard
- [ ] Check upload folder isn't too large
  ```powershell
  du -sh "app\static\uploads"  # Linux/Mac
  # Or check properties in Windows Explorer
  ```

### Monthly

- [ ] Restart the server (graceful shutdown)
  ```powershell
  # Press Ctrl+C in terminal
  # Wait 5 seconds
  # Restart with python run.py
  ```
- [ ] Backup database:
  ```powershell
  Copy-Item "instance\ea_tutorial.db" "instance\ea_tutorial.db.backup"
  ```
- [ ] Check for updates to dependencies (optional)

---

## 🛑 Stopping the Server

### Graceful Shutdown

1. Go to terminal/PowerShell running the application
2. Press `Ctrl+C`
3. Wait for message: `Keyboard interrupt received`
4. Application stops safely

### Restart

```powershell
python run.py
```

---

## 🔧 Common Issues & Fixes

### Issue: Server crashes randomly

**Symptom:** Terminal closes or shows error

**Fixes:**
1. Run with auto-restart wrapper:
   ```powershell
   while ($true) {
       python run.py
       Start-Sleep -Seconds 5
   }
   ```

2. Use Task Scheduler with restart on failure

3. Keep terminal always visible (resize window to watch for crashes)

---

### Issue: Slow performance

**Symptom:** Pages load slowly, timeouts

**Causes & Fixes:**

1. **Too many users at once:**
   - Temporary: Restart server (`Ctrl+C` then `python run.py`)
   - Permanent: Use Gunicorn with more workers

2. **Database file too large:**
   - Check size: `ls -la instance/ea_tutorial.db`
   - Clean old data if needed
   - Consider archiving old records

3. **Server PC overloaded:**
   - Close other applications
   - Increase available RAM
   - Enable virtual memory

4. **Network congestion:**
   - Reduce number of simultaneous users
   - Check WiFi signal strength

---

### Issue: Database locked error

**Symptom:** Error message about database being locked

**Fixes:**

1. **Graceful restart:**
   ```powershell
   Ctrl+C
   # Wait 10 seconds
   python run.py
   ```

2. **Force cleanup:**
   ```powershell
   # Stop the application
   # Delete database file
   Remove-Item "instance\ea_tutorial.db"
   # Restart - it will recreate automatically
   python run.py
   ```

---

### Issue: Port 5000 already in use

**Symptom:** `Address already in use`

**Fix 1: Find and stop the process**
```powershell
netstat -ano | findstr :5000
# Note the PID number
taskkill /PID [PID] /F
# Then restart: python run.py
```

**Fix 2: Change port**

Edit `run.py`:
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)  # Changed from 5000 to 8000
```

Then access via: `http://[SERVER_IP]:8000`

---

### Issue: Can't connect from other PC

**Checklist:**

1. ✅ Server running? Terminal shows "Running on..."
2. ✅ Correct IP? Check with `ipconfig` on server
3. ✅ Same WiFi? Both PCs connected to same network
4. ✅ Firewall? Allow Python through Windows Firewall
5. ✅ Ping test:
   ```powershell
   ping 192.168.0.163  # Replace with your server IP
   ```
6. ✅ Try localhost on server:
   ```powershell
   # On server PC, open browser
   http://localhost:5000
   ```

---

## 📈 Performance Optimization (Optional)

### Use Gunicorn for Production-Like Performance

```powershell
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn (handles more users better)
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

**Note:** `-w 4` means 4 worker processes (adjust based on CPU cores)

### Enable Caching

Edit `run.py` to add caching headers for static files.

### Increase Max Upload Size

Edit `run.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB, adjust as needed
```

---

## 🔒 Security for Network Access

### Basic Authentication (Already Included)

Your app already has login system. Users must login with credentials:
- Admin
- Teacher  
- Student

### Additional: Windows Firewall Configuration

1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Click "Allow another app"
4. Browse to: `.\.venv\Scripts\python.exe`
5. Check "Private" (for home network)
6. Click OK

### Additional: Network Restriction (Advanced)

Edit `run.py` to restrict access to specific IP ranges:

```python
from flask import request
from functools import wraps

def require_local_network(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Only allow 192.168.x.x network
        if not request.remote_addr.startswith('192.168.'):
            return "Access denied", 403
        return f(*args, **kwargs)
    return decorated

# Then add @require_local_network above any route you want to restrict
```

---

## 📅 Scheduled Auto-Start (Windows Task Scheduler)

### Setup Auto-Start on Server Boot

1. Press `Win+R`, type `taskschd.msc`, press Enter
2. Right-click "Task Scheduler Library"
3. Select "Create Basic Task..."
4. Name: `EA Tutorial Hub Server`
5. Trigger: `At system startup`
6. Action: `Start a program`
   - Program: `C:\Users\[YourUsername]\Desktop\Project EA\.venv\Scripts\python.exe`
   - Arguments: `run.py`
   - Start in: `C:\Users\[YourUsername]\Desktop\Project EA`
7. Check "Run with highest privileges"
8. Finish

**Now the server automatically starts when PC boots!**

---

## 🆘 Emergency Recovery

### Application completely broken?

1. **Delete database and restart:**
   ```powershell
   Remove-Item "instance\ea_tutorial.db"
   python run.py
   ```
   This recreates the database with default data.

2. **Still broken? Reinstall dependencies:**
   ```powershell
   pip install --force-reinstall -r requirements.txt
   python run.py
   ```

3. **Still broken? Full reset:**
   ```powershell
   Remove-Item ".venv" -Recurse -Force
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python run.py
   ```

---

## 📊 Server Monitoring Dashboard

### Create a Simple Status Checker

Run this script on any PC to check server status:

```powershell
# Save as check_server.ps1
param(
    [string]$ServerIP = "192.168.0.163"
)

$url = "http://$ServerIP:5000"

Write-Host "Checking EA Tutorial Hub Server..."
Write-Host "=================================="
Write-Host "Server: $ServerIP"
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Status: ONLINE"
    Write-Host "Response Time: OK"
} catch {
    Write-Host "❌ Status: OFFLINE"
    Write-Host "Error: $($_.Exception.Message)"
}

# Ping test
Write-Host ""
Write-Host "Ping Test:"
$ping = Test-Connection -ComputerName $ServerIP -Count 1 -ErrorAction SilentlyContinue
if ($ping) {
    Write-Host "✅ Server reachable"
    Write-Host "Response time: $($ping.ResponseTime)ms"
} else {
    Write-Host "❌ Server not reachable"
}
```

Usage:
```powershell
.\check_server.ps1 -ServerIP 192.168.0.163
```

---

## 📝 Log Rotation (Optional)

### Save application logs to file

Edit `run.py`:

```python
import logging
from logging.handlers import RotatingFileHandler

if __name__ == '__main__':
    # Setup logging
    handler = RotatingFileHandler('app.log', maxBytes=10000000, backupCount=10)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    
    # Run app
    app.run(host='0.0.0.0', port=5000, debug=True)
```

Now logs are saved to `app.log` (helpful for debugging).

---

## ✅ Monitoring Checklist

Print and keep this near your server PC:

```
Weekly Server Check:
☐ Server online (http://[IP]:5000)
☐ Login works (Admin/admin123)
☐ Dashboard loads
☐ No errors in terminal
☐ Database file exists
☐ Database size reasonable
☐ Backup created (if doing manual backups)
☐ No network issues reported
```

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Start server | `python run.py` |
| Stop server | `Ctrl+C` in terminal |
| Check IP | `ipconfig` |
| Find process on port | `netstat -ano \| findstr :5000` |
| Kill process | `taskkill /PID [ID] /F` |
| Clear database | `Remove-Item instance\ea_tutorial.db` |
| Backup database | `Copy-Item instance\ea_tutorial.db instance\ea_tutorial.db.backup` |
| Check firewall | Windows Defender Firewall settings |

---

## 🎯 Typical Daily Operations

### Morning
- [ ] PC turned on (auto-starts with Task Scheduler)
- [ ] Server running in background
- [ ] Students can access: `http://[SERVER_IP]:5000`

### During Day
- [ ] Monitor for login errors (none should occur)
- [ ] Restart only if issue occurs

### Evening
- [ ] Keep PC on for late-night users
- [ ] Or shutdown at scheduled time

### Weekly Maintenance
- [ ] Restart server once for cleanup
- [ ] Backup database
- [ ] Check disk space

---

**Your EA Tutorial Hub is now set up for reliable 24x7 network operation!**

---

*Last Updated: December 21, 2025*
*Version: 1.0*
