# Phase 3 Testing Guide

## Pre-Testing Checklist

Before testing, ensure:
1. Application is running on http://localhost:5000
2. Database has been initialized with sample data
3. All code changes have been applied
4. No syntax errors in Python files

## Testing Scenarios

### 1. Admin Login Test

**Test Case: TC-1.1 - Admin Login with Fixed Username**
```
Steps:
1. Navigate to http://localhost:5000/auth/login
2. Enter Username: Admin
3. Enter Password: admin123
4. Click Login

Expected Result:
- Login successful
- Redirected to /admin/dashboard
- Admin dashboard displayed with stats
- Activity log shows login entry
```

**Test Case: TC-1.2 - Admin Dashboard Access**
```
Steps:
1. Login as Admin with credentials (Admin / admin123)
2. Access http://localhost:5000/admin/dashboard

Expected Result:
- Dashboard displays:
  - Total users count
  - Students count
  - Teachers count
  - Pending notes count
  - Recent activities section
- Admin controls visible:
  - Manage Users link
  - Create User Account link
  - Approve Notes link
  - Activity Log link
  - System Settings link
```

**Test Case: TC-1.3 - Activity Log Access**
```
Steps:
1. Login as Admin
2. Click "Activity Log" in admin menu or navigate to /admin/activity-log
3. View the activity log

Expected Result:
- Activity log page displays with:
  - Filter buttons for different action types
  - Table with recent activities
  - Columns: Timestamp, User, Action Type, Action, IP Address, Details
  - Pagination controls
- All login attempts visible in the log
```

### 2. Teacher Login Test

**Test Case: TC-2.1 - Teacher Login with Fixed Username**
```
Steps:
1. Navigate to http://localhost:5000/auth/login
2. Enter Username: Teacher
3. Enter Password: teacher123
4. Click Login

Expected Result:
- Login successful
- Redirected to /dashboard
- User dashboard displayed
- Profile shows "Teacher" role
- Activity log records successful login
```

**Test Case: TC-2.2 - Teacher Access to Features**
```
Steps:
1. Login as Teacher
2. Check navigation menu

Expected Result:
- Teacher can see:
  - Home, Notes, Quizzes navigation links
  - "Upload Notes" link (special for teacher/admin)
  - Profile menu with "Change Password" option
```

### 3. Student Login Test

**Test Case: TC-3.1 - Student Login with EA24 Format**
```
Steps:
1. Navigate to http://localhost:5000/auth/login
2. Enter Username: EA24C01
3. Enter Password: student123
4. Click Login

Expected Result:
- Login successful
- Redirected to /dashboard
- User dashboard displayed
- Activity log records successful login
```

**Test Case: TC-3.2 - Student Registration Validation**
```
Steps:
1. Navigate to http://localhost:5000/auth/register
2. Try to register with username "TestUser" (invalid format)
3. Click Register

Expected Result:
- Error message displayed: "Students must use EA24A01 format login ID"
- Registration rejected
```

**Test Case: TC-3.3 - Valid Student Registration**
```
Steps:
1. Navigate to http://localhost:5000/auth/register
2. Enter Username: EA24F04
3. Enter Password: test123456
4. Confirm Password: test123456
5. Click Register

Expected Result:
- Registration successful
- Flash message: "Registration successful! Please login."
- User directed to login page
- New account available for login
```

### 4. Password Management Tests

**Test Case: TC-4.1 - User Changes Own Password**
```
Steps:
1. Login with any valid user (e.g., EA24C01)
2. Click profile dropdown menu
3. Select "Change Password"
4. Enter current password: student123
5. Enter new password: newpass123
6. Confirm new password: newpass123
7. Click "Change Password"

Expected Result:
- Success message displayed
- Redirected to dashboard
- Activity log records "password_change" event
- User can login with new password on next attempt
```

**Test Case: TC-4.2 - Admin Resets User Password**
```
Steps:
1. Login as Admin
2. Navigate to Manage Users
3. Find user EA24C01
4. Click reset password button for that user
5. Enter new password: resetpass123
6. Click "Reset Password"

Expected Result:
- Success message: "Password reset for user EA24C01"
- Activity log records "password_reset_by_admin" event
- User can login with new password
- Password reset action shows admin's login_id in logs
```

**Test Case: TC-4.3 - Password Strength Validation**
```
Steps:
1. Login with any user
2. Navigate to Change Password
3. Try to enter password less than 6 characters (e.g., "pass")
4. Click Change Password

Expected Result:
- Error message: "Password must be at least 6 characters long"
- Password change rejected
```

**Test Case: TC-4.4 - Cannot Reuse Same Password**
```
Steps:
1. Login with EA24C01 (password: student123)
2. Change password to: newpass123
3. Immediately try to change password back to: student123
4. Try to use old password again

Expected Result:
- Should allow this as it's not the same as current
- But if set again to: newpass123
- Should reject with: "New password must be different from current password"
```

### 5. Activity Logging Tests

**Test Case: TC-5.1 - Failed Login Logging**
```
Steps:
1. Navigate to login page
2. Enter Username: Admin
3. Enter Password: wrongpassword
4. Click Login

Expected Result:
- Login fails with error message
- Activity log still records the attempt
- Admin can view failed attempts with "login_failed" action_type
```

**Test Case: TC-5.2 - Activity Log Filtering**
```
Steps:
1. Login as Admin
2. Navigate to Activity Log
3. Click "Login (X)" filter button
4. View filtered results

Expected Result:
- Only login activities displayed
- Count matches displayed number
- Other action types not shown
```

**Test Case: TC-5.3 - Activity Log Pagination**
```
Steps:
1. Login as Admin
2. Navigate to Activity Log
3. Generate multiple activities (by logins)
4. Navigate through pages using pagination

Expected Result:
- 50 items per page displayed
- Page numbers shown correctly
- Next/Previous buttons work
- Can jump to specific pages
```

### 6. User Management Tests

**Test Case: TC-6.1 - Admin Creates New Student**
```
Steps:
1. Login as Admin
2. Navigate to "Create User Account"
3. Enter Login ID: EA24G05
4. Enter Password: newstudent123
5. Select Role: student
6. Click Create

Expected Result:
- Success message displayed
- New user appears in user list
- New user can login with provided credentials
```

**Test Case: TC-6.2 - Admin Disables User Account**
```
Steps:
1. Login as Admin
2. Navigate to Manage Users
3. Find a user (e.g., EA24D02)
4. Click toggle status button
5. Try to login as that user

Expected Result:
- Account status shows as disabled
- User cannot login
- Error message: "Your account has been deactivated. Contact admin."
- Activity log records status change
```

### 7. Login Format Validation

**Test Case: TC-7.1 - Invalid Student Format Rejected**
```
Steps:
1. Try login with username: "Student01" (not EA format)
2. Try login with username: "Admin" as student role
3. Try login with username: "EA23A01" (year too low)

Expected Result:
- All rejected with format error
- Clear error message about correct format
```

**Test Case: TC-7.2 - Valid EA Format Accepted**
```
Steps:
1. Login with username: EA24Z99 (valid format)
2. Login with username: EA25A01 (future year)
3. Login with username: EA24T50 (valid variant)

Expected Result:
- All valid formats accepted if credentials correct
- Only rejected if password wrong or account doesn't exist
```

## Testing Checklist

**Security & Access Control:**
- [ ] Admin cannot see teacher-only features
- [ ] Student cannot access admin functions
- [ ] Guests cannot access protected pages
- [ ] Session expires properly on logout
- [ ] Failed logins don't create security gaps

**Data Integrity:**
- [ ] Activity logs accurately record all actions
- [ ] Password changes don't affect other user data
- [ ] User deletion cascades properly
- [ ] No orphaned records in database

**User Experience:**
- [ ] Error messages are clear and actionable
- [ ] Success messages confirm completed actions
- [ ] Navigation is intuitive
- [ ] Forms validate before submission
- [ ] Pagination works smoothly

**Performance:**
- [ ] Activity log loads quickly even with many entries
- [ ] Filter operations are responsive
- [ ] No database connection errors
- [ ] Page load times acceptable (<2 seconds)

## Known Test Credentials

Admin:
- Username: Admin
- Password: admin123

Teacher:
- Username: Teacher
- Password: teacher123

Students:
- Username: EA24C01, Password: student123
- Username: EA24D02, Password: student123
- Username: EA24E03, Password: student123

## Troubleshooting

### Issue: Login page shows validation error
**Solution:** Ensure username format is correct (Admin, Teacher, or EA24A01)

### Issue: Activity log not showing entries
**Solution:** Check database is initialized; run init_sample_data.py

### Issue: Password change fails
**Solution:** Verify current password is correct and new password is different

### Issue: Admin cannot see activity log link
**Solution:** Logout and login again; check admin role is set correctly

## Reporting Issues

Document any issues found including:
1. Test case that failed
2. Expected vs. actual result
3. Steps to reproduce
4. Screenshots/error messages
5. Database state (if relevant)

## Sign-Off

- Testing Date: _______________
- Tester Name: _______________
- All Tests Passed: Yes / No
- Issues Found: _______________

For any issues or questions, contact the development team.
