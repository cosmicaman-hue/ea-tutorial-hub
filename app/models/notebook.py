from app import db
from datetime import datetime

# ── Grade → points mapping (single source of truth) ──────────────────────────
GRADE_POINTS = {
    'Excellent':     5,
    'Very Good':     4,
    'Good':          3,
    'Fair':          2,
    'Satisfactory':  1,
    'Incomplete':   -5,
    'Untidy work':  -3,
    'Not submitted': -10,
}

DEFAULT_MAX_POINTS = 20
DEFAULT_MIN_POINTS = -30


class NotebookSubjectConfig(db.Model):
    """Configurable subject list per group/class/type (school or tuition)."""
    __tablename__ = 'notebook_subject_configs'

    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.String(10), nullable=False)
    class_name = db.Column(db.String(20), nullable=True)
    notebook_type = db.Column(db.String(20), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'group': self.group,
            'class_name': self.class_name,
            'notebook_type': self.notebook_type,
            'subject_name': self.subject_name,
            'order_index': self.order_index,
            'is_active': self.is_active,
        }


class NotebookCheck(db.Model):
    """One notebook-check session per student (by roll_number) per date per type."""
    __tablename__ = 'notebook_checks'

    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(30), nullable=False)
    student_name = db.Column(db.String(200))
    student_json_id = db.Column(db.Integer)
    group = db.Column(db.String(10))
    class_name = db.Column(db.String(20))
    date_checked = db.Column(db.Date, nullable=False)
    notebook_type = db.Column(db.String(20), nullable=False)
    consolidated_remarks = db.Column(db.Text)
    total_points = db.Column(db.Integer, default=0)
    recorded_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subject_checks = db.relationship(
        'NotebookSubjectCheck',
        backref='notebook_check',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='NotebookSubjectCheck.id',
    )

    def to_dict(self):
        return {
            'id': self.id,
            'roll_number': self.roll_number,
            'student_name': self.student_name,
            'student_json_id': self.student_json_id,
            'group': self.group,
            'class_name': self.class_name,
            'date_checked': self.date_checked.isoformat(),
            'notebook_type': self.notebook_type,
            'consolidated_remarks': self.consolidated_remarks,
            'total_points': self.total_points,
            'recorded_by': self.recorded_by,
            'created_at': self.created_at.isoformat(),
            'subject_checks': [sc.to_dict() for sc in self.subject_checks],
        }


class NotebookSubjectCheck(db.Model):
    """Per-subject row within a NotebookCheck session."""
    __tablename__ = 'notebook_subject_checks'

    id = db.Column(db.Integer, primary_key=True)
    notebook_check_id = db.Column(
        db.Integer, db.ForeignKey('notebook_checks.id'), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    is_checked = db.Column(db.Boolean, default=False)
    grade = db.Column(db.String(30), nullable=True)   # e.g. 'Excellent', 'Good', …
    points = db.Column(db.Integer, default=0)
    remarks = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'subject_name': self.subject_name,
            'is_checked': self.is_checked,
            'grade': self.grade,
            'points': self.points,
            'remarks': self.remarks,
        }


class NotebookScoreSettings(db.Model):
    """Singleton row: configurable max / min score limits for notebook checks."""
    __tablename__ = 'notebook_score_settings'

    id = db.Column(db.Integer, primary_key=True)
    max_points = db.Column(db.Integer, default=DEFAULT_MAX_POINTS, nullable=False)
    min_points = db.Column(db.Integer, default=DEFAULT_MIN_POINTS, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(120))

    @classmethod
    def get_settings(cls):
        """Return (or create) the singleton settings row."""
        s = cls.query.first()
        if not s:
            s = cls(max_points=DEFAULT_MAX_POINTS, min_points=DEFAULT_MIN_POINTS)
            from app import db as _db
            _db.session.add(s)
            _db.session.commit()
        return s

    def to_dict(self):
        return {
            'max_points': self.max_points,
            'min_points': self.min_points,
        }


class NotebookStudentExemption(db.Model):
    """Marks a subject as not-applicable for a specific student."""
    __tablename__ = 'notebook_student_exemptions'

    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(30), nullable=False, index=True)
    subject_name = db.Column(db.String(100), nullable=False)
    notebook_type = db.Column(db.String(20), nullable=False)   # 'school' | 'tuition'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            'roll_number', 'subject_name', 'notebook_type',
            name='uq_nb_student_exemption',
        ),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'roll_number': self.roll_number,
            'subject_name': self.subject_name,
            'notebook_type': self.notebook_type,
        }
