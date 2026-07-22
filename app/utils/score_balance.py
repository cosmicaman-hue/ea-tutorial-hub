"""
score_balance.py — Pure calculation helpers for student star and VETO balances.

These functions operate on the offline-data dict (already loaded by the caller)
and have no Flask or database dependencies. They can therefore be imported from
anywhere without circular-import risk — including scoreboard.py routes and
future test files.

Formula (mirrors offline_scoreboard.html JS):
  Stars:  current month:    student.stars   (authoritative ledger)
          historical month: carry + awards - used  (from month profile)
  VETOs:  individual + role_grant + awards - used  (current month)
          carry + role_grant + awards - used        (historical months)
"""
from datetime import datetime
from app.utils.helpers import norm_roll as _norm_roll, safe_int as _safe_int, month_key as _month_key


def _iter_month_profiles(data, month_key):
    """Return the month profile rows for a month as a list."""
    month = _month_key(month_key)
    month_profiles = (data.get('month_roster_profiles', {}) or {}).get(month, {}) or {}
    if isinstance(month_profiles, list):
        return [row for row in month_profiles if isinstance(row, dict)]
    if isinstance(month_profiles, dict):
        return [row for row in month_profiles.values() if isinstance(row, dict)]
    return []


def _find_month_profile(data, student_id, month_key):
    """Return the best matching month profile for a student/month."""
    sid = _safe_int(student_id, 0)
    if sid <= 0:
        return None

    profiles = _iter_month_profiles(data, month_key)
    if not profiles:
        return None

    for profile in profiles:
        profile_sid = _safe_int(profile.get('studentId') or profile.get('student_id'), 0)
        if profile_sid == sid:
            return profile

    roll_key = get_roll_for_month(data, sid, month_key)
    if roll_key:
        normalized_roll = _norm_roll(roll_key)
        for profile in profiles:
            if _norm_roll(profile.get('roll')) == normalized_roll:
                return profile

    return None


# ── Roll-history resolution ────────────────────────────────────────────────

def get_roll_for_month(data, student_id, month_key):
    """Return the roll number a student held in a given month.

    Walks data['roll_history'] — entries added by the /record-roll-change
    endpoint — so that profile lookups use the correct roll key even after
    a student has been promoted to a new roll number.

    A history entry with effective_month='2025-09' means:
      • new_roll applies from 2025-09 onwards
      • old_roll applies for all months before 2025-09

    Returns None if the student is not found.
    """
    sid = _safe_int(student_id, 0)
    if sid <= 0:
        return None

    month = _month_key(month_key)
    students = data.get('students', []) or []
    student = next(
        (s for s in students if _safe_int(s.get('id'), 0) == sid),
        None
    )
    if not student:
        return None

    current_roll = _norm_roll(student.get('roll'))
    roll_history = data.get('roll_history', []) or []

    # Entries for this student, newest-change-first
    entries = sorted(
        [e for e in roll_history
         if isinstance(e, dict) and _safe_int(e.get('student_id'), 0) == sid],
        key=lambda e: str(e.get('effective_month') or ''),
        reverse=True,
    )

    if not entries:
        return current_roll

    roll = current_roll
    for entry in entries:
        eff_month = str(entry.get('effective_month') or '').strip()
        if eff_month > month:
            # This change happened AFTER the requested month — use old_roll
            old = _norm_roll(entry.get('old_roll'))
            if old:
                roll = old
        else:
            # This change was in effect at the requested month — stop walking back
            break

    return roll


# ── Star balance ──────────────────────────────────────────────────────────

def compute_star_balance(data, student_id, month_key, current_month=None):
    """Authoritative available-star count for a student in a month.

    Formula:
        current month    → student.stars (global ledger — single source of truth)
        historical month → max(0, profile_carry + month_awards - month_used)

    The current-month branch makes `student.stars` authoritative so that
    manual edits, deductions, and Star→VETO conversions are always reflected
    in the displayed balance. Auto-recompute was removed in favor of this
    ledger-only model; carry+awards-used is only used to render past months
    where the ledger value (current) does not apply.

    Parameters
    ----------
    data          : offline data dict
    student_id    : int
    month_key     : YYYY-MM to compute for
    current_month : YYYY-MM treated as "current". Defaults to today's month.
    """
    sid = _safe_int(student_id, 0)
    students = data.get('students', []) or []
    student = next((s for s in students if _safe_int(s.get('id'), 0) == sid), None)
    if not student:
        return 0

    month = _month_key(month_key)
    global_stars = max(0, _safe_int(student.get('stars'), 0))

    if not current_month:
        current_month = datetime.now().strftime('%Y-%m')
    current_month = _month_key(current_month) or current_month

    # Current month (or caller did not specify a historical key) — the ledger
    # is authoritative. Never dilute it with derived values.
    if not month or month == current_month:
        return global_stars

    profile = _find_month_profile(data, sid, month)

    if profile and profile.get('month_star_count') is not None:
        carry = max(0, _safe_int(profile.get('month_star_count'), 0))
        scores = data.get('scores') or []
        awards = sum(
            _safe_int(r.get('stars'), 0)
            for r in scores
            if isinstance(r, dict)
            and _safe_int(r.get('studentId'), 0) == sid
            and _month_key(r.get('month') or r.get('date')) == month
            and _safe_int(r.get('stars'), 0) > 0
        )
        used = sum(
            abs(_safe_int(r.get('stars'), 0))
            for r in scores
            if isinstance(r, dict)
            and _safe_int(r.get('studentId'), 0) == sid
            and _month_key(r.get('month') or r.get('date')) == month
            and _safe_int(r.get('stars'), 0) < 0
        )
        return max(0, carry + awards - used)

    return global_stars


# ── VETO balance ──────────────────────────────────────────────────────────

def compute_veto_balance(data, student_id, month_key, current_month):
    """Authoritative available-VETO count for a student in a month.

    Formula mirrors offline_scoreboard.html::getAvailableVetosForMonth():
      Current month: individual + awards - used + role_veto_count (live field)
      Historical:    carry + role_grant_snapshot + awards - used

    Parameters
    ----------
    data          : offline data dict (already loaded)
    student_id    : int
    month_key     : YYYY-MM to compute for
    current_month : YYYY-MM — the server's current month (not calculated here
                    to keep this module import-free from datetime deps)
    """
    sid = _safe_int(student_id, 0)
    students = data.get('students', []) or []
    student = next((s for s in students if _safe_int(s.get('id'), 0) == sid), None)
    if not student:
        return 0

    month = _month_key(month_key)
    individual = max(0, _safe_int(student.get('veto_count'), 0))

    scores_for_month = [
        r for r in (data.get('scores') or [])
        if isinstance(r, dict)
        and _safe_int(r.get('studentId'), 0) == sid
        and _month_key(r.get('month') or r.get('date')) == month
    ]
    awards = sum(
        _safe_int(r.get('vetos'), 0)
        for r in scores_for_month
        if _safe_int(r.get('vetos'), 0) > 0
    )
    used = sum(
        abs(_safe_int(r.get('vetos'), 0))
        for r in scores_for_month
        if _safe_int(r.get('vetos'), 0) < 0
    )

    if month == current_month:
        role_veto = max(0, _safe_int(student.get('role_veto_count'), 0))
        # For the current month, veto_count and role_veto_count are live-decremented
        # counters. Subtracting used (the score-entry negative delta) on top of this
        # causes a double-deduction.
        return max(0, individual + awards + role_veto)

    # Historical month — use the monthly role-grant snapshot
    role_veto_monthly = data.get('role_veto_monthly', {}) or {}
    grants = role_veto_monthly.get(month, {}) or {}
    role_grant = max(0, _safe_int(
        grants.get(str(sid)) if str(sid) in grants else grants.get(sid), 0
    ))

    profile = _find_month_profile(data, sid, month)
    carry = max(0, _safe_int((profile or {}).get('month_veto_count'), 0))

    return max(0, carry + role_grant + awards - used)
