# 🚀 24x7 Network Deployment - Complete Checklist

## 📋 Pre-Deployment Checklist

### On the Server PC (The PC running 24x7)

- [ ] **Hardware Ready**
  - [ ] Server PC selected (will run continuously)
  - [ ] Connected to WiFi network
  - [ ] Power supply reliable (or UPS available)
  - [ ] Minimum 2GB RAM available
  - [ ] At least 5GB free disk space

- [ ] **Software Ready**
  - [ ] Windows 10/11 with latest updates
  - [ ] Python 3.10+ installed
  - [ ] Git installed (recommended)
  - [ ] Web browser available (Chrome/Firefox/Edge)

- [ ] **Application Preparation**
  - [ ] Application folder ready (`C:\Users\[YourUsername]\Desktop\Project EA`)
  - [ ] Read: `README.md`
  - [ ] Read: `NETWORK_DEPLOYMENT_GUIDE.md`
  - [ ] Read: `SERVER_OPERATIONS_GUIDE.md`

---

## ✅ Quick Setup (15-30 minutes)

### Step 1: Initial Server Setup (First Time Only)

On the server PC, open PowerShell and run:

```powershell
cd "C:\Users\[YourUsername]\Desktop\Project EA"
python server_setup.py
```

This will:
- ✅ Check Python installation
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Create launcher scripts
- ✅ Configure firewall

**Expected output:** "Setup Complete! ✅"

### Step 2: Start the Server

Choose one method:

**Method A: Easiest (Recommended for Daily Use)**
```bash
Double-click: run_server.bat
```

**Method B: PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
python run.py
```

**Method C: Direct Command**
```bash
python run.py
```

**Expected output:**
```
 * Running on http://0.0.0.0:5000
 * Debugger is active!
 * Press CTRL+C to quit
```

### Step 3: Get Your Server IP

On the server PC, open PowerShell:

```powershell
ipconfig
```

Look for "IPv4 Address" in WiFi adapter section. Example: `192.168.0.163`

### Step 4: Access from Another PC

On ANY other PC on your WiFi network:

1. Open web browser
2. Go to: `http://[YOUR_SERVER_IP]:5000`
3. You should see the login page

**Example:** `http://192.168.0.163:5000`

### Step 5: Login and Test

Use default credentials:
```
Username: Admin
Password: admin123
```

Then verify:
- [ ] Dashboard loads
- [ ] Can navigate pages
- [ ] No error messages

**✅ Done! Your server is now accessible 24x7**

---

## 🎯 Setup for Auto-Start on Boot (Optional but Recommended)

### For Truly 24x7 Operation

### Option A: Windows Task Scheduler (Easy & Reliable)

1. **Open Task Scheduler:**
   - Press `Win+R`
   - Type: `taskschd.msc`
   - Press Enter

2. **Create Task:**
   - Right-click "Task Scheduler Library"
   - Click "Create Basic Task..."
   - Name: `EA Tutorial Hub - Server`
   - Description: `Starts the Flask application on system startup`

3. **Set Trigger:**
   - Trigger tab
   - Click "New..."
   - Select "At system startup"
   - Click OK

4. **Set Action:**
   - Action tab
   - Click "New..."
   - Program: `C:\Users\[YourUsername]\.venv\Scripts\python.exe`
   - Arguments: `run.py`
   - Start in: `C:\Users\[YourUsername]\Desktop\Project EA`
   - Click OK

5. **Set Options:**
   - General tab
   - Check: "Run with highest privileges"
   - Check: "Run whether user is logged in or not"
   - Click OK

6. **Finish:**
   - Check "Open the Properties dialog"
   - Go to Conditions tab
   - Uncheck "Stop if the computer switches to battery power" (if on laptop)
   - Click OK

**✅ Server will now auto-start on PC boot!**

### Option B: Startup Folder (Simple)

1. **Create shortcut:**
   - Right-click `run_server.bat`
   - Select "Create shortcut"

2. **Move to Startup folder:**
   - Press `Win+R`
   - Type: `shell:startup`
   - Press Enter
   - Move the shortcut here

**✅ Server will auto-start on PC boot!**

---

## 📊 Monitoring & Maintenance

### Daily Checks (2 minutes)

```
Every morning:
☐ Check PC is on
☐ Terminal window open (or check Task Scheduler)
☐ Visit http://[SERVER_IP]:5000 from another PC
☐ Should see login page
```

### Weekly Maintenance (10 minutes)

```
Once per week:
☐ Restart server (Ctrl+C, then restart)
☐ Backup database: SERVER_OPERATIONS_GUIDE.md
☐ Check no error messages in terminal
☐ Verify at least one user can login
```

### Monthly Tasks (30 minutes)

```
Once per month:
☐ Restart server for system cleanup
☐ Check database file size (should be small, <50MB)
☐ Review activity logs in admin dashboard
☐ Clean old uploaded files if needed
```

---

## 🔐 Default Credentials

Keep these safe:

```
Admin Account:
  Username: Admin
  Password: admin123

Teacher Account:
  Username: Teacher
  Password: teacher123

Student Account:
  Username: EA24C001
  Password: student123

⚠️ IMPORTANT: Change these passwords in production!
Edit: app/utils/ai_quiz_generator.py (see instructions in admin panel)
```

---

## 🌐 Network Access URLs

After server is running at `http://192.168.0.163:5000`:

| Page | URL |
|------|-----|
| **Main/Login** | `http://192.168.0.163:5000` |
| **Dashboard** | `http://192.168.0.163:5000/dashboard` |
| **Admin Panel** | `http://192.168.0.163:5000/admin/dashboard` |
| **Quizzes** | `http://192.168.0.163:5000/quiz` |
| **Notes** | `http://192.168.0.163:5000/notes` |
| **Profile** | `http://192.168.0.163:5000/profile` |

---

## ⚡ Troubleshooting Quick Reference

### Problem: Can't connect from other PC

**Checklist:**
```
1. Is server PC connected to WiFi? ☐
2. Is other PC on same WiFi network? ☐
3. Is Python application running? ☐
   - Check: Terminal shows "Running on..."
4. Correct IP address? ☐
   - Run on server PC: ipconfig
5. Can you ping server? ☐
   - From other PC: ping 192.168.0.163
6. Try localhost on server PC: ☐
   - http://localhost:5000
```

If still failing, see: `NETWORK_DEPLOYMENT_GUIDE.md` → Troubleshooting section

### Problem: Server keeps crashing

**Quick Fix:**
1. Run `network_setup.bat`
2. Choose option "7. Restart Server"
3. Or restart server PC

### Problem: Port 5000 already in use

**Fix:**
```powershell
netstat -ano | findstr :5000
taskkill /PID [PID_NUMBER] /F
python run.py
```

### Problem: Database error

**Quick Fix:**
1. Stop server: `Ctrl+C`
2. Delete database:
   ```powershell
   Remove-Item "instance\ea_tutorial.db"
   ```
3. Restart: `python run.py`

---

## 📱 Multi-Device Support

Your application will work on:

| Device | Browser | Status |
|--------|---------|--------|
| Desktop PC | Chrome | ✅ Supported |
| Laptop | Firefox | ✅ Supported |
| Smartphone | Safari | ✅ Supported |
| Tablet | Edge | ✅ Supported |
| Smart TV | Chrome | ✅ Supported |

**Just use:** `http://[SERVER_IP]:5000`

---

## 🔒 Security Notes

### Already Secured:
- ✅ Login authentication required
- ✅ User roles (Admin/Teacher/Student)
- ✅ Session management
- ✅ Database validation

### Optional Enhancements:
- Change default passwords (recommended)
- Restrict to local network only
- Use HTTPS (requires setup)
- Regular database backups

---

## 📞 Help & Support

### If Something Goes Wrong:

**Check these files first:**

1. `NETWORK_DEPLOYMENT_GUIDE.md` - Initial setup help
2. `SERVER_OPERATIONS_GUIDE.md` - Daily operation & issues
3. `README.md` - Project overview
4. `PHASE_5_QUICK_START.md` - Feature overview

### Quick Command Reference:

```powershell
# Activate environment
.\.venv\Scripts\Activate.ps1

# Start server
python run.py

# Stop server
Ctrl+C

# Check IP
ipconfig

# Check port
netstat -ano | findstr :5000

# Find process using port
netstat -ano | findstr :5000

# Kill process
taskkill /PID [PID] /F

# Backup database
Copy-Item "instance\ea_tutorial.db" "instance\ea_tutorial.db.backup"

# Reset database
Remove-Item "instance\ea_tutorial.db"
```

---

## ✨ Performance Tips

### For Smooth 24x7 Operation:

1. **Keep PC cool:**
   - Ensure adequate ventilation
   - Monitor CPU/RAM usage

2. **Stable power:**
   - Use UPS if possible
   - Disable sleep mode

3. **Network stability:**
   - WiFi 5GHz for better speed
   - WiFi extender if signal weak
   - Check for interference

4. **Server resources:**
   - Close unnecessary applications
   - Monitor disk space
   - Restart weekly (recommended)

---

## 📅 Implementation Timeline

### Week 1: Setup
- Day 1: Install Python, run server_setup.py
- Day 2: Test on server PC
- Day 3: Test from other PCs
- Day 4-7: Verify stability

### Week 2: Stabilization
- Monitor for any issues
- Restart server daily (first week)
- Create backups
- Document any errors

### Week 3+: Production
- Server should run reliably
- Restart once per week
- Monitor occasionally
- Backup data regularly

---

## ✅ Final Checklist Before Going 24x7

Before leaving your server running, verify:

- [ ] Server PC has power connected
- [ ] PC is not set to sleep/hibernate
- [ ] Windows firewall allows Python
- [ ] Application tested from 2+ other devices
- [ ] Database backed up
- [ ] Admin credentials changed (optional but recommended)
- [ ] No error messages in server terminal
- [ ] Server IP documented somewhere
- [ ] All users have login credentials
- [ ] Monitor checklist created and printed

---

## 🎉 Success Criteria

Your 24x7 deployment is successful when:

✅ Server PC turned on, stays on continuously
✅ Flask application runs automatically (Task Scheduler)
✅ Login page accessible from any PC on WiFi
✅ Multiple users can login simultaneously
✅ Database grows but stays under 100MB
✅ No crashes for at least 1 week
✅ Admins can access dashboard without errors
✅ Students can take quizzes and upload notes
✅ Teachers can grade and view submissions

---

## 🚀 What's Next?

### After 24x7 Setup:

1. **Usage Phase:**
   - Let students/teachers use the system
   - Gather feedback
   - Monitor performance

2. **Optional Enhancements:**
   - Change default passwords
   - Configure backup strategy
   - Setup monitoring alerts
   - Use Gunicorn for better performance

3. **Future Upgrades:**
   - Deploy to cloud (AWS, Azure, etc.)
   - Add SSL/HTTPS
   - Increase database size
   - Advanced monitoring

---

**Your EA Tutorial Hub is now ready for 24x7 operation!**

For detailed help, see the guides in the main folder.

---

*Last Updated: December 21, 2025*
*Version: 1.0*
