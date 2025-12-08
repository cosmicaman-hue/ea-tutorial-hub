from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Quiz, QuizQuestion, QuizAnswer
from sqlalchemy import func
from datetime import datetime

quiz_bp = Blueprint('quiz', __name__, url_prefix='/quiz')

@quiz_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    subject = request.args.get('subject', 'all')
    class_level = request.args.get('class', 'all')
    
    query = Quiz.query.filter_by(is_active=True)
    
    if subject != 'all':
        query = query.filter_by(subject=subject)
    if class_level != 'all':
        query = query.filter_by(class_level=class_level)
    
    quizzes = query.order_by(Quiz.created_at.desc()).paginate(page=page, per_page=12)
    
    subjects = db.session.query(Quiz.subject).filter_by(is_active=True).distinct().all()
    classes = db.session.query(Quiz.class_level).filter_by(is_active=True).distinct().all()
    
    return render_template('quiz/index.html', quizzes=quizzes, subjects=subjects, classes=classes,
                          selected_subject=subject, selected_class=class_level)

@quiz_bp.route('/<int:quiz_id>')
@login_required
def view(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if not quiz.is_active and current_user.role != 'admin':
        flash('This quiz is not available', 'error')
        return redirect(url_for('quiz.index'))
    
    # Check if user has already attempted
    attempt_count = QuizAnswer.query.filter_by(quiz_id=quiz_id, user_id=current_user.id).first()
    
    if attempt_count and not quiz.allow_retake:
        flash('You have already completed this quiz and retakes are not allowed', 'error')
        return redirect(url_for('quiz.index'))
    
    return render_template('quiz/view.html', quiz=quiz)

@quiz_bp.route('/<int:quiz_id>/start')
@login_required
def start(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if not quiz.is_active and current_user.role != 'admin':
        flash('This quiz is not available', 'error')
        return redirect(url_for('quiz.index'))
    
    # Check if user has already attempted
    previous_answers = QuizAnswer.query.filter_by(quiz_id=quiz_id, user_id=current_user.id).all()
    
    if previous_answers and not quiz.allow_retake:
        flash('You have already completed this quiz and retakes are not allowed', 'error')
        return redirect(url_for('quiz.index'))
    
    # Delete previous answers if retake is allowed
    if previous_answers and quiz.allow_retake:
        for answer in previous_answers:
            db.session.delete(answer)
        db.session.commit()
    
    questions = quiz.questions
    return render_template('quiz/start.html', quiz=quiz, questions=questions)

@quiz_bp.route('/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    data = request.get_json()
    
    total_points = 0
    correct_answers = 0
    
    for question_id, student_answer in data.get('answers', {}).items():
        question = QuizQuestion.query.get(question_id)
        if not question or question.quiz_id != quiz_id:
            continue
        
        is_correct = student_answer.upper() == question.correct_answer.upper()
        points = question.points if is_correct else 0
        
        if is_correct:
            correct_answers += 1
        total_points += points
        
        answer = QuizAnswer(
            quiz_id=quiz_id,
            question_id=int(question_id),
            user_id=current_user.id,
            student_answer=student_answer,
            is_correct=is_correct,
            points_earned=points
        )
        db.session.add(answer)
    
    db.session.commit()
    
    percentage = (total_points / quiz.total_points * 100) if quiz.total_points > 0 else 0
    passed = percentage >= quiz.passing_score
    
    return jsonify({
        'success': True,
        'total_points': total_points,
        'correct_answers': correct_answers,
        'total_questions': len(quiz.questions),
        'percentage': round(percentage, 2),
        'passed': passed,
        'passing_score': quiz.passing_score,
        'redirect_url': url_for('quiz.results', quiz_id=quiz_id)
    })

@quiz_bp.route('/<int:quiz_id>/results')
@login_required
def results(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    user_answers = QuizAnswer.query.filter_by(quiz_id=quiz_id, user_id=current_user.id).all()
    
    if not user_answers:
        flash('No quiz attempt found', 'error')
        return redirect(url_for('quiz.index'))
    
    total_points = sum(answer.points_earned for answer in user_answers)
    correct_count = sum(1 for answer in user_answers if answer.is_correct)
    
    percentage = (total_points / quiz.total_points * 100) if quiz.total_points > 0 else 0
    passed = percentage >= quiz.passing_score
    
    return render_template('quiz/results.html', quiz=quiz, user_answers=user_answers,
                          total_points=total_points, correct_count=correct_count,
                          percentage=round(percentage, 2), passed=passed)

@quiz_bp.route('/my-attempts')
@login_required
def my_attempts():
    page = request.args.get('page', 1, type=int)
    
    # Get unique quizzes user has attempted
    quiz_attempts = db.session.query(
        Quiz,
        func.sum(QuizAnswer.points_earned).label('total_points'),
        func.count(QuizAnswer.id).label('attempt_count'),
        func.max(QuizAnswer.submitted_at).label('last_attempt')
    ).join(QuizAnswer).filter(
        QuizAnswer.user_id == current_user.id
    ).group_by(Quiz.id).order_by(
        QuizAnswer.submitted_at.desc()
    ).paginate(page=page, per_page=10)
    
    return render_template('quiz/my_attempts.html', quiz_attempts=quiz_attempts)
