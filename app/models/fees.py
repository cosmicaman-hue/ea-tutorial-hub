from app import db
from datetime import datetime

class FeeTransaction(db.Model):
    __tablename__ = 'fee_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    roll_number = db.Column(db.String(50), nullable=False)
    student_name = db.Column(db.String(255), nullable=False)
    txn_id = db.Column(db.String(100), unique=True, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    mode = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), default='tuition')
    ref_no = db.Column(db.String(100), nullable=True)
    note = db.Column(db.Text, nullable=True)
    recorded_by = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='confirmed')
    is_reversal = db.Column(db.Boolean, default=False)
    original_txn_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'roll_number': self.roll_number,
            'student_name': self.student_name,
            'txn_id': self.txn_id,
            'date': self.date,
            'amount': self.amount,
            'mode': self.mode,
            'category': self.category,
            'ref_no': self.ref_no,
            'note': self.note,
            'recorded_by': self.recorded_by,
            'status': self.status,
            'is_reversal': self.is_reversal,
            'original_txn_id': self.original_txn_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
