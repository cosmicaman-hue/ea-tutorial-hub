# EA Tutorial Hub

A comprehensive online learning platform with quiz competitions, PDF notes repository, and role-based access control.

## Current Version: Phase 3 - Production Enhanced

### Latest Updates (Phase 3)
✓ Fixed Admin/Teacher usernames for production deployment
✓ Enhanced password management system with admin reset capability
✓ Comprehensive activity logging and monitoring dashboard
✓ Improved user validation and authentication
✓ Student login format enforcement (EA24A01 only)

See [PHASE_3_IMPLEMENTATION.md](PHASE_3_IMPLEMENTATION.md) for detailed Phase 3 changes.

## Features

### 1. **User Management**
- Role-based authentication (Admin, Teacher, Student)
- **Fixed admin/teacher usernames** (Admin, Teacher)
- Student login ID validation (format: EA24A01)
- Password change capability for all users
- Admin password reset for other users
- First-time login profile completion
- User account management by admin
- Activity logging for all user actions

### 2. **Notes Repository**
- Upload and manage PDF notes
- Organize by subject and class
- Admin approval workflow
- Download tracking
- Full-text search capability

### 3. **Online Quiz System**
- Create and manage quizzes
- Multiple question types (MCQ, True/False, Short Answer)
- Real-time scoring
- Timer-based quizzes
- Performance tracking
- Optional retakes

### 4. **Student Profile**
- Comprehensive profile information
- Contact details
- Address information
- Guardian information
- Personal interests and hobbies
- School details

### 5. **Admin Monitoring** (NEW - Phase 3)
- Real-time activity logging dashboard
- Login/logout tracking
- Password change monitoring
- IP address recording
- Filterable activity logs
- User management with password reset

## Default Login Credentials

```
Admin Account:
  Username: Admin
  Password: admin123

Teacher Account:
  Username: Teacher
  Password: teacher123

Student Accounts (Sample):
  EA24C01: student123
  EA24D02: student123
  EA24E03: student123
```

## Installation

### Prerequisites
- Python 3.7+
- pip
- Virtual Environment (optional but recommended)

### Setup

1. **Clone or extract the project:**
```bash
cd "Project EA"
```

2. **Create and activate virtual environment (if not already done):**
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
Edit `.env` file with your settings (already created with defaults)

5. **Initialize database:**
```bash
python run.py
```

The application will create the SQLite database on first run.

## Running the Application

```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Default Admin Account

For initial setup, you need to create an admin account. Run the application and:

1. Go to `/auth/register` to create an account
2. Manually change the role to 'admin' in the database, OR
3. Use the admin panel to create additional users

## Project Structure

```
Project EA/
├── app/
│   ├── models/
│   │   ├── user.py          # User model with login validation
│   │   ├── student_profile.py
│   │   ├── notes.py
│   │   └── quiz.py
│   ├── routes/
│   │   ├── auth.py          # Authentication routes
│   │   ├── dashboard.py     # Dashboard routes
│   │   ├── admin.py         # Admin panel routes
│   │   ├── notes.py         # Notes management routes
│   │   └── quiz.py          # Quiz routes
│   ├── templates/
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── admin/
│   │   ├── notes/
│   │   └── quiz/
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/main.js
│   │   └── uploads/         # PDF uploads directory
│   └── __init__.py
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── .env                      # Environment configuration
└── README.md
```

## Login ID Format

The login ID must follow this format: **EA24A01**

- **EA**: Fixed prefix (mandatory)
- **24**: Year (starting from 24 onwards)
- **A**: Category (A, B, C, D, E, F, T, or Z)
- **01**: Serial number (01 to 99)

## Usage Guide

### For Students
1. Register with a valid login ID
2. Complete profile information on first login
3. Browse available notes by subject/class
4. Take quizzes and track progress
5. View performance history

### For Teachers
1. Create account with teacher role (admin assigns)
2. Upload PDF notes with relevant metadata
3. Notes go through admin approval
4. View upload statistics
5. Track which students access materials

### For Admins
1. Manage all user accounts
2. Approve/reject uploaded notes
3. Create teacher and student accounts
4. System settings and maintenance
5. View platform statistics

## Database Models

### User
- Login ID, Password, Role
- Active status, First login flag
- Created/Last login timestamps

### StudentProfile
- Personal information (Name, DOB, etc.)
- Contact details
- Address information
- Guardian information
- School details

### Notes
- Title, Description, Subject, Class
- File path, File size, Total pages
- Upload tracking, Download count
- Approval status

### Quiz
- Title, Subject, Class
- Duration, Total points, Passing score
- Questions, Answers, Results

## Security Features

- Password hashing with Werkzeug
- CSRF protection via Flask
- SQL injection prevention via SQLAlchemy ORM
- Session-based authentication
- File upload validation
- Login ID format validation

## File Upload

- Supported format: PDF only
- Maximum file size: 50 MB
- Stored in: `app/static/uploads/`
- File naming: Timestamp-based for uniqueness

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers

## Performance Considerations

- SQLite database (suitable for small to medium deployments)
- Local file storage
- Can run on standard PC with minimal resources
- Scalable to larger deployments with PostgreSQL/MySQL

## Troubleshooting

### Database Issues
- Delete `ea_tutorial.db` file and restart to reset database
- Check file permissions in `app/static/uploads/`

### Login Issues
- Ensure login ID matches format (EA + digits/letters)
- Check user account is active in admin panel

### File Upload Issues
- Verify PDF is not corrupted
- Check file size is under 50 MB
- Ensure `app/static/uploads/` directory exists

## License

This project is provided as-is for educational purposes.

## Support

For issues or questions, please contact the administrator.

---

**EA Tutorial Hub** - Empowering Education through Technology
