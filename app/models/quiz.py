from app import db
from datetime import datetime

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(100), default='General')
    class_level = db.Column(db.String(20), default='All Levels')
    duration_minutes = db.Column(db.Integer, default=60)
    total_points = db.Column(db.Integer, default=100)
    passing_score = db.Column(db.Integer, default=40)
    is_active = db.Column(db.Boolean, default=True)
    allow_retake = db.Column(db.Boolean, default=True)
    show_results = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', cascade='all, delete-orphan')
    answers = db.relationship('QuizAnswer', backref='quiz', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Quiz {self.title}>'


class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), default='multiple_choice')  # multiple_choice, true_false, short_answer
    points = db.Column(db.Integer, default=1)
    order = db.Column(db.Integer)
    
    # For multiple choice/true-false
    option_a = db.Column(db.String(500))
    option_b = db.Column(db.String(500))
    option_c = db.Column(db.String(500))
    option_d = db.Column(db.String(500))
    correct_answer = db.Column(db.String(10))  # A, B, C, D, or answer text
    
    # Explanation for learning
    explanation = db.Column(db.Text)
    
    def __repr__(self):
        return f'<QuizQuestion {self.id}>'


class QuizAnswer(db.Model):
    __tablename__ = 'quiz_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    student_answer = db.Column(db.String(500))
    is_correct = db.Column(db.Boolean)
    points_earned = db.Column(db.Integer, default=0)
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<QuizAnswer {self.id}>'
