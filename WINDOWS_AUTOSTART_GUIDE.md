# Windows Task Scheduler Setup for Auto-Start

**Setup EA Tutorial Hub to Auto-Start on Every Server PC Boot**

---

## 🎯 What This Does

When the server PC boots, your EA Tutorial Hub automatically:
- ✅ Starts the Flask application
- ✅ Makes it accessible on your network
- ✅ No manual intervention needed
- ✅ Runs even if no one is logged in

---

## 📋 Prerequisites

Before starting this setup:

1. ✅ Python 3.10+ installed
2. ✅ Application folder exists: `C:\Users\[YourUsername]\Desktop\Project EA`
3. ✅ Virtual environment created (run `server_setup.py`)
4. ✅ Application tested manually (can run with `python run.py`)

---

## 🚀 Method 1: Easiest - Startup Folder (Windows)

### 2-Minute Setup

**Step 1: Create Shortcut**

1. Navigate to: `C:\Users\[YourUsername]\Desktop\Project EA`
2. Right-click `run_server.bat`
3. Select "Create shortcut"
4. A file `run_server.bat - Shortcut` appears

**Step 2: Move to Startup Folder**

1. Right-click on the shortcut
2. Select "Cut"
3. Press `Win+R`
4. Type: `shell:startup`
5. Press Enter (Startup folder opens)
6. Right-click in the folder
7. Select "Paste"

**Step 3: Done!**

- ✅ Server will auto-start on next boot
- ✅ Shortcut now in: `C:\Users\[YourUsername]\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
- ✅ No need to login

---

## 🚀 Method 2: Task Scheduler (More Reliable)

### 5-Minute Setup

**Step 1: Open Task Scheduler**

1. Press `Win+R`
2. Type: `taskschd.msc`
3. Press Enter
4. Task Scheduler opens

**Step 2: Create New Task**

1. In left panel, right-click: "Task Scheduler Library"
2. Select: "Create Basic Task..."
3. Enter:
   - **Name:** `EA Tutorial Hub - Server`
   - **Description:** `Starts EA Tutorial Hub Flask application on system startup`
4. Click: "Next"

**Step 3: Set Trigger**

1. Select: "At system startup"
2. Click: "Next"

**Step 4: Set Action**

1. Select: "Start a program"
2. Click: "Next"
3. In "Program/script" field, enter:
   ```
   C:\Users\[YourUsername]\.venv\Scripts\python.exe
   ```
   (Replace `[YourUsername]` with your actual username)

4. In "Arguments" field, enter:
   ```
   run.py
   ```

5. In "Start in" field, enter:
   ```
   C:\Users\[YourUsername]\Desktop\Project EA
   ```
   (Replace `[YourUsername]` with your actual username)

6. Click: "Next"

**Step 5: Set Options**

1. Check: "Run with highest privileges"
2. Click: "Finish"

**Step 6: Additional Configuration (Important)**

1. Go to: `Task Scheduler Library`
2. Find: `EA Tutorial Hub - Server`
3. Right-click it
4. Select: "Properties"
5. Go to: "Conditions" tab
6. Uncheck: "Stop if the computer switches to battery power"
   (Only if running on laptop/UPS)
7. Go to: "Settings" tab
8. Check: "If the task fails, restart every: 1 minute"
9. Check: "If the task is already running, then the following rule applies: Do not start a new instance"
10. Click: "OK"

**Step 7: Test the Task**

1. Go back to Task Scheduler Library
2. Find: `EA Tutorial Hub - Server`
3. Right-click it
4. Select: "Run"
5. Check: Terminal window opens with Flask running
6. To stop testing, close the terminal or press Ctrl+C

**Step 8: Done!**

- ✅ Task is now scheduled
- ✅ Will auto-start on every boot
- ✅ Will auto-restart if it crashes

---

## 🚀 Method 3: Advanced - PowerShell Script

### For Technical Users

**Step 1: Create PowerShell Script**

Create file: `setup_autostart.ps1`

```powershell
# EA Tutorial Hub - Task Scheduler Setup Script
# Run with admin rights

$TaskName = "EA Tutorial Hub - Server"
$TaskDescription = "Starts EA Tutorial Hub Flask application on system startup"
$TaskPath = "\EA Tutorial Hub\"
$ScriptPath = "C:\Users\[YourUsername]\Desktop\Project EA"
$PythonExe = "C:\Users\[YourUsername]\Desktop\Project EA\.venv\Scripts\python.exe"

# Create action
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "run.py" `
    -WorkingDirectory $ScriptPath

# Create trigger
$Trigger = New-ScheduledTaskTrigger -AtStartup

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# Create principal
$Principal = New-ScheduledTaskPrincipal `
    -UserID "NT AUTHORITY\SYSTEM" `
    -RunLevel "Highest" `
    -LogonType "ServiceAccount"

# Register task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Description $TaskDescription `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Force

Write-Host "✅ Task created successfully!"
Write-Host "Task name: $TaskName"
Write-Host "Will auto-start on next boot"
```

**Step 2: Run PowerShell Script**

1. Right-click PowerShell
2. Select "Run as Administrator"
3. Run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   C:\path\to\setup_autostart.ps1
   ```

---

## 🔍 Verify Auto-Start is Working

### Before Reboot

**Visual Verification:**
1. Open Task Scheduler
2. Find: `EA Tutorial Hub - Server`
3. Status should show: "Ready"

**Run Test:**
1. Right-click the task
2. Select "Run"
3. Terminal opens
4. Flask starts successfully

### After Reboot

**Test Auto-Start:**
1. Restart server PC
2. Wait 30 seconds after login
3. Flask terminal should appear automatically
4. Or check from another PC: `http://[SERVER_IP]:5000`

---

## ⚙️ Viewing Active Task

### Check What's Running

```powershell
# List all scheduled tasks
Get-ScheduledTask

# Filter for EA tasks
Get-ScheduledTask | Where-Object {$_.TaskName -like "*EA*"}

# Get detailed info
Get-ScheduledTask "EA Tutorial Hub - Server" | Get-ScheduledTaskInfo
```

---

## 🛠️ Troubleshooting Auto-Start

### Task Not Running

**Check 1: Task Scheduler Status**
```powershell
Get-ScheduledTask "EA Tutorial Hub - Server" | Format-List
```

**Check 2: Last Result Code**
- In Task Scheduler, click task
- Look at "Last Run Result"
- `0x0` = Success
- Other codes indicate errors

**Check 3: Event Viewer**
1. Press `Win+R`
2. Type: `eventvwr.msc`
3. Go: Windows Logs > System
4. Look for errors from Task Scheduler

### Python Not Found

**Error:** `The system cannot find the file specified`

**Fix:**
1. Verify Python path:
   ```powershell
   dir "C:\Users\[YourUsername]\.venv\Scripts\python.exe"
   ```
2. Use full path in Task Scheduler
3. No quotes in "Program/script" field
4. Quotes OK in "Arguments" field

### Permission Denied

**Error:** `Access denied` or `Failed to execute`

**Fix:**
1. Run Task Scheduler as Administrator
2. Set task to "Run with highest privileges"
3. Restart PC

### Port Already in Use

**Error:** `Address already in use`

**Fix:**
1. Check if multiple instances running:
   ```powershell
   tasklist | findstr python
   ```
2. Kill all instances:
   ```powershell
   taskkill /F /IM python.exe
   ```
3. Set Task Scheduler: "If the task is already running, do not start a new instance"

---

## 📊 Task Scheduler Status Dashboard

### Quick Check Command

```powershell
# Create a status checker
$task = Get-ScheduledTask "EA Tutorial Hub - Server"
$info = Get-ScheduledTaskInfo $task

Write-Host "EA Tutorial Hub - Auto-Start Status:"
Write-Host "===================================="
Write-Host "Status: $($task.State)"
Write-Host "Last Run: $($info.LastRunTime)"
Write-Host "Last Result: $($info.LastTaskResult)"
Write-Host "Next Run: $($info.NextRunTime)"
```

---

## 🔐 Security Considerations

### Auto-Start Best Practices

1. **Service Account:**
   - Task runs under SYSTEM account
   - No user login required
   - Perfect for 24x7 operation

2. **Port Access:**
   - Port 5000 open to local network
   - Still requires login to use application
   - Firewall rules applied

3. **Process Isolation:**
   - Python runs isolated
   - Limited memory/CPU usage
   - Can be monitored/limited

---

## 📖 Disabling Auto-Start

### Temporary Disable

```powershell
Disable-ScheduledTask -TaskName "EA Tutorial Hub - Server"
```

### Re-enable

```powershell
Enable-ScheduledTask -TaskName "EA Tutorial Hub - Server"
```

### Delete Task

```powershell
Unregister-ScheduledTask -TaskName "EA Tutorial Hub - Server" -Confirm:$false
```

Or in GUI:
1. Task Scheduler
2. Right-click task
3. Select "Delete"

---

## 📋 Uninstall/Cleanup

### Complete Removal of Auto-Start

1. **Delete scheduled task:**
   ```powershell
   Unregister-ScheduledTask -TaskName "EA Tutorial Hub - Server" -Confirm:$false
   ```

2. **Delete startup shortcut:**
   ```powershell
   Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\run_server.bat - Shortcut.lnk"
   ```

3. **Manual check:**
   - Task Scheduler: No EA tasks
   - Startup folder: No EA shortcuts

---

## ✅ Verification Checklist

Before considering auto-start complete:

- [ ] Task created in Task Scheduler
- [ ] Task status: "Ready"
- [ ] Last Run Result: "0x0"
- [ ] Manual test successful (Right-click > Run)
- [ ] Reboot test successful
- [ ] Access from network PC after reboot
- [ ] Terminal visible showing Flask running
- [ ] No error messages

---

## 🎯 Common Configurations

### Configuration A: Headless Server
- [ ] Task Scheduler method
- [ ] Run with highest privileges
- [ ] No terminal visible (optional: wrap in PowerShell to keep alive)

### Configuration B: Visible Terminal
- [ ] Startup folder method
- [ ] Terminal window visible
- [ ] Can minimize but not close

### Configuration C: Unattended Operation
- [ ] Task Scheduler
- [ ] All auto-recovery options enabled
- [ ] UPS backup power
- [ ] Monthly manual restarts

---

## 🔗 Related Resources

- Main guide: `NETWORK_DEPLOYMENT_GUIDE.md`
- Operations guide: `SERVER_OPERATIONS_GUIDE.md`
- Quick start: `24X7_QUICK_START.md`
- Setup script: `server_setup.py`
- Launcher batch: `run_server.bat`

---

## 📞 Quick Reference

```powershell
# View task details
Get-ScheduledTask "EA Tutorial Hub - Server" | Format-List

# Test run task
(Get-ScheduledTask "EA Tutorial Hub - Server").Actions

# Check execution history
Get-WinEvent -Path "C:\Windows\System32\winevt\Logs\System.evtx" -FilterXPath "*[System[Provider[@Name='Microsoft-Windows-TaskScheduler/Operational']]]" | Select-Object TimeCreated, Message | head -20

# Disable task temporarily
Disable-ScheduledTask -TaskName "EA Tutorial Hub - Server"

# Enable task
Enable-ScheduledTask -TaskName "EA Tutorial Hub - Server"

# Change task settings
Get-ScheduledTask "EA Tutorial Hub - Server" | Stop-ScheduledTask
# Then recreate with new settings
```

---

## 🎉 You're Done!

Your EA Tutorial Hub is now set up for:

✅ Automatic startup on PC boot
✅ 24x7 continuous operation
✅ Network access from any PC
✅ Auto-recovery if crashes
✅ No manual startup needed

---

**Your application is now truly 24x7 ready!**

*Last Updated: December 21, 2025*
*Version: 1.0*
