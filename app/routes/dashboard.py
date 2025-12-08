from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Notes, Quiz
from sqlalchemy import or_
import os

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    
    # Get featured notes and quizzes
    featured_notes = Notes.query.filter_by(is_approved=True).order_by(Notes.created_at.desc()).limit(6).all()
    featured_quizzes = Quiz.query.filter_by(is_active=True).order_by(Quiz.created_at.desc()).limit(6).all()
    
    return render_template('dashboard/index.html', notes=featured_notes, quizzes=featured_quizzes)

@dashboard_bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')  # all, notes, quizzes
    
    results = {'notes': [], 'quizzes': []}
    
    if query:
        if category in ['all', 'notes']:
            notes = Notes.query.filter(
                Notes.is_approved == True,
                or_(
                    Notes.title.ilike(f'%{query}%'),
                    Notes.description.ilike(f'%{query}%'),
                    Notes.subject.ilike(f'%{query}%'),
                    Notes.tags.ilike(f'%{query}%')
                )
            ).all()
            results['notes'] = notes
        
        if category in ['all', 'quizzes']:
            quizzes = Quiz.query.filter(
                Quiz.is_active == True,
                or_(
                    Quiz.title.ilike(f'%{query}%'),
                    Quiz.description.ilike(f'%{query}%'),
                    Quiz.subject.ilike(f'%{query}%')
                )
            ).all()
            results['quizzes'] = quizzes
    
    return render_template('dashboard/search.html', query=query, results=results, category=category)

@dashboard_bp.route('/profile')
@login_required
def profile():
    return render_template('dashboard/profile.html', user=current_user, profile=current_user.student_profile)

@dashboard_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        try:
            profile = current_user.student_profile
            if not profile:
                from app.models import StudentProfile
                profile = StudentProfile(user_id=current_user.id)
            
            profile.first_name = request.form.get('first_name')
            profile.second_name = request.form.get('second_name')
            profile.third_name = request.form.get('third_name', '')
            profile.contact_number_1 = request.form.get('contact_number_1')
            profile.contact_number_2 = request.form.get('contact_number_2', '')
            profile.hobbies = request.form.get('hobbies', '')
            profile.improvement_areas = request.form.get('improvement_areas', '')
            
            db.session.add(profile)
            db.session.commit()
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('dashboard/edit_profile.html', user=current_user, profile=current_user.student_profile)
