"""
AI Quiz Generation Routes
Allows Admin and Teacher to create quizzes from uploaded documents using AI
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import db
from app.models import Quiz, QuizQuestion, User
from app.utils.ai_quiz_generator import AIQuizGenerator
from datetime import datetime

quiz_ai_bp = Blueprint('quiz_ai', __name__, url_prefix='/quiz-ai')

# Configuration
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'md'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
UPLOAD_FOLDER = 'uploads/documents'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath):
    """Extract text from various file types"""
    try:
        filename = os.path.basename(filepath)
        ext = filename.rsplit('.', 1)[1].lower()
        
        if ext == 'txt' or ext == 'md':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif ext == 'pdf':
            try:
                import PyPDF2
                text = ""
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text()
                return text
            except ImportError:
                return f"Please install PyPDF2 to extract PDF files: pip install PyPDF2"
        
        elif ext == 'docx':
            try:
                from docx import Document
                doc = Document(filepath)
                text = "\n".join([p.text for p in doc.paragraphs])
                return text
            except ImportError:
                return f"Please install python-docx to extract DOCX files: pip install python-docx"
        
        return "Unsupported file format"
    
    except Exception as e:
        return f"Error reading file: {str(e)}"

@quiz_ai_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_ai_quiz():
    """Create quiz using AI from uploaded document"""
    
    # Check permissions
    if current_user.role not in ['admin', 'teacher']:
        flash('Only admins and teachers can create quizzes', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # Handle file upload
        if 'document' not in request.files:
            flash('No document uploaded', 'error')
            return redirect(request.url)
        
        file = request.files['document']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('Invalid file type. Allowed: txt, pdf, docx, md', 'error')
            return redirect(request.url)
        
        if file.content_length > MAX_FILE_SIZE:
            flash('File too large. Max size: 5MB', 'error')
            return redirect(request.url)
        
        try:
            # Save uploaded file
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Extract text from document
            document_content = extract_text_from_file(filepath)
            
            if document_content.startswith('Error') or document_content.startswith('Please'):
                flash(document_content, 'warning')
                os.remove(filepath)
                return redirect(request.url)
            
            # Get parameters
            num_questions = min(int(request.form.get('num_questions', 10)), 50)
            difficulty = request.form.get('difficulty', 'medium')
            ai_provider = request.form.get('ai_provider', 'openai')
            quiz_title = request.form.get('quiz_title', 'AI Generated Quiz')
            
            # Generate quiz using AI
            generator = AIQuizGenerator()
            quiz_data = generator.generate_quiz(
                document_content=document_content,
                num_questions=num_questions,
                difficulty=difficulty,
                ai_provider=ai_provider
            )
            
            if 'error' in quiz_data:
                flash(f"AI Error: {quiz_data['error']}", 'error')
                os.remove(filepath)
                return redirect(request.url)
            
            # Save quiz to database
            quiz = Quiz(
                title=quiz_data.get('quiz_title', quiz_title),
                description=quiz_data.get('description', ''),
                created_by=current_user.id,
                is_active=True,
                ai_generated=True,
                ai_provider=ai_provider,
                source_document=filename
            )
            db.session.add(quiz)
            db.session.flush()  # Get quiz.id
            
            # Add questions
            for idx, q_data in enumerate(quiz_data.get('questions', [])):
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_text=q_data.get('question_text', ''),
                    question_type='multiple_choice',
                    options=q_data.get('options', []),
                    correct_answer=q_data.get('correct_answer', 'A'),
                    explanation=q_data.get('explanation', ''),
                    order=idx + 1
                )
                db.session.add(question)
            
            db.session.commit()
            
            # Clean up uploaded file (optional - can keep for reference)
            os.remove(filepath)
            
            flash(f'Quiz "{quiz.title}" created successfully with {len(quiz_data.get("questions", []))} questions!', 'success')
            return redirect(url_for('quiz.view', quiz_id=quiz.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating quiz: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('quiz/create_ai.html')

@quiz_ai_bp.route('/preview', methods=['POST'])
@login_required
def preview_quiz():
    """Preview quiz before saving (API endpoint)"""
    
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.json
        document_content = data.get('document_content', '')
        num_questions = min(int(data.get('num_questions', 10)), 50)
        difficulty = data.get('difficulty', 'medium')
        ai_provider = data.get('ai_provider', 'openai')
        
        generator = AIQuizGenerator()
        quiz_data = generator.generate_quiz(
            document_content=document_content,
            num_questions=num_questions,
            difficulty=difficulty,
            ai_provider=ai_provider
        )
        
        return jsonify(quiz_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@quiz_ai_bp.route('/list', methods=['GET'])
@login_required
def ai_quiz_list():
    """List AI-generated quizzes"""
    
    if current_user.role == 'admin':
        # Admin sees all AI quizzes
        quizzes = Quiz.query.filter_by(ai_generated=True).all()
    elif current_user.role == 'teacher':
        # Teacher sees own AI quizzes
        quizzes = Quiz.query.filter_by(ai_generated=True, created_by=current_user.id).all()
    else:
        flash('Only admins and teachers can view this', 'error')
        return redirect(url_for('dashboard.index'))
    
    return render_template('quiz/ai_quiz_list.html', quizzes=quizzes)

# Models extension (add to Quiz model in models/quiz.py)
# ai_generated = db.Column(db.Boolean, default=False)
# ai_provider = db.Column(db.String(50))  # openai, gemini, claude
# source_document = db.Column(db.String(255))  # filename of source document
