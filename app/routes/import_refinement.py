"""
Import Refinement Module
Handles historical data import vs latest roster import with proper isolation
"""

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import json
import os


def get_current_month_key():
    """Get current month in YYYY-MM format"""
    return datetime.now().strftime('%Y-%m')


def get_current_month_start():
    """Get first day of current month"""
    return datetime.now().replace(day=1).date()


def is_historical_date(date_value):
    """Check if a date is in a previous month (not current month)"""
    if isinstance(date_value, str):
        try:
            date_value = datetime.fromisoformat(date_value).date()
        except:
            return False

    if not isinstance(date_value, date):
        return False

    current_month_start = get_current_month_start()
    return date_value < current_month_start


def is_current_month_date(date_value):
    """Check if a date is in the current month"""
    if isinstance(date_value, str):
        try:
            date_value = datetime.fromisoformat(date_value).date()
        except:
            return False

    if not isinstance(date_value, date):
        return False

    current_month_start = get_current_month_start()
    # Get next month start
    next_month = (datetime.now().replace(day=1) + relativedelta(months=1)).date()

    return current_month_start <= date_value < next_month


def preserve_student_status(new_student_data, existing_students_map):
    """
    Preserve student active/inactive status from existing system data

    Args:
        new_student_data: dict with student data from import
        existing_students_map: dict mapping roll -> existing student data

    Returns:
        Updated student data with preserved status
    """
    roll = new_student_data.get('roll')

    if roll and roll in existing_students_map:
        existing_student = existing_students_map[roll]

        # Preserve critical system fields
        new_student_data['active'] = existing_student.get('active', True)
        new_student_data['id'] = existing_student.get('id')

        # Preserve stars and veto_count (system managed)
        if 'stars' in existing_student:
            new_student_data['stars'] = existing_student['stars']
        if 'veto_count' in existing_student:
            new_student_data['veto_count'] = existing_student['veto_count']

        # Preserve profile_data (system settings)
        if 'profile_data' in existing_student:
            # Merge but prefer existing profile_data for system fields
            new_profile = new_student_data.get('profile_data', {})
            existing_profile = existing_student.get('profile_data', {})

            # Update scoreboard fields from import
            merged_profile = existing_profile.copy()
            if 'fees' in new_profile:
                merged_profile['fees'] = new_profile['fees']
            if 'total_score' in new_profile:
                merged_profile['total_score'] = new_profile['total_score']
            if 'rank' in new_profile:
                merged_profile['rank'] = new_profile['rank']
            if 'vote_power' in new_profile:
                merged_profile['vote_power'] = new_profile['vote_power']

            new_student_data['profile_data'] = merged_profile
    else:
        # New student - set defaults
        new_student_data['active'] = True
        if 'stars' not in new_student_data:
            new_student_data['stars'] = 0
        if 'veto_count' not in new_student_data:
            new_student_data['veto_count'] = 0

    return new_student_data


def filter_scores_by_date_range(scores, filter_function):
    """
    Filter scores based on date criteria

    Args:
        scores: list of score records
        filter_function: function that takes a date and returns True/False

    Returns:
        Filtered list of scores
    """
    filtered = []
    for score in scores:
        score_date = score.get('date')
        if score_date and filter_function(score_date):
            filtered.append(score)

    return filtered


def merge_scores_preserving_existing(new_scores, existing_scores, filter_function):
    """
    Merge new scores with existing scores, preserving existing data

    Args:
        new_scores: scores from import
        existing_scores: scores already in system
        filter_function: function to filter which scores to update

    Returns:
        Merged scores list
    """
    # Create map of existing scores by student_id + date
    existing_map = {}
    for score in existing_scores:
        key = f"{score.get('studentId')}_{score.get('date')}"
        existing_map[key] = score

    # Filter new scores
    filtered_new = filter_scores_by_date_range(new_scores, filter_function)

    # Add/update filtered scores
    for new_score in filtered_new:
        key = f"{new_score.get('studentId')}_{new_score.get('date')}"
        existing_map[key] = new_score

    # Keep all existing scores
    return list(existing_map.values())


def validate_import_data(data, import_type='historical'):
    """
    Validate that import data meets requirements

    Args:
        data: imported data dict
        import_type: 'historical' or 'latest_roster'

    Returns:
        (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Import data must be a dictionary"

    if 'students' not in data:
        return False, "Import data must contain 'students' array"

    if 'scores' not in data:
        return False, "Import data must contain 'scores' array"

    students = data.get('students', [])
    scores = data.get('scores', [])

    if not isinstance(students, list):
        return False, "'students' must be an array"

    if not isinstance(scores, list):
        return False, "'scores' must be an array"

    if len(students) == 0:
        return False, "No students found in import data"

    # Validate scores are for the correct time period
    if import_type == 'historical':
        current_month_scores = [s for s in scores if is_current_month_date(s.get('date'))]
        if current_month_scores:
            return False, f"Historical import contains {len(current_month_scores)} scores from current month. Please use 'Latest Roster' import for current month data."

    elif import_type == 'latest_roster':
        historical_scores = [s for s in scores if is_historical_date(s.get('date'))]
        if historical_scores:
            return False, f"Latest roster import contains {len(historical_scores)} scores from previous months. Please use 'Historical Data' import for previous months."

    return True, ""


# Export functions
__all__ = [
    'get_current_month_key',
    'get_current_month_start',
    'is_historical_date',
    'is_current_month_date',
    'preserve_student_status',
    'filter_scores_by_date_range',
    'merge_scores_preserving_existing',
    'validate_import_data'
]
