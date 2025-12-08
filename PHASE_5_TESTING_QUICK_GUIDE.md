# Phase 5 Features - Quick Testing Guide

## Pre-Testing Checklist

- [ ] Application running on http://127.0.0.1:5000
- [ ] Logged in as Admin (Admin/admin123)
- [ ] Database initialized with sample data
- [ ] New dependencies installed (requests, python-docx, PyPDF2)

---

## Test 1: Admin Dashboard Navigation

### Objective
Verify new navigation links appear on Admin Dashboard

### Steps
1. Login as Admin (Admin/admin123)
2. Go to Admin Dashboard
3. Look for new sections:
   - "AI-Powered Features" card
   - "Student Profiles" card
4. Verify buttons are visible:
   - "Create Quiz with AI"
   - "View AI Quizzes"
   - "View All Profiles"

### Expected Result
✅ All new sections and buttons visible and clickable

### Troubleshooting
- If buttons not visible, check admin role is assigned
- If links broken, verify blueprint registration in `app/__init__.py`

---

## Test 2: AI Quiz Creation Page Access

### Objective
Verify AI quiz creation page loads properly

### Steps
1. From Admin Dashboard, click "Create Quiz with AI"
2. Verify page loads with:
   - File upload area
   - Quiz title input
   - Number of questions slider (1-50)
   - Difficulty level dropdown
   - AI provider selector (OpenAI, Gemini, Claude)
   - "Generate Quiz" button
   - Instructions section

### Expected Result
✅ Page fully loaded with all form elements

### Troubleshooting
- If page shows 404, check `app/routes/quiz_ai.py` exists
- If form elements missing, check `app/templates/quiz/create_ai.html`

---

## Test 3: Sample Document Upload

### Objective
Test file upload functionality with valid document

### Steps
1. On AI Quiz Creation page
2. Create a test document:
   ```
   Save this as sample.txt:
   
   Chapter 1: Introduction to Biology
   Biology is the study of living organisms.
   There are many branches of biology.
   What is cell biology? Cell biology studies cells.
   What are organelles? Organelles are structures within cells.
   ```
3. Click upload area and select sample.txt
4. Verify file appears as selected

### Expected Result
✅ File selected and displayed in upload area

### Troubleshooting
- If upload fails, check file format (use TXT, PDF, DOCX, MD)
- If file size error, check file < 5MB

---

## Test 4: AI Provider Selection

### Objective
Verify all AI providers are selectable

### Steps
1. On AI Quiz Creation page
2. Click AI Provider dropdown
3. Verify options available:
   - OpenAI
   - Google Gemini
   - Anthropic Claude
4. Select each one to verify working

### Expected Result
✅ All three providers selectable

### Troubleshooting
- If dropdown empty, check `app/templates/quiz/create_ai.html` form field

---

## Test 5: Quiz Parameters Configuration

### Objective
Test parameter selections before generation

### Steps
1. Fill form with:
   - Title: "Biology Basics Quiz"
   - Questions: Slide to 15
   - Difficulty: Select "Medium"
   - Provider: Select "OpenAI"
2. Upload sample document (from Test 3)

### Expected Result
✅ All parameters accepted and set correctly

---

## Test 6: Student Profile Viewer Access

### Objective
Verify Profile Viewer page loads

### Steps
1. From Admin Dashboard, click "View All Profiles"
2. Verify page loads with:
   - 4 statistics cards (Total, Complete, Completion %, Incomplete)
   - Filter form (Search, Class, School, Gender, Sort)
   - Student list table
   - "Apply Filters" and "Export to CSV" buttons

### Expected Result
✅ Profile viewer page fully loaded with all elements

### Troubleshooting
- If page shows 404, check `app/routes/profile_viewer.py` exists
- If no students shown, check database has students

---

## Test 7: Student Filtering

### Objective
Test filter functionality

### Steps
1. On Profile Viewer page
2. In Search box, type student name or ID
3. Click "Apply Filters"
4. Verify results filtered correctly

### Expected Result
✅ Table shows only matching students

### Troubleshooting
- If no results, try different search term
- Clear search and try class/school filters

---

## Test 8: CSV Export

### Objective
Test profile export functionality

### Steps
1. On Profile Viewer page
2. Apply any filters (optional)
3. Click "Export to CSV" button
4. Verify download started
5. Open downloaded CSV file
6. Verify columns: ID, Name, Email, Class, School, Gender, Created, Last Login

### Expected Result
✅ CSV file downloaded and opens in spreadsheet app with correct data

### Troubleshooting
- If download fails, check browser download settings
- If CSV empty, verify students in database

---

## Test 9: View Student Profile Details

### Objective
Test detailed profile view

### Steps
1. On Profile Viewer page
2. Click "View" button for any student
3. Verify page shows:
   - Personal Information section
   - Contact Information section
   - Academic Information section
   - Account Status section
   - Recent Activities table (up to 20)
   - Quiz Attempts table (up to 10)

### Expected Result
✅ Detailed profile page fully loaded with all sections

### Troubleshooting
- If some sections empty, student data may not be complete
- Check database for student record

---

## Test 10: Profile Statistics API

### Objective
Test statistics endpoint

### Steps
1. Open browser console (F12)
2. Go to: http://127.0.0.1:5000/admin/profiles/api/stats
3. Verify JSON response shows:
   - by_class: distribution by class
   - by_school: distribution by school
   - by_gender: distribution by gender
   - total_students: count
   - complete_profiles: count
   - completion_percentage: percentage
   - inactive_students: count
   - no_login_students: count

### Expected Result
✅ JSON API returns valid statistics data

### Troubleshooting
- If 403 error, ensure Admin role
- If empty statistics, check database has students

---

## Test 11: Database Model Verification

### Objective
Verify Quiz model changes applied

### Steps
1. Open terminal
2. Enter Python shell:
   ```bash
   python
   ```
3. Run:
   ```python
   from app import db, create_app
   app = create_app()
   with app.app_context():
       from app.models.quiz import Quiz
       print(Quiz.__table__.columns.keys())
   ```
4. Verify output includes new columns:
   - ai_generated
   - ai_provider
   - source_document
   - created_by

### Expected Result
✅ All new columns present in Quiz model

### Troubleshooting
- If columns missing, database may need reset
- Delete `instance/ea_tutorial.db` and restart app to reinitialize

---

## Test 12: Form Validation

### Objective
Test form validation on AI Quiz creation

### Steps
1. On AI Quiz Creation page
2. Try submitting form WITHOUT:
   - File uploaded
   - Quiz title entered
   - Provider selected
3. Verify error messages appear

### Expected Result
✅ Form validation prevents submission with missing required fields

### Troubleshooting
- If no validation, check form validation in template/routes

---

## Test 13: Pagination

### Objective
Test pagination on profile list

### Steps (if > 20 students)
1. On Profile Viewer page
2. Scroll to bottom
3. Verify pagination controls (Previous, page numbers, Next)
4. Click "Next" to go to page 2
5. Verify students change
6. Click "Previous" to return to page 1

### Expected Result
✅ Pagination works correctly, showing 20 students per page

### Troubleshooting
- If pagination missing, check database has 20+ students
- If navigation broken, check pagination template

---

## Test 14: Access Control

### Objective
Verify only Admin can access Profile Viewer

### Steps
1. Logout from Admin account
2. Login as Teacher (Teacher/teacher123)
3. Try accessing: http://127.0.0.1:5000/admin/profiles/
4. Verify access denied or redirect to dashboard

### Expected Result
✅ Teacher cannot access Admin-only profile viewer

### Troubleshooting
- If Teacher can access, check role verification in `profile_viewer.py`

---

## Test 15: Sorting

### Objective
Test profile list sorting

### Steps
1. On Profile Viewer page
2. In Sort dropdown, select "Name"
3. Click "Apply Filters"
4. Verify table sorted by name (A-Z)
5. Repeat with "Class" and "Created Date"

### Expected Result
✅ Table correctly sorted by selected field

### Troubleshooting
- If sorting not working, check sort logic in `profile_viewer.py`

---

## Test Results Summary

| Test # | Feature | Status | Notes |
|--------|---------|--------|-------|
| 1 | Dashboard Navigation | [ ] | |
| 2 | AI Quiz Page Load | [ ] | |
| 3 | Document Upload | [ ] | |
| 4 | AI Provider Selection | [ ] | |
| 5 | Parameters Config | [ ] | |
| 6 | Profile Viewer Load | [ ] | |
| 7 | Student Filtering | [ ] | |
| 8 | CSV Export | [ ] | |
| 9 | Profile Details | [ ] | |
| 10 | Statistics API | [ ] | |
| 11 | Database Model | [ ] | |
| 12 | Form Validation | [ ] | |
| 13 | Pagination | [ ] | |
| 14 | Access Control | [ ] | |
| 15 | Sorting | [ ] | |

**Overall Status:** [ ] All Tests Passed

---

## Performance Testing (Optional)

### Large Dataset Test
1. Check application with 100+ students
2. Verify Profile Viewer still responsive
3. Test CSV export (should complete in < 5 seconds)
4. Verify pagination fast with many pages

### Document Processing Test
1. Test with 10-page PDF
2. Test with large DOCX file
3. Measure processing time
4. Typical: 30-60 seconds

---

## Known Limitations (By Design)

- Maximum file size: 5MB
- Maximum questions per quiz: 50
- Profiles per page: 20 (for performance)
- Activities shown: last 20
- Quiz attempts shown: last 10
- AI providers: 3 (OpenAI, Gemini, Claude)

---

## Next Steps After Testing

If all tests pass:
1. ✅ Add API keys to `.env` for production use
2. ✅ Create sample AI quizzes for demonstration
3. ✅ Train admin users on new features
4. ✅ Monitor first AI quiz generation in production
5. ✅ Gather user feedback for Phase 6

If tests fail:
1. ❌ Review error logs in terminal
2. ❌ Check error messages in browser console
3. ❌ Verify database initialized with sample data
4. ❌ Contact support with error details

---

## Support Commands

### Restart Application
```bash
cd "c:\Users\sujit\Desktop\Project EA"
.\.venv\Scripts\python.exe run.py
```

### Reset Database
```bash
# Delete database file (will be recreated)
rm instance/ea_tutorial.db
# Restart application
```

### Check Python Packages
```bash
pip list | findstr requests python-docx PyPDF2
```

### View Application Logs
- Check terminal output while running
- Check browser console (F12) for client-side errors

---

**Testing Version:** 1.0
**Last Updated:** January 2024
**Status:** Ready for Testing ✅
