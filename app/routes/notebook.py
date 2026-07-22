import copy
import json
import os
import tempfile
from flask import Blueprint, render_template, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import func

from app import db, csrf
from app.models.notebook import (
    NotebookSubjectConfig, NotebookCheck, NotebookSubjectCheck,
    NotebookScoreSettings, NotebookStudentExemption,
    GRADE_POINTS,
)
from app.models.student_profile import StudentProfile
from app.models.points import StudentPoints

notebook_bp = Blueprint('notebook', __name__, url_prefix='/notebooks')

DEFAULT_SCHOOL_SUBJECTS = [
    'Maths', 'English', 'Science', 'Social Science',
    'Hindi', 'IT / AI', 'Sanskrit',
]
DEFAULT_TUITION_SUBJECTS = ['Maths', 'Science', 'English']


# ─── JSON data helpers ─────────────────────────────────────────────────────────

def _load_json_data():
    """
    Return the offline scoreboard JSON. Uses the shared mtime-based cache so
    multiple notebook API calls within the same page load don't re-parse the
    4+ MB file.

    IMPORTANT: returned dict is the shared cached object. DO NOT mutate it.
    For write paths, use _save_json_data() which atomically replaces the file.
    """
    from app.utils.data_paths import load_json_data_cached
    data = load_json_data_cached()
    return data if data is not None else {}


def _save_json_data(data: dict):
    from app.utils.data_paths import (
        get_data_path, prime_data_cache, invalidate_data_cache,
    )
    from app.utils.file_operations import SafeFileWriter
    from pathlib import Path
    path = get_data_path()
    success = SafeFileWriter.write_json(Path(path), data, backup=True)
    if not success:
        raise IOError(f"Failed to safely write JSON data to {path} via SafeFileWriter.")
    # Refresh shared cache so subsequent reads don't re-parse from disk.
    try:
        if isinstance(data, dict):
            prime_data_cache(data)
        else:
            invalidate_data_cache()
    except Exception:
        invalidate_data_cache()


def _get_active_students():
    data = _load_json_data()
    students = data.get('students', [])
    from app.utils.student_roster import get_active_students_for_month
    return get_active_students_for_month(students)


def _student_by_roll(roll: str):
    for s in _get_active_students():
        if str(s.get('roll', '')) == str(roll):
            return s
    return None


def _add_score_to_json(student_json_id: int, check_date: date,
                        total_points: int, notes: str):
    # Deep-copy because _load_json_data() now returns a shared cached dict;
    # mutating it would corrupt the cache. Writes are rare, so the copy cost
    # is acceptable here.
    data = copy.deepcopy(_load_json_data())
    scores = data.get('scores', [])
    date_str = check_date.isoformat()
    month_str = date_str[:7]
    now_iso = datetime.utcnow().isoformat()

    note_prefix = notes.split(']')[0] + ']' if ']' in notes else notes[:20]

    existing = None
    for score in scores:
        if (score.get('studentId') == student_json_id
                and str(score.get('date', '')) == date_str
                and str(score.get('notes', '')).startswith(note_prefix)):
            existing = score
            break

    if existing:
        existing['points'] = total_points
        existing['notes'] = notes
        existing['updated_at'] = now_iso
    else:
        max_id = max((s.get('id', 0) for s in scores), default=0)
        scores.append({
            'id': max_id + 1,
            'studentId': student_json_id,
            'date': date_str,
            'month': month_str,
            'points': total_points,
            'stars': 0,
            'vetos': 0,
            'star_usage_normal': 0,
            'star_usage_disciplinary': 0,
            'notes': notes,
            'created_at': now_iso,
            'updated_at': now_iso,
        })

    data['scores'] = scores
    data['updated_at'] = now_iso
    data['server_updated_at'] = now_iso
    _save_json_data(data)


def _remove_score_from_json(student_json_id: int, check_date: date, note_prefix: str):
    # Deep-copy: see note in _add_score_to_json.
    data = copy.deepcopy(_load_json_data())
    date_str = check_date.isoformat()
    data['scores'] = [
        s for s in data.get('scores', [])
        if not (s.get('studentId') == student_json_id
                and str(s.get('date', '')) == date_str
                and str(s.get('notes', '')).startswith(note_prefix))
    ]
    now_iso = datetime.utcnow().isoformat()
    data['updated_at'] = now_iso
    data['server_updated_at'] = now_iso
    _save_json_data(data)


# ─── Auth helper ───────────────────────────────────────────────────────────────

def _staff_required():
    if current_user.role not in ('admin', 'teacher'):
        abort(403)


# ─── Main page ─────────────────────────────────────────────────────────────────

@notebook_bp.route('/')
@login_required
def index():
    _staff_required()
    return render_template('notebook/index.html')


# ─── Dropdown data (from JSON) ─────────────────────────────────────────────────

@notebook_bp.route('/api/groups')
@login_required
def api_groups():
    _staff_required()
    students = _get_active_students()
    groups = sorted({str(s.get('group', '')) for s in students if s.get('group')})
    return jsonify({'groups': groups})


@notebook_bp.route('/api/classes')
@login_required
def api_classes():
    _staff_required()
    group = request.args.get('group', '').strip()
    if not group:
        return jsonify({'classes': []})
    students = _get_active_students()
    classes = sorted({
        str(s.get('class', '')) for s in students
        if str(s.get('group', '')) == group and s.get('class') is not None
    }, key=lambda x: (len(x), x))
    return jsonify({'classes': classes})


@notebook_bp.route('/api/students')
@login_required
def api_students():
    _staff_required()
    group = request.args.get('group', '').strip()
    class_name = request.args.get('class_name', '').strip()
    if not group or not class_name:
        return jsonify({'students': []})
    students = _get_active_students()
    filtered = [
        s for s in students
        if str(s.get('group', '')) == group
        and str(s.get('class', '')) == class_name
    ]
    filtered.sort(key=lambda s: str(s.get('roll', '')))
    return jsonify({'students': [
        {
            'id': s.get('id'),
            'roll': s.get('roll', ''),
            'name': s.get('name') or s.get('base_name') or s.get('roll', ''),
        }
        for s in filtered
    ]})


# ─── Subject list ──────────────────────────────────────────────────────────────

@notebook_bp.route('/api/subjects')
@login_required
def api_subjects():
    _staff_required()
    group = request.args.get('group', '').strip()
    class_name = request.args.get('class_name', '').strip()
    nb_type = request.args.get('type', 'school').strip()

    if not group:
        return jsonify({'subjects': [], 'is_default': False})

    configs = (
        NotebookSubjectConfig.query
        .filter_by(group=group, notebook_type=nb_type, is_active=True)
        .filter(
            (NotebookSubjectConfig.class_name == class_name) |
            (NotebookSubjectConfig.class_name.is_(None))
        )
        .order_by(
            NotebookSubjectConfig.class_name.desc().nullslast(),
            NotebookSubjectConfig.order_index,
        )
        .all()
    )

    seen: dict = {}
    for c in configs:
        name = c.subject_name
        if name not in seen or c.class_name is not None:
            seen[name] = c
    result = sorted(seen.values(), key=lambda x: x.order_index)

    if not result:
        defaults = DEFAULT_SCHOOL_SUBJECTS if nb_type == 'school' else DEFAULT_TUITION_SUBJECTS
        return jsonify({
            'subjects': [{'id': None, 'name': s} for s in defaults],
            'is_default': True,
        })

    return jsonify({
        'subjects': [{'id': c.id, 'name': c.subject_name} for c in result],
        'is_default': False,
    })


# ─── Score settings ────────────────────────────────────────────────────────────

@notebook_bp.route('/api/score-settings')
@login_required
def api_score_settings():
    _staff_required()
    settings = NotebookScoreSettings.get_settings()
    return jsonify(settings.to_dict())


@notebook_bp.route('/api/score-settings', methods=['POST'])
@csrf.exempt
@login_required
def api_update_score_settings():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Admin only'}), 403
    try:
        data = request.get_json()
        max_pts = int(data.get('max_points', 20))
        min_pts = int(data.get('min_points', -30))
        if max_pts <= 0:
            return jsonify({'success': False, 'error': 'Max points must be positive'}), 400
        if min_pts >= 0:
            return jsonify({'success': False, 'error': 'Min points must be negative'}), 400
        if max_pts > 1000 or min_pts < -1000:
            return jsonify({'success': False, 'error': 'Values out of range (−1000 to +1000)'}), 400

        settings = NotebookScoreSettings.get_settings()
        settings.max_points = max_pts
        settings.min_points = min_pts
        settings.updated_by = current_user.login_id
        db.session.commit()
        return jsonify({'success': True, **settings.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── Student subject exemptions ────────────────────────────────────────────────

@notebook_bp.route('/api/exemptions')
@login_required
def api_get_exemptions():
    _staff_required()
    roll = request.args.get('roll', '').strip()
    nb_type = request.args.get('type', 'school').strip()
    if not roll:
        return jsonify({'exemptions': []})
    exemptions = NotebookStudentExemption.query.filter_by(
        roll_number=roll, notebook_type=nb_type
    ).all()
    return jsonify({'exemptions': [ex.subject_name for ex in exemptions]})


@notebook_bp.route('/api/exemptions', methods=['POST'])
@csrf.exempt
@login_required
def api_set_exemption():
    _staff_required()
    try:
        data = request.get_json()
        roll = str(data.get('roll', '')).strip()
        nb_type = str(data.get('type', '')).strip()
        subject = str(data.get('subject', '')).strip()[:100]
        exempt = bool(data.get('exempt', True))

        if not roll or nb_type not in ('school', 'tuition') or not subject:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        if exempt:
            existing = NotebookStudentExemption.query.filter_by(
                roll_number=roll, subject_name=subject, notebook_type=nb_type
            ).first()
            if not existing:
                db.session.add(NotebookStudentExemption(
                    roll_number=roll, subject_name=subject, notebook_type=nb_type
                ))
                db.session.commit()
        else:
            NotebookStudentExemption.query.filter_by(
                roll_number=roll, subject_name=subject, notebook_type=nb_type
            ).delete()
            db.session.commit()

        all_exemptions = NotebookStudentExemption.query.filter_by(
            roll_number=roll, notebook_type=nb_type
        ).all()
        return jsonify({
            'success': True,
            'exemptions': [ex.subject_name for ex in all_exemptions],
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── Load existing check for prefill ──────────────────────────────────────────

@notebook_bp.route('/api/check')
@login_required
def api_get_check():
    _staff_required()
    roll = request.args.get('roll', '').strip()
    date_str = request.args.get('date', '')
    nb_type = request.args.get('type', 'school')

    if not roll or not date_str:
        return jsonify({'check': None})

    try:
        check_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        return jsonify({'error': 'Invalid date'}), 400

    check = NotebookCheck.query.filter_by(
        roll_number=roll,
        date_checked=check_date,
        notebook_type=nb_type,
    ).first()

    return jsonify({'check': check.to_dict() if check else None})


# ─── Save notebook check ───────────────────────────────────────────────────────

@notebook_bp.route('/save', methods=['POST'])
@csrf.exempt
@login_required
def save_check():
    _staff_required()
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'Invalid data'}), 400

        roll = str(data.get('roll', '')).strip()
        date_str = data.get('date', '')
        nb_type = data.get('type', 'school')
        subjects_data = data.get('subjects', [])
        consolidated_remarks = str(data.get('consolidated_remarks', ''))[:1000]

        if not roll:
            return jsonify({'success': False, 'error': 'Roll number required'}), 400

        student = _student_by_roll(roll)
        if not student:
            return jsonify({'success': False,
                            'error': f'Student {roll} not found in active roster'}), 404

        student_json_id = student.get('id')
        student_name = student.get('name') or student.get('base_name') or roll
        group = str(student.get('group', ''))
        class_name = str(student.get('class', ''))

        if nb_type not in ('school', 'tuition'):
            return jsonify({'success': False, 'error': 'Invalid notebook type'}), 400

        try:
            check_date = datetime.fromisoformat(date_str).date()
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid date format'}), 400

        if check_date > date.today():
            return jsonify({'success': False, 'error': 'Cannot record future dates'}), 400

        # ── Score limits ─────────────────────────────────────────────────────
        settings = NotebookScoreSettings.get_settings()

        # ── Validate + calculate subjects ────────────────────────────────────
        raw_total = 0
        validated = []
        for s in subjects_data:
            if not isinstance(s, dict):
                continue
            name = str(s.get('name', ''))[:100].strip()
            if not name:
                continue
            is_checked = bool(s.get('is_checked', False))
            is_exempt = bool(s.get('is_exempt', False))
            grade = str(s.get('grade', '')).strip()
            remarks = str(s.get('remarks', ''))[:500]

            # Derive points from grade; fall back to legacy numeric field
            if is_checked and grade in GRADE_POINTS:
                pts = GRADE_POINTS[grade]
            elif is_checked:
                try:
                    pts = max(-10, min(5, int(s.get('points', 0))))
                except (ValueError, TypeError):
                    pts = 0
                grade = ''
            else:
                pts = 0
                grade = ''

            if is_checked and not is_exempt:
                raw_total += pts

            if not is_exempt:          # Exempt subjects are not persisted
                validated.append({
                    'name': name, 'is_checked': is_checked,
                    'grade': grade, 'points': pts, 'remarks': remarks,
                })

        # Apply global score limits (clamping)
        total_points = max(settings.min_points, min(settings.max_points, raw_total))

        # ── Upsert NotebookCheck ─────────────────────────────────────────────
        check = NotebookCheck.query.filter_by(
            roll_number=roll,
            date_checked=check_date,
            notebook_type=nb_type,
        ).first()

        if check:
            for sc in list(check.subject_checks):
                db.session.delete(sc)
            db.session.flush()
            check.consolidated_remarks = consolidated_remarks
            check.total_points = total_points
            check.student_name = student_name
            check.student_json_id = student_json_id
            check.group = group
            check.class_name = class_name
            check.recorded_by = current_user.login_id
            check.updated_at = datetime.utcnow()
        else:
            check = NotebookCheck(
                roll_number=roll,
                student_name=student_name,
                student_json_id=student_json_id,
                group=group,
                class_name=class_name,
                date_checked=check_date,
                notebook_type=nb_type,
                consolidated_remarks=consolidated_remarks,
                total_points=total_points,
                recorded_by=current_user.login_id,
            )
            db.session.add(check)
            db.session.flush()
        for s in validated:
            db.session.add(NotebookSubjectCheck(
                notebook_check_id=check.id,
                subject_name=s['name'],
                is_checked=s['is_checked'],
                grade=s['grade'] or None,
                points=s['points'],
                remarks=s['remarks'],
            ))

        # ── Sync to SQL student_points ────────────────────────────────────────
        student_db = StudentProfile.query.filter_by(roll_number=roll).first()
        if student_db:
            entry_type = f'notebook_{nb_type}'
            label = 'School' if nb_type == 'school' else 'Tuition'
            checked_names = [s['name'] for s in validated if s['is_checked']]
            notes = (
                f'[NOTEBOOK:{label.upper()}] '
                + (', '.join(checked_names) if checked_names else 'No subjects checked')
            )
            
            points_record = StudentPoints.query.filter_by(
                student_id=student_db.id,
                date_recorded=check_date,
                entry_type=entry_type
            ).first()
            
            if points_record:
                points_record.points = total_points
                points_record.notes = notes
                points_record.recorded_by = current_user.login_id
                points_record.updated_at = datetime.utcnow()
            else:
                points_record = StudentPoints(
                    student_id=student_db.id,
                    date_recorded=check_date,
                    points=total_points,
                    stars=0,
                    vetos=0,
                    notes=notes,
                    recorded_by=current_user.login_id,
                    entry_type=entry_type
                )
                db.session.add(points_record)

        db.session.commit()

        # ── Sync to JSON scoreboard ──────────────────────────────────────────
        label = 'School' if nb_type == 'school' else 'Tuition'
        checked_names = [s['name'] for s in validated if s['is_checked']]
        notes = (
            f'[NOTEBOOK:{label.upper()}] '
            + (', '.join(checked_names) if checked_names else 'No subjects checked')
        )
        if student_json_id:
            try:
                _add_score_to_json(student_json_id, check_date, total_points, notes)
            except Exception as e:
                current_app.logger.warning(f'Could not write notebook score to JSON: {e}')

        capped_msg = ''
        if total_points != raw_total:
            sign_r = '+' if raw_total >= 0 else ''
            sign_t = '+' if total_points >= 0 else ''
            capped_msg = f' (raw {sign_r}{raw_total} → capped to {sign_t}{total_points})'

        sign = '+' if total_points >= 0 else ''
        return jsonify({
            'success': True,
            'check_id': check.id,
            'total_points': total_points,
            'raw_points': raw_total,
            'message': (
                f'Saved! Notebook points: {sign}{total_points}{capped_msg} added to scoreboard.'
            ),
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error saving notebook check: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── Records ───────────────────────────────────────────────────────────────────

@notebook_bp.route('/api/records')
@login_required
def api_records():
    _staff_required()
    group = request.args.get('group', '').strip()
    class_name = request.args.get('class_name', '').strip()
    roll = request.args.get('roll', '').strip()
    nb_type = request.args.get('type', '').strip()
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)

    query = NotebookCheck.query
    if group:
        query = query.filter_by(group=group)
    if class_name:
        query = query.filter_by(class_name=class_name)
    if roll:
        query = query.filter_by(roll_number=roll)
    if nb_type:
        query = query.filter_by(notebook_type=nb_type)
    if month:
        query = query.filter(func.extract('month', NotebookCheck.date_checked) == month)
    if year:
        query = query.filter(func.extract('year', NotebookCheck.date_checked) == year)

    checks = query.order_by(NotebookCheck.date_checked.desc()).limit(300).all()

    records = []
    for check in checks:
        checked_count = sum(1 for sc in check.subject_checks if sc.is_checked)
        total_count = len(check.subject_checks)
        records.append({
            'id': check.id,
            'roll_number': check.roll_number,
            'student_name': check.student_name or check.roll_number,
            'group': check.group or '',
            'class_name': check.class_name or '',
            'date_checked': check.date_checked.isoformat(),
            'notebook_type': check.notebook_type,
            'total_points': check.total_points,
            'checked_count': checked_count,
            'total_subjects': total_count,
            'consolidated_remarks': check.consolidated_remarks or '',
            'recorded_by': check.recorded_by or '',
        })

    return jsonify({'records': records})


@notebook_bp.route('/api/records/<int:check_id>')
@login_required
def api_record_detail(check_id):
    _staff_required()
    check = NotebookCheck.query.get_or_404(check_id)
    return jsonify({'check': check.to_dict()})


@notebook_bp.route('/api/records/<int:check_id>', methods=['DELETE'])
@csrf.exempt
@login_required
def api_delete_record(check_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Admin only'}), 403
    check = NotebookCheck.query.get_or_404(check_id)
    if check.student_json_id:
        label = 'School' if check.notebook_type == 'school' else 'Tuition'
        try:
            _remove_score_from_json(
                check.student_json_id,
                check.date_checked,
                f'[NOTEBOOK:{label.upper()}]',
            )
        except Exception as e:
            current_app.logger.warning(f'Could not remove notebook score from JSON: {e}')
    # Delete from StudentPoints
    student_db = StudentProfile.query.filter_by(roll_number=check.roll_number).first()
    if student_db:
        entry_type = f'notebook_{check.notebook_type}'
        StudentPoints.query.filter_by(
            student_id=student_db.id,
            date_recorded=check.date_checked,
            entry_type=entry_type
        ).delete(synchronize_session=False)

    db.session.delete(check)
    db.session.commit()
    return jsonify({'success': True})


# ─── Notifications ─────────────────────────────────────────────────────────────

@notebook_bp.route('/api/notifications')
@login_required
def api_notifications():
    _staff_required()
    group = request.args.get('group', '').strip()
    class_name = request.args.get('class_name', '').strip()
    nb_type = request.args.get('type', '').strip()
    days = request.args.get('days', 30, type=int)
    cutoff = date.today() - timedelta(days=max(1, min(days, 365)))

    query = NotebookCheck.query.filter(NotebookCheck.date_checked >= cutoff)
    if group:
        query = query.filter_by(group=group)
    if class_name:
        query = query.filter_by(class_name=class_name)
    if nb_type:
        query = query.filter_by(notebook_type=nb_type)

    checks = query.order_by(NotebookCheck.date_checked.desc()).all()

    # Pre-load exemptions for all rolls in one DB round-trip
    all_rolls = {c.roll_number for c in checks}
    exemption_map: dict = {}   # (roll, type) → set of exempt subject names
    if all_rolls:
        exemptions = NotebookStudentExemption.query.filter(
            NotebookStudentExemption.roll_number.in_(all_rolls)
        ).all()
        for ex in exemptions:
            key = (ex.roll_number, ex.notebook_type)
            exemption_map.setdefault(key, set()).add(ex.subject_name)

    notifications = []
    seen: set = set()

    for check in checks:
        key = (check.roll_number, check.notebook_type)
        if key in seen:
            continue
        seen.add(key)

        exempt_subs = exemption_map.get(key, set())
        applicable = [sc for sc in check.subject_checks
                      if sc.subject_name not in exempt_subs]
        unchecked = [sc.subject_name for sc in applicable if not sc.is_checked]

        if unchecked:
            total_applicable = len(applicable)
            notifications.append({
                'roll_number': check.roll_number,
                'student_name': check.student_name or check.roll_number,
                'group': check.group or '',
                'class_name': check.class_name or '',
                'notebook_type': check.notebook_type,
                'date_checked': check.date_checked.isoformat(),
                'unchecked_subjects': unchecked,
                'severity': 'full' if len(unchecked) == total_applicable else 'partial',
            })

    # Students with no check at all in the window
    all_students = _get_active_students()
    if group:
        all_students = [s for s in all_students if str(s.get('group', '')) == group]
    if class_name:
        all_students = [s for s in all_students if str(s.get('class', '')) == class_name]

    types_to_check = [nb_type] if nb_type else ['school', 'tuition']
    for student in all_students:
        roll = str(student.get('roll', ''))
        for t in types_to_check:
            if (roll, t) not in seen:
                notifications.append({
                    'roll_number': roll,
                    'student_name': student.get('name') or student.get('base_name') or roll,
                    'group': str(student.get('group', '')),
                    'class_name': str(student.get('class', '')),
                    'notebook_type': t,
                    'date_checked': None,
                    'unchecked_subjects': [],
                    'severity': 'never',
                })

    return jsonify({'notifications': notifications})


# ─── Subject configuration ─────────────────────────────────────────────────────

@notebook_bp.route('/api/subject-configs')
@login_required
def api_subject_configs():
    _staff_required()
    group = request.args.get('group', '').strip()
    nb_type = request.args.get('type', '').strip()

    query = NotebookSubjectConfig.query
    if group:
        query = query.filter_by(group=group)
    if nb_type:
        query = query.filter_by(notebook_type=nb_type)

    configs = query.order_by(
        NotebookSubjectConfig.group,
        NotebookSubjectConfig.notebook_type,
        NotebookSubjectConfig.order_index,
    ).all()

    return jsonify({'configs': [c.to_dict() for c in configs]})


@notebook_bp.route('/api/subject-configs/save', methods=['POST'])
@csrf.exempt
@login_required
def api_save_subject_config():
    _staff_required()
    try:
        data = request.get_json()
        group = str(data.get('group', '')).strip()
        class_name = data.get('class_name') or None
        nb_type = str(data.get('notebook_type', '')).strip()
        subject_name = str(data.get('subject_name', '')).strip()[:100]

        if not group or nb_type not in ('school', 'tuition') or not subject_name:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        exists = NotebookSubjectConfig.query.filter_by(
            group=group, class_name=class_name,
            notebook_type=nb_type, subject_name=subject_name,
        ).first()
        if exists:
            return jsonify({'success': False,
                            'error': 'Subject already exists for this group/type'}), 409

        max_order = (
            db.session.query(func.max(NotebookSubjectConfig.order_index))
            .filter_by(group=group, notebook_type=nb_type)
            .scalar()
        ) or 0

        config = NotebookSubjectConfig(
            group=group, class_name=class_name,
            notebook_type=nb_type, subject_name=subject_name,
            order_index=max_order + 1, is_active=True,
        )
        db.session.add(config)
        db.session.commit()
        return jsonify({'success': True, 'config': config.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@notebook_bp.route('/api/subject-configs/<int:config_id>/toggle', methods=['POST'])
@csrf.exempt
@login_required
def api_toggle_subject_config(config_id):
    _staff_required()
    config = NotebookSubjectConfig.query.get_or_404(config_id)
    config.is_active = not config.is_active
    db.session.commit()
    return jsonify({'success': True, 'is_active': config.is_active})


@notebook_bp.route('/api/subject-configs/<int:config_id>', methods=['DELETE'])
@csrf.exempt
@login_required
def api_delete_subject_config(config_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Admin only'}), 403
    config = NotebookSubjectConfig.query.get_or_404(config_id)
    db.session.delete(config)
    db.session.commit()
    return jsonify({'success': True})


@notebook_bp.route('/api/subject-configs/reorder', methods=['POST'])
@csrf.exempt
@login_required
def api_reorder_subject_configs():
    _staff_required()
    try:
        data = request.get_json()
        for item in data.get('order', []):
            cfg = NotebookSubjectConfig.query.get(item['id'])
            if cfg:
                cfg.order_index = int(item['order_index'])
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ─── Student notebook history (for profile modal) ──────────────────────────────

@notebook_bp.route('/api/student-history/<roll>')
@login_required
def api_student_history(roll):
    _staff_required()
    checks = (
        NotebookCheck.query
        .filter_by(roll_number=roll)
        .order_by(NotebookCheck.date_checked.desc())
        .limit(50)
        .all()
    )
    return jsonify({'history': [c.to_dict() for c in checks]})
