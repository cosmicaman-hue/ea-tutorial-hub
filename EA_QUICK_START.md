# ⚡ EXCEL ACADEMY - Quick Start Guide

## 🎯 Start Using in 3 Steps

### Step 1: Open the System
```
URL: http://127.0.0.1:5000/scoreboard/offline
Or: http://[your-server-ip]:5000/scoreboard/offline
```
✅ System loads immediately - no login required

### Step 2: View Current Scoreboard
```
1. You see the "Scoreboard" tab active by default
2. Select current month (e.g., "Feb 2026")
3. See all students ranked by score
4. Medals show top 3 performers
```

### Step 3: Start Recording Scores
```
1. Click "Record Score" tab
2. Select student name
3. Pick date
4. Enter points (can be negative)
5. Select month
6. Click "Save Score"
✅ Score appears in scoreboard immediately
```

---

## 📊 Main Screens Explained

### SCOREBOARD Tab 📊
**What it shows:**
- All students ranked by monthly total
- Daily scores for each date
- Search and filter options
- Performance statistics

**What to do:**
- Select different months to see past data
- Filter by class to see specific grades
- Search for individual students
- Click on student name for details

### RECORD SCORE Tab ➕
**What it does:**
- Records individual daily scores
- Supports positive/negative points
- Flexible date selection
- Optional notes for each score

**Quick entry:**
- Select student → date → points → save
- Takes 10 seconds per entry
- Bulk entry: Record one student per day

### STUDENTS Tab 👥
**What it shows:**
- List of all students
- Student details (roll, name, class, fees)
- Delete option for each student

**What to do:**
- Add new students before scoring them
- Remove students who left
- Edit student information
- View current roster

### RANKINGS Tab 🏆
**What it shows:**
- Monthly top performers
- Rankings with medals/positions
- Total scores per student
- Sorted automatically

**What to do:**
- Select month to view rankings
- Identify top performers
- See performance trends
- Award recognitions based on rankings

### TOOLS Tab 🔧
**What it shows:**
- Import/Export options
- Data backup tools
- Database management

**What to do:**
- Import from Excel files
- Export data for reports
- Backup data regularly
- Restore from backups

---

## 🎓 Using with Sample Data

### Pre-loaded Students:
- ✅ Ayush Gupta (EA24A01) - Class 4
- ✅ Abdul Arman (EA24A02) - Class 4
- ✅ Ayat Parveen (EA24A03) - Class 4
- ✅ Tanu Sinha (EA24A04) - Class 4
- ✅ Rashi (EA24A05) - Class 3
- ✅ Siddharth Mallik (EA24E01) - Class 3
- ✅ Sanaya Sinha (EA24E02) - Class 3
- ✅ Dhruv Mallick (EA25E03) - Class 5

### Try Recording Scores:
```
Example Entry:
- Student: Ayush Gupta
- Date: Today
- Points: 85
- Month: Feb 2026
- Notes: "Good performance"

Then click Scoreboard to see score updated!
```

---

## 📁 Importing Your Excel Data

### From EA STUDENT SCORE TALLY v5.5.xlsm:

**Method 1: Direct Import**
```
1. Click Tools tab
2. Click "Import Excel File"
3. Select your .xlsx file
4. Click Import
✅ Data loads automatically
```

**Method 2: Manual Entry**
```
1. Open your Excel file
2. Go to current month sheet
3. For each student:
   - Note: Roll No., Name, Class
   - Check daily scores
   - Go to "Record Score" tab
   - Enter each day's score manually
4. For bulk import, export your Excel as JSON first
```

### Excel Sheet Structure:
```
Column A: Roll No. (EA24A01)
Column B: Class (4)
Column C: Student Name (Ayush Gupta)
Column D+: Daily Scores (dates as headers)

Example:
| Roll No. | Class | Student Name | 2026-02-01 | 2026-02-02 | 2026-02-03 |
|----------|-------|--------------|------------|------------|------------|
| EA24A01  | 4     | Ayush Gupta  | 45         | 30         | 50         |
| EA24A02  | 4     | Tanu Sinha   | 40         | 35         | 45         |
```

---

## 💾 Backup Your Data

### Auto Backup:
✅ Automatically saved in browser storage
✅ Survives browser restart
✅ Lost only if cache is cleared

### Manual Backup (Recommended):
```
1. Click Tools tab
2. Click "Export as JSON"
3. Save file to your computer
4. Download completes: EA_Scoreboard_Backup.json
```

### Restore from Backup:
```
1. Click Tools tab
2. Click "Import JSON"
3. Select your backup file
4. Data restores immediately
```

---

## 🔍 Finding Information

### Find a Specific Student:
```
Scoreboard Tab → Search field → Type name
Results update instantly
```

### See Class Performance:
```
Scoreboard Tab → Filter by Class → Select class
Shows only students in that class
```

### Check Rankings:
```
Rankings Tab → Select month → View sorted list
Top 3 get medals, rest numbered
```

### Check Monthly Total:
```
Scoreboard Tab → Find student row → Last column
Yellow-highlighted number = total for month
```

---

## ⚙️ Common Tasks

### Add a New Student:
```
1. Students tab
2. Fill: Roll No., Name, Class, Fees (optional)
3. Click "Add Student"
✅ Appears in scoreboard
```

### Remove a Student:
```
1. Students tab
2. Find student row
3. Click "Delete"
4. Confirm deletion
✅ Student and scores removed
```

### Correct a Score:
```
Current system: Record again with correct amount
Method: Add negative score to offset, then add correct score
Example: Recorded 50, should be 30 → Add -20, then Add 0
```

### View Past Months:
```
Scoreboard tab → Click month button
Shows all students and scores for that month
Months available: Aug 2024 → Feb 2026+
```

---

## 🎨 Understanding the Colors

| Color | Meaning |
|-------|---------|
| 🔵 Blue | Primary interface, headers |
| 🟢 Green | Positive scores/success |
| 🔴 Red | Negative scores, delete action |
| 🟡 Yellow | Monthly totals, important |
| 🥇 Gold | Rank 1 (top scorer) |
| 🥈 Silver | Rank 2 |
| 🥉 Bronze | Rank 3 |

---

## 🚀 Tips & Tricks

### Bulk Scoring:
- Set default month first
- Record same student multiple days
- Use copy-paste in notes field

### Month Planning:
- Review previous month rankings
- Plan next month targets
- Track year-long trends

### Mobile Use:
- Works on tablets and phones
- Landscape for better table view
- Portrait for forms

### Data Safety:
- Export JSON weekly
- Keep backup files
- Multiple copies recommended

---

## ❓ Frequently Asked Questions

**Q: Can I access this offline?**
A: Yes! Once loaded, works with no internet.

**Q: Where is my data stored?**
A: On your device in browser storage, not on any server.

**Q: Will I lose data on browser restart?**
A: No, it stays in localStorage.

**Q: Can I export to Excel?**
A: Yes! Click Tools → Export as Excel

**Q: How many students can I add?**
A: 500+ comfortably, depends on device memory.

**Q: Can I undo a deletion?**
A: Only if you restore from a backup JSON file.

**Q: How do I use on different computers?**
A: Export JSON on first computer, import JSON on second.

**Q: Can I have multiple months open?**
A: Yes, switch between months anytime.

---

## 📞 Need Help?

1. **Check this guide** - Answer usually here
2. **Check main guide** - See EA_SCORING_SYSTEM_GUIDE.md
3. **Try sample data** - Test with pre-loaded students
4. **Export data** - Backup before trying advanced features

---

## 🎯 First Day Checklist

- [ ] Load system at http://127.0.0.1:5000/scoreboard/offline
- [ ] View sample scoreboard (already has data)
- [ ] Add your first student
- [ ] Record a test score
- [ ] View scoreboard with new score
- [ ] Export data as backup
- [ ] Bookmark the URL for quick access
- [ ] Share URL with team members

---

**System Ready: ✅**
**Data Safe: ✅**
**Offline Working: ✅**

**Start scoring now! →** Click any student to see options.

---

**Version**: 1.0 | **Date**: Feb 5, 2026 | **Status**: Production Ready
