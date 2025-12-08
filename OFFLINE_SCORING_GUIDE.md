# 📱 EA Tutorial Hub - Offline Scoring System

## Overview

The Student Scoring System now comes with **two versions**:

1. **Online Version** - Flask-based, uses database, requires server
2. **Offline Version** - Standalone HTML, uses localStorage, works anywhere

Both versions sync seamlessly and support the same features.

---

## 🎯 Offline Version Features

### ✅ Complete Functionality
- ➕ Add/Edit/Delete Students
- 📊 Track Points, Stars, and Vetos
- 🎓 Manage Extended Student Profiles
- 📈 View Rankings and Leaderboards
- 📅 Month-based Data Navigation
- 🔍 Search and Filter Students
- 📤 Export Data to Excel/JSON
- 📥 Import Data from Excel/JSON
- 💾 Automatic Data Persistence
- ⚡ Zero Internet Required

### 📱 Access Points

**Online (with internet):**
```
http://127.0.0.1:5000/scoreboard/          (requires login)
http://192.168.x.x:5000/scoreboard/        (network access)
```

**Offline (no login needed):**
```
http://127.0.0.1:5000/scoreboard/offline   (no login required)
file:///path/to/offline_scoreboard.html    (direct file access)
```

---

## 💾 Data Storage

### Browser Storage
- **Technology**: HTML5 localStorage
- **Capacity**: ~5-10 MB per domain
- **Persistence**: Survives browser restart
- **Security**: Domain-specific, cannot access other sites

### Storage Structure
```javascript
{
  "students": [
    {
      "id": 1707150000000,
      "roll_number": "EA24A01",
      "full_name": "Ayush Gupta",
      "class_name": "4",
      "group": "A",
      "profile_data": {
        "fatherName": "Rajesh Gupta",
        "motherName": "Priya Gupta",
        "dateOfBirth": "2008-05-15",
        "bloodGroup": "O+",
        ...
      }
    }
  ],
  "points": [
    {
      "id": 1707150000001,
      "student_id": 1707150000000,
      "date": "2026-02-05",
      "points": 85,
      "stars": 1,
      "vetos": 0,
      "notes": "Good performance"
    }
  ]
}
```

---

## 🔄 Syncing Between Versions

### Export from Offline → Import to Online
1. Open **Offline Version** → ⚙️ Settings
2. Click **📥 Export Data**
3. Saves JSON file to downloads
4. Open **Online Version** → Import Excel/Data
5. Upload the JSON file

### Export from Online → Download for Offline
1. Open **Online Version** → Admin Panel
2. Export student data
3. Save JSON file
4. Open **Offline Version** → ⚙️ Settings
5. Click **📤 Import Data** → Upload file

---

## 🚀 How to Use Offline Version

### Opening the Application

**Option 1: Via Web Browser**
```
1. Make sure Flask is running: python run.py
2. Visit: http://127.0.0.1:5000/scoreboard/offline
3. No login required
4. Fully functional offline
```

**Option 2: Direct File Access**
```
1. Open this file in browser:
   C:\Users\sujit\Desktop\Project EA\app\static\offline_scoreboard.html
2. Works completely offline
3. No server needed
```

**Option 3: Share with Others**
```
1. Send the file offline_scoreboard.html
2. They can open it in any browser
3. Each browser gets its own data storage
```

### Adding Students

```
1. Click "➕ Add Student"
2. Enter:
   - Roll Number (e.g., EA24A01)
   - Full Name
   - Class (3-10)
   - Group (A, B, C, D)
3. Click "✓ Add Student"
4. Data saved instantly to browser
```

### Recording Points

```
1. Click "⭐ Add Points"
2. Select Student
3. Enter Date
4. Enter Points (0-100)
5. Enter ⭐ Stars (recognition)
6. Enter 🚫 Vetos (penalties)
7. Optional: Add notes
8. Click "✓ Save Points"
```

### Editing Student Profile

```
1. Click on student name in scoreboard
2. Fills modal with existing data
3. Update any fields:
   - Personal: Father/Mother name, DOB, Blood group
   - Contact: Phone, Email, Address
   - Academic: Admission date, Academic year
4. Click "✓ Save Profile"
```

### Importing from Excel

```
1. Prepare Excel file with columns:
   Roll | Name | Class | 2026-02-01 | 2026-02-02 | ...
2. Save as .xlsx
3. Click "📊 Import Excel"
4. Select file
5. Data imports and merges automatically
```

### Filtering Data

**By Date:**
- Use "Date From" and "Date To" pickers
- Or click month tabs: [Feb 2026] [Jan 2026] [Dec 2025] [Nov 2025]

**By Class/Group:**
- Select from dropdown filters
- Instantly filters table

**By Search:**
- Type student name or roll number
- Real-time search results

---

## 📊 Ranking System

### Score Calculation
```
Net Score = Points + (Stars × 10) - (Vetos × 5)
```

### Medals
- 🥇 **Gold** - Rank 1 (yellow)
- 🥈 **Silver** - Rank 2 (gray)
- 🥉 **Bronze** - Rank 3 (orange)
- 🔹 **Blue** - Rank 4+ (blue)

---

## 💾 Data Management

### Export Data
```
1. ⚙️ Settings → 📥 Export Data
2. Downloads as: ea_scoring_backup_YYYY-MM-DD.json
3. Keep backups regularly
4. Can import later to restore
```

### Import Data
```
1. ⚙️ Settings → 📤 Import Data
2. Select previously exported .json file
3. Merges with existing data
4. No data loss
```

### Backup Best Practices
```
✓ Export weekly
✓ Store backups in cloud (Google Drive, Dropbox)
✓ Keep 4-5 recent backups
✓ Test import before deleting local data
```

---

## ⚠️ Important Notes

### Data Persistence
- **Browser-Specific**: Each browser has separate storage
- **Device-Specific**: Data not synced across devices
- **Clear Cache Warning**: Clearing browser cache deletes data
- **Backup First**: Always backup before clearing cache

### Browser Compatibility
✅ Chrome/Edge
✅ Firefox
✅ Safari
✅ Mobile browsers (Chrome, Safari, Firefox)

### Limitations
- Max ~5-10 MB storage (handles ~10,000 records)
- Requires localStorage enabled
- Works on HTTPS and HTTP
- Cannot sync with server automatically

---

## 🔒 Security & Privacy

- **Local Storage**: Data stored in browser only
- **No Upload**: Data never sent to server
- **No Tracking**: No analytics or monitoring
- **Privacy**: Your data stays on your device
- **Export Control**: You control all data movement

---

## 🆘 Troubleshooting

### Data Not Saving
```
Problem: Added students but they disappeared
Solution:
1. Check if localStorage is enabled
2. Try incognito/private mode
3. Close all other tabs with same app
```

### Can't Import Excel
```
Problem: File not importing
Solution:
1. Ensure .xlsx format (not .xls)
2. Check first row has headers: Roll, Name, Class
3. Dates must be YYYY-MM-DD format
4. Numbers only in data columns
```

### Lost Data
```
Problem: Data was cleared accidentally
Solution:
1. Check if you have export JSON backup
2. Settings → Import Data → Select backup file
3. Or re-add data manually
```

### Sync Issues Between Versions
```
Problem: Online and offline data different
Solution:
1. Export from one version
2. Import to another version
3. Latest version wins (manual merge)
```

---

## 📱 Mobile Usage

### Phone/Tablet
1. Open: `http://192.168.x.x:5000/scoreboard/offline`
2. Bookmark for quick access
3. Works offline on device
4. Full functionality on mobile

### Offline on Mobile
```
1. Open offline version in Chrome
2. Menu → "Install app" / "Add to home"
3. Works like native app
4. Complete offline access
```

---

## 🔄 Data Flow

```
Online Version (DB)
        ↓ Export
    JSON File
        ↓ Import
Offline Version (localStorage)
        ↓ Export
    JSON File
        ↓ Import
    Back to Online
```

---

## 📋 Excel Format Example

```
Roll         | Name      | Class | 2026-02-01 | 2026-02-02 | 2026-02-03
EA24A01      | Ayush     | 4     | 85         | 90         | 88
EA24A02      | Ayat      | 4     | 92         | 88         | 91
EA24B01      | Pari      | 4     | 78         | 82         | 80
EA24B02      | Rahul     | 4     | 88         | 85         | 90
EA24C01      | Priya     | 5     | 95         | 92         | 94
```

**Requirements:**
- First row MUST have headers
- Column names: Roll, Name, Class (or variations)
- Date columns: YYYY-MM-DD format
- Save as .xlsx
- One student per row

---

## 🎯 Use Cases

### Scenario 1: Classroom (No Internet)
```
1. Open offline version on laptop
2. Teachers record points during class
3. Automatic rankings displayed
4. Export data at end of day
5. Sync to server when internet available
```

### Scenario 2: Multiple Devices
```
1. Record data on phone (offline)
2. Export data from phone
3. Import on laptop (online version)
4. Sync to server database
```

### Scenario 3: Backup & Recovery
```
1. Daily export at end of day
2. Store in cloud drive
3. If data lost, import backup
4. System restored instantly
```

---

## 🚀 Quick Start

```
1. Open: http://127.0.0.1:5000/scoreboard/offline
2. Click "➕ Add Student"
3. Add 3-4 students
4. Click "⭐ Add Points"
5. Record some scores
6. View rankings automatically
7. Export data to backup
8. You're ready!
```

---

## 📞 Support

**For Technical Issues:**
- Check browser console (F12)
- Try clearing cache and reload
- Test in different browser
- Export backup if experiencing issues

**For Feature Requests:**
- The system uses localStorage
- Maximum storage ~5-10 MB
- For more storage, use online version

---

## ✅ Offline System Checklist

- [x] Add/Edit/Delete Students
- [x] Record Points, Stars, Vetos
- [x] Extended Student Profiles
- [x] Month-based Navigation
- [x] Search and Filtering
- [x] Automatic Ranking
- [x] Excel Import
- [x] JSON Export/Import
- [x] Data Persistence
- [x] Mobile Responsive
- [x] No Internet Required
- [x] No Login Required

---

**Version**: 1.0
**Last Updated**: February 5, 2026
**Status**: Production Ready

All data stays with you. No tracking. No sync without your permission.
