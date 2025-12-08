# EA Tutorial Hub - Complete Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [System Architecture](#system-architecture)
4. [Installation & Setup](#installation--setup)
5. [Usage Guide](#usage-guide)
6. [Database Schema](#database-schema)
7. [API Routes](#api-routes)
8. [Administration Guide](#administration-guide)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)

---

## Introduction

**EA Tutorial Hub** is a comprehensive online learning platform built with Flask and SQLite, designed to run locally on a simple PC. It combines features of a Learning Management System (LMS), quiz competition platform, and document repository.

### Key Statistics
- **Languages:** Python (Flask), HTML, CSS, JavaScript
- **Database:** SQLite3 (local file-based)
- **Server:** Flask Development Server (can be upgraded to production WSGI)
- **Browser Support:** Chrome, Firefox, Safari, Edge (latest versions)
- **Data Storage:** All data stored locally on your machine

---

## Features

### 1. Authentication & Authorization

✅ **Three Role Levels:**
- **Admin** - Full system access, user management, content approval
- **Teacher** - Upload notes, view student progress
- **Student** - Access notes, take quizzes, view results

✅ **Login ID Validation**
- Format: EA + 2 digits (24+) + Category (A/B/C/D/E/F/T/Z) + 2 digits (01-99)
- Examples: EA24A01, EA25B50, EA26Z99
- Automatically enforced by system

✅ **Session Management**
- Secure password hashing using Werkzeug
- Session-based authentication with Flask-Login
- Automatic logout after inactivity

### 2. Student Profile System

Comprehensive profile form on first login including:
- Personal Information: First, Second, Third Name, DOB, Gender, Religion
- School Details: School Name, Class, Section, Roll Number
- Contact: Phone numbers, Email
- Address: Village/Area, Post Office, District, State, Pin Code
- Guardian: Father, Mother, Guardian names and contact
- Additional: Blood Group, Aadhar Number, Hobbies, Improvement Areas

### 3. Notes Repository

✅ **Upload Management**
- Support for PDF files only (max 50 MB)
- Automatic metadata extraction (page count)
- Unique file naming with timestamps
- Admin approval workflow

✅ **Organization**
- Filter by Subject and Class Level
- Full-text search capability
- Tags and descriptions
- Download tracking
- Automatic page count detection

✅ **Download Functionality**
- Secure download links
- Download count statistics
- Storage in `app/static/uploads/`

### 4. Quiz System

✅ **Question Types**
- Multiple Choice (A, B, C, D)
- True/False
- Short Answer

✅ **Quiz Features**
- Real-time scoring
- Customizable duration (minutes)
- Pass/fail criteria (percentage-based)
- Optional retakes
- Time-limited attempts
- Instant result display

✅ **Performance Tracking**
- Question-level feedback
- Correct answer display
- Explanation for each question
- Attempt history
- Score trends

---

## System Architecture

### Technology Stack

```
Frontend:
├── HTML5 (Bootstrap 5 framework)
├── CSS3 (Custom responsive styling)
└── JavaScript (Vanilla JS + Bootstrap JS)

Backend:
├── Python 3.7+
├── Flask 2.3.3
├── Flask-SQLAlchemy 3.0.5 (ORM)
├── Flask-Login 0.6.2 (Authentication)
└── Werkzeug 2.3.7 (Security)

Database:
└── SQLite3 (File-based, local storage)

Additional Libraries:
├── python-dotenv (Environment config)
├── PyPDF2 (PDF page counting)
└── email-validator (Email validation)
```

### Directory Structure

```
Project EA/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User account model
│   │   ├── student_profile.py   # Student data model
│   │   ├── notes.py             # PDF notes model
│   │   └── quiz.py              # Quiz & questions models
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication (login, register)
│   │   ├── dashboard.py         # Home, search, profile
│   │   ├── admin.py             # Admin panel
│   │   ├── notes.py             # Notes CRUD operations
│   │   └── quiz.py              # Quiz operations
│   │
│   ├── templates/
│   │   ├── base.html            # Master template
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   └── complete_profile.html
│   │   ├── dashboard/
│   │   │   ├── index.html
│   │   │   ├── search.html
│   │   │   ├── profile.html
│   │   │   └── edit_profile.html
│   │   ├── admin/
│   │   │   ├── dashboard.html
│   │   │   ├── manage_users.html
│   │   │   ├── create_user.html
│   │   │   ├── pending_notes.html
│   │   │   └── settings.html
│   │   ├── notes/
│   │   │   ├── index.html
│   │   │   ├── view.html
│   │   │   ├── upload.html
│   │   │   └── my_uploads.html
│   │   └── quiz/
│   │       ├── index.html
│   │       ├── view.html
│   │       ├── start.html
│   │       ├── results.html
│   │       └── my_attempts.html
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # Custom styling
│   │   ├── js/
│   │   │   └── main.js          # Client-side logic
│   │   └── uploads/             # PDF storage (auto-created)
│   │
│   └── __init__.py              # Flask app initialization
│
├── run.py                       # Application entry point
├── init_sample_data.py          # Sample data initialization
├── requirements.txt             # Python dependencies
├── .env                         # Configuration file
├── ea_tutorial.db              # SQLite database (auto-created)
├── README.md                    # Full documentation
└── QUICK_START.md              # Quick start guide
```

---

## Installation & Setup

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Windows/macOS/Linux
- 500 MB free disk space
- Modern web browser

### Step 1: Install Python Dependencies

```bash
cd "Project EA"
pip install -r requirements.txt
```

### Step 2: Initialize Database

```bash
python run.py
```

The application will:
- Create `ea_tutorial.db` (SQLite database)
- Create all necessary tables
- Start the Flask development server

### Step 3: Load Sample Data (Optional)

```bash
python init_sample_data.py
```

This creates:
- 1 Admin account (EA24A01)
- 1 Teacher account (EA24B01)
- 3 Student accounts (EA24C01, EA24D02, EA24E03)
- 2 Sample quizzes with questions
- Default password for all: username123

### Step 4: Access the Application

Open your browser and go to:
```
http://localhost:5000
```

---

## Usage Guide

### For Students

#### 1. Register an Account
```
URL: http://localhost:5000/auth/register
- Enter Login ID (format: EA24A01)
- Set a password (minimum 6 characters)
- Confirm password
- Click "Create Account"
```

#### 2. Complete Your Profile
```
On first login:
- Fill all required fields (marked with *)
- Add optional information
- Click "Complete Registration"
- Profile data saved to database
```

#### 3. Browse and Download Notes
```
Navigate: Notes section → Filter by Subject/Class
- Search for specific topics
- View note details
- Click "Download PDF" to save
- Access from My Downloads
```

#### 4. Take Quizzes
```
Navigate: Quizzes section → Choose a quiz
- Click "Start Quiz"
- Answer all questions within time limit
- Timer counts down
- Submit answers
- View instant results with explanations
- Optionally retake if allowed
```

#### 5. Track Progress
```
Navigate: Quiz section → My Attempts
- View all quiz attempts
- See scores and percentages
- Review detailed results
- Compare performance over time
```

### For Teachers

#### 1. Upload Notes
```
Navigate: Upload Notes
- Select PDF file (50 MB max)
- Enter title and description
- Choose subject and class level
- Add tags for searchability
- Click "Upload Notes"
- Status: Pending admin approval
```

#### 2. Monitor Uploads
```
Navigate: My Uploads
- View all your uploaded files
- See approval status
- Check download statistics
- Track student engagement
```

#### 3. Create Quizzes
```
Note: Requires admin role (contact system admin)
- Add quiz title and details
- Create questions
- Set passing score
- Configure quiz settings
```

### For Admins

#### 1. Create User Accounts
```
Navigate: Admin Panel → Manage Users → Create User
- Enter login ID (validate format)
- Set temporary password
- Assign role (Student/Teacher)
- Account created and active
```

#### 2. Manage Users
```
Navigate: Admin Panel → Manage Users
- View all user accounts
- Filter by role
- Enable/disable accounts
- Monitor login activity
```

#### 3. Approve Content
```
Navigate: Admin Panel → Pending Notes
- Review uploaded PDF notes
- Approve quality submissions
- Reject inappropriate content
- Manage content library
```

#### 4. Create Quizzes
```
Navigate: Admin Panel → Quiz Management
- Add new quizzes
- Create questions with multiple types
- Set points and passing criteria
- Configure time limits
- Publish to students
```

#### 5. System Settings
```
Navigate: Admin Panel → Settings
- Configure upload limits
- Manage system parameters
- View platform statistics
- Database maintenance
```

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    login_id VARCHAR(7) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'student',  -- admin, teacher, student
    is_active BOOLEAN DEFAULT True,
    first_login BOOLEAN DEFAULT True,
    created_at DATETIME,
    last_login DATETIME
);
```

### Student Profiles Table

```sql
CREATE TABLE student_profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE FOREIGN KEY,
    first_name VARCHAR(100),
    second_name VARCHAR(100),
    third_name VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(20),
    religion VARCHAR(50),
    nationality VARCHAR(50),
    school_name VARCHAR(200),
    class_name VARCHAR(20),
    section VARCHAR(10),
    contact_number_1 VARCHAR(15),
    contact_number_2 VARCHAR(15),
    email VARCHAR(120) UNIQUE,
    village_area VARCHAR(100),
    post_office VARCHAR(100),
    district VARCHAR(100),
    state VARCHAR(100),
    pin_code VARCHAR(10),
    hobbies TEXT,
    improvement_areas TEXT,
    father_name VARCHAR(100),
    mother_name VARCHAR(100),
    guardian_name VARCHAR(100),
    blood_group VARCHAR(5),
    aadhar_number VARCHAR(12),
    created_at DATETIME,
    updated_at DATETIME
);
```

### Notes Table

```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    subject VARCHAR(100),
    class_level VARCHAR(20),
    file_path VARCHAR(500),
    file_size INTEGER,
    uploaded_by INTEGER FOREIGN KEY,
    is_approved BOOLEAN DEFAULT False,
    total_pages INTEGER,
    language VARCHAR(50),
    tags VARCHAR(500),
    download_count INTEGER DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME
);
```

### Quizzes Table

```sql
CREATE TABLE quizzes (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    subject VARCHAR(100),
    class_level VARCHAR(20),
    duration_minutes INTEGER,
    total_points INTEGER,
    passing_score INTEGER,
    is_active BOOLEAN DEFAULT True,
    allow_retake BOOLEAN DEFAULT True,
    show_results BOOLEAN DEFAULT True,
    created_at DATETIME,
    updated_at DATETIME
);
```

### Quiz Questions Table

```sql
CREATE TABLE quiz_questions (
    id INTEGER PRIMARY KEY,
    quiz_id INTEGER FOREIGN KEY,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50),  -- multiple_choice, true_false, short_answer
    points INTEGER DEFAULT 1,
    option_a VARCHAR(500),
    option_b VARCHAR(500),
    option_c VARCHAR(500),
    option_d VARCHAR(500),
    correct_answer VARCHAR(10),
    explanation TEXT,
    order INTEGER
);
```

### Quiz Answers Table

```sql
CREATE TABLE quiz_answers (
    id INTEGER PRIMARY KEY,
    quiz_id INTEGER FOREIGN KEY,
    question_id INTEGER FOREIGN KEY,
    user_id INTEGER FOREIGN KEY,
    student_answer VARCHAR(500),
    is_correct BOOLEAN,
    points_earned INTEGER DEFAULT 0,
    submitted_at DATETIME
);
```

---

## API Routes

### Authentication Routes

```
GET  /auth/login              # Login page
POST /auth/login              # Login submission
GET  /auth/register           # Registration page
POST /auth/register           # Registration submission
GET  /auth/complete-profile   # Profile completion form
POST /auth/complete-profile   # Profile submission
GET  /auth/logout             # Logout (redirect to login)
```

### Dashboard Routes

```
GET /                         # Home page / Dashboard
GET /search                   # Search notes & quizzes
GET /profile                  # View student profile
GET /profile/edit             # Edit profile form
POST /profile/edit            # Update profile
```

### Notes Routes

```
GET  /notes                   # Browse all notes
GET  /notes/<id>              # View note details
GET  /notes/<id>/download     # Download PDF file
GET  /notes/upload            # Upload form
POST /notes/upload            # Process upload
GET  /notes/my-uploads        # View uploaded notes
```

### Quiz Routes

```
GET  /quiz                    # Browse all quizzes
GET  /quiz/<id>               # Quiz details
GET  /quiz/<id>/start         # Start quiz (timer begins)
POST /quiz/<id>/submit        # Submit answers
GET  /quiz/<id>/results       # View results
GET  /quiz/my-attempts        # View attempt history
```

### Admin Routes

```
GET  /admin/dashboard         # Admin dashboard
GET  /admin/users             # Manage users
GET  /admin/users/create      # Create user form
POST /admin/users/create      # Create user
GET  /admin/users/<id>/toggle-status  # Enable/disable
GET  /admin/notes/pending     # Pending approval
GET  /admin/notes/<id>/approve        # Approve note
GET  /admin/notes/<id>/reject         # Reject note
GET  /admin/settings          # System settings
```

---

## Administration Guide

### Creating User Accounts

**Method 1: Admin Panel**
1. Go to `/admin/users/create`
2. Enter login ID (validate format)
3. Set password
4. Select role
5. Click "Create User"

**Method 2: Database Query**
```python
from app import db, create_app
from app.models import User

app = create_app()
with app.app_context():
    user = User(login_id='EA24A01', role='admin')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
```

### Approving Content

1. Navigate to `/admin/notes/pending`
2. Review each PDF note
3. Click "Approve" to publish
4. Click "Reject" to delete and notify uploader

### Modifying Database

```python
# Connect to database
from app import db, create_app
from app.models import User, StudentProfile

app = create_app()
with app.app_context():
    # Query users
    users = User.query.all()
    
    # Update user
    user = User.query.filter_by(login_id='EA24A01').first()
    user.is_active = False
    db.session.commit()
    
    # Delete user
    db.session.delete(user)
    db.session.commit()
```

### Backup Database

```bash
# Copy the database file
copy ea_tutorial.db ea_tutorial.db.backup

# On macOS/Linux
cp ea_tutorial.db ea_tutorial.db.backup
```

### Reset Database

```bash
# Delete database (WARNING: Deletes all data)
del ea_tutorial.db

# Restart application
python run.py
```

---

## Troubleshooting

### Issue: Application won't start

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
pip install -r requirements.txt
python run.py
```

### Issue: Can't login

**Common Causes:**
1. Invalid login ID format
2. User account disabled
3. Wrong password

**Solution:**
- Check login ID: Must be EA + 2 digits + letter + 2 digits
- Admin to enable account: `/admin/users/` toggle status
- Reset password via admin panel

### Issue: PDF upload fails

**Possible Reasons:**
1. File is not PDF
2. File size exceeds 50 MB
3. PDF is corrupted
4. Upload folder doesn't exist

**Solution:**
```bash
# Check uploads folder exists
mkdir -p app/static/uploads

# Verify PDF integrity with a different tool
# Compress PDF to reduce size (use online compressor)
```

### Issue: Database locked

**Error:** `database is locked`

**Cause:** Multiple Flask instances or incomplete transaction

**Solution:**
```bash
# Kill Flask process
# Delete any .db-journal files
del ea_tutorial.db-journal

# Restart application
python run.py
```

### Issue: Slow application performance

**Solutions:**
1. Archive old quizzes
2. Clean up uploads folder
3. Delete old quiz attempts
4. Use database indexing for queries

```python
# Delete old data (example)
from app import db, create_app
from app.models import QuizAnswer
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    old_answers = QuizAnswer.query.filter(
        QuizAnswer.submitted_at < datetime.now() - timedelta(days=365)
    ).delete()
    db.session.commit()
```

### Issue: Can't reset password

**Solution:**
```python
from app import db, create_app
from app.models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(login_id='EA24A01').first()
    user.set_password('new_password_123')
    db.session.commit()
```

---

## Security Considerations

### Current Implementation

✅ **Implemented Security Features:**
- Password hashing (Werkzeug)
- CSRF protection (Flask-Login)
- SQL injection prevention (SQLAlchemy ORM)
- Session management
- Input validation
- File type validation (PDF only)
- File size limits

### Development vs. Production

**Development (Current Setup):**
- Debug mode enabled
- Development server used
- SQLite database
- Local file storage
- Shared secret key

**For Production Deployment:**

1. **Disable Debug Mode**
```python
app.run(debug=False)
```

2. **Use Production Server**
```bash
# Install Gunicorn
pip install gunicorn

# Run application
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

3. **Generate Secure Secret Key**
```python
import secrets
print(secrets.token_hex(32))
# Use this in .env SECRET_KEY
```

4. **Enable HTTPS**
```bash
# Generate SSL certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Run with HTTPS
gunicorn --certfile=cert.pem --keyfile=key.pem -b 0.0.0.0:5000 run:app
```

5. **Upgrade Database**
```bash
# Install PostgreSQL
# Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost/ea_tutorial

# Migrate data and restart
```

6. **Implement Backups**
```bash
# Automated daily backup script
# Upload to cloud storage
# Maintain version control
```

7. **Setup Firewall**
```bash
# Allow only port 5000 (or 443 for HTTPS)
# Restrict access by IP if needed
# Block unnecessary ports
```

### Compliance

- Ensure student data privacy (GDPR, local regulations)
- Implement data retention policies
- Setup audit logging
- Create user data export feature
- Implement right to be forgotten

---

## Additional Resources

### File Organization
- Configuration: `.env`
- Database: `ea_tutorial.db`
- PDFs: `app/static/uploads/`
- Logs: Check terminal output

### Useful Commands

```bash
# Start application
python run.py

# Load sample data
python init_sample_data.py

# Access Python shell
python -c "from app import *; ..."

# Check Python version
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# List installed packages
pip list

# Export database to CSV
sqlite3 ea_tutorial.db ".mode csv" ".output data.csv" "SELECT * FROM users;"
```

### Browser Developer Tools

```javascript
// Check network requests
// Monitor console for JavaScript errors
// Inspect elements for styling issues
// Use Network tab to debug slow requests

// To enable:
Press F12 in your browser
```

---

## Support & Contact

For issues not covered in this documentation:

1. Check the README.md for quick answers
2. Review terminal logs for error messages
3. Check browser console (F12) for JavaScript errors
4. Verify all dependencies are installed correctly
5. Test with sample data first

---

**Last Updated:** December 8, 2025
**Version:** 1.0
**Status:** Ready for Deployment

Enjoy your EA Tutorial Hub! 🎓
