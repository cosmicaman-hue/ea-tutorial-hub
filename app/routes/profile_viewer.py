"""
Admin Profile Viewer Routes
View and manage all student profiles dynamically
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, StudentProfile
from sqlalchemy import func

profile_viewer_bp = Blueprint('profile_viewer', __name__, url_prefix='/admin/profiles')

@profile_viewer_bp.route('/', methods=['GET', 'POST'])
@login_required
def view_all_profiles():
    """View and filter all student profiles"""
    
    if current_user.role != 'admin':
        flash('Only admins can access this', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get filter parameters
    search_query = request.args.get('search', '')
    class_filter = request.args.get('class', '')
    school_filter = request.args.get('school', '')
    gender_filter = request.args.get('gender', '')
    sort_by = request.args.get('sort', 'created')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    query = db.session.query(User, StudentProfile).outerjoin(StudentProfile)
    query = query.filter(User.role == 'student')
    
    # Apply filters
    if search_query:
        query = query.filter(
            db.or_(
                User.login_id.ilike(f'%{search_query}%'),
                StudentProfile.first_name.ilike(f'%{search_query}%'),
                StudentProfile.second_name.ilike(f'%{search_query}%'),
                StudentProfile.email.ilike(f'%{search_query}%')
            )
        )
    
    if class_filter:
        query = query.filter(StudentProfile.class_name == class_filter)
    
    if school_filter:
        query = query.filter(StudentProfile.school_name.ilike(f'%{school_filter}%'))
    
    if gender_filter:
        query = query.filter(StudentProfile.gender == gender_filter)
    
    # Apply sorting
    if sort_by == 'name':
        query = query.order_by(StudentProfile.first_name)
    elif sort_by == 'class':
        query = query.order_by(StudentProfile.class_name)
    elif sort_by == 'school':
        query = query.order_by(StudentProfile.school_name)
    else:  # created (default)
        query = query.order_by(User.created_at.desc())
    
    # Paginate
    paginated = query.paginate(page=page, per_page=per_page)
    profiles = paginated.items
    
    # Get distinct values for filters
    classes = db.session.query(StudentProfile.class_name).distinct().all()
    schools = db.session.query(StudentProfile.school_name).distinct().all()
    genders = db.session.query(StudentProfile.gender).distinct().all()
    
    # Statistics
    total_students = User.query.filter_by(role='student').count()
    profiles_complete = StudentProfile.query.count()
    
    return render_template(
        'admin/view_all_profiles.html',
        profiles=profiles,
        paginated=paginated,
        search_query=search_query,
        class_filter=class_filter,
        school_filter=school_filter,
        gender_filter=gender_filter,
        sort_by=sort_by,
        classes=[c[0] for c in classes if c[0]],
        schools=[s[0] for s in schools if s[0]],
        genders=[g[0] for g in genders if g[0]],
        total_students=total_students,
        profiles_complete=profiles_complete
    )

@profile_viewer_bp.route('/<int:profile_id>', methods=['GET'])
@login_required
def view_profile_detail(profile_id):
    """View detailed profile of a student"""
    
    if current_user.role != 'admin':
        flash('Only admins can access this', 'error')
        return redirect(url_for('dashboard.index'))
    
    profile = StudentProfile.query.get_or_404(profile_id)
    user = User.query.get(profile.user_id)
    
    # Get student's activity
    from app.models.user import ActivityLog
    activities = ActivityLog.query.filter_by(user_id=user.id).order_by(
        ActivityLog.timestamp.desc()
    ).limit(20).all()
    
    # Get student's quiz attempts
    from app.models.quiz import QuizAnswer
    quiz_attempts = QuizAnswer.query.filter_by(student_id=user.id).order_by(
        QuizAnswer.attempt_date.desc()
    ).limit(10).all()
    
    return render_template(
        'admin/profile_detail.html',
        profile=profile,
        user=user,
        activities=activities,
        quiz_attempts=quiz_attempts
    )

@profile_viewer_bp.route('/api/stats', methods=['GET'])
@login_required
def get_profile_stats():
    """Get profile statistics (API endpoint)"""
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    stats = {
        'total_students': User.query.filter_by(role='student').count(),
        'profiles_complete': StudentProfile.query.count(),
        'by_class': {},
        'by_school': {},
        'by_gender': {},
        'recent_registrations': User.query.filter_by(role='student').order_by(
            User.created_at.desc()
        ).limit(5).count()
    }
    
    # Class distribution
    class_dist = db.session.query(
        StudentProfile.class_name,
        func.count(StudentProfile.id)
    ).group_by(StudentProfile.class_name).all()
    stats['by_class'] = {c[0]: c[1] for c in class_dist if c[0]}
    
    # School distribution
    school_dist = db.session.query(
        StudentProfile.school_name,
        func.count(StudentProfile.id)
    ).group_by(StudentProfile.school_name).all()
    stats['by_school'] = {s[0]: s[1] for s in school_dist if s[0]}
    
    # Gender distribution
    gender_dist = db.session.query(
        StudentProfile.gender,
        func.count(StudentProfile.id)
    ).group_by(StudentProfile.gender).all()
    stats['by_gender'] = {g[0]: g[1] for g in gender_dist if g[0]}
    
    return jsonify(stats)

@profile_viewer_bp.route('/export', methods=['GET'])
@login_required
def export_profiles():
    """Export all profiles as CSV"""
    
    if current_user.role != 'admin':
        flash('Only admins can access this', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        import csv
        from io import StringIO
        from flask import send_file
        
        # Query all profiles
        profiles = db.session.query(User, StudentProfile).outerjoin(StudentProfile).filter(
            User.role == 'student'
        ).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = [
            'Login ID', 'First Name', 'Second Name', 'Third Name', 'Gender',
            'Date of Birth', 'Email', 'Phone 1', 'Phone 2', 'School', 'Class',
            'Section', 'Village/Area', 'District', 'Nationality', 'Religion',
            'Account Created', 'Last Login'
        ]
        writer.writerow(headers)
        
        # Data rows
        for user, profile in profiles:
            if profile:
                row = [
                    user.login_id,
                    profile.first_name or '',
                    profile.second_name or '',
                    profile.third_name or '',
                    profile.gender or '',
                    profile.date_of_birth or '',
                    profile.email or '',
                    profile.contact_number_1 or '',
                    profile.contact_number_2 or '',
                    profile.school_name or '',
                    profile.class_name or '',
                    profile.section or '',
                    profile.village_area or '',
                    profile.district or '',
                    profile.nationality or '',
                    profile.religion or '',
                    user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                    user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else ''
                ]
                writer.writerow(row)
        
        output.seek(0)
        
        # Return as attachment
        from flask import make_response
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=student_profiles.csv"
        response.headers["Content-Type"] = "text/csv"
        
        return response
    
    except Exception as e:
        flash(f'Error exporting profiles: {str(e)}', 'error')
        return redirect(url_for('profile_viewer.view_all_profiles'))
