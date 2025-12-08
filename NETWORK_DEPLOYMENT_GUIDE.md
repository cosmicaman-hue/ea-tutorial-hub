# 24x7 Network Deployment Guide

**Setup EA Tutorial Hub on a Server PC in your WiFi Network**

---

## 📋 Overview

This guide will help you:
1. ✅ Prepare your server PC
2. ✅ Install Python and dependencies
3. ✅ Copy the application
4. ✅ Configure for 24x7 running
5. ✅ Access from other PCs on the network

---

## 🖥️ Requirements

### Server PC (The PC running 24x7)
- Windows, Mac, or Linux
- Python 3.10+
- Minimum 2GB RAM
- Connected to your WiFi network
- Can be left running continuously

### Client PCs (Access the application)
- Any PC on the same WiFi network
- Modern web browser (Chrome, Firefox, Safari, Edge)

---

## 📦 Step 1: Prepare Your Server PC

### A. Install Python (if not already installed)

**Windows:**
1. Download Python 3.11 from https://www.python.org/downloads/
2. Run installer
3. **IMPORTANT:** Check "Add Python to PATH"
4. Click "Install Now"

**Verify installation:**
```bash
python --version
```

### B. Install Git (Optional but recommended)

Download from: https://git-scm.com/download/win

---

## 📥 Step 2: Copy Application to Server PC

### Option A: Using GitHub (Recommended for 24x7 setup)

```bash
# Open PowerShell or Command Prompt on server PC
cd Desktop
git clone https://github.com/cosmicaman-hue/ea-tutorial-hub.git
cd ea-tutorial-hub
```

### Option B: Manual Copy

1. Copy the entire `Project EA` folder to server PC
2. Place it somewhere accessible (e.g., `C:\Apps\ea-tutorial-hub`)

---

## ⚙️ Step 3: Setup Virtual Environment

On your **server PC**, open PowerShell and run:

```bash
# Navigate to application folder
cd C:\Users\[YourUsername]\Desktop\Project EA
# Or wherever you copied it

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Step 4: Run Application on Server

### Option A: Basic Running (Simple 24x7)

```bash
# Make sure you're in the project folder
# And virtual environment is activated

python run.py
```

**Note:** Keep this terminal/PowerShell window open 24x7

### Option B: Background Service (Advanced - Windows)

Create a batch file `run_server.bat`:

```batch
@echo off
cd /d "C:\Users\[YourUsername]\Desktop\Project EA"
.\.venv\Scripts\python.exe run.py
pause
```

Save as `run_server.bat` in the project folder.

Double-click to run in background.

### Option C: Windows Task Scheduler (Best for 24x7)

1. Open Task Scheduler (search in Windows)
2. Create Basic Task
3. Name: "EA Tutorial Hub Server"
4. Trigger: "At system startup"
5. Action: "Start a program"
   - Program: `.\.venv\Scripts\python.exe`
   - Arguments: `run.py`
   - Start in: `C:\Users\[YourUsername]\Desktop\Project EA`
6. Check "Run with highest privileges"
7. Click OK

This will auto-start the application whenever the server PC boots up.

---

## 🌐 Step 5: Find Your Server IP Address

### On Server PC:

**Windows - PowerShell:**
```bash
ipconfig
```

Look for "IPv4 Address" - should be something like: `192.168.x.x` or `10.0.x.x`

**Example output:**
```
IPv4 Address . . . . . . . . . . . : 192.168.0.163
```

---

## 💻 Step 6: Access from Other PCs

### From any PC on your WiFi network:

1. Open web browser (Chrome, Firefox, etc.)
2. Enter URL: `http://[SERVER_IP]:5000`
   - Replace `[SERVER_IP]` with your server's IP (e.g., `http://192.168.0.163:5000`)
3. You should see the login page

### Example URLs:
- `http://192.168.0.163:5000` - Main page
- `http://192.168.0.163:5000/auth/login` - Login
- `http://192.168.0.163:5000/admin/dashboard` - Admin dashboard

---

## 🔑 Default Credentials

```
Username: Admin
Password: admin123

OR

Username: Teacher
Password: teacher123

OR

Username: EA24C001
Password: student123
```

---

## ⚡ Important Configuration Notes

### 1. Server PC Network Settings

**Windows Firewall:**
- Application should auto-request firewall access
- If blocked, manually allow:
  1. Settings → Privacy & Security → Firewall
  2. "Allow an app through firewall"
  3. Find "python.exe"
  4. Check "Private" (if on home network)

### 2. Port Configuration

The application runs on port `5000` by default.

If you need to change it, edit `run.py`:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Change 5000 to your port
```

### 3. Network Discovery

Make sure all PCs are on the **same WiFi network** (same SSID).

---

## 🔒 Optional: Security for Network Access

### A. Add Simple Password Protection (Future Enhancement)

Currently, the app uses login credentials. This is sufficient.

### B. Restrict to Specific IPs

Edit `run.py` to only allow certain IPs:

```python
# Add near the top
from functools import wraps
from flask import request

def check_ip(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow connections from your network only
        allowed_ips = ['192.168.0.*']  # Adjust to your network
        if not request.remote_addr.startswith('192.168.0.'):
            return "Access denied", 403
        return f(*args, **kwargs)
    return decorated
```

---

## 🆘 Troubleshooting

### Issue: Can't connect from other PC

**Solution:**
1. Check server IP: `ipconfig` on server PC
2. Ping server: `ping 192.168.0.163` from client PC
3. Check firewall: Allow Python through Windows Firewall
4. Make sure both PCs on same WiFi network

### Issue: Application closes/crashes

**Solution:**
1. Check error messages in terminal
2. Make sure database file exists: `instance/ea_tutorial.db`
3. Restart with: `python run.py`

### Issue: Database locked error

**Solution:**
1. Stop the application (Ctrl+C)
2. Delete `instance/ea_tutorial.db`
3. Restart: `python run.py`

### Issue: Port already in use

**Solution:**
1. Find process using port 5000: `netstat -ano | findstr :5000`
2. Kill process: `taskkill /PID [PID_NUMBER] /F`
3. Or change port in `run.py`

---

## 📊 Monitoring Your Server

### Check Application Status

From any PC on network:
- Visit: `http://[SERVER_IP]:5000`
- Should see login page

### Monitor Server PC

Keep terminal open to see:
- Access logs
- Error messages
- Database operations

---

## 🔄 Keeping It Running 24x7

### Recommended Setup:

1. **Task Scheduler** on server PC (auto-starts on reboot)
2. **UPS/Power backup** (optional, keeps server running during power cuts)
3. **Monitor regularly** from other PCs
4. **Restart weekly** (maintenance) - optional but recommended

### Restart Procedure:

```bash
# In terminal on server PC
Ctrl+C  # Stop application
python run.py  # Restart
```

---

## 📱 Multi-Device Access

All these devices can access simultaneously:

- 💻 Laptop on WiFi
- 📱 Smartphone on WiFi
- 🖥️ Desktop on WiFi
- 📊 Tablet on WiFi

Just use: `http://[SERVER_IP]:5000`

---

## 🚀 Advanced: Production Setup (Optional)

For better 24x7 performance, consider:

### 1. Use Gunicorn instead of Flask development server

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### 2. Use Nginx as reverse proxy

```bash
# Install Nginx
# Configure to forward to Flask
```

### 3. Use Docker

```bash
# Containerize the application
# Run in Docker for better isolation
```

These are optional for production but not needed for basic 24x7 operation.

---

## ✅ Quick Start Checklist

- [ ] Python 3.10+ installed on server PC
- [ ] Application copied to server PC
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Application tested locally on server PC
- [ ] Server IP address noted (e.g., 192.168.0.163)
- [ ] Windows Firewall configured (Python allowed)
- [ ] Task Scheduler configured (optional but recommended)
- [ ] Tested access from another PC on network
- [ ] Credentials verified working

---

## 📞 Support

### Common Commands

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start application
python run.py

# Deactivate virtual environment
deactivate

# Install/update dependencies
pip install -r requirements.txt

# Check what's running on port 5000
netstat -ano | findstr :5000
```

### Check Status

- **Application URL:** `http://[SERVER_IP]:5000`
- **Admin Dashboard:** `http://[SERVER_IP]:5000/admin/dashboard`
- **Status:** All pages should load without errors

---

## 🎯 Next Steps

1. Follow steps 1-6 on your server PC
2. Test access from another PC
3. Configure Task Scheduler for auto-start
4. Monitor first week
5. Create backup of database regularly

---

**Your EA Tutorial Hub is now ready for 24x7 network deployment!**

Last Updated: December 21, 2025
Version: 1.0
