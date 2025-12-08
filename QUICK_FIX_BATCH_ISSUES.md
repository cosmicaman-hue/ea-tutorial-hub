# ⚡ QUICK FIX - If run_server.bat Not Working

**Fast solutions if the batch file isn't executing**

---

## ❌ Problem: File Won't Execute / Double-Click Does Nothing

### Solution 1: Use PowerShell Instead (Fastest Fix)

**On Server PC, open PowerShell:**

1. Press `Win+R`
2. Type: `powershell`
3. Press Enter

**Then run:**

```powershell
cd "C:\Users\[YourUsername]\Desktop\Project EA"
python run.py
```

Replace `[YourUsername]` with your actual username.

**Done!** The application starts immediately.

---

### Solution 2: Simple Launcher Script

**Create a new file called `START_HERE.bat`:**

Copy this and save as `START_HERE.bat` in Project EA folder:

```batch
@echo off
cd /d "%~dp0"
python run.py
pause
```

**Then just double-click `START_HERE.bat`**

---

### Solution 3: Check Batch File Association

**The batch file might not be associated with command processor:**

1. Right-click `run_server.bat`
2. Select "Open with"
3. Select "Command Prompt"
4. Check "Always use this app"
5. Click OK

Now try double-clicking again.

---

### Solution 4: Manual Command

**Open Command Prompt (not PowerShell):**

1. Press `Win+R`
2. Type: `cmd`
3. Press Enter

**Then:**

```batch
cd /d "C:\Users\[YourUsername]\Desktop\Project EA"
run_server.bat
```

---

## ❌ Problem: "Python not found" Error

### Solution:

**Python is not in your PATH**

1. Uninstall Python completely
2. Download from: https://www.python.org/downloads/
3. Run installer
4. **CRITICAL:** Check the box "Add Python to PATH"
5. Click "Install Now"
6. After installation, restart your PC
7. Try again

---

## ❌ Problem: "Virtual environment failed"

### Quick Fix:

**Delete and recreate:**

1. Open PowerShell (as Administrator)
2. Navigate to Project EA folder
3. Run:

```powershell
Remove-Item ".venv" -Recurse -Force
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

---

## ❌ Problem: "Port 5000 already in use"

### Solution:

**Kill the process using port 5000:**

```powershell
netstat -ano | findstr :5000
# Note the PID number
taskkill /PID [PID_NUMBER] /F

# Then restart
python run.py
```

Or use a different port:

Edit `run.py` and change:
```python
app.run(host='0.0.0.0', port=8000, debug=True)  # Changed from 5000 to 8000
```

Then access: `http://[IP]:8000`

---

## ❌ Problem: Firewall Blocking

### Solution:

**Allow Python through firewall:**

1. Open "Windows Defender Firewall"
2. Click "Allow an app through firewall"
3. Click "Allow another app"
4. Browse to: `.venv\Scripts\python.exe` in your project folder
5. Check "Private" (for home network)
6. Click OK

---

## ✅ Quick Test - Is Everything Working?

**Run this to verify:**

```powershell
# In PowerShell
cd "C:\Users\[YourUsername]\Desktop\Project EA"

# Check Python
python --version

# Check virtual environment
.\.venv\Scripts\Activate.ps1

# Check dependencies
pip list | findstr flask

# Try to start (will fail if port in use, that's OK)
python run.py
```

---

## 🎯 The Simplest Method (Just Do This)

Instead of using batch files, just use PowerShell every time:

1. Press `Win+R`
2. Type: `powershell`
3. Run:
```powershell
cd "C:\Users\[YourUsername]\Desktop\Project EA"
python run.py
```

**That's it! Application starts.**

---

## 📋 Step-by-Step for Server PC

### Step 1: Install Python
- Download: https://www.python.org/downloads/
- **CHECK: "Add Python to PATH"**
- Restart PC

### Step 2: Copy Project Files
- USB drive or network share
- Paste to: `C:\Users\[YourUsername]\Desktop\Project EA`

### Step 3: Setup (In PowerShell as Admin)
```powershell
cd "C:\Users\[YourUsername]\Desktop\Project EA"
python server_setup.py
```

### Step 4: Start Server
```powershell
python run.py
```

### Step 5: Access from Your PC
- Get server IP: `ipconfig` on server PC
- Visit: `http://[IP]:5000` on your PC

---

## 💡 Pro Tip

**Create a shortcut on Desktop:**

1. On server PC, create shortcut to PowerShell:
   ```
   %SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe
   ```

2. Right-click shortcut → Properties

3. In "Target", add at the end:
   ```
   -NoExit -Command "cd 'C:\Users\[YourUsername]\Desktop\Project EA'; python run.py"
   ```

4. Click OK

**Now just double-click that shortcut to start server!**

---

## 🚀 If All Else Fails

**Use this foolproof method:**

1. Open PowerShell
2. Copy-paste this entire command:

```powershell
cd "C:\Users\$env:USERNAME\Desktop\Project EA"; python run.py
```

This automatically uses your username!

---

**One of these solutions will definitely work!**

Most common issue: **Python not in PATH** → Reinstall Python and check the box!

---

*Quick Fix Guide - December 21, 2025*
