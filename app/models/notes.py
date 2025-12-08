from app import db
from datetime import datetime

class Notes(db.Model):
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(100), nullable=False, index=True)
    class_level = db.Column(db.String(20), nullable=False, index=True)  # e.g., "Class 9", "Class 10"
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # in bytes
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)  # Admin approval required
    
    # Metadata
    total_pages = db.Column(db.Integer)
    language = db.Column(db.String(50), default='English')
    tags = db.Column(db.String(500))  # Comma-separated
    
    # Analytics
    download_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notes {self.title}>'
