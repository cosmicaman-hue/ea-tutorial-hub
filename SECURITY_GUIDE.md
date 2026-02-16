# 🔒 Project EA Security Guide

**Last Updated:** 2026-02-13
**Version:** 1.0

## Table of Contents
1. [Security Improvements Completed](#security-improvements-completed)
2. [Critical: First-Time Setup](#critical-first-time-setup)
3. [Environment Variables](#environment-variables)
4. [Authentication & Access Control](#authentication--access-control)
5. [Data Protection](#data-protection)
6. [Network Security](#network-security)
7. [Security Checklist](#security-checklist)
8. [Incident Response](#incident-response)

---

## Security Improvements Completed

### ✅ Fixed Critical Security Issues (2026-02-13)

1. **Removed Hardcoded Credentials**
   - **Issue:** Admin password `917511` and Teacher password `EA25T01` were hardcoded
   - **Fix:** Now uses environment variables `ADMIN_PASSWORD` and `TEACHER_PASSWORD`
   - **Files Changed:**
     - [app/routes/auth.py](app/routes/auth.py:57-62)
     - [run.py](run.py:21-27)
     - [.env](.env:9-11)

2. **Strong SECRET_KEY Generated**
   - **Issue:** Weak default SECRET_KEY `your-secret-key-change-this-in-production`
   - **Fix:** Generated cryptographically secure 64-character hex key
   - **Impact:** Protects session cookies and CSRF tokens
   - **File Changed:** [.env](.env:3)

3. **CSRF Protection Added**
   - **Issue:** No CSRF protection on forms (vulnerable to cross-site request forgery)
   - **Fix:** Implemented Flask-WTF CSRF protection on all forms
   - **Files Changed:**
     - [app/__init__.py](app/__init__.py) - Added CSRFProtect
     - [app/templates/auth/login.html](app/templates/auth/login.html)
     - [app/templates/auth/register.html](app/templates/auth/register.html)
     - [app/templates/auth/change_password.html](app/templates/auth/change_password.html)
     - [app/templates/auth/complete_profile.html](app/templates/auth/complete_profile.html)
   - **Exempted:** `/scoreboard/offline-data` (uses sync key authentication)

4. **Rate Limiting Implemented**
   - **Issue:** No protection against brute force attacks
   - **Fix:** Added Flask-Limiter with specific limits per route
   - **Limits:**
     - Login: 10 attempts per minute
     - Registration: 5 per hour
     - Password Change: 3 per hour
     - Default: 200 per day, 50 per hour
   - **File Changed:** [app/__init__.py](app/__init__.py), [app/routes/auth.py](app/routes/auth.py)

5. **Enhanced File Upload Validation**
   - **Issue:** Limited validation on Excel imports
   - **Fix:** Added comprehensive validation:
     - File extension check (.xlsx, .xls, .xlsm)
     - MIME type verification
     - File size validation (max 50MB)
     - Secure openpyxl loading (data_only=True, keep_vba=False)
     - Automatic temp file cleanup
   - **File Changed:** [app/routes/scoreboard.py](app/routes/scoreboard.py:1673-1707)

6. **Fixed Hardcoded Paths**
   - **Issue:** Launcher had hardcoded path `C:\Users\sujit\Desktop\Project EA`
   - **Fix:** Now uses dynamic path detection via `__file__`
   - **Impact:** Portable across different systems
   - **File Changed:** [launcher.py](launcher.py:20-21)

---

## Critical: First-Time Setup

### 🚨 MUST DO IMMEDIATELY AFTER DEPLOYMENT

1. **Change Default Passwords**

   The system has new secure default passwords set in `.env`:
   - Admin: `ExcelAdmin@2026!Secure`
   - Teacher: `ExcelTeacher@2026!Secure`

   **CRITICAL:** Change these immediately after first login using the `/auth/change-password` route.

2. **Update Environment Variables**

   Edit the `.env` file with production-specific values:
   ```env
   FLASK_ENV=production
   SECRET_KEY=<keep the generated one - do not change>
   ADMIN_PASSWORD=<your-strong-admin-password>
   TEACHER_PASSWORD=<your-strong-teacher-password>
   ```

3. **Install New Dependencies**

   The security fixes require new packages:
   ```bash
   pip install -r requirements.txt
   ```

   New packages added:
   - Flask-WTF==1.2.1 (CSRF protection)
   - Flask-Limiter==3.5.0 (Rate limiting)

4. **Verify Installation**

   Test the following:
   - [ ] Login page loads (should work with new passwords)
   - [ ] Forms have CSRF tokens (view page source, search for `csrf_token`)
   - [ ] Rate limiting works (try 11 failed logins - should be blocked)
   - [ ] Excel import validates files

---

## Environment Variables

### Current Configuration

Location: `.env` file in project root

```env
FLASK_APP=run.py
FLASK_ENV=development                    # Change to 'production' for live deployment
SECRET_KEY=<64-char-hex-key>            # DO NOT CHANGE - auto-generated secure key
DATABASE_URL=sqlite:///ea_tutorial.db
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=52428800             # 50MB file upload limit

# Authentication (CHANGE THESE!)
ADMIN_PASSWORD=ExcelAdmin@2026!Secure
TEACHER_PASSWORD=ExcelTeacher@2026!Secure

# Optional: Sync replication key
SYNC_SHARED_KEY=<your-sync-key-if-using-multi-node>
```

### Password Requirements

**Strong Password Guidelines:**
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Not based on dictionary words
- Unique (not reused from other systems)

**Examples of Strong Passwords:**
```
EA-Admin#2026$Secure!Today
Teach3r@Excel*Academy^2026
```

**Bad Passwords (DO NOT USE):**
```
password123
admin2026
EA25T01
```

---

## Authentication & Access Control

### User Roles & Permissions

| Role | Login ID Format | Permissions | Default Password Source |
|------|----------------|-------------|------------------------|
| Admin | `Admin` | Full access: import, add/delete students, modify all data | `.env` ADMIN_PASSWORD |
| Teacher | `Teacher` | View all, add points, view profiles | `.env` TEACHER_PASSWORD |
| Student | `EA24A01` | View own profile, view scoreboard | Roll number or custom |

### Auto-Creation of Student Accounts

**Security Note:** Students are auto-created on first valid login attempt.

**How it works:**
1. Student enters valid login ID format (e.g., `EA24A01`)
2. Student enters any valid roll number format as password
3. System creates account with that password (hashed)
4. Student must complete profile on first login

**Recommendation:** Consider disabling auto-creation in production and require admin approval.

### Login Rate Limiting

**Protection Against Brute Force:**
- Login attempts: **10 per minute per IP**
- Registration: **5 per hour per IP**
- Password changes: **3 per hour per IP**

**When Rate Limit Exceeded:**
- User sees: "429 Too Many Requests"
- Wait 60 seconds for login attempts to reset
- Activity is logged for monitoring

### CSRF Protection

**All forms now require CSRF tokens:**
- Login form
- Registration form
- Profile completion
- Password change
- Admin operations (via JavaScript in offline scoreboard)

**How it works:**
1. Server generates unique token per session
2. Token embedded in form as hidden field: `<input type="hidden" name="csrf_token" value="...">`
3. Server validates token on form submission
4. Invalid/missing token = 400 Bad Request

**Exempted endpoints:**
- `/scoreboard/offline-data` - Uses sync key authentication instead

---

## Data Protection

### Database Security

**Location:** `instance/ea_tutorial.db` (SQLite)

**Protections:**
- Passwords hashed with Werkzeug (PBKDF2)
- SQLAlchemy ORM prevents SQL injection
- Activity logging tracks all actions

**Backup Recommendations:**
```bash
# Automated daily backup
cp instance/ea_tutorial.db instance/backups/ea_tutorial_$(date +%Y%m%d).db

# Keep last 30 days
find instance/backups/ -name "*.db" -mtime +30 -delete
```

### File Upload Security

**Excel Import Protection:**
- File extension whitelist: `.xlsx`, `.xls`, `.xlsm`
- MIME type validation
- File size limit: 50MB (configurable)
- VBA macros disabled (`keep_vba=False`)
- Formula execution disabled (`data_only=True`)
- Automatic cleanup of temp files

**Allowed MIME types:**
- `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `application/vnd.ms-excel`
- `application/vnd.ms-excel.sheet.macroEnabled.12`

### Session Security

**Configuration:**
- Secret key: 64-character cryptographically secure random hex
- Session cookie: HTTPOnly, Secure (in production)
- Login tracking: IP address, timestamp logged

**Session Timeout:**
- Default: Flask's permanent session (31 days)
- **Recommendation:** Set shorter timeout for production:
  ```python
  app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
  ```

---

## Network Security

### Deployment Configurations

#### Local Network (Current Setup)

**Server Info:**
- Hostname: `ExcelAcademy`
- IP: `192.168.0.163`
- Port: `5000`
- Protocol: HTTP (no SSL/TLS)

**Access:**
- Desktop: `http://127.0.0.1:5000`
- Mobile (same network): `http://192.168.0.163:5000`

**Security Concerns:**
- ⚠️ No encryption (HTTP not HTTPS)
- ⚠️ Passwords transmitted in plaintext over local network
- ✅ Acceptable for trusted local network only
- ❌ DO NOT expose to internet

#### Production Deployment (Recommended)

**If deploying to public internet, you MUST:**

1. **Use HTTPS with SSL/TLS Certificate**
   - Get free certificate from Let's Encrypt
   - Use reverse proxy (nginx/Apache) with SSL termination

   Example nginx config:
   ```nginx
   server {
       listen 443 ssl;
       server_name ea.yourschool.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. **Use Production WSGI Server**
   - Replace Flask dev server with Gunicorn/uWSGI

   Example with Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 127.0.0.1:5000 run:app
   ```

3. **Configure Firewall**
   ```bash
   # Ubuntu/Debian
   sudo ufw allow 443/tcp
   sudo ufw deny 5000/tcp  # Block direct access
   sudo ufw enable
   ```

4. **Set Secure Session Cookies**

   Add to `app/__init__.py`:
   ```python
   app.config['SESSION_COOKIE_SECURE'] = True
   app.config['SESSION_COOKIE_HTTPONLY'] = True
   app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
   ```

### Peer-to-Peer Synchronization

**Sync Key Authentication:**
- Endpoint: `/scoreboard/offline-data`
- Protected by: `SYNC_SHARED_KEY` environment variable
- CSRF exempt (uses key-based auth instead)

**Security Recommendations:**
- Use strong, random sync key (32+ characters)
- Change sync key if compromised
- Monitor sync activity in logs
- Restrict sync to trusted IPs only

---

## Security Checklist

### Pre-Deployment Checklist

- [ ] Changed default admin password
- [ ] Changed default teacher password
- [ ] Updated `FLASK_ENV=production` in `.env`
- [ ] Generated new `SECRET_KEY` (or kept auto-generated one)
- [ ] Installed all dependencies from `requirements.txt`
- [ ] Tested login with new passwords
- [ ] Verified CSRF tokens appear in forms
- [ ] Tested rate limiting (try 11 failed logins)
- [ ] Backed up existing database
- [ ] Set appropriate file permissions on `.env` (chmod 600)
- [ ] Reviewed activity logs for suspicious entries

### Production Deployment Checklist

- [ ] SSL/TLS certificate installed
- [ ] Using production WSGI server (Gunicorn/uWSGI)
- [ ] Reverse proxy configured (nginx/Apache)
- [ ] Firewall configured (only 80/443 open)
- [ ] Secure session cookies enabled
- [ ] Database backups automated
- [ ] Log rotation configured
- [ ] Monitoring/alerting set up
- [ ] Incident response plan documented

### Monthly Security Review

- [ ] Review activity logs for anomalies
- [ ] Check for failed login attempts
- [ ] Update dependencies (`pip list --outdated`)
- [ ] Review user accounts (remove inactive)
- [ ] Test backup restoration
- [ ] Verify SSL certificate not expiring soon
- [ ] Review and rotate passwords if needed

---

## Incident Response

### Suspected Unauthorized Access

**Immediate Actions:**
1. Change all admin/teacher passwords via `/auth/change-password`
2. Review activity logs: `SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 100;`
3. Check for unauthorized users: `SELECT * FROM user WHERE is_active=1;`
4. Disable suspicious accounts: Update `is_active=0`

**Investigation:**
```python
# Connect to database
sqlite3 instance/ea_tutorial.db

# Check recent logins
SELECT user_id, action, timestamp, ip_address
FROM activity_log
WHERE action_type='login'
ORDER BY timestamp DESC
LIMIT 50;

# Check failed login attempts
SELECT action, timestamp, ip_address
FROM activity_log
WHERE action_type='login_failed'
ORDER BY timestamp DESC;
```

### Data Breach Response

**If database compromised:**
1. Immediately shut down server
2. Disconnect from network
3. Preserve evidence (copy database, logs)
4. Restore from last known good backup
5. Force password reset for all users
6. Notify affected users (if required by policy/law)

### Password Reset Procedure

**Admin/Teacher Password Reset:**
1. Edit `.env` file
2. Update `ADMIN_PASSWORD` or `TEACHER_PASSWORD`
3. Restart server: `python run.py`
4. Login with new password
5. Change password again via web interface

**Student Password Reset:**
1. Admin logs in
2. Access database directly or use admin panel
3. Set temporary password
4. Notify student to change password on next login

---

## Additional Security Recommendations

### Future Enhancements

**High Priority:**
1. Implement 2FA (Two-Factor Authentication) for admin/teacher
2. Add email verification for student registration
3. Implement password complexity requirements
4. Add account lockout after X failed attempts
5. Encrypt sensitive data at rest

**Medium Priority:**
1. Add audit trail viewing in admin panel
2. Implement IP whitelisting for admin access
3. Add reCAPTCHA to login/register forms
4. Enable database encryption (switch to PostgreSQL with encryption)
5. Implement automated security scanning

**Low Priority:**
1. Add password expiry policy (force change every 90 days)
2. Implement session timeout warnings
3. Add security headers (X-Frame-Options, CSP, etc.)
4. Enable detailed security logging
5. Implement intrusion detection

### Security Headers (Add to nginx/Apache)

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

---

## Support & Contact

**Security Issues:**
- Report security vulnerabilities immediately
- Do not disclose publicly until fixed
- Contact: [Add contact information]

**Documentation:**
- Main README: [EA_README.md](EA_README.md)
- Quick Start: [EA_QUICK_START.md](EA_QUICK_START.md)
- Deployment: [24X7_DEPLOYMENT_CHECKLIST.md](24X7_DEPLOYMENT_CHECKLIST.md)

---

**Last Security Audit:** 2026-02-13
**Next Scheduled Review:** 2026-03-13
**Document Version:** 1.0
**Status:** ✅ All critical issues resolved
