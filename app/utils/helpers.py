"""
helpers.py — Single source of truth for shared pure-function utilities.

All other modules (scoreboard.py, student_roster.py, score_balance.py, etc.)
should import from here instead of re-implementing these functions.
"""
import re
from datetime import datetime


def safe_int(value, default=0):
    """Parse an integer safely, returning default on failure."""
    try:
        if value in (None, ''):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    """Parse a float safely, returning default on failure."""
    try:
        if value in (None, ''):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def norm_roll(value):
    """Normalise a roll-number string to uppercase stripped form."""
    return str(value or '').strip().upper()


def month_key(value):
    """Extract YYYY-MM from any date-like string."""
    text = str(value or '').strip()
    if re.match(r'^\d{4}-\d{2}$', text):
        return text
    if len(text) >= 7 and re.match(r'^\d{4}-\d{2}', text[:7]):
        return text[:7]
    return ''


def parse_stamp(value):
    """Parse an ISO timestamp to a float epoch. Returns 0.0 on failure."""
    raw = str(value or '').strip()
    if not raw:
        return 0.0
    try:
        return datetime.fromisoformat(raw.replace('Z', '+00:00')).timestamp()
    except Exception:
        return 0.0


def name_key(value):
    """Normalise a student name for comparison: lowercase, strip decorations."""
    text = str(value or '').strip().lower()
    text = re.sub(r'\s*\([^)]*\)', ' ', text)
    text = re.sub(r'[^a-z0-9]+', '', text)
    return text
