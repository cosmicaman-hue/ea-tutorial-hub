from app import db
from datetime import datetime
import json

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, unique=True)
    
    # Basic Information
    first_name = db.Column(db.String(100), nullable=True)
    second_name = db.Column(db.String(100), nullable=True)
    third_name = db.Column(db.String(100))
    full_name = db.Column(db.String(300))  # Combined name for easier access
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20))
    religion = db.Column(db.String(50))
    nationality = db.Column(db.String(50), default='India')
    
    # School Information
    school_name = db.Column(db.String(200))
    class_name = db.Column(db.String(20), nullable=False)
    group = db.Column(db.String(5), default='A')  # A, B, C, D
    section = db.Column(db.String(10))
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    
    # Contact Information
    contact_number_1 = db.Column(db.String(15))
    contact_number_2 = db.Column(db.String(15))
    email = db.Column(db.String(120), unique=True, nullable=True)
    
    # Address
    village_area = db.Column(db.String(100))
    post_office = db.Column(db.String(100))
    district = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pin_code = db.Column(db.String(10))
    
    # Personal Interests
    hobbies = db.Column(db.Text)  # Comma-separated or JSON
    improvement_areas = db.Column(db.Text)  # Comma-separated or JSON
    
    # Additional fields
    father_name = db.Column(db.String(100))
    mother_name = db.Column(db.String(100))
    guardian_name = db.Column(db.String(100))
    guardian_contact = db.Column(db.String(15))
    
    blood_group = db.Column(db.String(5))
    aadhar_number = db.Column(db.String(12))
    
    # Profile data - JSON field for extended information
    profile_data = db.Column(db.JSON, default={})
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudentProfile {self.full_name or self.roll_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'roll_number': self.roll_number,
            'full_name': self.full_name,
            'class': self.class_name,
            'group': self.group,
            'email': self.email,
            'contact_number': self.contact_number_1,
            'profile_data': self.profile_data or {}
        }

