from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    login_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # admin, teacher, student
    is_active = db.Column(db.Boolean, default=True)
    first_login = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(50))
    password_changed_at = db.Column(db.DateTime)
    
    # Relationships
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user_rel', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def validate_login_id(login_id):
        """
        Validate login ID format:
        - Students: EA24A01 format
        - Admin: 'Admin'
        - Teacher: 'Teacher'
        """
        if login_id in ['Admin', 'Teacher']:
            return True
        
        # Student format: EA + 2 digits (24+) + letter (A-Z) + 2 digits (01-99)
        pattern = r'^EA\d{2}[A-Z]\d{2}$'
        if not re.match(pattern, login_id):
            return False
        
        year = int(login_id[2:4])
        last_digits = int(login_id[5:7])
        
        if year < 24:
            return False
        if not (1 <= last_digits <= 99):
            return False
        
        return True
    
    def __repr__(self):
        return f'<User {self.login_id}>'


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    action_type = db.Column(db.String(50))  # login, logout, upload, approve, delete, etc.
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ActivityLog {self.user_id} - {self.action_type}>'
