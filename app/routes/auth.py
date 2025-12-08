from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, StudentProfile
from app.models.user import ActivityLog
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

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
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        login_id = request.form.get('login_id', '')
        password = request.form.get('password', '')
        
        # Convert to uppercase for student IDs, but preserve case for Admin/Teacher
        if login_id not in ['Admin', 'Teacher']:
            login_id = login_id.upper()
        
        # Validate login ID format
        if not User.validate_login_id(login_id):
            flash('Invalid login ID format. Admin: "Admin", Teacher: "Teacher", Student: "EA24A01"', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(login_id=login_id).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account is disabled. Contact admin.', 'error')
                log_activity(0, f'Login blocked for {login_id} - account inactive', 'login_failed', 'Account inactive', request.remote_addr)
                return redirect(url_for('auth.login'))
            
            login_user(user)
            user.last_login = datetime.utcnow()
            user.last_login_ip = request.remote_addr
            db.session.commit()
            
            # Log successful login
            log_activity(user.id, f'{user.role.capitalize()} login successful', 'login', f'IP: {request.remote_addr}', request.remote_addr)
            
            if user.first_login and user.role == 'student':
                return redirect(url_for('auth.complete_profile'))
            
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('dashboard.index'))
        else:
            log_activity(0, f'Failed login attempt for {login_id}', 'login_failed', 'Invalid credentials', request.remote_addr)
            flash('Invalid login ID or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
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
        
        user = User(login_id=login_id, role='student', first_login=True)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        log_activity(user.id, 'Student account registered', 'register', f'Login ID: {login_id}', request.remote_addr)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    if not current_user.first_login:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            profile = StudentProfile(
                user_id=current_user.id,
                first_name=request.form.get('first_name'),
                second_name=request.form.get('second_name'),
                third_name=request.form.get('third_name', ''),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date(),
                gender=request.form.get('gender'),
                religion=request.form.get('religion'),
                nationality=request.form.get('nationality', 'India'),
                school_name=request.form.get('school_name'),
                class_name=request.form.get('class_name'),
                section=request.form.get('section'),
                roll_number=request.form.get('roll_number', ''),
                contact_number_1=request.form.get('contact_number_1'),
                contact_number_2=request.form.get('contact_number_2', ''),
                email=request.form.get('email', current_user.login_id + '@school.local'),
                village_area=request.form.get('village_area'),
                post_office=request.form.get('post_office'),
                district=request.form.get('district'),
                state=request.form.get('state'),
                pin_code=request.form.get('pin_code'),
                hobbies=request.form.get('hobbies', ''),
                improvement_areas=request.form.get('improvement_areas', ''),
                father_name=request.form.get('father_name', ''),
                mother_name=request.form.get('mother_name', ''),
                guardian_name=request.form.get('guardian_name', ''),
                guardian_contact=request.form.get('guardian_contact', ''),
                blood_group=request.form.get('blood_group', ''),
                aadhar_number=request.form.get('aadhar_number', '')
            )
            
            current_user.first_login = False
            db.session.add(profile)
            db.session.commit()
            
            log_activity(current_user.id, 'Student profile completed', 'profile_complete', 'First login profile setup', request.remote_addr)
            
            flash('Profile completed successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error completing profile: {str(e)}', 'error')
    
    return render_template('auth/complete_profile.html')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_user.check_password(current_password):
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
        return redirect(url_for('dashboard.index'))
    
    return render_template('auth/change_password.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_activity(current_user.id, f'{current_user.role.capitalize()} logout', 'logout', f'IP: {request.remote_addr}', request.remote_addr)
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login'))
