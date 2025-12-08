# EA Tutorial Hub - File Structure Guide

## Complete Project Organization

```
Project EA/
│
├── 📄 DOCUMENTATION FILES (Read These First!)
│   ├── README.md                      # Full feature & setup documentation
│   ├── QUICK_START.md                 # 2-minute quick start guide
│   ├── DOCUMENTATION.md               # Complete technical reference
│   ├── TESTING_GUIDE.md               # Test cases & validation
│   ├── PROJECT_DELIVERY_SUMMARY.md    # Delivery checklist & status
│   └── This File                      # You are here!
│
├── 🚀 APPLICATION ENTRY POINT
│   └── run.py                         # Start the application here
│
├── 📦 CONFIGURATION FILES
│   ├── requirements.txt               # Python package dependencies
│   ├── .env                           # Environment variables
│   └── .venv/                         # Virtual environment (auto-created)
│
├── 🔧 INITIALIZATION
│   └── init_sample_data.py            # Load sample data for testing
│
├── 📁 APPLICATION FOLDER (app/)
│   ├── __init__.py                    # Flask app initialization
│   │
│   ├── models/                        # Database Models (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── user.py                    # User model (login validation)
│   │   ├── student_profile.py         # Student information model
│   │   ├── notes.py                   # PDF notes model
│   │   └── quiz.py                    # Quiz & questions models
│   │
│   ├── routes/                        # Application Routes (Flask Blueprints)
│   │   ├── __init__.py
│   │   ├── auth.py                    # Login/Register/Profile routes
│   │   ├── dashboard.py               # Home/Search/Profile routes
│   │   ├── admin.py                   # Admin panel routes
│   │   ├── notes.py                   # Notes management routes
│   │   └── quiz.py                    # Quiz operations routes
│   │
│   ├── templates/                     # HTML Templates (Jinja2)
│   │   ├── base.html                  # Master layout template
│   │   │
│   │   ├── auth/                      # Authentication pages
│   │   │   ├── login.html             # Login form
│   │   │   ├── register.html          # Registration form
│   │   │   └── complete_profile.html  # Profile completion form
│   │   │
│   │   ├── dashboard/                 # Main dashboard pages
│   │   │   ├── index.html             # Home page
│   │   │   ├── search.html            # Search results
│   │   │   ├── profile.html           # View profile
│   │   │   └── edit_profile.html      # Edit profile
│   │   │
│   │   ├── admin/                     # Admin panel pages
│   │   │   ├── dashboard.html         # Admin dashboard
│   │   │   ├── manage_users.html      # User management
│   │   │   ├── create_user.html       # Create user form
│   │   │   ├── pending_notes.html     # Content approval
│   │   │   └── settings.html          # System settings
│   │   │
│   │   ├── notes/                     # Notes pages
│   │   │   ├── index.html             # Browse notes
│   │   │   ├── view.html              # View single note
│   │   │   ├── upload.html            # Upload form
│   │   │   └── my_uploads.html        # Manage uploads
│   │   │
│   │   └── quiz/                      # Quiz pages
│   │       ├── index.html             # Browse quizzes
│   │       ├── view.html              # Quiz details
│   │       ├── start.html             # Quiz interface
│   │       ├── results.html           # Quiz results
│   │       └── my_attempts.html       # Attempt history
│   │
│   └── static/                        # Static Files (CSS, JS, Uploads)
│       ├── css/
│       │   └── style.css              # Custom styling (100+ rules)
│       ├── js/
│       │   └── main.js                # Client-side logic
│       └── uploads/                   # PDF file storage (auto-created)
│           └── [PDF files stored here]
│
├── 📊 DATABASE
│   └── ea_tutorial.db                 # SQLite database (auto-created)
│
└── 🔌 OTHER DIRECTORIES
    ├── .vscode/                       # VS Code configuration
    ├── instance/                      # Flask instance folder
    └── __pycache__/                   # Python bytecode cache

```

---

## File Descriptions

### 📄 Documentation Files

| File | Purpose | Read When |
|------|---------|-----------|
| **README.md** | Complete feature list and installation guide | First thing to read |
| **QUICK_START.md** | Get running in 2 minutes | Want to start immediately |
| **DOCUMENTATION.md** | Technical reference and detailed guide | Need complete details |
| **TESTING_GUIDE.md** | Test cases and validation procedures | Want to test all features |
| **PROJECT_DELIVERY_SUMMARY.md** | Delivery checklist and project status | Verify what's included |

### 🚀 Startup Files

| File | Purpose |
|------|---------|
| **run.py** | Main entry point - Start app with: `python run.py` |
| **init_sample_data.py** | Load demo data - Run: `python init_sample_data.py` |
| **requirements.txt** | Package list - Install with: `pip install -r requirements.txt` |
| **.env** | Configuration - Edit to customize settings |

### 🔧 Backend Files (app/models/)

| File | Purpose | Contains |
|------|---------|----------|
| **user.py** | User model | Login validation, password hashing, role management |
| **student_profile.py** | Student data | 30+ profile fields for admission form |
| **notes.py** | Notes model | PDF storage, metadata, approval workflow |
| **quiz.py** | Quiz system | Quizzes, questions, answers, scoring |

### 🛣️ Route Files (app/routes/)

| File | Purpose | Routes Handled |
|------|---------|----------------|
| **auth.py** | Authentication | Login, register, profile completion, logout |
| **dashboard.py** | Main pages | Home, search, profile viewing/editing |
| **admin.py** | Admin panel | User management, content approval, settings |
| **notes.py** | Notes management | Browse, upload, download, manage notes |
| **quiz.py** | Quiz system | Browse quizzes, take, submit, view results |

### 📄 Template Files (app/templates/)

**Layout Templates:**
- **base.html** - Master layout with navigation, header, footer

**Authentication (auth/):**
- **login.html** - Login form with validation
- **register.html** - Registration form
- **complete_profile.html** - Comprehensive student profile form

**Dashboard (dashboard/):**
- **index.html** - Home page with featured content
- **search.html** - Search results page
- **profile.html** - Student profile viewing
- **edit_profile.html** - Profile editing form

**Admin (admin/):**
- **dashboard.html** - Admin statistics and quick links
- **manage_users.html** - User listing and management
- **create_user.html** - Create new account form
- **pending_notes.html** - Content approval interface
- **settings.html** - System configuration

**Notes (notes/):**
- **index.html** - Browse and filter notes
- **view.html** - Single note detail page
- **upload.html** - PDF upload form
- **my_uploads.html** - Manage uploaded notes

**Quiz (quiz/):**
- **index.html** - Quiz listing and filtering
- **view.html** - Quiz details and instructions
- **start.html** - Quiz taking interface with timer
- **results.html** - Quiz results and explanations
- **my_attempts.html** - Quiz attempt history

### 🎨 Static Files (app/static/)

| File | Purpose | Lines |
|------|---------|-------|
| **css/style.css** | Custom styling | 200+ CSS rules |
| **js/main.js** | Client-side functionality | 15+ JavaScript functions |
| **uploads/** | PDF storage directory | Auto-created for uploads |

### 📊 Database Files

| File | Purpose | Type |
|------|---------|------|
| **ea_tutorial.db** | Main SQLite database | Binary (auto-created) |

---

## File Relationships

```
Request Flow:
────────────

User Request
    ↓
app/__init__.py (Flask app setup)
    ↓
app/routes/[category].py (Blueprint routes)
    ↓
app/models/[model].py (Database operations)
    ↓
app/templates/[category]/[page].html (Response rendered)
    ↓
app/static/css/style.css (Styling applied)
app/static/js/main.js (Interactivity added)
    ↓
Response sent to browser
```

---

## Important Directories

### ✅ Should Exist
- `app/` - Main application folder
- `app/models/` - Database models
- `app/routes/` - Application routes
- `app/templates/` - HTML templates
- `app/static/` - CSS, JS, uploads

### ⚠️ Auto-Created on First Run
- `.venv/` - Virtual environment
- `app/static/uploads/` - PDF storage
- `ea_tutorial.db` - SQLite database
- `instance/` - Flask instance folder
- `__pycache__/` - Python cache

### 🚫 Do Not Delete
- Any file in `app/models/`
- Any file in `app/routes/`
- Any file in `app/templates/`
- `run.py` (main entry point)
- `requirements.txt` (dependencies list)

---

## File Size Guide

| Component | Typical Size |
|-----------|--------------|
| Single PDF note | 1-20 MB |
| Database (empty) | < 1 MB |
| Database (with data) | 5-50 MB |
| Virtual environment (.venv) | 500 MB |
| Total project (without .venv) | 5-10 MB |

---

## Configuration Priority

Files are read in this order:

1. `.env` file (takes highest priority)
2. Environment variables (system-level)
3. Default values in code

### Key Configuration Files

**`.env` File** - All settings in one place:
```ini
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-key-here
DATABASE_URL=sqlite:///ea_tutorial.db
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=52428800
```

---

## Development vs Production Files

### Development (Current)
```
Local files:
├── ea_tutorial.db (local storage)
├── app/static/uploads/ (local storage)
└── .env (development config)
```

### Production (Future)
```
Would need:
├── Remote database (PostgreSQL)
├── Cloud storage (S3, Azure)
├── SSL certificates
└── Production .env config
```

---

## Access Patterns

### Student Files
- Templates: `auth/`, `dashboard/`, `quiz/`, `notes/`
- Routes: `auth.py`, `dashboard.py`, `quiz.py`, `notes.py`
- Models: `user.py`, `student_profile.py`, `quiz.py`, `notes.py`

### Teacher Files
- Templates: `auth/`, `dashboard/`, `notes/`
- Routes: `auth.py`, `dashboard.py`, `notes.py`
- Models: `user.py`, `notes.py`

### Admin Files
- Templates: `auth/`, `admin/`, `dashboard/`
- Routes: `auth.py`, `admin.py`, `dashboard.py`
- Models: All models

---

## File Modification Guide

### Safe to Modify
- `.env` - Customize configuration
- `app/static/css/style.css` - Add custom styling
- `app/static/js/main.js` - Add custom functionality

### Should Not Modify (Unless Experienced)
- `app/models/` - Database schemas
- `app/routes/` - Core logic
- `requirements.txt` - Dependency versions
- `run.py` - Application initialization

### Templates (Safe to Customize)
- Can modify HTML in `app/templates/`
- Can change styling and layout
- Can add new sections
- Cannot change template logic (requires route changes)

---

## Backup Important Files

For regular backups, save these files:

**Critical Files:**
- `ea_tutorial.db` - All data
- `app/static/uploads/` - All PDF notes
- `.env` - Configuration

**Optional (can be recreated):**
- `app/` - Source code (version control recommended)
- `requirements.txt` - Dependencies list

---

## File Organization Best Practices

### For Adding New Features

```
1. Create model in app/models/[feature].py
2. Create routes in app/routes/[feature].py
3. Create templates in app/templates/[feature]/
4. Add CSS to app/static/css/style.css
5. Add JS to app/static/js/main.js
6. Register blueprint in app/__init__.py
```

### For Maintenance

```
1. Check logs in terminal
2. Review database in ea_tutorial.db
3. Monitor uploads folder size
4. Backup database regularly
5. Update dependencies in requirements.txt
```

---

## File Permissions

### Ensure Read/Write Access To:
- Project folder
- `ea_tutorial.db` file
- `app/static/uploads/` directory
- `.env` file

### Ensure Read Access To:
- All files in `app/` folder
- `requirements.txt`
- Documentation files

---

## Troubleshooting File Issues

### "File not found" error
```bash
# Verify file exists
ls -la filename
# Check file path is correct
# Ensure you're in project directory
```

### "Permission denied" error
```bash
# Check read/write permissions
# Run as administrator/sudo if needed
```

### "Database locked" error
```bash
# Check if .db-journal file exists
# Delete it if application not running
del ea_tutorial.db-journal
```

---

## Summary

| Type | Count | Location |
|------|-------|----------|
| Documentation files | 5 | Root directory |
| Python source files | 11 | app/ directory |
| HTML templates | 22 | app/templates/ |
| Static files | 2 | app/static/ |
| Configuration files | 2 | Root + .env |
| Database tables | 6 | ea_tutorial.db |

**Total:** 48+ files implementing complete learning management system

---

**Last Updated:** December 8, 2025  
**Version:** 1.0  

For any questions, refer to the specific documentation file mentioned in the Documentation Files section above.
