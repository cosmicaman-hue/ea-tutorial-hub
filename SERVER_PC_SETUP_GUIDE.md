# 🖥️ SERVER PC SETUP GUIDE

**Complete step-by-step instructions to setup EA Tutorial Hub on a different PC**

---

## 📋 Overview

You want to run the application on a **different PC** than the one you're working on now. This guide shows you exactly what to do on that server PC.

---

## 🎯 Scenario

```
Your Current PC (where you have the project):
  └─ Project folder exists
  └─ Python might not be installed
  └─ NOT the server

Server PC (different computer on your WiFi):
  └─ This is where the app will run 24x7
  └─ Needs Python installation
  └─ Needs project files copied
  └─ Needs setup completed
```

---

## 📋 What You Need

**On Server PC:**
- Windows 10/11 (or Mac/Linux)
- Admin access to install software
- WiFi connection
- At least 5GB free disk space
- USB drive or network access to copy files (optional)

---

## ✅ STEP 1: Copy Project Files to Server PC

### Option A: Using USB Drive (Easiest)

**On Your Current PC:**
1. Get a USB drive (8GB+ recommended)
2. Copy entire `Project EA` folder to USB
3. Eject USB safely

**On Server PC:**
1. Insert USB drive
2. Copy `Project EA` folder to: `C:\Users\[YourUsername]\Desktop\`
3. Eject USB drive

### Option B: Using Network Share

**On Your Current PC:**
1. Right-click `Project EA` folder
2. Select "Give access to" → "Specific people"
3. Share with your network

**On Server PC:**
1. Open File Explorer
2. Go to: `\\[YOUR_CURRENT_PC_IP]\Users\[YourUsername]\Desktop\Project EA`
3. Copy entire folder to Server PC Desktop

### Option C: Download from GitHub

**On Server PC:**
1. Open PowerShell
2. Run:
```powershell
cd Desktop
git clone https://github.com/cosmicaman-hue/ea-tutorial-hub.git
cd ea-tutorial-hub
```

---

## 🐍 STEP 2: Install Python on Server PC

### For Windows:

**Important:** Python MUST be added to PATH

1. Download Python from: https://www.python.org/downloads/
   - Get version 3.10 or higher
   - Recommended: Latest 3.11 or 3.12

2. Run installer

3. **CRITICAL - Check these boxes:**
   - ☑️ "Install launcher for all users"
   - ☑️ **"Add Python [version] to PATH"** ← MUST CHECK THIS!

4. Click "Install Now"

5. Wait for completion

6. Click "Disable path length limit" (if prompted)

### Verify Installation:

1. Open PowerShell on server PC
2. Run:
```powershell
python --version
```

**Should show:** `Python 3.x.x`

If it shows "command not found", Python was not added to PATH:
- Uninstall and reinstall
- Make sure to check "Add Python to PATH"

---

## 📥 STEP 3: Setup Project on Server PC

### Open PowerShell on Server PC:

1. Press `Win+R`
2. Type: `powershell`
3. Press Enter

### Navigate to Project:

```powershell
cd "C:\Users\[YourUsername]\Desktop\Project EA"
```

Replace `[YourUsername]` with actual username.

### Run Setup:

```powershell
python server_setup.py
```

**This will automatically:**
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Setup launcher scripts
- ✅ Configure firewall
- ✅ Display network information

**Expected output:**
```
[Step 1] Checking Python Installation
✅ Python found: Python 3.x.x

[Step 2] Creating Virtual Environment
✅ Virtual environment created at: ...\.venv

[Step 3] Installing Dependencies
✅ Dependencies installed successfully

[Step 4] Checking Database
✅ Database not found (will be created on first run)

[Step 5] Network Information
Server Hostname: SERVERNAME
Server IP Address: 192.168.0.163

[Step 6] Creating Launcher Scripts
✅ Created: run_server.bat
✅ Created: network_setup.bat
✅ Created: run_server.ps1

[Step 7] Creating Server Configuration
✅ Configuration file created: server_config.txt

Setup Complete! ✅
```

---

## 🚀 STEP 4: Start the Server

### Method 1: Using Batch File (Easiest)

**On Server PC:**
1. Navigate to: `C:\Users\[YourUsername]\Desktop\Project EA`
2. Double-click: `run_server.bat`

**Expected:**
- Terminal/PowerShell window opens
- Shows Flask starting messages
- Shows: "Running on http://0.0.0.0:5000"
- Keep this window open

### Method 2: Using PowerShell

**On Server PC, in PowerShell:**
```powershell
cd "C:\Users\[YourUsername]\Desktop\Project EA"
.\.venv\Scripts\Activate.ps1
python run.py
```

**Keep PowerShell window open!**

---

## 🌐 STEP 5: Find Server IP Address

### On Server PC - Open PowerShell and run:

```powershell
ipconfig
```

Look for **WiFi adapter** section (not Ethernet) and find:
```
IPv4 Address . . . . . . . . . . . : 192.168.0.163
```

**Note this IP address** - you'll need it to access from other PCs.

Example IPs:
- `192.168.0.163`
- `192.168.1.100`
- `10.0.0.50`

---

## 💻 STEP 6: Access from Your Current PC

### On Your Current PC:

1. Open web browser (Chrome, Firefox, Edge, Safari)
2. Type in address bar: `http://192.168.0.163:5000`
   - Replace `192.168.0.163` with the actual server IP
3. Press Enter

**You should see the EA Tutorial Hub login page!**

### Login with:
```
Username: Admin
Password: admin123
```

---

## 🔧 STEP 7: Setup Auto-Start (Optional but Recommended)

Want the application to start automatically when server PC boots?

### Use Windows Task Scheduler:

1. On Server PC, press `Win+R`
2. Type: `taskschd.msc`
3. Press Enter (Task Scheduler opens)

4. Right-click "Task Scheduler Library"
5. Select "Create Basic Task..."

6. **General Tab:**
   - Name: `EA Tutorial Hub Server`
   - Check: "Run with highest privileges"

7. **Trigger Tab:**
   - Select: "At system startup"
   - Click: Next

8. **Action Tab:**
   - Program: `C:\Users\[YourUsername]\.venv\Scripts\python.exe`
   - Arguments: `run.py`
   - Start in: `C:\Users\[YourUsername]\Desktop\Project EA`
   - Click: Next

9. **Finish:** Click OK

**Now the app auto-starts on every server PC boot!**

---

## ⚡ Troubleshooting on Server PC

### Issue: "Python not found" error

**Cause:** Python not in PATH

**Fix:**
1. Uninstall Python
2. Reinstall and **CHECK** "Add Python to PATH"
3. Restart server PC
4. Try again

### Issue: "Permission denied" when running setup

**Fix:**
1. Right-click PowerShell
2. Select "Run as Administrator"
3. Run command again

### Issue: "Virtual environment creation failed"

**Fix:**
```powershell
# Delete broken venv
Remove-Item ".venv" -Recurse -Force

# Recreate
python -m venv .venv

# Activate and install
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Issue: Port 5000 already in use

**Check what's using it:**
```powershell
netstat -ano | findstr :5000
```

**Kill process:**
```powershell
taskkill /PID [PID_NUMBER] /F
```

Then restart server.

### Issue: Can't access from other PC

**Checklist:**
- [ ] Server terminal shows "Running on http://0.0.0.0:5000"
- [ ] Both PCs on same WiFi network
- [ ] Correct server IP address used
- [ ] No firewall blocking (see below)

**Firewall Fix:**
1. On Server PC, open "Windows Defender Firewall"
2. Click "Allow an app through firewall"
3. Click "Allow another app"
4. Browse to: `.\.venv\Scripts\python.exe`
5. Check "Private"
6. Click OK

---

## 🎯 Quick Checklist for Server PC

- [ ] USB drive with Project EA copied
- [ ] Project EA pasted to Desktop
- [ ] Python installed (check PATH)
- [ ] PowerShell opened as Admin
- [ ] `python server_setup.py` ran successfully
- [ ] `run_server.bat` or `python run.py` starts without errors
- [ ] Server IP identified (from `ipconfig`)
- [ ] Can access from your PC: `http://[IP]:5000`
- [ ] Login works with Admin/admin123
- [ ] (Optional) Task Scheduler auto-start configured

---

## 📊 Network Setup Diagram

```
Your Current PC                Server PC (Running 24x7)
└─ Access application    ←→    ├─ Python running
  via browser                    ├─ Flask on port 5000
  http://[IP]:5000             ├─ Database file
                                └─ Connected to WiFi
```

---

## 🔐 Security Notes

### On Server PC:

1. **Keep terminal window visible** so you can monitor for errors
2. **Restart weekly** for stability
3. **Don't close the terminal** while it should be running
4. **Monitor disk space** - database will grow slowly

### On Your Current PC:

1. Change default passwords after setup (in admin panel)
2. Only share server IP with authorized users
3. Don't leave credentials on sticky notes

---

## 📱 Multi-Device Access

Once server is running, access from:

- 💻 Multiple PCs on same WiFi
- 📱 Smartphones on same WiFi
- 📊 Tablets on same WiFi
- 🖥️ Any device with web browser

**URL:** `http://[SERVER_IP]:5000`

---

## 🆘 Help Commands (Server PC)

```powershell
# Check Python installed
python --version

# Check server IP
ipconfig

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start server
python run.py

# Stop server
Ctrl+C (in PowerShell)

# Check port status
netstat -ano | findstr :5000

# Kill process on port
taskkill /PID [ID] /F

# Run diagnostics
python network_setup.bat
```

---

## ✅ Success Confirmation

You're ready when:

✅ Server PC has Python installed
✅ Project files copied to Server PC
✅ Setup script ran successfully
✅ Server started (`run_server.bat` or `python run.py`)
✅ Can access from Your Current PC
✅ Login works
✅ Dashboard loads without errors

---

## 🎉 Congratulations!

Your EA Tutorial Hub is now:

1. ✅ Running on Server PC
2. ✅ Accessible from your current PC
3. ✅ Accessible from any PC on WiFi
4. ✅ Ready for 24x7 operation

---

## 🚀 Next Steps

1. **Today:**
   - Setup server PC following this guide
   - Test access from your PC
   - Verify all features work

2. **This Week:**
   - Monitor server for stability
   - Create database backup
   - Setup auto-start (if desired)

3. **Ongoing:**
   - Weekly restart
   - Monthly backup
   - Monitor usage

---

## 📞 If You Still Have Issues

**Check these files:**
- `NETWORK_DEPLOYMENT_GUIDE.md` - Complete setup guide
- `SERVER_OPERATIONS_GUIDE.md` - Operations & troubleshooting
- `24X7_QUICK_START.md` - Quick reference

**Or use diagnostic tool on server PC:**
```powershell
python network_setup.bat
```

---

*Guide Created: December 21, 2025*
*For Server PC Setup*
*Version 1.0*
