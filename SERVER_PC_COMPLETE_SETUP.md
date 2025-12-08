# 🎯 SERVER PC - COMPLETE SETUP & TROUBLESHOOTING

**Everything you need to get the application running on your server PC**

---

## 📌 Your Situation

- ✅ You have the project on your current PC
- ✅ You have a DIFFERENT PC that will be the server
- ❌ `run_server.bat` not executing properly
- ❓ Confused about what to do on the server PC

**This guide covers all of it!**

---

## 🚀 THE FASTEST PATH (Do This First)

### On Your Current PC:

**Copy project folder to USB or prepare to share:**

1. Go to: `C:\Users\sujit\Desktop\Project EA`
2. Right-click folder → Copy
3. Paste to USB drive OR keep ready to copy

### On Server PC (The one running 24x7):

**Step 1: Paste Project Files**

Paste `Project EA` folder to: `C:\Users\[YourUsername]\Desktop\`

**Step 2: Install Python (If Not Already Installed)**

- Go to: https://www.python.org/downloads/
- Download Python 3.11 or higher
- Run installer
- **☑️ CRITICAL: CHECK "Add Python to PATH"**
- Click "Install Now"
- Restart PC

**Step 3: Open PowerShell (NOT Command Prompt)**

Press `Win+R`, type `powershell`, press Enter

**Step 4: Run These Commands:**

```powershell
cd "C:\Users\[YourUsername]\Desktop\Project EA"
python server_setup.py
```

Wait for it to complete (shows "Setup Complete! ✅")

**Step 5: Start Server**

```powershell
python run.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
 * Debugger is active!
```

**Step 6: Find Your IP**

On server PC, open another PowerShell window:
```powershell
ipconfig
```

Look for "IPv4 Address" (like `192.168.0.163`)

**Step 7: Access from Your Current PC**

On your current PC, open browser:
```
http://192.168.0.163:5000
```
(Use the actual IP from step 6)

**✅ DONE! You're live!**

---

## ❌ If Batch File Still Doesn't Work

### Use PowerShell Instead (Recommended)

**Don't bother with .bat files, use this:**

```powershell
cd "C:\Users\[YourUsername]\Desktop\Project EA"
python run.py
```

This always works!

### Alternative: Simple Launcher

Create a new file named `START.bat`:

```batch
@echo off
cd /d "%~dp0"
python run.py
pause
```

Save in Project EA folder, double-click to run.

---

## 🎯 What Exactly to Do on Server PC

### Setup Phase (First Time - 20 minutes)

| Step | What to Do | Expected Result |
|------|-----------|-----------------|
| 1 | Copy Project EA folder to Desktop | Folder appears at `C:\Users\[You]\Desktop\Project EA` |
| 2 | Install Python 3.10+ | Command `python --version` works |
| 3 | Open PowerShell | PowerShell window open |
| 4 | Run `python server_setup.py` | "Setup Complete! ✅" message appears |
| 5 | Run `python run.py` | Flask shows "Running on http://0.0.0.0:5000" |
| 6 | Run `ipconfig` | Shows IPv4 Address (e.g., `192.168.0.163`) |

### Access Phase (Daily)

1. On Server PC: Run `python run.py` (or use PowerShell command above)
2. On Your PC: Visit `http://[SERVER_IP]:5000`
3. Login with `Admin` / `admin123`

### Optional: Auto-Start (One Time)

**Windows Task Scheduler:**

1. Press `Win+R`, type `taskschd.msc`, press Enter
2. Right-click "Task Scheduler Library" → "Create Basic Task..."
3. Name: `EA Server`
4. Trigger: "At system startup"
5. Action: Start program
   - Program: `C:\Users\[YourUsername]\.venv\Scripts\python.exe`
   - Arguments: `run.py`
   - Start in: `C:\Users\[YourUsername]\Desktop\Project EA`
6. Check "Run with highest privileges"
7. Click OK

Now app auto-starts on PC boot!

---

## 📊 Before vs After

### Before Setup:
```
Your PC ──→ Project EA ──→ Only accessible on this PC
```

### After Setup:
```
Server PC ──→ Project EA ──→ Accessible from WiFi
    ↑
    └─── Your PC accesses via: http://[IP]:5000
         Other PCs also: http://[IP]:5000
         Phones too: http://[IP]:5000
```

---

## 🔍 Troubleshooting Server PC Setup

### Issue: Python Not Found

```
python: command not found
```

**Cause:** Python not in PATH

**Fix:**
1. Go to: Control Panel → Programs → Programs and Features
2. Find Python, click Modify
3. Check "Add Python to PATH"
4. Click Next → Finish
5. Restart PC
6. Try again

### Issue: Virtual Environment Fails

```
ERROR: Command not found
```

**Fix:**
```powershell
# Delete broken venv
Remove-Item ".venv" -Recurse -Force

# Create new one
python -m venv .venv

# Activate
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Issue: Port 5000 Already in Use

```
Address already in use
```

**Fix 1:**
```powershell
netstat -ano | findstr :5000
taskkill /PID [PID] /F
python run.py
```

**Fix 2: Use different port**

Edit `run.py`:
```python
app.run(host='0.0.0.0', port=8000, debug=True)  # Change from 5000 to 8000
```

Then access: `http://[IP]:8000`

### Issue: "Connection refused" from Your PC

**Checklist:**
- [ ] Server PC terminal shows "Running on..."
- [ ] Both PCs on same WiFi
- [ ] Using correct server IP
- [ ] Windows firewall allows Python

**Firewall Fix:**
1. Settings → Privacy & Security → Firewall
2. "Allow an app through firewall"
3. "Allow another app"
4. Browse to: `.venv\Scripts\python.exe`
5. Check "Private"
6. OK

### Issue: Database Error

```
no such table: user
```

**Fix:**
```powershell
# Stop server: Ctrl+C
# Delete database
Remove-Item "instance\ea_tutorial.db"
# Restart
python run.py
```

It will recreate automatically.

### Issue: Setup Script Fails

```
ModuleNotFoundError: No module named 'flask'
```

**Fix:**
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

---

## ✅ Verification Checklist

Before declaring success, verify:

- [ ] Python installed and in PATH (`python --version` works)
- [ ] Project files in: `C:\Users\[You]\Desktop\Project EA`
- [ ] Server setup ran: `python server_setup.py`
- [ ] Server starts: `python run.py` shows "Running on..."
- [ ] Can find IP: `ipconfig` shows IPv4 Address
- [ ] Can access from your PC: `http://[IP]:5000` shows login page
- [ ] Can login: `Admin` / `admin123` works
- [ ] Dashboard loads without errors
- [ ] Terminal still shows no errors

---

## 📚 File Reference

### On Server PC After Setup

```
Project EA/
├── run.py (main application)
├── requirements.txt (dependencies)
├── server_setup.py (setup script)
├── run_server.bat (launcher - use if works)
├── run_server_simple.bat (simpler launcher)
├── network_setup.bat (diagnostics)
├── .venv/ (virtual environment - created by setup)
├── app/ (application code)
├── instance/ (database - created on first run)
└── [documentation files]
```

---

## 🎯 Quick Commands (Copy-Paste Ready)

### For Server PC PowerShell:

**Setup (first time only):**
```powershell
cd "C:\Users\$env:USERNAME\Desktop\Project EA"
python server_setup.py
```

**Start server (daily):**
```powershell
cd "C:\Users\$env:USERNAME\Desktop\Project EA"
python run.py
```

**Check if running (on other PowerShell window):**
```powershell
netstat -ano | findstr :5000
```

**Find IP:**
```powershell
ipconfig | findstr "IPv4"
```

---

## 📱 Access from Multiple Devices

Once server running at `http://192.168.0.163:5000`:

| Device | How to Access |
|--------|---------------|
| Your PC | Open browser: `http://192.168.0.163:5000` |
| Smartphone on WiFi | Same: `http://192.168.0.163:5000` |
| Tablet on WiFi | Same: `http://192.168.0.163:5000` |
| Other PC on WiFi | Same: `http://192.168.0.163:5000` |

All use the same URL!

---

## 🔐 Default Credentials

```
Admin:
  Username: Admin
  Password: admin123

Teacher:
  Username: Teacher
  Password: teacher123

Student:
  Username: EA24C001
  Password: student123
```

---

## 💡 Pro Tips

1. **Keep PowerShell window open** - Application needs it open to keep running

2. **Restart weekly** - For optimal performance:
   ```powershell
   Ctrl+C  (stop server)
   # Wait 5 seconds
   python run.py  (restart)
   ```

3. **Backup database** - Weekly backup:
   ```powershell
   Copy-Item "instance\ea_tutorial.db" "instance\ea_tutorial.db.backup"
   ```

4. **Monitor disk space** - Database grows slowly but check monthly

5. **Check logs** - Terminal shows all access logs and errors

---

## 🚀 Once It's Running

### Daily Operation:

1. Keep server PC on
2. Keep `python run.py` running (in PowerShell or with auto-start)
3. Access from any device: `http://[IP]:5000`

### Weekly:

1. Check no error messages in terminal
2. Restart server (Ctrl+C, then restart)
3. Backup database

### Monthly:

1. Full verification
2. Check for updates
3. Monitor database size

---

## 📞 If You Need Help

**Quick reference files:**

1. `SERVER_PC_SETUP_GUIDE.md` - Step-by-step for server PC
2. `QUICK_FIX_BATCH_ISSUES.md` - If batch files not working
3. `SERVER_OPERATIONS_GUIDE.md` - Daily operations
4. `24X7_QUICK_START.md` - Quick reference

---

## ✨ Summary

### The Absolute Simplest Path:

1. Copy Project EA to Server PC Desktop
2. Install Python (check PATH box!)
3. Open PowerShell
4. Run: `python server_setup.py`
5. Run: `python run.py`
6. Access from your PC via browser

**That's literally all you need to do!**

### Don't worry about:
- ❌ Batch files (use PowerShell)
- ❌ Complex setup (automated by script)
- ❌ Manual configuration (all done)

Just follow the 6 steps above and you're done!

---

## 🎉 You're All Set!

Your server PC is now ready to run EA Tutorial Hub 24x7, accessible from any device on your WiFi network.

**Start with the "Fastest Path" section above and you'll be up and running in 20 minutes!**

---

*Complete Server PC Setup Guide*
*December 21, 2025*
*Version 1.0*
