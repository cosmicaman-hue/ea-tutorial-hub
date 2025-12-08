# EA Tutorial Hub - Testing Guide

## Overview

This guide helps you test all features of EA Tutorial Hub to ensure everything is working correctly.

## Prerequisites

- Application running on http://localhost:5000
- Sample data initialized (run `python init_sample_data.py`)
- Browser with developer tools (F12)

## Test Accounts

Use these credentials for testing:

| Role | Login ID | Password |
|------|----------|----------|
| Admin | EA24A01 | admin123 |
| Teacher | EA24B01 | teacher123 |
| Student 1 | EA24C01 | student123 |
| Student 2 | EA24D02 | student123 |
| Student 3 | EA24E03 | student123 |

---

## 1. Authentication Tests

### 1.1 Login Test

**Test Case:** Valid Login
```
Steps:
1. Go to http://localhost:5000/auth/login
2. Enter login ID: EA24A01
3. Enter password: admin123
4. Click "Login"
Expected: Redirect to dashboard
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Invalid Password
```
Steps:
1. Go to http://localhost:5000/auth/login
2. Enter login ID: EA24A01
3. Enter password: wrong123
4. Click "Login"
Expected: Error message shown
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Invalid Login ID Format
```
Steps:
1. Go to http://localhost:5000/auth/register
2. Enter login ID: INVALID
3. Enter password: test123
4. Confirm password: test123
5. Click "Create Account"
Expected: Error message about format
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

### 1.2 Registration Test

**Test Case:** New User Registration
```
Steps:
1. Go to http://localhost:5000/auth/register
2. Enter login ID: EA24F10
3. Enter password: newuser123
4. Confirm password: newuser123
5. Click "Create Account"
Expected: Redirected to login page
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

### 1.3 Profile Completion Test

**Test Case:** Complete Profile on First Login
```
Steps:
1. Login with newly created EA24F10 account
2. Should automatically go to profile completion
3. Fill all required fields
4. Click "Complete Registration"
Expected: Profile saved, redirect to dashboard
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

---

## 2. Notes Management Tests

### 2.1 Teacher Note Upload

**Test Case:** Upload Valid PDF
```
Steps:
1. Login as teacher (EA24B01)
2. Navigate to "Upload Notes"
3. Create a test PDF file or use existing
4. Fill in details:
   - Title: "Mathematics Algebra Basics"
   - Subject: "Mathematics"
   - Class: "Class 9"
   - Description: "Test upload"
   - Tags: "algebra, equations"
5. Click "Upload Notes"
Expected: Success message, status pending
Actual: ________________
Status: ☐ PASS ☐ FAIL

Files to test:
- Valid PDF (expected: upload success)
- Document file (expected: upload fails)
- Oversized file (expected: upload fails)
```

### 2.2 Admin Note Approval

**Test Case:** Approve Pending Note
```
Steps:
1. Login as admin (EA24A01)
2. Navigate to "Pending Notes"
3. Review uploaded note
4. Click "Approve"
Expected: Note status changes to "Published"
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Reject Pending Note
```
Steps:
1. Login as admin (EA24A01)
2. Navigate to "Pending Notes"
3. Click "Reject"
Expected: Note deleted, file removed
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

### 2.3 Student Note Access

**Test Case:** Browse and Download Notes
```
Steps:
1. Login as student (EA24C01)
2. Navigate to "Notes"
3. Filter by subject: "Mathematics"
4. Filter by class: "Class 9"
5. Click on a note
6. Click "Download PDF"
Expected: PDF downloads to computer
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Search Notes
```
Steps:
1. Navigate to dashboard search
2. Type "algebra"
3. Select "Notes" category
4. Click Search
Expected: Show matching notes
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

---

## 3. Quiz System Tests

### 3.1 Quiz Functionality

**Test Case:** Start and Complete Quiz
```
Steps:
1. Login as student (EA24C01)
2. Navigate to "Quizzes"
3. Choose "Mathematics - Algebra Basics"
4. Click "Start Quiz"
5. Answer all 5 questions:
   - Q1: Select option B
   - Q2: Select option A
   - Q3: Select True
   - Q4: Select option C
   - Q5: Select option B
6. Click "Submit Quiz"
Expected: Results page shows 100%
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Quiz Timer
```
Steps:
1. Start a quiz
2. Observe timer counting down
3. Wait for timer to near completion
Expected: Timer updates every second
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Quiz Retake
```
Steps:
1. Complete a quiz
2. On results page, click "Retake Quiz"
3. Answer same questions differently
4. Submit
Expected: New attempt recorded
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

### 3.2 Performance Tracking

**Test Case:** View Quiz Attempts
```
Steps:
1. Login as student
2. Navigate to "Quiz" → "My Attempts"
3. Review attempt history
Expected: All attempted quizzes listed
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

---

## 4. User Management Tests

### 4.1 Admin User Management

**Test Case:** Create New User
```
Steps:
1. Login as admin (EA24A01)
2. Navigate to "Manage Users" → "Create User"
3. Enter:
   - Login ID: EA24Z99
   - Password: newuser123
   - Role: Student
4. Click "Create User"
Expected: User created, appears in list
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Disable User Account
```
Steps:
1. In user list, find a user
2. Click "Disable" button
3. Try to login with that account
Expected: Login fails with error
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

### 4.2 User Roles

**Test Case:** Student Permissions
```
Steps:
1. Login as student (EA24C01)
Expected: Cannot access:
   - Admin panel
   - Upload notes
   - Create quizzes
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Teacher Permissions
```
Steps:
1. Login as teacher (EA24B01)
Expected: Can access:
   - Upload notes
   - View uploads
Cannot access:
   - Admin panel
   - User management
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Admin Permissions
```
Steps:
1. Login as admin (EA24A01)
Expected: Can access:
   - Admin panel
   - User management
   - Content approval
   - Settings
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

---

## 5. Profile Management Tests

### 5.1 Student Profile

**Test Case:** View Profile
```
Steps:
1. Login as student
2. Click profile icon → "My Profile"
Expected: All profile info displayed
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Edit Profile
```
Steps:
1. On profile page, click "Edit Profile"
2. Modify first name to "Updated"
3. Click "Save Changes"
Expected: Profile updated, confirmation shown
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

---

## 6. Search & Filter Tests

### 6.1 Notes Search

**Test Case:** Search by Subject
```
Steps:
1. Navigate to Notes
2. Click filter by subject
3. Select "Mathematics"
Expected: Only Math notes shown
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Search by Class
```
Steps:
1. Navigate to Notes
2. Click filter by class
3. Select "Class 9"
Expected: Only Class 9 notes shown
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Full Text Search
```
Steps:
1. Use search bar at top
2. Search for "algebra"
Expected: All matching notes shown
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

---

## 7. Database & Performance Tests

### 7.1 Data Persistence

**Test Case:** Data Survives Restart
```
Steps:
1. Create a new user (EA24X01)
2. Upload a note
3. Stop application (Ctrl+C)
4. Restart application (python run.py)
5. Login and check if data exists
Expected: All data preserved
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

### 7.2 Performance

**Test Case:** Page Load Time
```
Expected: < 2 seconds for all pages
Home: ______ seconds
Notes: ______ seconds
Quiz: ______ seconds
Admin: ______ seconds
Status: ☐ PASS ☐ FAIL
```

---

## 8. Browser Compatibility Tests

Test on different browsers:

**Chrome (Latest)**
- Notes upload: ☐ PASS ☐ FAIL
- Quiz timer: ☐ PASS ☐ FAIL
- Profile editing: ☐ PASS ☐ FAIL

**Firefox (Latest)**
- Notes upload: ☐ PASS ☐ FAIL
- Quiz timer: ☐ PASS ☐ FAIL
- Profile editing: ☐ PASS ☐ FAIL

**Safari (Latest)**
- Notes upload: ☐ PASS ☐ FAIL
- Quiz timer: ☐ PASS ☐ FAIL
- Profile editing: ☐ PASS ☐ FAIL

**Edge (Latest)**
- Notes upload: ☐ PASS ☐ FAIL
- Quiz timer: ☐ PASS ☐ FAIL
- Profile editing: ☐ PASS ☐ FAIL

---

## 9. Error Handling Tests

### 9.1 Invalid Input

**Test Case:** Empty Form Submission
```
Steps:
1. Go to registration page
2. Leave fields empty
3. Click "Create Account"
Expected: Validation error shown
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** SQL Injection Attempt
```
Steps:
1. Try to enter malicious SQL in search
2. Observe if escaped properly
Expected: No SQL injection executed
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

### 9.2 File Upload Errors

**Test Case:** Upload Non-PDF File
```
Steps:
1. Try to upload .doc file as PDF
Expected: File type error shown
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

**Test Case:** Upload Oversized File
```
Steps:
1. Try to upload file > 50 MB
Expected: Size error shown
Actual: ________________
Status: ☐ PASS ☐ FAIL
```

---

## 10. Mobile Responsiveness Tests

**Test Case:** Responsive Design (use F12 to test mobile view)

**Mobile View (320px width)**
- Navigation: ☐ PASS ☐ FAIL
- Forms: ☐ PASS ☐ FAIL
- Notes list: ☐ PASS ☐ FAIL
- Quiz questions: ☐ PASS ☐ FAIL

**Tablet View (768px width)**
- Navigation: ☐ PASS ☐ FAIL
- Forms: ☐ PASS ☐ FAIL
- Notes list: ☐ PASS ☐ FAIL
- Quiz questions: ☐ PASS ☐ FAIL

---

## Test Summary

```
Total Test Cases: ______
Passed: ______
Failed: ______
Success Rate: ______%

Issues Found:
1. ____________________
2. ____________________
3. ____________________

Status: ☐ READY FOR DEPLOYMENT
```

---

## Quick Smoke Test (5 Minutes)

```bash
# Run this for a quick test
1. python run.py
2. Open http://localhost:5000
3. Login as EA24A01 / admin123
4. Check dashboard loads
5. Upload a PDF note
6. Navigate to a quiz
7. Answer quiz questions
8. Logout

Expected: All pages load without errors
```

---

**Testing Completed By:** _________________
**Date:** _________________
**Signature:** _________________
