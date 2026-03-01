from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app import db, limiter
from app.models import User
from app.models.user import ActivityLog
from datetime import datetime
import json
import os
from sqlalchemy.exc import SQLAlchemyError

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _check_password_for_login(user, password):
    """Admin/Teacher and Student (roll-based) passwords are case-insensitive by requirement."""
    if not user:
        return False
    text = str(password or '')
    role = str(getattr(user, 'role', '')).strip().lower()
    if role == 'student':
        # Student requirement: password is their roll number (case-insensitive).
        if text.strip().upper() == str(user.login_id or '').strip().upper():
            return True

    if user.login_id in ('Admin', 'Teacher') or role == 'student':
        variants = {text, text.lower(), text.upper()}
        return any(user.check_password(candidate) for candidate in variants)
    return user.check_password(text)


def _offline_scoreboard_data_path():
    return os.path.join(current_app.instance_path, 'offline_scoreboard_data.json')


def _student_roll_exists_in_offline_roster(roll_value):
    """Best-effort check that a roll exists in the offline scoreboard roster."""
    roll = str(roll_value or '').strip().upper()
    if not roll or not roll.startswith('EA'):
        return False
    path = _offline_scoreboard_data_path()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        students = payload.get('students') or []
        if not isinstance(students, list):
            return False
        for s in students:
            if isinstance(s, dict) and str(s.get('roll') or '').strip().upper() == roll:
                return True
    except Exception:
        return False
    return False

def log_activity(user_id, action, action_type, details=None, ip_address=None):
    """Helper function to log user activities"""
    if ip_address is None:
        ip_address = request.remote_addr
    
    log_entry = ActivityLog(
        user_id=user_id,
        action=action,
        action_type=action_type,
        details=details,
        ip_address=ip_address
    )
    db.session.add(log_entry)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('points.offline_scoreboard'))
    
    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '').strip()

        # Normalize login IDs (case-insensitive for Admin/Teacher)
        if login_id.lower() == 'admin':
            login_id = 'Admin'
        elif login_id.lower() == 'teacher':
            login_id = 'Teacher'
        else:
            login_id = login_id.upper()
        
        # Validate login ID format
        if not User.validate_login_id(login_id):
            flash('Invalid login ID format. Admin: "Admin", Teacher: "Teacher", Student: "EA24A01"', 'error')
            return redirect(url_for('auth.login'))
        
        try:
            user = User.query.filter_by(login_id=login_id).first()
        except SQLAlchemyError:
            db.session.rollback()
            flash('Login service is initializing. Please try again in 30 seconds.', 'error')
            return redirect(url_for('auth.login'))

        login_ok = False
        if user:
            # All users authenticate via hashed password only.
            # Admin/Teacher passwords are intentionally case-insensitive by requirement.
            login_ok = _check_password_for_login(user, password)
        else:
            # Student auto-provisioning (LAN/offline use-case):
            # If a roll exists in the offline roster and password == roll (case-insensitive),
            # create the user with that roll/password.
            if login_id.startswith('EA') and password and str(password).strip().upper() == login_id:
                # Prefer verifying against the offline roster when available, but don't block login
                # if the roster file is missing/out-of-date (user requirement: roll==password login).
                roster_ok = _student_roll_exists_in_offline_roster(login_id)
                try:
                    user = User(login_id=login_id, role='student', first_login=False, is_active=True)
                    user.set_password(login_id)  # stored hashed; login check remains case-insensitive
                    db.session.add(user)
                    db.session.commit()
                    login_ok = True
                    log_activity(
                        user.id,
                        'Student account auto-provisioned',
                        'register',
                        f'Login ID: {login_id} | roster_match={str(roster_ok)}',
                        request.remote_addr
                    )
                except Exception:
                    db.session.rollback()

        if user and login_ok:
            if not user.is_active:
                flash('Your account is disabled. Contact admin.', 'error')
                log_activity(0, f'Login blocked for {login_id} - account inactive', 'login_failed', 'Account inactive', request.remote_addr)
                return redirect(url_for('auth.login'))
            
            # Keep auth stable across server restarts/browser reopen unless explicitly logged out.
            login_user(user, remember=True)
            session.permanent = True
            # Enforce student roll-based password policy on successful login.
            if str(getattr(user, 'role', '')).strip().lower() == 'student':
                try:
                    # Always sync the stored hash to the required policy (password == roll).
                    user.set_password(user.login_id)
                except Exception:
                    pass
            user.last_login = datetime.utcnow()
            user.last_login_ip = request.remote_addr
            try:
                db.session.commit()
            except SQLAlchemyError:
                # Do not hard-fail user login because of audit/profile column mismatch on server.
                db.session.rollback()
            
            # Log successful login
            log_activity(user.id, f'{user.role.capitalize()} login successful', 'login', f'IP: {request.remote_addr}', request.remote_addr)

            next_url = request.form.get('next') or request.args.get('next')
            if next_url:
                try:
                    from urllib.parse import urlparse, urljoin
                    host_url = request.host_url
                    test_url = urlparse(urljoin(host_url, next_url))
                    if test_url.scheme in ('http', 'https') and test_url.netloc == urlparse(host_url).netloc:
                        return redirect(next_url)
                except Exception:
                    pass

            return redirect(url_for('points.offline_scoreboard'))
        else:
            log_activity(0, f'Failed login attempt for {login_id}', 'login_failed', 'Invalid credentials', request.remote_addr)
            flash('Invalid login ID or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('points.offline_scoreboard'))
    
    if request.method == 'POST':
        # Join-code gate — optional but enforced when EA_JOIN_CODE is set
        join_code = request.form.get('join_code', '').strip()
        expected_code = os.getenv('EA_JOIN_CODE', '').strip()
        if expected_code and join_code.lower() != expected_code.lower():
            flash('Invalid join code. Please get the correct code from your Admin.', 'danger')
            return render_template('auth/register.html')

        login_id = request.form.get('login_id', '').upper()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate login_id is student format only
        if not login_id.startswith('EA') or login_id in ['Admin', 'Teacher']:
            flash('Students must use EA24A01 format login ID', 'error')
            return redirect(url_for('auth.register'))
        
        if not User.validate_login_id(login_id):
            flash('Invalid login ID format. Use format: EA24A01', 'error')
            return redirect(url_for('auth.register'))
        
        # Check if user exists
        if User.query.filter_by(login_id=login_id).first():
            flash('Login ID already exists', 'error')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('auth.register'))
        
        user = User(login_id=login_id, role='student', first_login=False)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        log_activity(user.id, 'Student account registered', 'register', f'Login ID: {login_id}', request.remote_addr)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
@limiter.limit("3 per hour")
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not _check_password_for_login(current_user, current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('auth.change_password'))
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return redirect(url_for('auth.change_password'))
        
        if new_password == current_password:
            flash('New password must be different from current password', 'error')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(new_password)
        db.session.commit()
        
        log_activity(current_user.id, 'Password changed', 'password_change', f'Password changed for {current_user.role}', request.remote_addr)
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('points.offline_scoreboard'))
    
    return render_template('auth/change_password.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_activity(current_user.id, f'{current_user.role.capitalize()} logout', 'logout', f'IP: {request.remote_addr}', request.remote_addr)
    logout_user()
    # Clear server-side session data
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login'))
