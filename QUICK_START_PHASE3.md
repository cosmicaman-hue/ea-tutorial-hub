# Phase 3 Quick Start Guide - Updated

## New in Phase 3

✅ Fixed Admin and Teacher usernames  
✅ Enhanced password management system  
✅ Comprehensive activity logging  
✅ Admin monitoring dashboard  
✅ Improved security features

## 5-Minute Quick Start

### Step 1: Start the Application
```bash
cd "Project EA"
.venv\Scripts\activate  # Windows: activate venv
python init_sample_data.py  # Initialize database
python run.py  # Start Flask app
```

The application will be available at: **http://localhost:5000**

### Step 2: Login with Default Credentials

**Admin Login:**
- Open: http://localhost:5000/auth/login
- Username: `Admin`
- Password: `admin123`
- You'll see the Admin Dashboard with activity monitoring

**Teacher Login:**
- Username: `Teacher`
- Password: `teacher123`
- Access teaching features and content creation

**Student Login:**
- Username: `EA24C01`
- Password: `student123`
- Or use: `EA24D02` or `EA24E03` (same password)

### Step 3: Key Features to Try

#### As Admin:
1. Click **Admin Panel** in navigation
2. View **Activity Log** - See all user activities in real-time
3. Go to **Manage Users** - Reset passwords for any user
4. Check **Recent Activities** - See recent login attempts
5. Use **Change Password** (in user menu) - Change your admin password

#### As Teacher:
1. Click **Change Password** to set a new password
2. Navigate to **Upload Notes** to submit content
3. Check **Activity Log** to see your login history

#### As Student:
1. Complete profile on first login
2. Click **Change Password** to secure your account
3. Browse notes and take quizzes
4. Check your activity in admin logs (if admin checks)

## New Phase 3 Features

### 1. Fixed Usernames
- No more EA24A01 format for admin/teacher
- Use simple fixed names: **Admin** and **Teacher**
- Students still use EA24A01 format

### 2. Password Management
- All users can change their password: **User Menu → Change Password**
- Admins can reset passwords for any user: **Admin → Manage Users → Reset Password**
- Passwords require minimum 6 characters
- Track when passwords were last changed

### 3. Activity Monitoring
- Admin can view all activities: **Admin Panel → Activity Log**
- See login/logout times
- Track password changes
- Monitor file uploads
- View failed login attempts
- Filter by activity type

### 4. Security Improvements
- IP address tracking for all logins
- Timestamped activity logs
- Failed login recording
- User status management (activate/deactivate accounts)

## Important URLs

| Feature | URL | Role |
|---------|-----|------|
| Login | `/auth/login` | All |
| Register (Student) | `/auth/register` | Public |
| Change Password | `/auth/change-password` | All Logged-in |
| Admin Dashboard | `/admin/dashboard` | Admin |
| Activity Log | `/admin/activity-log` | Admin |
| Manage Users | `/admin/users` | Admin |
| Reset User Password | `/admin/users/<id>/reset-password` | Admin |
| Upload Notes | `/notes/upload` | Teacher/Admin |
| Browse Quizzes | `/quiz` | All |

## Default Test Accounts

```
┌─────────────────────────────────────────┐
│ ADMIN ACCOUNT                           │
├─────────────────────────────────────────┤
│ Username: Admin                         │
│ Password: admin123                      │
│ Role: System Administrator              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ TEACHER ACCOUNT                         │
├─────────────────────────────────────────┤
│ Username: Teacher                       │
│ Password: teacher123                    │
│ Role: Instructor                        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ STUDENT ACCOUNTS (Sample)               │
├─────────────────────────────────────────┤
│ Username: EA24C01 | Password: student123│
│ Username: EA24D02 | Password: student123│
│ Username: EA24E03 | Password: student123│
└─────────────────────────────────────────┘
```

## Admin Quick Tasks

### Check Who's Online
1. Go to **Admin Panel → Activity Log**
2. Filter by action type: **Login**
3. See recent successful logins

### Reset Student Password
1. Go to **Manage Users**
2. Find the student by login ID
3. Click **Reset Password**
4. Enter new password
5. Inform student of new password

### Deactivate a User Account
1. Go to **Manage Users**
2. Find the user
3. Click toggle status button
4. Account is now deactivated
5. User cannot login

### View Security Audit
1. Go to **Activity Log**
2. See all actions: logins, logouts, password changes
3. Sort by date and time
4. Check IP addresses for suspicious activity

## Student Quick Tasks

### Change Your Password
1. Click your username in top right
2. Select **Change Password**
3. Enter current password
4. Enter new password (6+ characters)
5. Confirm new password
6. Click **Change Password**

### Take a Quiz
1. From dashboard, click **Quizzes**
2. Select a quiz
3. Click **Start Quiz**
4. Answer questions
5. Submit and see results

### View Your Profile
1. Click your username → **My Profile**
2. Review/edit your information
3. Click **Save** if changes made

## Teacher Quick Tasks

### Upload PDF Notes
1. Click **Upload Notes** in navigation
2. Fill in title and description
3. Select subject and class level
4. Choose PDF file (max 50MB)
5. Click **Upload**
6. Admin will review and approve

### Change Password
1. Same as student process
2. Helps keep account secure

### View Your Uploads
1. Go to **Notes → My Uploads**
2. See status: Pending/Approved
3. Download or delete if pending

## Troubleshooting

### Forgot Password?
**For any user:**
- Contact your admin
- Admin can reset your password from **Manage Users**
- You'll get a new temporary password

### Can't Login with Student Format?
- Student usernames must be: **EA24A01**
- Must start with **EA**
- Year must be 24 or higher
- Letter can be A-Z (most are A-T)
- Last 2 digits: 01-99

### What if Admin Account Gets Locked?
- Restart application
- Database will be reset with fresh admin account
- OR delete `ea_tutorial.db` and re-run `init_sample_data.py`

### Activity Log Shows Error?
- Try refreshing the page
- Check if admin account has proper permissions
- Verify database file exists

## Next Steps

### After Initial Setup:
1. Create additional teacher accounts
2. Register students (or create them as admin)
3. Upload course materials
4. Create quizzes
5. Monitor activity regularly

### Customization:
- Edit site title in configuration
- Add your logo to static/images
- Customize CSS in app/static/css/style.css
- Add your school branding

### For Production:
- See **PHASE_3_DEPLOYMENT.md** for deployment instructions
- Set strong SECRET_KEY in .env
- Configure SSL/TLS
- Set up automated backups
- Configure email notifications (optional)

## Support & Documentation

For detailed information, see:
- **README.md** - Full feature documentation
- **PHASE_3_IMPLEMENTATION.md** - Technical implementation details
- **PHASE_3_TESTING.md** - Testing procedures
- **PHASE_3_DEPLOYMENT.md** - Production deployment guide

## Getting Help

If something doesn't work:
1. Check the Activity Log for errors
2. Review Flask application console output
3. Verify database was initialized: `python init_sample_data.py`
4. Ensure virtual environment is activated
5. Check port 5000 is available

## Important Notes

⚠️ **For Testing Only:**
- This is a development setup
- Don't use in production without SSL/TLS
- Always backup your database
- Change default passwords before going live

✅ **Best Practices:**
- Change admin/teacher passwords immediately
- Review activity logs regularly
- Backup database daily
- Test password reset procedures
- Monitor system resources

## Quick Reference - Keyboard Shortcuts

(To be implemented in future versions)

## Video Tutorials

Links to video tutorials (to be added)

---

**Happy Learning! 🎓**

For the latest updates, visit the project repository or contact your system administrator.
