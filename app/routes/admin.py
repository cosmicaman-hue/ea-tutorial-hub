from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Notes, StudentProfile, Quiz, QuizQuestion
from app.models.user import ActivityLog
from datetime import datetime
import os
import string
import random

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def generate_temp_password(length=8):
    """Generate a random temporary password"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_notes = Notes.query.count()
    pending_notes = Notes.query.filter_by(is_approved=False).count()
    total_quizzes = Quiz.query.count()
    
    # Get recent activity
    recent_logins = ActivityLog.query.filter_by(action_type='login').order_by(ActivityLog.timestamp.desc()).limit(10).all()
    recent_activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    stats = {
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_notes': total_notes,
        'pending_notes': pending_notes,
        'total_quizzes': total_quizzes
    }
    
    return render_template('admin/dashboard.html', stats=stats, recent_activities=recent_activities)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    role = request.args.get('role', 'all')
    
    query = User.query
    if role != 'all':
        query = query.filter_by(role=role)
    
    users = query.paginate(page=page, per_page=20)
    return render_template('admin/manage_users.html', users=users, selected_role=role)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        login_id = request.form.get('login_id', '').upper()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')
        
        if not User.validate_login_id(login_id):
            flash('Invalid login ID format', 'error')
            return redirect(url_for('admin.create_user'))
        
        if User.query.filter_by(login_id=login_id).first():
            flash('Login ID already exists', 'error')
            return redirect(url_for('admin.create_user'))
        
        user = User(login_id=login_id, role=role, first_login=True)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {login_id} created successfully', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/create_user.html')

@admin_bp.route('/users/<int:user_id>/toggle-status')
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot disable your own account', 'error')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f'User status updated', 'success')
    
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
@admin_required
def reset_password(user_id):
    """Admin can reset any user's password"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return redirect(url_for('admin.reset_password', user_id=user_id))
        
        user.set_password(new_password)
        db.session.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=current_user.id,
            action=f'Admin reset password for {user.login_id}',
            action_type='password_reset_by_admin',
            details=f'Password reset for {user.role} account: {user.login_id}',
            ip_address=request.remote_addr
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'Password reset for user {user.login_id}', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/reset_password.html', user=user)

@admin_bp.route('/notes/pending')
@login_required
@admin_required
def pending_notes():
    page = request.args.get('page', 1, type=int)
    notes = Notes.query.filter_by(is_approved=False).paginate(page=page, per_page=20)
    return render_template('admin/pending_notes.html', notes=notes)

@admin_bp.route('/notes/<int:note_id>/approve')
@login_required
@admin_required
def approve_note(note_id):
    note = Notes.query.get_or_404(note_id)
    note.is_approved = True
    db.session.commit()
    flash(f'Notes "{note.title}" approved', 'success')
    return redirect(url_for('admin.pending_notes'))

@admin_bp.route('/notes/<int:note_id>/reject')
@login_required
@admin_required
def reject_note(note_id):
    note = Notes.query.get_or_404(note_id)
    if os.path.exists(note.file_path):
        os.remove(note.file_path)
    db.session.delete(note)
    db.session.commit()
    flash('Notes rejected and deleted', 'success')
    return redirect(url_for('admin.pending_notes'))

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    return render_template('admin/settings.html')

@admin_bp.route('/activity-log')
@login_required
@admin_required
def activity_log():
    """Monitor all user activities on the website"""
    page = request.args.get('page', 1, type=int)
    action_type = request.args.get('action_type', 'all')
    
    query = ActivityLog.query
    if action_type != 'all':
        query = query.filter_by(action_type=action_type)
    
    activities = query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=50)
    
    # Get action type counts
    action_types = db.session.query(ActivityLog.action_type, db.func.count()).group_by(ActivityLog.action_type).all()
    
    return render_template('admin/activity_log.html', activities=activities, action_types=action_types, selected_action=action_type)
