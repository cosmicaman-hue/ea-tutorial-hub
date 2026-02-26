# Session and Personalization Fixes

## Issues Identified:

### 1. Session Switching Between Users
**Root Causes:**
- Missing session cookie security configuration
- localStorage persists across users on shared devices
- No localStorage cleanup on logout
- Default role fallback to 'student'

### 2. Data Not Personalized for Students
**Root Cause:**
- All students see the full scoreboard with all students
- No filtering based on logged-in user
- Students should only see their own data

### 3. Missing Session Configuration
**Root Cause:**
- No SESSION_COOKIE_HTTPONLY setting
- No SESSION_COOKIE_SAMESITE setting
- No PERMANENT_SESSION_LIFETIME setting

## Fixes to Apply:

### Fix 1: Add Proper Session Configuration
### Fix 2: Clear localStorage on Logout
### Fix 3: Filter Scoreboard Data for Students
### Fix 4: Add Student Profile Endpoint
