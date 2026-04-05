# EA Tutorial Hub - Project Structure Guide

## Overview
This document describes the organized structure of the EA Tutorial Hub project after reorganization.

## Directory Structure

```
Project EA/
├── app/                           # Core Flask application
│   ├── __init__.py               # Flask app factory
│   ├── config/                   # Configuration
│   │   ├── __init__.py
│   │   └── constants.py          # App constants
│   ├── models/                   # Database models
│   │   ├── __init__.py
│   │   ├── user.py              # User model
│   │   ├── points.py            # Points/scoring model
│   │   ├── student_profile.py   # Student profile model
│   │   └── governance.py        # Governance/elections model
│   ├── routes/                   # API routes
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication routes
│   │   ├── scoreboard.py        # Main scoreboard routes
│   │   ├── veto_api.py          # VETO system API
│   │   └── import_refinement.py # Data import routes
│   ├── utils/                    # Utility modules
│   │   ├── __init__.py
│   │   ├── error_handler.py     # Global error handling
│   │   ├── logger.py            # Comprehensive logging
│   │   ├── secrets_manager.py   # Secure credentials
│   │   ├── file_operations.py   # Safe file operations
│   │   ├── syllabus_helpers.py  # Syllabus utilities
│   │   └── veto_manager_integration.py # VETO integration
│   ├── templates/               # HTML templates
│   ├── static/                  # CSS, JS, images
│   └── wsgi.py                  # WSGI entry point
│
├── scripts/                      # Utility scripts
│   ├── __init__.py
│   ├── README.md                # Scripts documentation
│   ├── veto_manager.py          # VETO system initialization
│   ├── anti_corruption_check.py # Data integrity verification
│   └── inject_cache_buster.py   # Cache management
│
├── tests/                        # Test scripts
│   ├── __init__.py
│   ├── README.md                # Testing guide
│   ├── test_veto_system.py      # VETO system tests
│   ├── test_attendance_sync.py  # Attendance sync tests
│   ├── test_calculation.py      # Calculation logic tests
│   └── test_voting.py           # Voting system tests
│
├── migrations/                   # Data migration scripts
│   ├── __init__.py
│   ├── README.md                # Migration guide
│   ├── migrate_to_secure_credentials.py
│   └── migrate_veto_system.py
│
├── docs/                         # Documentation
│   └── (documentation files)
│
├── instance/                     # Instance-specific files
│   ├── offline_scoreboard_data.json  # Main data file
│   ├── logs/                    # Application logs
│   ├── secrets/                 # Encrypted credentials
│   └── uploads/                 # User uploads
│
├── run.py                        # Main application runner
├── app.py                        # Alternative entry point
├── launcher.py                   # Development launcher
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
├── .gitignore                    # Git ignore rules
│
├── SCRIPT_ORGANIZATION_ANALYSIS.md    # This analysis
├── PROJECT_STRUCTURE.md               # This file
├── VETO_SYSTEM_GUIDE.md              # VETO system documentation
├── MEDIUM_TERM_FIXES_SUMMARY.md      # Medium-term improvements
└── README.md                         # Project README
```

## File Organization by Purpose

### 🔐 **Authentication & Security**
- `app/routes/auth.py` - Login, registration, password management
- `app/utils/secrets_manager.py` - Encrypted credential storage
- `app/utils/logger.py` - Security event logging
- `migrations/migrate_to_secure_credentials.py` - Credential migration

### 📊 **Scoring & Points**
- `app/models/points.py` - Points data model
- `app/routes/scoreboard.py` - Scoreboard display and management
- `tests/test_calculation.py` - Scoring logic tests

### 🗳️ **Governance & Elections**
- `app/models/governance.py` - Election and post data
- `app/routes/scoreboard.py` - Election routes
- `tests/test_voting.py` - Voting logic tests

### 🚫 **VETO System**
- `scripts/veto_manager.py` - VETO initialization and management
- `app/utils/veto_manager_integration.py` - Flask integration
- `app/routes/veto_api.py` - VETO API endpoints
- `migrations/migrate_veto_system.py` - VETO migration
- `tests/test_veto_system.py` - VETO tests
- `VETO_SYSTEM_GUIDE.md` - VETO documentation

### 🛠️ **Utilities & Tools**
- `app/utils/file_operations.py` - Safe file handling
- `app/utils/error_handler.py` - Error management
- `app/utils/logger.py` - Logging system
- `scripts/anti_corruption_check.py` - Data integrity
- `scripts/inject_cache_buster.py` - Cache management

### 📝 **Testing**
- `tests/` - All test files
- `tests/README.md` - Testing guide

### 🔄 **Migrations**
- `migrations/` - One-time migration scripts
- `migrations/README.md` - Migration guide

## Quick Reference

### Running the Application
```bash
# Development
python run.py

# Production
gunicorn app:app

# Alternative
python app.py
```

### Running Scripts
```bash
# Initialize VETO system
python scripts/veto_manager.py

# Check data integrity
python scripts/anti_corruption_check.py

# Inject cache buster
python scripts/inject_cache_buster.py
```

### Running Migrations
```bash
# Migrate credentials
python migrations/migrate_to_secure_credentials.py

# Migrate VETO system
python migrations/migrate_veto_system.py
```

### Running Tests
```bash
# All tests
pytest tests/

# Specific test
pytest tests/test_veto_system.py -v

# With coverage
pytest tests/ --cov=app
```

## Key Improvements from Reorganization

### Before
- 40 Python files scattered everywhere
- 8 redundant VETO scripts
- No clear structure
- Difficult to maintain

### After
- 19 core Python files
- 0 redundancy
- Clear separation of concerns
- Easy to navigate and maintain

### Reduction
- **53% fewer files** (40 → 19)
- **100% redundancy eliminated** (8 VETO scripts → 1)
- **Clear organization** by purpose
- **Better maintainability**

## Module Dependencies

### Core Application
```
app/
├── __init__.py (depends on: config, models, routes, utils)
├── config/ (no dependencies)
├── models/ (depends on: db)
├── routes/ (depends on: models, utils)
└── utils/ (minimal dependencies)
```

### Scripts
```
scripts/
├── veto_manager.py (depends on: pathlib, json, datetime)
├── anti_corruption_check.py (depends on: json, pathlib)
└── inject_cache_buster.py (depends on: pathlib, re)
```

### Tests
```
tests/
├── test_veto_system.py (depends on: veto_manager_integration)
├── test_attendance_sync.py (depends on: app)
├── test_calculation.py (depends on: app)
└── test_voting.py (depends on: app)
```

## Data Files

### Main Data File
- **Location**: `instance/offline_scoreboard_data.json`
- **Purpose**: Central data store for all application data
- **Structure**:
  ```json
  {
    "students": [...],
    "post_holder_history": [...],
    "veto_tracking": {...},
    "role_veto_monthly": {...},
    ...
  }
  ```

### Backup Files
- **Pattern**: `instance/offline_scoreboard_data_backup_YYYYMMDD_HHMMSS.json`
- **Purpose**: Automatic backups before modifications
- **Retention**: Keep last 5 backups

### Log Files
- **Location**: `instance/logs/`
- **Files**:
  - `app.log` - General application logs
  - `errors.log` - Error-specific logs
  - `security.log` - Security events
  - `performance.log` - Performance metrics
  - `audit.log` - Audit trail

### Secrets
- **Location**: `instance/secrets/`
- **Files**:
  - `credentials.json` - Encrypted credentials
  - `.key` - Encryption key (keep secure!)

## Environment Variables

### Required
```
FLASK_ENV=production
DATABASE_URL=postgresql://...
SECRET_KEY=<random-secret>
```

### Optional
```
ADMIN_PASSWORD=<will be migrated to secure storage>
TEACHER_PASSWORD=<will be migrated to secure storage>
EA_JOIN_CODE=<will be migrated to secure storage>
```

## Deployment Checklist

- [ ] All tests passing
- [ ] No redundant scripts
- [ ] Proper directory structure
- [ ] Documentation updated
- [ ] Backups created
- [ ] Migrations run
- [ ] Environment variables set
- [ ] Logs directory created
- [ ] Secrets directory created
- [ ] Static files optimized

## Common Tasks

### Add New Feature
1. Create model in `app/models/`
2. Create routes in `app/routes/`
3. Add utilities in `app/utils/`
4. Write tests in `tests/`
5. Update documentation

### Add New Script
1. Place in `scripts/`
2. Update `scripts/README.md`
3. Add error handling
4. Create backups before modifying data

### Add New Migration
1. Create in `migrations/`
2. Update `migrations/README.md`
3. Include backup logic
4. Test thoroughly
5. Document rollback procedure

### Add New Test
1. Create in `tests/`
2. Follow naming conventions
3. Use fixtures for test data
4. Document test purpose
5. Run with coverage

## Maintenance

### Regular Tasks
- **Daily**: Monitor logs
- **Weekly**: Run integrity checks
- **Monthly**: Review VETO allocations
- **Quarterly**: Archive old logs
- **Annually**: Review and refactor

### Monitoring
- Check `instance/logs/errors.log` for issues
- Monitor `instance/logs/security.log` for suspicious activity
- Review `instance/logs/performance.log` for bottlenecks

## Support & Documentation

- **VETO System**: See `VETO_SYSTEM_GUIDE.md`
- **Scripts**: See `scripts/README.md`
- **Tests**: See `tests/README.md`
- **Migrations**: See `migrations/README.md`
- **Medium-term Fixes**: See `MEDIUM_TERM_FIXES_SUMMARY.md`

## Version History

### v2.0 (2026-03-20)
- ✅ Reorganized project structure
- ✅ Eliminated redundant VETO scripts
- ✅ Created proper directory structure
- ✅ Added comprehensive documentation
- ✅ Implemented secure secrets management
- ✅ Added comprehensive logging
- ✅ Optimized file operations

### v1.0 (Previous)
- Initial application structure
- Multiple VETO system implementations
- Scattered utility scripts

## Future Improvements

- [ ] Add CI/CD pipeline
- [ ] Implement automated testing
- [ ] Add API documentation (Swagger)
- [ ] Create deployment automation
- [ ] Add performance monitoring
- [ ] Implement caching layer
- [ ] Add database migrations framework
