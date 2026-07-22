"""
student_roster.py — Pure calculation helpers for student active roster checks.

Replicates the client-side lifecycle and visibility checks to determine if a
student profile is active for a given month or globally.
"""
from datetime import datetime
from app.utils.helpers import norm_roll, safe_int, month_key

def get_current_month():
    """Get the current UTC month in YYYY-MM format."""
    return datetime.utcnow().strftime('%Y-%m')

def is_roll_change_retired(student):
    """Check if the student is retired due to a roll change."""
    reason = str(student.get('retired_reason') or '').strip().lower()
    return reason.startswith('roll_changed_to:')

def is_student_active_for_month(student, target_month=None):
    """
    Determine if a student is active and visible for a specific month.
    Replicates the logic of client-side isStudentVisibleForMonth and getActiveStudents.
    """
    if not student:
        return False
    if student.get('active') is False:
        return False
    if is_roll_change_retired(student):
        return False

    month = month_key(target_month) if target_month else get_current_month()

    # Deactivation guard: student left after a certain month
    dm = str(student.get('deactivation_month') or '').strip()
    if dm and month >= dm:
        return False

    # Activation guard: student joined from a certain month onwards
    af = str(student.get('active_from_month') or '').strip()
    if af and month < af:
        return False

    return True

def get_active_students_for_month(students, target_month=None):
    """
    Returns the list of active students for the target month.
    """
    month = month_key(target_month) if target_month else get_current_month()
    return [s for s in students if s and s.get('roll') and is_student_active_for_month(s, month)]
