from app import db
from datetime import datetime, date
import json

class StudentPoints(db.Model):
    """Model to track points/stars/vetos for students"""
    __tablename__ = 'student_points'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    date_recorded = db.Column(db.Date, nullable=False)
    points = db.Column(db.Integer, default=0)  # Daily score/points
    stars = db.Column(db.Integer, default=0)   # Stars awarded
    vetos = db.Column(db.Integer, default=0)   # Vetos (negative points)
    notes = db.Column(db.Text)                 # Notes about the points
    recorded_by = db.Column(db.String(120))    # Who recorded this
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    student = db.relationship('StudentProfile', backref=db.backref('points_records', lazy=True, cascade='all, delete-orphan'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'date': self.date_recorded.isoformat(),
            'points': self.points,
            'stars': self.stars,
            'vetos': self.vetos,
            'notes': self.notes,
            'recorded_by': self.recorded_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class StudentLeaderboard(db.Model):
    """Model to store aggregated monthly/yearly leaderboard data"""
    __tablename__ = 'student_leaderboard'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    total_points = db.Column(db.Integer, default=0)
    total_stars = db.Column(db.Integer, default=0)
    total_vetos = db.Column(db.Integer, default=0)
    rank = db.Column(db.Integer)
    days_active = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    student = db.relationship('StudentProfile', backref=db.backref('leaderboard_entries', lazy=True, cascade='all, delete-orphan'))
    
    __table_args__ = (db.UniqueConstraint('student_id', 'year', 'month', name='_student_year_month_uc'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'year': self.year,
            'month': self.month,
            'total_points': self.total_points,
            'total_stars': self.total_stars,
            'total_vetos': self.total_vetos,
            'rank': self.rank,
            'days_active': self.days_active,
            'last_updated': self.last_updated.isoformat()
        }


class MonthlyPointsSummary(db.Model):
    """Model to store daily/monthly point summaries"""
    __tablename__ = 'monthly_points_summary'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    date_month = db.Column(db.Date, nullable=False)  # First day of month
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    summary_data = db.Column(db.JSON, default={})  # {date: points_value, ...}
    total_points = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    student = db.relationship('StudentProfile', backref=db.backref('monthly_summaries', lazy=True, cascade='all, delete-orphan'))
    
    __table_args__ = (db.UniqueConstraint('student_id', 'year', 'month', name='_student_month_summary_uc'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'year': self.year,
            'month': self.month,
            'summary_data': self.summary_data,
            'total_points': self.total_points,
            'updated_at': self.updated_at.isoformat()
        }
