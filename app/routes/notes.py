from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import Notes
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import PyPDF2

notes_bp = Blueprint('notes', __name__, url_prefix='/notes')

ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_pdf_page_count(filepath):
    try:
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return len(pdf_reader.pages)
    except:
        return None

@notes_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    subject = request.args.get('subject', 'all')
    class_level = request.args.get('class', 'all')
    
    query = Notes.query.filter_by(is_approved=True)
    
    if subject != 'all':
        query = query.filter_by(subject=subject)
    if class_level != 'all':
        query = query.filter_by(class_level=class_level)
    
    notes = query.order_by(Notes.created_at.desc()).paginate(page=page, per_page=12)
    
    # Get unique subjects and classes for filters
    subjects = db.session.query(Notes.subject).filter_by(is_approved=True).distinct().all()
    classes = db.session.query(Notes.class_level).filter_by(is_approved=True).distinct().all()
    
    return render_template('notes/index.html', notes=notes, subjects=subjects, classes=classes,
                          selected_subject=subject, selected_class=class_level)

@notes_bp.route('/<int:note_id>')
@login_required
def view(note_id):
    note = Notes.query.get_or_404(note_id)
    if not note.is_approved and note.uploaded_by != current_user.id and current_user.role != 'admin':
        flash('This note is not available', 'error')
        return redirect(url_for('notes.index'))
    
    note.download_count += 1
    db.session.commit()
    
    return render_template('notes/view.html', note=note)

@notes_bp.route('/<int:note_id>/download')
@login_required
def download(note_id):
    note = Notes.query.get_or_404(note_id)
    if not note.is_approved and note.uploaded_by != current_user.id and current_user.role != 'admin':
        flash('This note is not available', 'error')
        return redirect(url_for('notes.index'))
    
    if os.path.exists(note.file_path):
        return send_file(note.file_path, as_attachment=True, download_name=secure_filename(note.title + '.pdf'))
    else:
        flash('File not found', 'error')
        return redirect(url_for('notes.index'))

@notes_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if current_user.role not in ['teacher', 'admin']:
        flash('Only teachers and admins can upload notes', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file provided', 'error')
            return redirect(url_for('notes.upload'))
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('notes.upload'))
        
        if not allowed_file(file.filename):
            flash('Only PDF files are allowed', 'error')
            return redirect(url_for('notes.upload'))
        
        if len(file.read()) > MAX_FILE_SIZE:
            flash('File size exceeds 50MB limit', 'error')
            return redirect(url_for('notes.upload'))
        
        file.seek(0)
        
        try:
            filename = secure_filename(f"{datetime.utcnow().timestamp()}_{file.filename}")
            upload_folder = 'app/static/uploads'
            os.makedirs(upload_folder, exist_ok=True)
            
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            
            page_count = get_pdf_page_count(filepath)
            file_size = os.path.getsize(filepath)
            
            note = Notes(
                title=request.form.get('title'),
                description=request.form.get('description', ''),
                subject=request.form.get('subject'),
                class_level=request.form.get('class_level'),
                file_path=filepath,
                file_size=file_size,
                total_pages=page_count,
                uploaded_by=current_user.id,
                is_approved=current_user.role == 'admin',  # Auto-approve for admins
                tags=request.form.get('tags', ''),
                language=request.form.get('language', 'English')
            )
            
            db.session.add(note)
            db.session.commit()
            
            status = 'approved' if note.is_approved else 'pending approval'
            flash(f'Notes uploaded successfully and {status}', 'success')
            return redirect(url_for('notes.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error uploading notes: {str(e)}', 'error')
    
    return render_template('notes/upload.html')

@notes_bp.route('/my-uploads')
@login_required
def my_uploads():
    if current_user.role not in ['teacher', 'admin']:
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    notes = Notes.query.filter_by(uploaded_by=current_user.id).order_by(Notes.created_at.desc()).paginate(page=page, per_page=12)
    return render_template('notes/my_uploads.html', notes=notes)
