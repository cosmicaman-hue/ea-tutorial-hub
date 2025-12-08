# EA Tutorial Hub - Quick Start Guide

## System Overview

**EA Tutorial Hub** is a comprehensive online learning platform designed to run locally on a simple PC. It provides:

✅ **Online Quiz Competitions** - Real-time scoring, performance tracking, optional retakes
✅ **PDF Notes Repository** - Organize by subject/class, download tracking, admin approval
✅ **Role-Based Access** - Admin, Teacher, and Student roles with different privileges
✅ **Student Profiles** - Comprehensive admission form-like profiles with school details
✅ **Local Data Storage** - SQLite database stores all data locally on your PC

## Quick Start (2 minutes)

### 1. Start the Application
```bash
cd "Project EA"
.\.venv\Scripts\python.exe run.py
```

### 2. Open in Browser
Navigate to: `http://localhost:5000`

### 3. Create Your First Account
- Click on "Register" or go to `/auth/register`
- Use login ID format: **EA24A01** (Example: EA24A01, EA24B99, EA25F50)
- Set a password (minimum 6 characters)
- Complete your profile with school details

### 4. Access Admin Panel
To create teacher/student accounts and manage the platform:
- Create a user account
- Manually change the role in the database file (ea_tutorial.db), OR
- Contact the project developer for admin setup

## Login ID Format Explanation

Format: **EA24A01**

| Part | Example | Rules |
|------|---------|-------|
| Prefix | EA | Always "EA" (mandatory) |
| Year | 24 | Must be 24 or higher |
| Category | A | Must be one of: A, B, C, D, E, F, T, Z |
| Serial | 01 | Number from 01 to 99 |

**Valid Examples:** EA24A01, EA24C50, EA25Z99, EA26B15
**Invalid Examples:** EB24A01, EA23A01, EA24G01, EA24A00, EA24A100

## Features Guide

### For Students

1. **Browse Notes**
   - Go to "Notes" section
   - Filter by Subject or Class
   - Search for specific topics
   - Download PDFs to study

2. **Take Quizzes**
   - Go to "Quizzes" section
   - Choose a quiz
   - Answer questions within time limit
   - Get instant results and explanations

3. **Track Progress**
   - View quiz attempts history
   - See scores and performance
   - Review explanations for wrong answers

4. **Complete Profile**
   - Fill comprehensive student information
   - Add school and contact details
   - Update personal interests and hobbies
   - Manage guardian information

### For Teachers

1. **Upload Notes**
   - Go to "Upload Notes"
   - Select PDF file (max 50 MB)
   - Add title, subject, class, description
   - Add relevant tags for easy search
   - Submit for admin approval

2. **Track Uploads**
   - View all your uploaded notes
   - See approval status (Pending/Published)
   - Monitor download counts

3. **Create Quizzes** (Admin Feature)
   - Teachers need admin to set up quizzes
   - Provide questions and answers
   - Set difficulty and passing score

### For Admins

1. **Manage Users**
   - Create student and teacher accounts
   - View all registered users
   - Disable inactive accounts
   - Manage user roles

2. **Approve Content**
   - Review uploaded PDF notes
   - Approve or reject submissions
   - Manage platform quality

3. **System Settings**
   - Configure system parameters
   - Manage upload limits
   - View platform statistics

4. **Create Quizzes**
   - Add new quizzes
   - Create questions with multiple types
   - Set scoring and passing criteria
   - Manage quiz availability

## File Structure

```
Project EA/
├── app/                          # Main application folder
│   ├── models/                   # Database models
│   │   ├── user.py              # User accounts with ID validation
│   │   ├── student_profile.py   # Student information
│   │   ├── notes.py             # Notes/PDFs database
│   │   └── quiz.py              # Quiz questions and answers
│   ├── routes/                   # Application logic
│   │   ├── auth.py              # Login/Registration
│   │   ├── dashboard.py         # Main dashboard
│   │   ├── admin.py             # Admin controls
│   │   ├── notes.py             # Notes management
│   │   └── quiz.py              # Quiz functionality
│   ├── templates/                # HTML pages
│   │   ├── base.html            # Main layout
│   │   ├── auth/                # Login/Register pages
│   │   ├── dashboard/           # Main pages
│   │   ├── admin/               # Admin pages
│   │   ├── notes/               # Notes pages
│   │   └── quiz/                # Quiz pages
│   ├── static/                   # CSS, JS, Uploads
│   │   ├── css/style.css        # Styling
│   │   ├── js/main.js           # JavaScript
│   │   └── uploads/             # PDF storage (auto-created)
│   └── __init__.py              # App initialization
├── run.py                        # Start the application
├── requirements.txt              # Python packages
├── .env                          # Configuration
├── ea_tutorial.db               # Database (auto-created)
└── README.md                     # Full documentation
```

## Database Location

The SQLite database is stored at:
```
c:\Users\sujit\Desktop\Project EA\ea_tutorial.db
```

This file contains all user accounts, student profiles, notes, and quiz data. You can backup this file to preserve all data.

## Configuration

Edit `.env` file to customize settings:

```ini
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-this-in-production
DATABASE_URL=sqlite:///ea_tutorial.db
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=52428800  # 50 MB
```

## Troubleshooting

### Issue: Application won't start
**Solution:** 
```bash
# Reinstall dependencies
pip install -r requirements.txt
# Run again
.\.venv\Scripts\python.exe run.py
```

### Issue: Can't login with created account
**Solution:**
- Ensure Login ID follows format: EA + 2 digits (24+) + allowed letter + 2 digits (01-99)
- Check "is_active" field in database is True

### Issue: Can't upload PDF files
**Solution:**
- Ensure `app/static/uploads/` folder exists
- Check file is a valid PDF (not corrupted)
- Maximum file size is 50 MB

### Issue: Database errors
**Solution:**
- Delete `ea_tutorial.db` and restart to create new database
- Ensure you have write permissions in project folder

## System Requirements

- **OS:** Windows, macOS, or Linux
- **RAM:** Minimum 512 MB (1 GB recommended)
- **Storage:** 500 MB for application + space for PDFs
- **Python:** 3.7 or higher
- **Browser:** Any modern browser (Chrome, Firefox, Safari, Edge)

## Security Notes

⚠️ **For Production Use:**
- Change `SECRET_KEY` in `.env`
- Use a proper WSGI server (Gunicorn, uWSGI)
- Enable HTTPS
- Setup proper backups
- Use PostgreSQL/MySQL instead of SQLite
- Configure firewall rules

## Performance Tips

1. **Optimize PDFs** before uploading to reduce file sizes
2. **Archive old quizzes** to keep database responsive
3. **Regular backups** of `ea_tutorial.db` file
4. **Clean uploads folder** periodically
5. **Monitor disk space** for PDF storage

## Useful Commands

### Access Database
```bash
# Using Python
python
>>> from app import db, create_app
>>> app = create_app()
>>> with app.app_context():
>>>     from app.models import User
>>>     users = User.query.all()
>>>     for user in users:
>>>         print(user.login_id)
```

### Reset Database
```bash
# Delete the database file to start fresh
del ea_tutorial.db
# Restart the application
.\.venv\Scripts\python.exe run.py
```

## Support & Help

For issues or questions:
1. Check the README.md file for detailed documentation
2. Review template files for understanding the layout
3. Check browser console (F12) for JavaScript errors
4. Review terminal output for application logs

## Next Steps

1. ✅ Application is now running
2. 📝 Create an admin account
3. 👥 Add student and teacher accounts
4. 📚 Upload some sample notes
5. ❓ Create some quiz questions
6. 🎓 Start learning!

---

**Enjoy EA Tutorial Hub!** 🎉
For more information, see README.md
