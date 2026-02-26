from flask import Blueprint, render_template, request, jsonify, current_app, send_file, after_this_request, Response, stream_with_context
from flask_login import login_required, current_user
from app import db, csrf, limiter
from app.models import User
from app.utils.syllabus_helpers import merge_syllabus_catalog_superset, merge_syllabus_tracking_superset
from datetime import datetime, date, timedelta, timezone
from dateutil.relativedelta import relativedelta
import calendar
import openpyxl
from werkzeug.utils import secure_filename
import os
import json
import re
import tempfile
import shutil
import glob
import urllib.request
import urllib.error
from zoneinfo import ZoneInfo
from queue import Queue, Empty
import threading

points_bp = Blueprint('points', __name__, url_prefix='/scoreboard')
_sync_subscribers = []
_sync_lock = threading.Lock()

DEFAULT_PARTIES = [
    {"id": 1, "code": "MAP", "power": 15},
    {"id": 2, "code": "BWP", "power": 27},
    {"id": 3, "code": "ESP", "power": 30},
    {"id": 4, "code": "MRP", "power": 23},
    {"id": 5, "code": "SSP", "power": 57},
    {"id": 6, "code": "NJP", "power": 15},
]

DEFAULT_LEADERSHIP = [
    {"id": 1, "post": "LEADER (L)", "holder": "HARSH MALLICK"},
    {"id": 2, "post": "LEADER OF OPPOSITION (LoP)", "holder": ""},
    {"id": 3, "post": "CO-LEADER (CoL)", "holder": "REEYANSH LAMA"},
    {"id": 4, "post": "CODING & IT CAPTAIN (CITC)", "holder": "SAMARTH PATEL"},
    {"id": 5, "post": "DISCIPLINE & WELFARE IN-CHARGE (DWI)", "holder": "AANSH MANDAL"},
    {"id": 6, "post": "RESOURCE MANAGER (RM)", "holder": "RIYA SINGH"},
    {"id": 7, "post": "SPORTS CAPTAIN (SC)", "holder": "REEYANSH LAMA"},
    {"id": 8, "post": "ENGLISH CAPTAIN- SENIOR (ECS)", "holder": "ABDUL ARMAN"},
    {"id": 9, "post": "CULTURE & CREATIVE ARTS IN-CHARGE (CCAI)", "holder": "SAKSHI"},
    {"id": 10, "post": "CLEANLINESS IN-CHARGE (CI)", "holder": "SHANKAR PRADHAN"},
    {"id": 11, "post": "ENGLISH CAPTAIN- JUNIOR (ECJ)", "holder": "REHMATUN KHATUN"},
    {"id": 12, "post": "WELCOME & COMMUNICATION IN-CHARGE (WCI)", "holder": "SHOMIYA XALXO"},
    {"id": 13, "post": "LEADER", "holder": ""},
    {"id": 14, "post": "LEADER OF OPPOSITION", "holder": ""},
]


def _politics_file_path():
    return os.path.join(current_app.instance_path, 'scoreboard_politics.json')


def _offline_data_path():
    return os.path.join(current_app.instance_path, 'offline_scoreboard_data.json')


def _offline_backup_dir():
    return os.path.join(current_app.instance_path, 'offline_scoreboard_backups')

def _offline_hourly_backup_dir():
    return os.path.join(current_app.instance_path, 'offline_scoreboard_hourly_backups')

def _offline_startup_restore_dir():
    return os.path.join(current_app.instance_path, 'startup_restore_points')

def _restore_points_meta_path():
    return os.path.join(current_app.instance_path, 'restore_points_meta.json')


def _device_log_path():
    return os.path.join(current_app.instance_path, 'device_log.json')

def _load_restore_points_meta():
    path = _restore_points_meta_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _save_restore_points_meta(meta):
    _atomic_write_json(_restore_points_meta_path(), meta if isinstance(meta, dict) else {})


def _get_server_timezone():
    return os.getenv('EA_TIMEZONE', 'Asia/Kolkata').strip() or 'Asia/Kolkata'


def _server_now_iso():
    tz_name = _get_server_timezone()
    try:
        return datetime.now(ZoneInfo(tz_name)).isoformat()
    except Exception:
        if tz_name.lower() == 'asia/kolkata':
            return datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat()
        return datetime.utcnow().isoformat()


def _get_sync_peers():
    raw = os.getenv('SYNC_PEERS', '') or os.getenv('SYNC_PEER', '')
    if not raw:
        return []
    peers = []
    for token in re.split(r'[,;\s]+', raw.strip()):
        item = token.strip()
        if not item:
            continue
        if not re.match(r'^https?://', item, re.I):
            item = f'http://{item}'
        item = item.rstrip('/')
        peers.append(item)
    return list(dict.fromkeys(peers))


def _normalize_peer_list(raw_values):
    peers = []
    if not isinstance(raw_values, list):
        return peers
    for token in raw_values:
        item = str(token or '').strip()
        if not item:
            continue
        if not re.match(r'^https?://', item, re.I):
            item = f'http://{item}'
        item = item.rstrip('/')
        peers.append(item)
    return peers


def _forward_offline_data_to_peers(payload, extra_peers=None):
    peers = _get_sync_peers() + _normalize_peer_list(extra_peers or [])
    peers = list(dict.fromkeys(peers))
    if not peers:
        return
    current_origin = (request.host_url or '').rstrip('/')
    body = json.dumps({'data': payload}).encode('utf-8')
    for peer in peers:
        if peer.rstrip('/') == current_origin:
            continue
        target_url = f'{peer}/scoreboard/offline-data'
        req = urllib.request.Request(
            target_url,
            data=body,
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'X-EA-Replicated': '1',
                'X-EA-Sync-Key': os.getenv('SYNC_SHARED_KEY', '')
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=3):
                pass
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            continue


def _forward_offline_data_to_peers_async(payload, extra_peers=None):
    threading.Thread(
        target=_forward_offline_data_to_peers,
        args=(payload, extra_peers),
        daemon=True
    ).start()


def _atomic_write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix='offline_scoreboard_', suffix='.json')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, path)
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass


def _backup_offline_file(path, keep=50):
    if not os.path.exists(path):
        return
    os.makedirs(_offline_backup_dir(), exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'offline_scoreboard_{timestamp}.json'
    backup_path = os.path.join(_offline_backup_dir(), backup_name)
    shutil.copy2(path, backup_path)

    backups = sorted(
        [os.path.join(_offline_backup_dir(), f) for f in os.listdir(_offline_backup_dir()) if f.endswith('.json')],
        key=os.path.getmtime,
        reverse=True
    )
    for old in backups[keep:]:
        try:
            os.remove(old)
        except Exception:
            pass


def _backup_offline_hourly_immutable(payload, keep=24 * 30):
    """
    Create one immutable snapshot per hour (local server time).
    This is append-only per hour and protects against rapid accidental overwrites.
    """
    os.makedirs(_offline_hourly_backup_dir(), exist_ok=True)
    hour_key = datetime.now().strftime('%Y%m%d_%H')
    backup_name = f'offline_scoreboard_hourly_{hour_key}.json'
    backup_path = os.path.join(_offline_hourly_backup_dir(), backup_name)
    if not os.path.exists(backup_path):
        _atomic_write_json(backup_path, payload)

    backups = sorted(
        [os.path.join(_offline_hourly_backup_dir(), f) for f in os.listdir(_offline_hourly_backup_dir()) if f.endswith('.json')],
        key=os.path.getmtime,
        reverse=True
    )
    for old in backups[keep:]:
        try:
            os.remove(old)
        except Exception:
            pass


def _load_latest_offline_backup():
    backup_dir = _offline_backup_dir()
    if not os.path.isdir(backup_dir):
        return None
    backup_files = sorted(
        [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.json')],
        key=os.path.getmtime,
        reverse=True
    )
    for backup_path in backup_files:
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            continue
    return None


def _load_offline_data():
    path = _offline_data_path()
    if not os.path.exists(path):
        return _load_latest_offline_backup()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return _load_latest_offline_backup()


def _subscribe_sync_events():
    queue = Queue(maxsize=128)
    with _sync_lock:
        _sync_subscribers.append(queue)
    return queue


def _unsubscribe_sync_events(queue):
    with _sync_lock:
        if queue in _sync_subscribers:
            _sync_subscribers.remove(queue)


def _broadcast_sync_event(updated_at, source='server'):
    payload = json.dumps({
        'updated_at': updated_at,
        'source': source
    })
    stale = []
    with _sync_lock:
        for queue in _sync_subscribers:
            try:
                queue.put_nowait(payload)
            except Exception:
                stale.append(queue)
        for queue in stale:
            if queue in _sync_subscribers:
                _sync_subscribers.remove(queue)


def _save_offline_data(payload):
    path = _offline_data_path()
    _backup_offline_file(path)
    _atomic_write_json(path, payload)
    _backup_offline_hourly_immutable(payload)
    return payload


def _parse_sync_stamp(value):
    if not value:
        return 0.0
    try:
        text = str(value).strip().replace('Z', '+00:00')
        return datetime.fromisoformat(text).timestamp()
    except Exception:
        return 0.0


def _payload_sync_stamp(payload):
    if not isinstance(payload, dict):
        return 0.0
    return max(
        _parse_sync_stamp(payload.get('server_updated_at')),
        _parse_sync_stamp(payload.get('updated_at'))
    )


def _is_suspicious_student_shrink(existing_payload, incoming_payload):
    """Detect stale snapshots that would silently shrink student master data."""
    if not isinstance(existing_payload, dict) or not isinstance(incoming_payload, dict):
        return False

    existing_students = existing_payload.get('students', []) or []
    incoming_students = incoming_payload.get('students', []) or []
    if not existing_students or not incoming_students:
        return False

    existing_rolls = {
        _normalize_roll_value(s.get('roll'))
        for s in existing_students
        if isinstance(s, dict) and _normalize_roll_value(s.get('roll'))
    }
    incoming_rolls = {
        _normalize_roll_value(s.get('roll'))
        for s in incoming_students
        if isinstance(s, dict) and _normalize_roll_value(s.get('roll'))
    }
    if not existing_rolls or not incoming_rolls:
        return False

    removed_rolls = existing_rolls - incoming_rolls
    hard_drop = len(incoming_rolls) + 5 < len(existing_rolls)
    large_removed_set = len(removed_rolls) >= 8
    return hard_drop and large_removed_set


def _min_safe_student_roster():
    raw = str(os.getenv('EA_MIN_SAFE_STUDENT_ROSTER', '')).strip()
    if not raw:
        return 25
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return 25
    return max(1, min(value, 10000))


def _student_count(payload):
    if not isinstance(payload, dict):
        return 0
    students = payload.get('students') or []
    return len(students) if isinstance(students, list) else 0


def _is_tiny_roster(payload, min_count=25):
    count = _student_count(payload)
    # Only treat non-empty snapshots as corrupt. Empty snapshot may be intentional for fresh bootstraps.
    return count > 0 and count < max(1, int(min_count or 25))


def _load_json_file(path):
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _iter_offline_recovery_candidate_paths():
    """
    Yield local snapshot files that can be used to recover from a corrupt/tiny roster.
    This never deletes any files; it only reads candidates.
    """
    instance_dir = current_app.instance_path
    paths = set()
    # Prefer explicitly marked stable backups when available.
    patterns = [
        os.path.join(instance_dir, 'offline_scoreboard_data.STABLE_BACKUP*.json'),
        os.path.join(instance_dir, 'offline_scoreboard_data.pre_*.json'),
        os.path.join(_offline_backup_dir(), '*.json'),
        os.path.join(_offline_hourly_backup_dir(), '*.json'),
        os.path.join(_offline_startup_restore_dir(), '*.json'),
    ]
    for pattern in patterns:
        try:
            for match in glob.glob(pattern):
                if match and os.path.isfile(match):
                    paths.add(match)
        except Exception:
            continue

    live_path = _offline_data_path()
    if live_path in paths:
        paths.remove(live_path)

    for path in sorted(paths, key=os.path.getmtime, reverse=True):
        yield path


def _best_local_snapshot(min_students=25, candidate_limit=80):
    best = None
    best_stamp = 0.0
    best_mtime = 0.0
    best_count = 0
    best_src = ''
    considered = 0
    for path in _iter_offline_recovery_candidate_paths():
        considered += 1
        if considered > candidate_limit:
            break
        payload = _load_json_file(path)
        if not payload:
            continue
        count = _student_count(payload)
        if count < min_students:
            continue
        stamp = _payload_sync_stamp(payload)
        mtime = 0.0
        try:
            mtime = float(os.path.getmtime(path))
        except Exception:
            mtime = 0.0
        # Prefer higher sync stamp; fall back to mtime for payloads missing stamps.
        rank_stamp = stamp if stamp else mtime
        if not best or (rank_stamp, mtime, count) > (best_stamp, best_mtime, best_count):
            best = payload
            best_stamp = rank_stamp
            best_mtime = mtime
            best_count = count
            best_src = path
    return best, best_src


def _fetch_peer_offline_payload(base_url, timeout_sec=2.5):
    if not base_url:
        return None
    peer = str(base_url).rstrip('/')
    url = f'{peer}/scoreboard/offline-data'
    req = urllib.request.Request(url, method='GET', headers={'Cache-Control': 'no-store'})
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read()
    except Exception:
        return None
    try:
        if not body:
            return None
        parsed = json.loads(body.decode('utf-8', errors='replace'))
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    data = parsed.get('data')
    return data if isinstance(data, dict) else None


def _best_peer_snapshot(min_students=25):
    peers = _get_sync_peers()
    best = None
    best_stamp = 0.0
    best_count = 0
    best_src = ''
    for peer in peers:
        payload = _fetch_peer_offline_payload(peer, timeout_sec=2.5)
        if not payload:
            continue
        count = _student_count(payload)
        if count < min_students:
            continue
        stamp = _payload_sync_stamp(payload) or 0.0
        if not best or (stamp, count) > (best_stamp, best_count):
            best = payload
            best_stamp = stamp
            best_count = count
            best_src = peer
    return best, best_src


def _recover_tiny_roster_if_needed(payload, min_students=25):
    """
    If the current payload appears corrupt (tiny roster), recover from the best peer or local snapshot.
    This avoids ever serving or persisting the known "20 students" stale snapshot.
    """
    if not _is_tiny_roster(payload, min_students):
        return payload, ''

    recovered, src = _best_peer_snapshot(min_students=min_students)
    if not recovered:
        recovered, src = _best_local_snapshot(min_students=min_students)

    if recovered and not _is_tiny_roster(recovered, min_students):
        try:
            _save_offline_data(recovered)
        except Exception:
            current_app.logger.exception("Failed to persist recovered roster snapshot from %s", src or 'unknown source')
        current_app.logger.warning(
            "Recovered tiny roster (%s students) using %s (%s students).",
            _student_count(payload),
            src or 'unknown source',
            _student_count(recovered),
        )
        return recovered, src

    return payload, ''


def _recover_stale_snapshot_if_needed(payload, min_students=25, min_newer_seconds=30, allow_local_scan=False):
    """
    If a peer has a clearly newer healthy snapshot, adopt it locally.
    This heals nodes that remain stuck on an older server_updated_at.
    """
    if not isinstance(payload, dict):
        return payload, ''

    local_stamp = _payload_sync_stamp(payload) or 0.0
    best_payload = None
    best_src = ''
    best_stamp = local_stamp

    # Prefer a newer peer snapshot first when peers are configured.
    peer_payload, peer_src = _best_peer_snapshot(min_students=min_students)
    peer_stamp = _payload_sync_stamp(peer_payload) if peer_payload else 0.0
    if peer_payload and peer_stamp > best_stamp:
        best_payload = peer_payload
        best_src = peer_src
        best_stamp = peer_stamp

    # Optional local backup scan (expensive): disabled on hot sync paths by default.
    if allow_local_scan:
        local_payload, local_src = _best_local_snapshot(min_students=min_students)
        local_best_stamp = _payload_sync_stamp(local_payload) if local_payload else 0.0
        if local_payload and local_best_stamp > best_stamp:
            best_payload = local_payload
            best_src = local_src
            best_stamp = local_best_stamp

    if best_payload and best_stamp >= (local_stamp + float(min_newer_seconds or 0)):
        try:
            _save_offline_data(best_payload)
        except Exception:
            current_app.logger.exception("Failed to persist stale-recovery snapshot from %s", best_src or 'unknown source')
        current_app.logger.warning(
            "Recovered stale snapshot from %s (local=%s, recovered=%s).",
            best_src or 'unknown source',
            payload.get('server_updated_at') or payload.get('updated_at') or '',
            best_payload.get('server_updated_at') or best_payload.get('updated_at') or '',
        )
        return best_payload, best_src

    return payload, ''


def _ensure_score_timestamps(payload):
    """
    Backfill missing score timestamps for legacy rows so client-side merge logic
    can consistently prefer the newest snapshot.
    """
    if not isinstance(payload, dict):
        return False
    scores = payload.get('scores')
    if not isinstance(scores, list):
        return False

    changed = False
    fallback = str(payload.get('server_updated_at') or payload.get('updated_at') or _server_now_iso()).strip() or _server_now_iso()
    for row in scores:
        if not isinstance(row, dict):
            continue
        updated_at = str(row.get('updated_at') or '').strip()
        created_at = str(row.get('created_at') or '').strip()
        if not updated_at:
            row['updated_at'] = created_at or fallback
            updated_at = str(row.get('updated_at') or '').strip()
            changed = True
        if not created_at:
            row['created_at'] = updated_at or fallback
            changed = True
    return changed


def _normalize_roll_value(value):
    return str(value or '').strip().upper()


def _parse_int_safe(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_holder_status(value):
    text = str(value or '').strip().lower()
    if text == 'suspended':
        return 'suspended'
    if text == 'vacant':
        return 'vacant'
    return 'active'


def _normalize_post_text(value):
    return str(value or '').strip().lower()


def _leadership_role_type(post_name):
    text = _normalize_post_text(post_name)
    if not text:
        return ''
    if 'leader of opposition' in text or '(lop)' in text:
        return 'lop'
    if 'co-leader' in text or 'co leader' in text or '(col)' in text:
        return 'co_leader'
    if ('leader' in text or '(l)' in text) and 'opposition' not in text:
        return 'leader'
    return ''


def _leadership_veto_quota(post_name):
    role_type = _leadership_role_type(post_name)
    if role_type == 'leader':
        return 5
    if role_type == 'co_leader':
        return 3
    if role_type == 'lop':
        return 2
    return 0


def _tenure_months_for_assignment(source, post_name=''):
    source_key = str(source or '').strip().lower()
    if source_key in ('class_rep', 'group_cr'):
        return 1
    if source_key == 'leadership' and _leadership_role_type(post_name) == 'co_leader':
        return 1
    return 2


def _parse_date_key(value):
    text = str(value or '').strip()
    if not text:
        return None
    try:
        if len(text) >= 10:
            return datetime.fromisoformat(text[:10]).date()
        return datetime.fromisoformat(text).date()
    except Exception:
        return None


def _is_assignment_active_by_tenure(elected_on, tenure_months=2, extension_months=0, on_date=None):
    start_date = _parse_date_key(elected_on)
    if not start_date:
        return False
    total_months = max(0, _parse_int_safe(tenure_months) + _parse_int_safe(extension_months))
    end_date = start_date + relativedelta(months=total_months)
    check_date = on_date if isinstance(on_date, date) else _parse_date_key(on_date)
    if not check_date:
        check_date = _parse_date_key(_server_now_iso())
    if not check_date:
        check_date = date.today()
    return start_date <= check_date <= end_date


def _build_student_lookups(data):
    students = data.get('students', []) or []
    by_id = {}
    by_roll = {}
    for student in students:
        sid = _parse_int_safe(student.get('id'), 0)
        if sid <= 0:
            continue
        by_id[sid] = student
        roll = _normalize_roll_value(student.get('roll'))
        if roll and roll not in by_roll:
            by_roll[roll] = sid
    return by_id, by_roll


def _compute_active_role_veto_quotas(data, date_key=None):
    by_id, by_roll = _build_student_lookups(data)
    quotas = {}
    check_date = _parse_date_key(date_key) if date_key else _parse_date_key(_server_now_iso())
    if not check_date:
        check_date = date.today()

    def _add_quota(student_id, amount):
        sid = _parse_int_safe(student_id, 0)
        quota = _parse_int_safe(amount, 0)
        if sid <= 0 or quota <= 0:
            return
        quotas[sid] = quotas.get(sid, 0) + quota

    for post in data.get('leadership', []) or []:
        if _normalize_holder_status(post.get('status')) != 'active':
            continue
        tenure_months = _tenure_months_for_assignment('leadership', post.get('post'))
        extension_months = _parse_int_safe(post.get('tenure_extension_months'), 0)
        if not _is_assignment_active_by_tenure(post.get('elected_on'), tenure_months, extension_months, check_date):
            continue
        quota = _leadership_veto_quota(post.get('post'))
        if quota <= 0:
            continue
        sid = _parse_int_safe(post.get('studentId'), 0)
        if sid <= 0:
            roll = _normalize_roll_value(post.get('roll'))
            sid = by_roll.get(roll, 0) if roll else 0
        if sid in by_id:
            _add_quota(sid, quota)

    # CR quota (+2) once per student if either class CR or group CR is active.
    cr_students = set()
    for rep in data.get('class_reps', []) or []:
        if _normalize_holder_status(rep.get('status') or 'active') != 'active':
            continue
        tenure_months = _tenure_months_for_assignment('class_rep', rep.get('post') or 'CR')
        extension_months = _parse_int_safe(rep.get('tenure_extension_months'), 0)
        if not _is_assignment_active_by_tenure(rep.get('elected_on'), tenure_months, extension_months, check_date):
            continue
        sid = _parse_int_safe(rep.get('studentId'), 0)
        if sid in by_id:
            cr_students.add(sid)

    for rep in data.get('group_crs', []) or []:
        if _normalize_holder_status(rep.get('status') or 'active') != 'active':
            continue
        tenure_months = _tenure_months_for_assignment('group_cr', rep.get('post') or 'CR')
        extension_months = _parse_int_safe(rep.get('tenure_extension_months'), 0)
        if not _is_assignment_active_by_tenure(rep.get('elected_on'), tenure_months, extension_months, check_date):
            continue
        sid = _parse_int_safe(rep.get('studentId'), 0)
        if sid in by_id:
            cr_students.add(sid)

    for sid in cr_students:
        _add_quota(sid, 2)

    return quotas


def _reconcile_role_veto_monthly(data, month_key=None, date_key=None):
    if not isinstance(data, dict):
        return
    by_id, _ = _build_student_lookups(data)
    if 'role_veto_monthly' not in data or not isinstance(data.get('role_veto_monthly'), dict):
        data['role_veto_monthly'] = {}

    resolved_month = str(month_key or _server_now_iso()[:7]).strip()
    if not re.match(r'^\d{4}-\d{2}$', resolved_month):
        resolved_month = _server_now_iso()[:7]
    applied_month = str(data.get('role_veto_applied_month') or '').strip()

    # Ensure monthly role grants do not accumulate across months.
    if applied_month and applied_month != resolved_month:
        prev_state = data['role_veto_monthly'].get(applied_month, {})
        if isinstance(prev_state, dict):
            for sid_text, grant_value in prev_state.items():
                sid = _parse_int_safe(sid_text, 0)
                grant = max(0, _parse_int_safe(grant_value, 0))
                if sid <= 0 or grant <= 0:
                    continue
                student = by_id.get(sid)
                if not student:
                    continue
                student['veto_count'] = max(0, _parse_int_safe(student.get('veto_count'), 0) - grant)

    target = _compute_active_role_veto_quotas(data, date_key=date_key)
    existing = data['role_veto_monthly'].get(resolved_month, {})
    if not isinstance(existing, dict):
        existing = {}

    next_state = {}
    all_ids = set()
    all_ids.update(str(k) for k in existing.keys())
    all_ids.update(str(k) for k in target.keys())

    for sid_text in all_ids:
        sid = _parse_int_safe(sid_text, 0)
        if sid <= 0:
            continue
        old_grant = _parse_int_safe(existing.get(str(sid)), 0)
        new_grant = _parse_int_safe(target.get(sid), 0)
        if new_grant > 0:
            next_state[str(sid)] = new_grant
        delta = new_grant - old_grant
        if delta == 0:
            continue
        student = by_id.get(sid)
        if not student:
            continue
        student['veto_count'] = max(0, _parse_int_safe(student.get('veto_count'), 0) + delta)

    data['role_veto_monthly'][resolved_month] = next_state
    data['role_veto_applied_month'] = resolved_month


def _reconcile_veto_counters_from_scores(data, month_key=None):
    if not isinstance(data, dict):
        return
    month = str(month_key or _server_now_iso()[:7]).strip()
    if not re.match(r'^\d{4}-\d{2}$', month):
        month = _server_now_iso()[:7]
    grants = {}
    if isinstance(data.get('role_veto_monthly'), dict):
        grants = data['role_veto_monthly'].get(month, {}) or {}
    if not isinstance(grants, dict):
        grants = {}

    net_by_student = {}
    for row in data.get('scores', []) or []:
        if not isinstance(row, dict):
            continue
        if str(row.get('month') or '').strip() != month:
            continue
        sid = _parse_int_safe(row.get('studentId'), 0)
        if sid <= 0:
            continue
        net_by_student[sid] = net_by_student.get(sid, 0) + _parse_int_safe(row.get('vetos'), 0)

    if not net_by_student:
        return
    students = data.get('students', []) or []
    by_id = { _parse_int_safe(s.get('id'), 0): s for s in students if _parse_int_safe(s.get('id'), 0) > 0 }
    for sid, net in net_by_student.items():
        student = by_id.get(sid)
        if not student:
            continue
        grant = _parse_int_safe(grants.get(str(sid)), 0)
        expected = max(0, grant + _parse_int_safe(net, 0))
        student['veto_count'] = expected


def _merge_teacher_scores(existing_data, incoming_data):
    """Merge teacher score payload safely across devices with different local IDs."""
    existing_scores = list(existing_data.get('scores', []) or [])
    incoming_scores = incoming_data.get('scores', []) or []
    if not incoming_scores:
        return existing_scores
    now_iso = _server_now_iso()

    existing_students = existing_data.get('students', []) or []
    incoming_students = incoming_data.get('students', []) or []

    existing_id_by_roll = {}
    existing_id_set = set()
    for student in existing_students:
        sid = student.get('id')
        if sid is None:
            continue
        existing_id_set.add(sid)
        roll = _normalize_roll_value(student.get('roll'))
        if roll and roll not in existing_id_by_roll:
            existing_id_by_roll[roll] = sid

    incoming_roll_by_id = {}
    for student in incoming_students:
        sid = student.get('id')
        if sid is None:
            continue
        roll = _normalize_roll_value(student.get('roll'))
        if roll:
            incoming_roll_by_id[str(sid)] = roll

    score_index = {}
    max_score_id = 0
    for idx, score in enumerate(existing_scores):
        sid = score.get('studentId')
        date_key = str(score.get('date') or '').strip()
        if sid is None or not date_key:
            continue
        score_index[(str(sid), date_key)] = idx
        max_score_id = max(max_score_id, _parse_int_safe(score.get('id')))

    for incoming in incoming_scores:
        if not isinstance(incoming, dict):
            continue
        recorded_by = str(incoming.get('recordedBy') or '').strip().lower()
        if recorded_by and recorded_by != 'teacher':
            continue
        if not recorded_by:
            continue
        incoming_sid = incoming.get('studentId')
        date_key = str(incoming.get('date') or '').strip()
        if incoming_sid is None or not date_key:
            continue

        incoming_roll = incoming_roll_by_id.get(str(incoming_sid), '')
        target_sid = existing_id_by_roll.get(incoming_roll)
        if target_sid is None and incoming_sid in existing_id_set:
            target_sid = incoming_sid
        if target_sid is None:
            continue

        index_key = (str(target_sid), date_key)
        existing_idx = score_index.get(index_key)
        existing_score = existing_scores[existing_idx] if existing_idx is not None else None
        # Teachers are not allowed to change stars/vetos directly. Preserve whatever is on record.
        approved_stars = _parse_int_safe(existing_score.get('stars')) if isinstance(existing_score, dict) else 0
        approved_vetos = _parse_int_safe(existing_score.get('vetos')) if isinstance(existing_score, dict) else 0
        month_key = str(incoming.get('month') or '').strip() or date_key[:7]
        normalized_score = {
            'studentId': target_sid,
            'date': date_key,
            'points': _parse_int_safe(incoming.get('points')),
            'stars': approved_stars,
            'vetos': approved_vetos,
            'month': month_key,
            'notes': str(incoming.get('notes') or ''),
            'recordedBy': 'teacher',
            # Critical for client convergence: without updated_at, stale local rows can
            # win tie-breaks and keep showing old points after a valid teacher update.
            'updated_at': str(incoming.get('updated_at') or now_iso).strip() or now_iso
        }
        if existing_idx is not None:
            # Keep the earliest known created_at when updating an existing record.
            existing_created = str(existing_score.get('created_at') or '').strip() if isinstance(existing_score, dict) else ''
            incoming_created = str(incoming.get('created_at') or '').strip()
            normalized_score['created_at'] = existing_created or incoming_created or normalized_score['updated_at']
            existing_score.update(normalized_score)
        else:
            max_score_id += 1
            normalized_score['id'] = max_score_id
            normalized_score['created_at'] = str(incoming.get('created_at') or normalized_score['updated_at']).strip() or normalized_score['updated_at']
            score_index[index_key] = len(existing_scores)
            existing_scores.append(normalized_score)

    return existing_scores


def _merge_appeals_superset(existing_appeals, incoming_appeals):
    """Merge appeals by id and keep the latest updated entry."""
    merged = {}

    def _appeal_key(item):
        if not isinstance(item, dict):
            return ''
        appeal_id = item.get('id')
        if appeal_id is None:
            return ''
        key = str(appeal_id).strip()
        return key

    for source in (existing_appeals or []), (incoming_appeals or []):
        for item in source:
            if not isinstance(item, dict):
                continue
            key = _appeal_key(item)
            if not key:
                continue
            prev = merged.get(key)
            if not prev:
                merged[key] = dict(item)
                continue
            prev_stamp = _parse_sync_stamp(prev.get('updated_at') or prev.get('created_at'))
            next_stamp = _parse_sync_stamp(item.get('updated_at') or item.get('created_at'))
            if next_stamp >= prev_stamp:
                merged[key] = dict(item)

    return list(merged.values())


def _filter_teacher_payload_to_current_month(incoming_data, teacher_login_id='Teacher'):
    """
    Teachers can only modify:
    - scores for the current server month (recordedBy=teacher)
    - attendance for the current server month
    - their own current-month appeals (e.g. star/veto approval requests)
    """
    if not isinstance(incoming_data, dict):
        return {}
    current_month = _server_now_iso()[:7]
    filtered = dict(incoming_data)

    filtered_scores = []
    for row in incoming_data.get('scores', []) or []:
        if not isinstance(row, dict):
            continue
        recorded_by = str(row.get('recordedBy') or '').strip().lower()
        if recorded_by != 'teacher':
            continue
        date_key = str(row.get('date') or '').strip()
        if not date_key or not date_key.startswith(current_month):
            continue
        month_key = str(row.get('month') or '').strip() or date_key[:7]
        if month_key != current_month:
            continue
        filtered_scores.append(row)
    filtered['scores'] = filtered_scores

    filtered_attendance = []
    for item in incoming_data.get('attendance', []) or []:
        if not isinstance(item, dict):
            continue
        date_key = str(item.get('date') or '').strip()
        if not date_key or not date_key.startswith(current_month):
            continue
        filtered_attendance.append(item)
    filtered['attendance'] = filtered_attendance

    # Appeals: allow only teacher-originated, current-month entries.
    filtered_appeals = []
    teacher_key = str(teacher_login_id or 'Teacher').strip().lower()
    for item in incoming_data.get('appeals', []) or []:
        if not isinstance(item, dict):
            continue
        from_role = str(item.get('from_role') or '').strip().lower()
        created_by = str(item.get('created_by') or '').strip().lower()
        if from_role and from_role != 'teacher' and created_by != teacher_key and created_by != 'teacher':
            continue
        score_month = str(item.get('score_month') or '').strip()
        score_date = str(item.get('score_date') or '').strip()
        month_key = score_month or (score_date[:7] if len(score_date) >= 7 else '')
        if not month_key:
            created_at = str(item.get('created_at') or '').strip()
            if len(created_at) >= 7:
                month_key = created_at[:7]
        if month_key != current_month:
            continue
        filtered_appeals.append(item)
    filtered['appeals'] = filtered_appeals

    # CRITICAL FIX: Ensure students are preserved for attendance merge identity lookup
    # The merge function needs student ID->roll mappings to properly identify attendance records
    if 'students' not in filtered and isinstance(incoming_data.get('students'), list):
        filtered['students'] = incoming_data.get('students', [])

    return filtered


def _build_teacher_replication_patch(full_payload, teacher_login_id='Teacher'):
    """Build a narrow replication patch safe to apply on master server."""
    current_month = _server_now_iso()[:7]
    payload = full_payload if isinstance(full_payload, dict) else {}

    students_min = []
    for student in payload.get('students', []) or []:
        if not isinstance(student, dict):
            continue
        sid = student.get('id')
        roll = _normalize_roll_value(student.get('roll'))
        if sid is None or not roll:
            continue
        students_min.append({'id': sid, 'roll': roll})

    scores = []
    for row in payload.get('scores', []) or []:
        if not isinstance(row, dict):
            continue
        recorded_by = str(row.get('recordedBy') or '').strip().lower()
        if recorded_by != 'teacher':
            continue
        date_key = str(row.get('date') or '').strip()
        if not date_key or not date_key.startswith(current_month):
            continue
        month_key = str(row.get('month') or '').strip() or date_key[:7]
        if month_key != current_month:
            continue
        scores.append(row)

    attendance = []
    for item in payload.get('attendance', []) or []:
        if not isinstance(item, dict):
            continue
        date_key = str(item.get('date') or '').strip()
        if not date_key or not date_key.startswith(current_month):
            continue
        attendance.append(item)

    appeals = []
    teacher_key = str(teacher_login_id or 'Teacher').strip().lower()
    for item in payload.get('appeals', []) or []:
        if not isinstance(item, dict):
            continue
        from_role = str(item.get('from_role') or '').strip().lower()
        created_by = str(item.get('created_by') or '').strip().lower()
        if from_role and from_role != 'teacher' and created_by != teacher_key and created_by != 'teacher':
            continue
        score_month = str(item.get('score_month') or '').strip()
        score_date = str(item.get('score_date') or '').strip()
        month_key = score_month or (score_date[:7] if len(score_date) >= 7 else '')
        if not month_key:
            created_at = str(item.get('created_at') or '').strip()
            if len(created_at) >= 7:
                month_key = created_at[:7]
        if month_key != current_month:
            continue
        appeals.append(item)

    syllabus_tracking = []
    for row in payload.get('syllabus_tracking', []) or []:
        if not isinstance(row, dict):
            continue
        key = str(row.get('key') or '').strip()
        if not key:
            continue
        syllabus_tracking.append(row)

    return {
        'actor_role': 'teacher',
        'replica_purpose': 'teacher_patch',
        'students': students_min,
        'scores': scores,
        'attendance': attendance,
        'appeals': appeals,
        'syllabus_tracking': syllabus_tracking,
        'updated_at': payload.get('updated_at')
    }


def _merge_month_students_superset(existing_ms, incoming_ms):
    """Superset merge for month_students: never let an incoming partial roster shrink an existing month's list."""
    if not isinstance(existing_ms, dict):
        existing_ms = {}
    if not isinstance(incoming_ms, dict):
        incoming_ms = {}
    merged = {}
    for month in set(list(existing_ms.keys()) + list(incoming_ms.keys())):
        existing_rolls = list(existing_ms.get(month) or [])
        incoming_rolls = list(incoming_ms.get(month) or [])
        seen = set(str(r or '').strip().upper() for r in existing_rolls if r)
        combined = list(existing_rolls)
        for r in incoming_rolls:
            key = str(r or '').strip().upper()
            if key and key not in seen:
                combined.append(r)
                seen.add(key)
        merged[month] = combined
    return merged


def _merge_month_roster_profiles_superset(existing_rp, incoming_rp):
    """Superset merge for month_roster_profiles: union by roll across months."""
    if not isinstance(existing_rp, dict):
        existing_rp = {}
    if not isinstance(incoming_rp, dict):
        incoming_rp = {}
    merged = {}
    for month in set(list(existing_rp.keys()) + list(incoming_rp.keys())):
        by_roll = {}
        for p in (existing_rp.get(month) or []):
            if not isinstance(p, dict):
                continue
            roll = str(p.get('roll') or '').strip().upper()
            if roll:
                by_roll[roll] = dict(p)
        for p in (incoming_rp.get(month) or []):
            if not isinstance(p, dict):
                continue
            roll = str(p.get('roll') or '').strip().upper()
            if roll:
                by_roll[roll] = {**(by_roll.get(roll) or {}), **p}
        merged[month] = list(by_roll.values())
    return merged


def _merge_students_preserve_active(existing_students, incoming_students):
    """Merge student lists, never downgrading active:True→False without a genuinely newer timestamp.
    This protects against sync-induced corruption where a peer device pushes stale active:false flags."""
    if not isinstance(existing_students, list):
        existing_students = []
    if not isinstance(incoming_students, list):
        incoming_students = []
    by_roll = {}
    for s in existing_students:
        if not isinstance(s, dict):
            continue
        roll = str(s.get('roll') or '').strip().upper()
        if roll:
            by_roll[roll] = dict(s)
    for s in incoming_students:
        if not isinstance(s, dict):
            continue
        roll = str(s.get('roll') or '').strip().upper()
        if not roll:
            continue
        existing = by_roll.get(roll)
        if not existing:
            by_roll[roll] = dict(s)
            continue
        existing_stamp = _parse_sync_stamp(existing.get('updated_at') or existing.get('created_at') or '')
        incoming_stamp = _parse_sync_stamp(s.get('updated_at') or s.get('created_at') or '')
        if incoming_stamp > existing_stamp:
            # Incoming record is genuinely newer — accept it as-is.
            by_roll[roll] = {**existing, **s}
        else:
            # Tie or existing is newer: merge but never downgrade active true→false.
            merged_s = {**existing, **s}
            if existing.get('active') is not False and merged_s.get('active') is False:
                merged_s['active'] = existing.get('active', True)
            by_roll[roll] = merged_s
    return list(by_roll.values())


def _merge_scores_superset(existing_scores, incoming_scores):
    """Merge score lists without dropping existing rows when an incoming snapshot is stale."""
    merged = {}
    max_score_id = 0

    def _normalize_score(score):
        if not isinstance(score, dict):
            return None, None
        sid = score.get('studentId')
        date_key = str(score.get('date') or '').strip()
        if sid is None or not date_key:
            return None, None
        month_key = str(score.get('month') or '').strip() or date_key[:7]
        normalized = dict(score)
        normalized['studentId'] = sid
        normalized['date'] = date_key
        normalized['month'] = month_key
        normalized['points'] = _parse_int_safe(score.get('points'))
        normalized['stars'] = _parse_int_safe(score.get('stars'))
        normalized['vetos'] = _parse_int_safe(score.get('vetos'))
        key = (str(sid), date_key, month_key)
        return key, normalized

    for score in existing_scores or []:
        key, normalized = _normalize_score(score)
        if key is None:
            continue
        merged[key] = normalized
        max_score_id = max(max_score_id, _parse_int_safe(normalized.get('id')))

    for score in incoming_scores or []:
        key, normalized = _normalize_score(score)
        if key is None:
            continue
        if key in merged:
            prev = merged[key]
            prev_stamp = _parse_sync_stamp(prev.get('updated_at', ''))
            next_stamp = _parse_sync_stamp(normalized.get('updated_at', ''))
            if next_stamp > prev_stamp:
                merged[key] = normalized
            elif next_stamp == prev_stamp and _parse_int_safe(normalized.get('id')) > _parse_int_safe(prev.get('id')):
                # Same age (or both missing updated_at): keep the higher-id record as tiebreaker.
                merged[key] = normalized
            # else prev is same age or newer — keep it
        else:
            merged[key] = normalized
        max_score_id = max(max_score_id, _parse_int_safe(normalized.get('id')))

    result = []
    for record in merged.values():
        if not _parse_int_safe(record.get('id')):
            max_score_id += 1
            record['id'] = max_score_id
        result.append(record)
    return result


def _merge_notification_history(existing_history, incoming_history):
    """Keep all notification history entries across sync peers."""
    merged = {}

    def _entry_key(item):
        if not isinstance(item, dict):
            return ''
        fp = str(item.get('fingerprint') or '').strip().lower()
        if fp:
            return fp
        title = str(item.get('title') or '').strip().lower()
        detail = str(item.get('detail') or '').strip().lower()
        meta = str(item.get('meta') or '').strip().lower()
        return f'{title}||{detail}||{meta}'

    for source in (existing_history or []), (incoming_history or []):
        for item in source:
            if not isinstance(item, dict):
                continue
            key = _entry_key(item)
            if not key:
                continue
            prev = merged.get(key)
            if not prev:
                merged[key] = dict(item)
                continue
            prev_stamp = _parse_sync_stamp(prev.get('logged_at'))
            next_stamp = _parse_sync_stamp(item.get('logged_at'))
            if next_stamp >= prev_stamp:
                merged[key] = dict(item)

    return list(merged.values())


def _merge_election_votes_superset(existing_votes, incoming_votes, mode='party'):
    """Merge election votes by voter key and keep latest timestamped entry."""
    merged = {}

    def _normalize_vote(item):
        if not isinstance(item, dict):
            return None, None
        post = str(item.get('post') or '').strip()
        if not post:
            return None, None
        normalized = dict(item)
        normalized['post'] = post
        if mode == 'party':
            party_id = _parse_int_safe(item.get('partyId'), 0)
            if party_id <= 0:
                return None, None
            normalized['partyId'] = party_id
            candidate_id = _parse_int_safe(item.get('candidateId'), 0)
            if candidate_id <= 0:
                return None, None
            normalized['candidateId'] = candidate_id
            key = f'{post}::party::{party_id}'
        elif mode == 'teacher':
            teacher_id = _parse_int_safe(item.get('teacherId'), 0)
            if teacher_id <= 0:
                return None, None
            normalized['teacherId'] = teacher_id
            candidate_id = _parse_int_safe(item.get('candidateId'), 0)
            if candidate_id <= 0:
                return None, None
            normalized['candidateId'] = candidate_id
            key = f'{post}::teacher::{teacher_id}'
        else:
            voter_id = _parse_int_safe(item.get('voterStudentId'), 0)
            if voter_id <= 0:
                return None, None
            normalized['voterStudentId'] = voter_id
            vote_type = str(item.get('voteType') or 'candidate').strip().lower()
            if vote_type not in ('candidate', 'abstain', 'nota'):
                vote_type = 'candidate'
            normalized['voteType'] = vote_type
            if vote_type == 'candidate':
                candidate_id = _parse_int_safe(item.get('candidateId'), 0)
                if candidate_id <= 0:
                    return None, None
                normalized['candidateId'] = candidate_id
            else:
                normalized['candidateId'] = None
            key = f'{post}::student::{voter_id}'
        return key, normalized

    for source in (existing_votes or []), (incoming_votes or []):
        for item in source:
            key, normalized = _normalize_vote(item)
            if key is None:
                continue
            prev = merged.get(key)
            if not prev:
                merged[key] = normalized
                continue
            prev_stamp = _parse_sync_stamp(prev.get('timestamp') or prev.get('updated_at') or prev.get('created_at'))
            next_stamp = _parse_sync_stamp(normalized.get('timestamp') or normalized.get('updated_at') or normalized.get('created_at'))
            if next_stamp >= prev_stamp:
                merged[key] = normalized

    return list(merged.values())


def _merge_pending_results_superset(existing_results, incoming_results):
    """Merge pending election results by post/source and keep latest record."""
    merged = {}

    def _entry_key(item):
        if not isinstance(item, dict):
            return ''
        post = str(item.get('post') or '').strip().lower()
        source = str(item.get('source') or '').strip().lower()
        if not post or not source:
            return ''
        return f'{post}::{source}'

    def _timestamp(item):
        if not isinstance(item, dict):
            return 0.0
        return max(
            _parse_sync_stamp(item.get('decided_at')),
            _parse_sync_stamp(item.get('updated_at')),
            _parse_sync_stamp(item.get('created_at'))
        )

    for source in (existing_results or []), (incoming_results or []):
        for item in source:
            if not isinstance(item, dict):
                continue
            key = _entry_key(item)
            if not key:
                continue
            prev = merged.get(key)
            if not prev or _timestamp(item) >= _timestamp(prev):
                merged[key] = dict(item)

    return list(merged.values())


def _normalize_attendance_status(value):
    status = str(value or '').strip().lower()
    if status in ('absent', 'late', 'leave', 'present'):
        return status
    return 'present'


def _merge_attendance_superset(existing_data, incoming_data):
    """Merge attendance by latest updated_at, keyed by date + roll (fallback studentId)."""
    existing_attendance = existing_data.get('attendance', []) if isinstance(existing_data, dict) else []
    incoming_attendance = incoming_data.get('attendance', []) if isinstance(incoming_data, dict) else []
    existing_students = existing_data.get('students', []) if isinstance(existing_data, dict) else []
    incoming_students = incoming_data.get('students', []) if isinstance(incoming_data, dict) else []

    def _normalize_att_roll(value):
        # Attendance payloads from older clients may contain formatted rolls
        # (spaces or separators). Normalize aggressively for stable identity mapping.
        return re.sub(r'[^A-Z0-9]', '', _normalize_roll_value(value))

    existing_id_by_roll = {}
    for student in existing_students or []:
        sid = _parse_int_safe(student.get('id'), 0)
        roll = _normalize_att_roll(student.get('roll'))
        if sid > 0 and roll and roll not in existing_id_by_roll:
            existing_id_by_roll[roll] = sid

    incoming_roll_by_id = {}
    for student in incoming_students or []:
        sid = _parse_int_safe(student.get('id'), 0)
        roll = _normalize_att_roll(student.get('roll'))
        if sid > 0 and roll:
            incoming_roll_by_id[str(sid)] = roll

    merged = {}

    def _normalize_item(item):
        if not isinstance(item, dict):
            return None, None
        date_key = str(item.get('date') or '').strip()
        if not date_key:
            return None, None
        roll = _normalize_att_roll(item.get('roll'))
        sid = _parse_int_safe(item.get('studentId'), 0)
        if not roll and sid > 0:
            roll = incoming_roll_by_id.get(str(sid), '')
        if roll and roll in existing_id_by_roll:
            sid = existing_id_by_roll[roll]
        identity = roll or (str(sid) if sid > 0 else '')
        if not identity:
            return None, None
        normalized = dict(item)
        normalized['date'] = date_key
        normalized['status'] = _normalize_attendance_status(item.get('status'))
        normalized['remarks'] = str(item.get('remarks') or '')
        if roll:
            normalized['roll'] = roll
        if sid > 0:
            normalized['studentId'] = sid
        key = f'{date_key}::{identity}'
        return key, normalized

    for source in (existing_attendance or []), (incoming_attendance or []):
        for item in source:
            key, normalized = _normalize_item(item)
            if key is None:
                continue
            prev = merged.get(key)
            if not prev:
                merged[key] = normalized
                continue
            prev_stamp = _parse_sync_stamp(prev.get('updated_at') or prev.get('created_at'))
            next_stamp = _parse_sync_stamp(normalized.get('updated_at') or normalized.get('created_at'))
            if next_stamp >= prev_stamp:
                merged[key] = normalized

    # SAFEGUARD: Ensure all merged attendance records have timestamps for proper sync ordering
    now_iso = _server_now_iso()
    for item in merged.values():
        if isinstance(item, dict):
            if not item.get('updated_at'):
                item['updated_at'] = item.get('created_at', now_iso)
            if not item.get('created_at'):
                item['created_at'] = now_iso

    return list(merged.values())


def _merge_fee_records_superset(existing_records, incoming_records):
    """
    Merge fee records by studentId.

    Safety: never lose evidence of payments (last_paid_date/payment_history) even if a stale device
    has a newer updated_at due to clock skew.
    """
    merged = {}

    def _normalize_record(item):
        if not isinstance(item, dict):
            return None, None
        sid = _parse_int_safe(item.get('studentId'), 0)
        if sid <= 0:
            return None, None
        normalized = dict(item)
        normalized['studentId'] = sid
        return str(sid), normalized

    def _max_date(a, b):
        a = str(a or '').strip()
        b = str(b or '').strip()
        if not a:
            return b
        if not b:
            return a
        # YYYY-MM-DD lexicographic compare works.
        return a if a >= b else b

    def _merge_payment_history(prev_list, next_list):
        merged_list = []
        seen = set()
        for src in (prev_list or []), (next_list or []):
            if not isinstance(src, list):
                continue
            for item in src:
                if not isinstance(item, dict):
                    continue
                date_key = str(item.get('date') or item.get('paid_on') or item.get('paidAt') or '').strip()
                amount_key = str(item.get('amount') or '').strip()
                note_key = str(item.get('note') or item.get('remarks') or '').strip().lower()
                fp = f'{date_key}::{amount_key}::{note_key}'
                if fp in seen:
                    continue
                seen.add(fp)
                merged_list.append(dict(item))
        # Keep stable ordering by (date, amount) when possible.
        def _sort_key(x):
            d = str(x.get('date') or x.get('paid_on') or x.get('paidAt') or '')
            a = _parse_int_safe(x.get('amount'), 0)
            return (d, a)
        try:
            merged_list.sort(key=_sort_key)
        except Exception:
            pass
        return merged_list

    def _parse_float(value):
        try:
            v = float(value)
            return v if v == v else None
        except Exception:
            return None

    def _choose_text(prev_val, next_val, prefer_next=False):
        prev_text = str(prev_val or '').strip()
        next_text = str(next_val or '').strip()
        if not prev_text:
            return next_text
        if not next_text:
            return prev_text
        return next_text if prefer_next else prev_text

    def _merge_pair(prev, nxt):
        prev_stamp = _parse_sync_stamp(prev.get('updated_at') or prev.get('created_at'))
        next_stamp = _parse_sync_stamp(nxt.get('updated_at') or nxt.get('created_at'))
        prefer_next = next_stamp >= prev_stamp

        result = dict(prev if not prefer_next else nxt)
        # Always preserve payment proof.
        result['payment_history'] = _merge_payment_history(prev.get('payment_history'), nxt.get('payment_history'))
        result['last_paid_date'] = _max_date(prev.get('last_paid_date'), nxt.get('last_paid_date'))

        # Prefer the latest cycle anchor so paid records don't revert to an older due date.
        result['start_date'] = _max_date(prev.get('start_date'), nxt.get('start_date'))

        # Numeric fields: prefer whichever record matches the chosen start_date (current cycle).
        chosen_cycle = str(result.get('start_date') or '').strip()
        prev_cycle = str(prev.get('start_date') or '').strip()
        next_cycle = str(nxt.get('start_date') or '').strip()
        cycle_source = None
        if chosen_cycle and chosen_cycle == next_cycle:
            cycle_source = nxt
        elif chosen_cycle and chosen_cycle == prev_cycle:
            cycle_source = prev
        else:
            cycle_source = nxt if prefer_next else prev

        amount = _parse_float(cycle_source.get('amount'))
        pending = _parse_float(cycle_source.get('pending_amount'))
        if amount is not None:
            result['amount'] = amount
        if pending is not None:
            result['pending_amount'] = pending

        # Period months: keep a sane integer.
        period = _parse_int_safe(cycle_source.get('period_months'), 0)
        if period > 0:
            result['period_months'] = period

        # Remarks: keep non-empty; prefer whichever record is newer.
        result['remarks'] = _choose_text(prev.get('remarks'), nxt.get('remarks'), prefer_next=prefer_next)

        # Timestamps: keep created_at earliest, updated_at latest-ish.
        created = _choose_text(prev.get('created_at'), nxt.get('created_at'), prefer_next=False)
        if created:
            result['created_at'] = created
        updated = _choose_text(prev.get('updated_at'), nxt.get('updated_at'), prefer_next=prefer_next)
        if updated:
            result['updated_at'] = updated

        # Ensure studentId preserved.
        result['studentId'] = _parse_int_safe(result.get('studentId'), _parse_int_safe(prev.get('studentId'), 0))
        return result

    for source in (existing_records or []), (incoming_records or []):
        for item in source:
            key, normalized = _normalize_record(item)
            if key is None:
                continue
            prev = merged.get(key)
            if not prev:
                merged[key] = normalized
                continue
            merged[key] = _merge_pair(prev, normalized)

    return list(merged.values())


def _merge_resource_cabinet_superset(existing_items, incoming_items):
    """Merge resource cabinet items by id (int)."""
    merged = {}

    def _normalize(item):
        if not isinstance(item, dict):
            return None, None
        item_id = _parse_int_safe(item.get('id'), 0)
        if item_id <= 0:
            return None, None
        normalized = dict(item)
        normalized['id'] = item_id
        normalized['name'] = str(item.get('name') or '').strip()
        normalized['unit'] = str(item.get('unit') or '').strip()
        normalized['price_per_unit'] = float(item.get('price_per_unit') or 0) if str(item.get('price_per_unit') or '').strip() else float(item.get('price_per_unit') or 0)
        normalized['total_held'] = max(0, _parse_int_safe(item.get('total_held'), 0))
        normalized['updated_at'] = str(item.get('updated_at') or normalized.get('updated_at') or '').strip()
        normalized['created_at'] = str(item.get('created_at') or normalized.get('created_at') or normalized['updated_at'] or '').strip()
        return str(item_id), normalized

    for src in (existing_items or []), (incoming_items or []):
        if not isinstance(src, list):
            continue
        for item in src:
            key, normalized = _normalize(item)
            if not key:
                continue
            prev = merged.get(key)
            if not prev:
                merged[key] = normalized
                continue
            prev_stamp = _parse_sync_stamp(prev.get('updated_at') or prev.get('created_at'))
            next_stamp = _parse_sync_stamp(normalized.get('updated_at') or normalized.get('created_at'))
            merged[key] = normalized if next_stamp >= prev_stamp else prev

    return list(merged.values())


def _resource_status_rank(value):
    text = str(value or '').strip().lower()
    ranks = {
        'draft': 0,
        'pending_teacher': 1,
        'recommended': 2,
        'not_recommended': 2,
        'pending_admin': 3,
        'approved': 4,
        'rejected': 4,
        'fulfilled': 5,
        'cancelled': 5
    }
    return ranks.get(text, 0)


def _merge_resource_requests_superset(existing_requests, incoming_requests):
    """
    Merge resource requests by id.
    Safety: never lose recommendation/approval decisions once present.
    """
    merged = {}

    def _normalize(item):
        if not isinstance(item, dict):
            return None, None
        rid = _parse_int_safe(item.get('id'), 0)
        if rid <= 0:
            return None, None
        normalized = dict(item)
        normalized['id'] = rid
        sid = _parse_int_safe(item.get('studentId'), 0)
        if sid > 0:
            normalized['studentId'] = sid
        normalized['month'] = str(item.get('month') or '').strip()
        normalized['status'] = str(item.get('status') or '').strip().lower()
        normalized['updated_at'] = str(item.get('updated_at') or '').strip()
        normalized['created_at'] = str(item.get('created_at') or normalized['updated_at'] or '').strip()
        return str(rid), normalized

    def _merge_pair(prev, nxt):
        prev_stamp = _parse_sync_stamp(prev.get('updated_at') or prev.get('created_at'))
        next_stamp = _parse_sync_stamp(nxt.get('updated_at') or nxt.get('created_at'))
        prefer_next = next_stamp >= prev_stamp
        base = dict(prev if not prefer_next else nxt)

        # Preserve decisions/proof.
        for key in ('teacher_decision', 'teacher_remark', 'teacher_login_id', 'teacher_updated_at',
                    'admin_decision', 'admin_remark', 'admin_login_id', 'admin_updated_at',
                    'approved_at', 'fulfilled_at', 'urgent'):
            prev_val = prev.get(key)
            next_val = nxt.get(key)
            if str(next_val or '').strip() and prefer_next:
                base[key] = next_val
            elif str(prev_val or '').strip() and not str(base.get(key) or '').strip():
                base[key] = prev_val

        # Preserve the furthest-along status.
        prev_status = str(prev.get('status') or '').strip().lower()
        next_status = str(nxt.get('status') or '').strip().lower()
        if _resource_status_rank(next_status) >= _resource_status_rank(prev_status):
            base['status'] = next_status or prev_status
        else:
            base['status'] = prev_status or next_status

        return base

    for src in (existing_requests or []), (incoming_requests or []):
        if not isinstance(src, list):
            continue
        for item in src:
            key, normalized = _normalize(item)
            if not key:
                continue
            prev = merged.get(key)
            if not prev:
                merged[key] = normalized
                continue
            merged[key] = _merge_pair(prev, normalized)

    return list(merged.values())


def _merge_leadership_superset(existing_posts, incoming_posts):
    """Merge leadership posts by id; never overwrite a populated holder with an empty one."""
    merged = {}
    def is_populated(p):
        return bool(str(p.get('holder') or '').strip() or str(p.get('roll') or '').strip())
    for p in (existing_posts or []):
        pid = int(p.get('id') or 0)
        if pid:
            merged[pid] = dict(p)
    for p in (incoming_posts or []):
        pid = int(p.get('id') or 0)
        if not pid:
            continue
        existing = merged.get(pid)
        if not existing:
            merged[pid] = dict(p)
            continue
        if is_populated(existing) and not is_populated(p):
            continue
        merged[pid] = {**existing, **p}
    return list(merged.values())


def _merge_group_crs_superset(existing_crs, incoming_crs):
    """Merge group CRs by id; prefer entries with studentId assigned.
    An 'ended' status is preserved unless the incoming entry assigns a *different* student
    (which indicates an intentional re-assignment, not a stale push)."""
    merged = {}
    for arr in [existing_crs or [], incoming_crs or []]:
        for cr in arr:
            cid = int(cr.get('id') or 0)
            if not cid:
                continue
            prev = merged.get(cid)
            if not prev:
                merged[cid] = dict(cr)
                continue
            if prev.get('studentId') and not cr.get('studentId'):
                continue
            new_entry = {**prev, **cr}
            # Preserve 'ended' against stale clients that still have 'active' for the same student.
            prev_status = str(prev.get('status') or '').strip().lower()
            new_status = str(cr.get('status') or '').strip().lower()
            if (prev_status == 'ended' and new_status not in ('ended',)
                    and prev.get('studentId') and cr.get('studentId')
                    and int(prev.get('studentId') or 0) == int(cr.get('studentId') or 0)):
                new_entry['status'] = 'ended'
            merged[cid] = new_entry
    return list(merged.values())


def _merge_class_reps_superset(existing_reps, incoming_reps):
    """Merge class reps by id; prefer entries with studentId assigned.
    An 'ended' status is preserved unless the incoming entry assigns a *different* student."""
    merged = {}
    for arr in [existing_reps or [], incoming_reps or []]:
        for rep in arr:
            rid = int(rep.get('id') or 0)
            if not rid:
                continue
            prev = merged.get(rid)
            if not prev:
                merged[rid] = dict(rep)
                continue
            if prev.get('studentId') and not rep.get('studentId'):
                continue
            new_entry = {**prev, **rep}
            prev_status = str(prev.get('status') or '').strip().lower()
            new_status = str(rep.get('status') or '').strip().lower()
            if (prev_status == 'ended' and new_status not in ('ended',)
                    and prev.get('studentId') and rep.get('studentId')
                    and int(prev.get('studentId') or 0) == int(rep.get('studentId') or 0)):
                new_entry['status'] = 'ended'
            merged[rid] = new_entry
    return list(merged.values())


def _merge_parties_superset(existing_parties, incoming_parties):
    """Merge parties by code; never overwrite non-empty members with empty."""
    merged = {}
    for arr in [existing_parties or [], incoming_parties or []]:
        for party in arr:
            key = str(party.get('code') or '').strip().upper() or str(party.get('id') or '')
            if not key:
                continue
            prev = merged.get(key)
            if not prev:
                merged[key] = dict(party)
                continue
            prev_members = prev.get('members') or []
            new_members = party.get('members') or []
            if prev_members and not new_members:
                merged[key] = {**prev, **party, 'members': prev_members}
            else:
                merged[key] = {**prev, **party}
    return list(merged.values())


def _merge_pending_cr_requests_superset(existing_reqs, incoming_reqs):
    """Merge pending CR requests by id.
    Never downgrade a resolved (approved/rejected) request back to pending.
    """
    merged = {}
    for arr in [existing_reqs or [], incoming_reqs or []]:
        for req in arr:
            if not isinstance(req, dict):
                continue
            rid = int(req.get('id') or 0)
            if not rid:
                continue
            prev = merged.get(rid)
            if not prev:
                merged[rid] = dict(req)
                continue
            prev_status = str(prev.get('status') or '').strip().lower()
            new_status = str(req.get('status') or '').strip().lower()
            # Keep the resolved state if it has already been acted on
            if prev_status in ('approved', 'rejected') and new_status == 'pending':
                continue
            merged[rid] = {**prev, **req}
    return list(merged.values())


def _merge_pending_cr_requests_teacher(existing_reqs, incoming_reqs, teacher_login_id):
    """Teacher-safe merge for pending CR requests.
    Teachers can only create new pending requests; they cannot resolve existing ones.
    """
    now_iso = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    existing = existing_reqs if isinstance(existing_reqs, list) else []
    by_id = {
        _parse_int_safe(req.get('id'), 0): dict(req)
        for req in existing
        if isinstance(req, dict) and _parse_int_safe(req.get('id'), 0) > 0
    }

    sanitized_new = []
    if not isinstance(incoming_reqs, list):
        incoming_reqs = []
    for raw in incoming_reqs:
        if not isinstance(raw, dict):
            continue
        rid = _parse_int_safe(raw.get('id'), 0)
        if rid <= 0 or rid in by_id:
            continue
        group = str(raw.get('group') or '').strip().upper()
        student_id = _parse_int_safe(raw.get('studentId'), 0)
        elected_on = str(raw.get('elected_on') or '').strip()[:10]
        if not group or student_id <= 0:
            continue
        post = str(raw.get('post') or f'CR - Group {group}').strip() or f'CR - Group {group}'
        note = str(raw.get('note') or '').strip()[:250]
        sanitized_new.append({
            'id': rid,
            'group': group,
            'post': post,
            'studentId': student_id,
            'elected_on': elected_on,
            'note': note,
            'requested_by': teacher_login_id or 'Teacher',
            'requested_at': str(raw.get('requested_at') or now_iso).strip() or now_iso,
            'status': 'pending',
            'updated_at': now_iso,
        })

    return _merge_pending_cr_requests_superset(existing, sanitized_new)


def _merge_resource_transactions_superset(existing_rows, incoming_rows):
    """Merge resource transactions by id."""
    merged = {}

    def _normalize(item):
        if not isinstance(item, dict):
            return None, None
        tid = _parse_int_safe(item.get('id'), 0)
        if tid <= 0:
            return None, None
        normalized = dict(item)
        normalized['id'] = tid
        sid = _parse_int_safe(item.get('studentId'), 0)
        if sid > 0:
            normalized['studentId'] = sid
        normalized['month'] = str(item.get('month') or '').strip()
        normalized['updated_at'] = str(item.get('updated_at') or '').strip()
        normalized['created_at'] = str(item.get('created_at') or normalized['updated_at'] or '').strip()
        return str(tid), normalized

    for src in (existing_rows or []), (incoming_rows or []):
        if not isinstance(src, list):
            continue
        for item in src:
            key, normalized = _normalize(item)
            if not key:
                continue
            prev = merged.get(key)
            if not prev:
                merged[key] = normalized
                continue
            prev_stamp = _parse_sync_stamp(prev.get('updated_at') or prev.get('created_at'))
            next_stamp = _parse_sync_stamp(normalized.get('updated_at') or normalized.get('created_at'))
            merged[key] = normalized if next_stamp >= prev_stamp else prev

    return list(merged.values())




def _merge_resource_advantage_deductions_superset(existing_rows, incoming_rows):
    """
    Merge resource_advantage_deductions by id.
    Safety rules:
    - Never delete a deduction record.
    - Once reversed=True, never revert back to False.
    - On conflict, keep the record that has reversed=True; otherwise keep the newer one.
    """
    merged = {}

    def _normalize(item):
        if not isinstance(item, dict):
            return None, None
        did = _parse_int_safe(item.get('id'), 0)
        if did <= 0:
            return None, None
        normalized = dict(item)
        normalized['id'] = did
        sid = _parse_int_safe(item.get('studentId'), 0)
        if sid > 0:
            normalized['studentId'] = sid
        normalized['month'] = str(item.get('month') or '').strip()
        normalized['points_deducted'] = max(0, _parse_int_safe(item.get('points_deducted'), 0))
        normalized['transaction_id'] = _parse_int_safe(item.get('transaction_id'), 0)
        normalized['reversed'] = bool(item.get('reversed'))
        normalized['created_at'] = str(item.get('created_at') or '').strip()
        return str(did), normalized

    for src in (existing_rows or []), (incoming_rows or []):
        if not isinstance(src, list):
            continue
        for item in src:
            key, normalized = _normalize(item)
            if not key:
                continue
            prev = merged.get(key)
            if not prev:
                merged[key] = normalized
                continue
            # Reversal is permanent — once reversed, keep it reversed regardless of timestamp.
            if prev.get('reversed') and not normalized.get('reversed'):
                continue  # keep prev (already reversed)
            if normalized.get('reversed') and not prev.get('reversed'):
                merged[key] = normalized  # incoming has reversal, take it
                continue
            # Both same reversal state — use the newer record.
            prev_stamp = _parse_sync_stamp(prev.get('created_at') or '')
            next_stamp = _parse_sync_stamp(normalized.get('created_at') or '')
            merged[key] = normalized if next_stamp >= prev_stamp else prev

    return list(merged.values())


def _build_teacher_resource_request(existing_payload, raw, teacher_login_id, month_key, now_iso):
    """Sanitize a teacher-created resource request row."""
    if not isinstance(existing_payload, dict) or not isinstance(raw, dict):
        return None

    rid = _parse_int_safe(raw.get('id'), 0)
    if rid <= 0:
        return None

    mode = str(raw.get('type') or '').strip().lower()
    if mode not in {'redeem_points', 'cash_purchase'}:
        return None

    month = str(raw.get('month') or month_key or '').strip()
    if month != str(month_key or '').strip():
        return None

    student_id = _parse_int_safe(raw.get('studentId'), 0)
    student_roll = _normalize_roll_value(raw.get('student_roll') or raw.get('studentRoll') or '')
    if student_id <= 0 and student_roll:
        student_id = _find_student_id_by_roll(existing_payload, student_roll)
    if student_id <= 0:
        return None

    students = existing_payload.get('students', []) if isinstance(existing_payload.get('students'), list) else []
    student_obj = next((s for s in students if _parse_int_safe((s or {}).get('id'), 0) == student_id), None)
    if not student_roll and isinstance(student_obj, dict):
        student_roll = _normalize_roll_value(student_obj.get('roll'))

    item_id = _parse_int_safe(raw.get('item_id') or raw.get('itemId'), 0)
    if item_id <= 0:
        return None

    cabinet = existing_payload.get('resource_cabinet', []) if isinstance(existing_payload.get('resource_cabinet'), list) else []
    cabinet_item = next((it for it in cabinet if _parse_int_safe((it or {}).get('id'), 0) == item_id), None)
    if not isinstance(cabinet_item, dict):
        return None

    qty = max(1, _parse_int_safe(raw.get('qty'), 1))

    def _float_or(value, default_value):
        try:
            return float(value)
        except Exception:
            return float(default_value)

    unit_price = max(0.0, _float_or(raw.get('price_per_unit'), cabinet_item.get('price_per_unit') or 0))
    total_cost = max(0.0, _float_or(raw.get('total_cost'), unit_price * qty))
    points_cost = max(0, _parse_int_safe(raw.get('points_cost'), 0))
    cash_paid = max(0, _parse_int_safe(raw.get('cash_paid'), 0))

    return {
        'id': rid,
        'type': mode,
        'studentId': student_id,
        'student_roll': student_roll,
        'month': month,
        'item_id': item_id,
        'item_name': str(raw.get('item_name') or cabinet_item.get('name') or '').strip(),
        'unit': str(raw.get('unit') or cabinet_item.get('unit') or '').strip(),
        'qty': qty,
        'price_per_unit': unit_price,
        'total_cost': total_cost,
        'points_cost': points_cost if mode == 'redeem_points' else 0,
        'cash_paid': cash_paid if mode == 'cash_purchase' else 0,
        'urgent': False,
        'admin_veto': False,
        'status': 'pending_teacher',
        'teacher_decision': '',
        'teacher_remark': '',
        'created_by_login_id': teacher_login_id,
        'created_at': now_iso,
        'updated_at': now_iso,
    }


def _merge_resource_requests_teacher(existing_payload, incoming_requests, teacher_login_id, month_key):
    """
    Teachers can only:
    - create new pending_teacher requests for the current server month
    - recommend / not recommend existing requests for the current month
    - add teacher remark
    """
    now_iso = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    existing_obj = existing_payload if isinstance(existing_payload, dict) else {}
    existing_requests = existing_obj.get('resource_requests', []) if isinstance(existing_obj.get('resource_requests'), list) else []
    by_id = {}
    for item in existing_requests:
        if isinstance(item, dict):
            rid = _parse_int_safe(item.get('id'), 0)
            if rid > 0 and rid not in by_id:
                by_id[rid] = dict(item)

    updated = []
    if not isinstance(incoming_requests, list):
        incoming_requests = []
    for raw in incoming_requests:
        if not isinstance(raw, dict):
            continue
        rid = _parse_int_safe(raw.get('id'), 0)
        if rid <= 0:
            continue

        if rid not in by_id:
            created = _build_teacher_resource_request(existing_obj, raw, teacher_login_id, month_key, now_iso)
            if created:
                updated.append(created)
            continue

        current = by_id[rid]
        if str(current.get('month') or '').strip() != str(month_key or '').strip():
            continue
        status = str(current.get('status') or '').strip().lower()
        if status not in {'pending_teacher', 'recommended', 'not_recommended', 'pending_admin'}:
            continue

        decision = str(raw.get('teacher_decision') or raw.get('decision') or '').strip().lower()
        remark = str(raw.get('teacher_remark') or raw.get('remark') or '').strip()
        if decision not in {'recommended', 'not_recommended'} and not remark:
            continue

        next_row = dict(current)
        if remark:
            next_row['teacher_remark'] = remark
        if decision in {'recommended', 'not_recommended'}:
            next_row['teacher_decision'] = decision
            if decision == 'recommended':
                next_row['status'] = 'pending_admin'
            else:
                next_row['status'] = 'not_recommended'
        next_row['teacher_login_id'] = teacher_login_id
        next_row['teacher_updated_at'] = now_iso
        next_row['updated_at'] = now_iso
        updated.append(next_row)

    return _merge_resource_requests_superset(existing_requests, updated)


def _find_student_id_by_roll(payload, roll_value):
    roll = _normalize_roll_value(roll_value)
    if not roll:
        return 0
    students = payload.get('students', []) if isinstance(payload, dict) else []
    if not isinstance(students, list):
        return 0
    for s in students:
        if not isinstance(s, dict):
            continue
        if _normalize_roll_value(s.get('roll')) == roll:
            return _parse_int_safe(s.get('id'), 0)
    return 0


def _student_resource_request_patch(existing_payload, actor_login_id, incoming_payload):
    """
    Build a safe patch from a student submission.
    Only allows creating a new resource request for the logged-in student.
    """
    current_month = _server_now_iso()[:7]
    student_id = _find_student_id_by_roll(existing_payload or {}, actor_login_id)
    if student_id <= 0:
        return None, "Student roll not found on server roster"

    incoming_requests = []
    if isinstance(incoming_payload, dict) and isinstance(incoming_payload.get('resource_requests'), list):
        incoming_requests = incoming_payload.get('resource_requests') or []
    if not incoming_requests:
        return None, "No resource request provided"

    raw = incoming_requests[0] if isinstance(incoming_requests[0], dict) else None
    if not raw:
        return None, "Invalid resource request"

    now_iso = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    rid = _parse_int_safe(raw.get('id'), 0)
    if rid <= 0:
        rid = int(datetime.now().timestamp() * 1000)

    req_type = str(raw.get('type') or '').strip().lower()
    if req_type not in {'redeem_points', 'cash_purchase'}:
        return None, "Invalid request type"

    item_id = _parse_int_safe(raw.get('item_id') or raw.get('itemId'), 0)
    qty = max(1, _parse_int_safe(raw.get('qty') or raw.get('quantity'), 0))
    if item_id <= 0:
        return None, "Item not selected"

    # Validate item exists.
    cabinet = (existing_payload or {}).get('resource_cabinet', []) or []
    if not isinstance(cabinet, list):
        cabinet = []
    item = next((it for it in cabinet if isinstance(it, dict) and _parse_int_safe(it.get('id'), 0) == item_id), None)
    if not item:
        return None, "Item not found in cabinet"

    price = float(item.get('price_per_unit') or 0)
    total_cost = max(0.0, price * float(qty))

    cash_paid = 0.0
    if req_type == 'cash_purchase':
        try:
            cash_paid = float(raw.get('cash_paid') or raw.get('paid_amount') or 0)
        except Exception:
            cash_paid = 0.0
        cash_paid = max(0.0, cash_paid)

    request_row = {
        'id': rid,
        'type': req_type,
        'studentId': student_id,
        'student_roll': _normalize_roll_value(actor_login_id),
        'month': current_month,
        'item_id': item_id,
        'item_name': str(item.get('name') or '').strip(),
        'unit': str(item.get('unit') or '').strip(),
        'qty': qty,
        'price_per_unit': price,
        'total_cost': total_cost,
        'cash_paid': cash_paid,
        'urgent': False,
        'status': 'pending_teacher',
        'created_at': now_iso,
        'updated_at': now_iso
    }
    return {'resource_requests': [request_row]}, ""


def _student_profile_change_appeal_patch(existing_payload, actor_login_id, incoming_payload):
    """
    Build a safe patch from a student submission for profile-change requests.
    Students can only create a new appeal of type=profile_change for themselves (append-only).
    """
    student_id = _find_student_id_by_roll(existing_payload or {}, actor_login_id)
    if student_id <= 0:
        return None, "Student roll not found on server roster"

    incoming_appeals = []
    if isinstance(incoming_payload, dict) and isinstance(incoming_payload.get('appeals'), list):
        incoming_appeals = incoming_payload.get('appeals') or []
    if not incoming_appeals:
        return None, "No appeal provided"

    raw = incoming_appeals[0] if isinstance(incoming_appeals[0], dict) else None
    if not raw:
        return None, "Invalid appeal"

    appeal_type = str(raw.get('type') or '').strip().lower()
    if appeal_type != 'profile_change':
        return None, "Invalid appeal type"

    existing_ids = set()
    for item in (existing_payload or {}).get('appeals', []) or []:
        if not isinstance(item, dict):
            continue
        aid = item.get('id')
        if aid is None:
            continue
        existing_ids.add(str(aid).strip())

    now_iso = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    aid = _parse_int_safe(raw.get('id'), 0)
    if aid <= 0:
        aid = int(datetime.now().timestamp() * 1000)
    if str(aid).strip() in existing_ids:
        return None, "Duplicate appeal id"

    requested_name = str(raw.get('requested_name') or raw.get('requestedName') or '').strip()
    requested_profile = raw.get('requested_profile_data') if isinstance(raw.get('requested_profile_data'), dict) else {}
    allowed_keys = {
        'fatherName', 'motherName', 'dateOfBirth', 'bloodGroup', 'aadhar',
        'phone', 'email', 'parentPhone', 'admissionDate', 'academicYear', 'address'
    }
    sanitized_profile = {k: requested_profile.get(k) for k in requested_profile.keys() if k in allowed_keys}
    if not requested_name and not sanitized_profile:
        return None, "No profile changes provided"

    # Resolve canonical student roll + name from the server roster.
    roll_norm = _normalize_roll_value(actor_login_id)
    student_name = ''
    for s in (existing_payload or {}).get('students', []) or []:
        if not isinstance(s, dict):
            continue
        if _parse_int_safe(s.get('id'), 0) == student_id:
            student_name = str(s.get('base_name') or s.get('name') or '').strip()
            break

    appeal_row = {
        'id': aid,
        'type': 'profile_change',
        'subject': 'Profile Change Request',
        'message': f"Student requested profile update for {student_name or roll_norm}.",
        'from_role': 'student',
        'created_by': roll_norm,
        'target_role': 'admin',
        'forwarded_to': 'admin',
        'status': 'pending_admin',
        'recommendation': '',
        'student_id': student_id,
        'student_roll': roll_norm,
        'student_name': student_name,
        'requested_name': requested_name,
        'requested_profile_data': sanitized_profile,
        'created_at': now_iso,
        'updated_at': now_iso,
    }
    return {'appeals': [appeal_row]}, ""


def _extract_month_roster_rolls(payload, month_key):
    rolls = set()
    if not isinstance(payload, dict):
        return rolls
    month_students = payload.get('month_students', {}) or {}
    month_profiles = payload.get('month_roster_profiles', {}) or {}

    for value in month_students.get(month_key, []) or []:
        roll = _normalize_roll_value(value)
        if roll.startswith('EA'):
            rolls.add(roll)

    for profile in month_profiles.get(month_key, []) or []:
        if not isinstance(profile, dict):
            continue
        roll = _normalize_roll_value(profile.get('roll'))
        if roll.startswith('EA'):
            rolls.add(roll)

    return rolls


def _enforce_current_month_roster_integrity(incoming_data, existing_data):
    """
    Prevent stale client snapshots from shrinking current-month roster visibility.
    Keeps/repairs student entries for current roster rolls (e.g. Feb 2026 46-student roster).
    """
    if not isinstance(incoming_data, dict):
        return incoming_data

    current_month = _server_now_iso()[:7]
    month_key = current_month
    incoming_rolls = _extract_month_roster_rolls(incoming_data, month_key)
    existing_rolls = _extract_month_roster_rolls(existing_data or {}, month_key)

    if not incoming_rolls and '2026-02' != month_key:
        month_key = '2026-02'
        incoming_rolls = _extract_month_roster_rolls(incoming_data, month_key)
        existing_rolls = _extract_month_roster_rolls(existing_data or {}, month_key)

    roster_rolls = incoming_rolls or existing_rolls
    if not roster_rolls:
        return incoming_data

    incoming_students = list(incoming_data.get('students', []) or [])
    existing_students = list((existing_data or {}).get('students', []) or [])

    by_roll_incoming = {}
    for student in incoming_students:
        if not isinstance(student, dict):
            continue
        roll = _normalize_roll_value(student.get('roll'))
        if roll and roll not in by_roll_incoming:
            by_roll_incoming[roll] = student

    by_roll_existing = {}
    for student in existing_students:
        if not isinstance(student, dict):
            continue
        roll = _normalize_roll_value(student.get('roll'))
        if roll and roll not in by_roll_existing:
            by_roll_existing[roll] = student

    profile_by_roll = {}
    month_profiles = (incoming_data.get('month_roster_profiles', {}) or {}).get(month_key, []) or []
    for profile in month_profiles:
        if not isinstance(profile, dict):
            continue
        roll = _normalize_roll_value(profile.get('roll'))
        if roll:
            profile_by_roll[roll] = profile

    next_id = max([_parse_int_safe(student.get('id'), 0) for student in incoming_students if isinstance(student, dict)] + [0])

    # Ensure each roster roll has a student record in incoming payload.
    for roll in sorted(roster_rolls):
        target = by_roll_incoming.get(roll)
        if target is None and roll in by_roll_existing:
            source = dict(by_roll_existing[roll])
            incoming_students.append(source)
            by_roll_incoming[roll] = source
            target = source
        if target is None:
            next_id += 1
            profile = profile_by_roll.get(roll, {})
            name = str(profile.get('base_name') or profile.get('name') or roll).strip() or roll
            raw_name = str(profile.get('name') or name).strip() or name
            class_value = profile.get('class')
            target = {
                'id': next_id,
                'roll': roll,
                'name': name,
                'base_name': name,
                'raw_name': raw_name,
                'class': _parse_int_safe(class_value, None) if class_value not in (None, '') else None,
                'fees': 0,
                'vote_power': None,
                'stars': 0,
                'veto_count': 0,
                'active': True
            }
            incoming_students.append(target)
            by_roll_incoming[roll] = target

        # Do not force-active here: admins may intentionally deactivate duplicates.
        # We only guarantee the roster roll has a record (to prevent "missing students" issues).
        if 'active' not in target:
            target['active'] = True

        # Align display identity with month profile if available.
        profile = profile_by_roll.get(roll)
        if isinstance(profile, dict):
            base_name = str(profile.get('base_name') or profile.get('name') or '').strip()
            raw_name = str(profile.get('name') or '').strip()
            if base_name:
                target['base_name'] = base_name
                target['name'] = base_name
            if raw_name:
                target['raw_name'] = raw_name
            class_value = profile.get('class')
            if class_value not in (None, ''):
                target['class'] = _parse_int_safe(class_value, target.get('class'))

    incoming_data['students'] = incoming_students

    # Normalize month_students list for target month to canonical roll values.
    month_students = incoming_data.setdefault('month_students', {})
    month_students[month_key] = sorted(roster_rolls)

    return incoming_data

def _normalize_parties(parties):
    normalized = []
    for idx, party in enumerate(parties, start=1):
        code = str(party.get('code', '')).strip()
        if not code:
            continue
        try:
            power = int(party.get('power') or 0)
        except (TypeError, ValueError):
            power = 0
        party_id = party.get('id') or idx
        normalized.append({'id': int(party_id), 'code': code, 'power': power})
    return normalized


def _normalize_leadership(posts):
    normalized = []
    for idx, post in enumerate(posts, start=1):
        title = str(post.get('post', '')).strip()
        if not title:
            continue
        holder = str(post.get('holder', '')).strip()
        post_id = post.get('id') or idx
        normalized.append({'id': int(post_id), 'post': title, 'holder': holder})
    return normalized


def _load_politics_data():
    path = _politics_file_path()
    if not os.path.exists(path):
        return {
            'parties': DEFAULT_PARTIES.copy(),
            'leadership': DEFAULT_LEADERSHIP.copy()
        }
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['parties'] = _normalize_parties(data.get('parties', []))
        data['leadership'] = _normalize_leadership(data.get('leadership', []))
        return data
    except Exception:
        return {
            'parties': DEFAULT_PARTIES.copy(),
            'leadership': DEFAULT_LEADERSHIP.copy()
        }


def _save_politics_data(data):
    os.makedirs(current_app.instance_path, exist_ok=True)
    payload = {
        'parties': _normalize_parties(data.get('parties', [])),
        'leadership': _normalize_leadership(data.get('leadership', []))
    }
    with open(_politics_file_path(), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def _extract_party_and_leadership(ws):
    parties = []
    leadership = []

    party_row = None
    party_col = None
    power_col = None
    post_row = None
    post_col = None
    holder_col = None

    for row in ws.iter_rows(min_row=1, max_row=50):
        for cell in row:
            if isinstance(cell.value, str):
                label = cell.value.strip().lower()
                if label == 'party':
                    party_row = cell.row
                    party_col = cell.column
                if label == 'power':
                    power_col = cell.column
                if label == 'post':
                    post_row = cell.row
                    post_col = cell.column
                if label == 'post holders':
                    holder_col = cell.column

    if party_row and party_col and power_col:
        for r in range(party_row + 1, party_row + 20):
            code = ws.cell(r, party_col).value
            power = ws.cell(r, power_col).value
            if not code:
                continue
            if str(code).strip().upper() == 'TOTAL':
                continue
            if isinstance(power, (int, float)):
                parties.append({'code': str(code).strip(), 'power': int(power)})

    if post_row and post_col and holder_col:
        for r in range(post_row + 1, post_row + 30):
            post = ws.cell(r, post_col).value
            holder = ws.cell(r, holder_col).value
            if post:
                leadership.append({'post': str(post).strip(), 'holder': str(holder).strip() if holder else ''})

    return parties, leadership


FEB26_SEED = json.loads(r'''
{
  "students": [
    { "id": 1, "roll": "EA24A01", "name": "Ayush Gupta** (CR) (Vv)", "class": 4, "fees": 500, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 2, "roll": "EA24A03", "name": "Ayat Parveen", "class": 4, "fees": 800, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 3, "roll": "EA24A04", "name": "Tanu Sinha**", "class": 4, "fees": 600, "total_score": 60, "rank": 20, "vote_power": 4 },
    { "id": 4, "roll": "EA24A05", "name": "Rashi (v)", "class": 3, "fees": 500, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 5, "roll": "EA25A07", "name": "Vishes Xalxo***(v)", "class": 3, "fees": 500, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 6, "roll": "EA25A13", "name": "Afreen Khatun", "class": 3, "fees": 600, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 7, "roll": "EA25A15", "name": "Ansh Kumar Singh", "class": 2, "fees": 0, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 8, "roll": "EA24B01", "name": "Pari Gupta****** (v)", "class": 6, "fees": 0, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 9, "roll": "EA24B03", "name": "Deep Das*", "class": 6, "fees": 1000, "total_score": 97, "rank": 12, "vote_power": 6 },
    { "id": 10, "roll": "EA24B09", "name": "Abdul Arman**** (ECS) (PP)", "class": 5, "fees": 1000, "total_score": 79, "rank": 16, "vote_power": 5 },
    { "id": 11, "roll": "EA25B05", "name": "Rajveer Thakur", "class": 6, "fees": 800, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 12, "roll": "EA25B06", "name": "Jay Arya***", "class": 5, "fees": 800, "total_score": 139, "rank": 6, "vote_power": 8 },
    { "id": 13, "roll": "EA25B10", "name": "Shiva Mallick (v)", "class": 5, "fees": 1000, "total_score": 160, "rank": 3, "vote_power": 9 },
    { "id": 14, "roll": "EA25B13", "name": "Rehmetun Khatun (ECJ)", "class": 6, "fees": 1200, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 15, "roll": "EA25B14", "name": "Prem Oraon*****", "class": 6, "fees": 800, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 16, "roll": "EA24C02", "name": "Sahil Yadav****************** (vvv)", "class": 8, "fees": 0, "total_score": 94, "rank": 13, "vote_power": 6 },
    { "id": 17, "roll": "EA24C03", "name": "Abhik Mallik", "class": 8, "fees": 1000, "total_score": 41, "rank": 25, "vote_power": 3 },
    { "id": 18, "roll": "EA24C06", "name": "Sakshi*** (v) (CCAI)", "class": 8, "fees": 1500, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 19, "roll": "EA25C07", "name": "Khushi Paswan** (v)", "class": 8, "fees": 500, "total_score": 72, "rank": 17, "vote_power": 4 },
    { "id": 20, "roll": "EA25C09", "name": "Shomiya Xalxo*** (WCI) (PP)", "class": 7, "fees": 1000, "total_score": 182, "rank": 2, "vote_power": 10 },
    { "id": 21, "roll": "EA25C10", "name": "Adarsh Arya*", "class": 8, "fees": 1200, "total_score": 1, "rank": 27, "vote_power": 1 },
    { "id": 22, "roll": "EA25C11", "name": "Sourav Das*", "class": 8, "fees": 1200, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 23, "roll": "EA25C12", "name": "Shubham Singha (PP)", "class": 8, "fees": 1200, "total_score": 47, "rank": 22, "vote_power": 3 },
    { "id": 24, "roll": "EA25C15", "name": "Nirupam Vaid*", "class": 8, "fees": 1500, "total_score": 35, "rank": 26, "vote_power": 2 },
    { "id": 25, "roll": "EA25C17", "name": "Alen Ghartimagar", "class": 8, "fees": 1500, "total_score": 63, "rank": 19, "vote_power": 4 },
    { "id": 26, "roll": "EA25C18", "name": "N Riya Kumari", "class": 8, "fees": 1500, "total_score": 118, "rank": 9, "vote_power": 7 },
    { "id": 27, "roll": "EA25C19", "name": "Samarth Patel*(CITC)", "class": 8, "fees": 1500, "total_score": 153, "rank": 5, "vote_power": 9 },
    { "id": 28, "roll": "EA25C20", "name": "Rishi Trivedi", "class": 8, "fees": 1500, "total_score": 90, "rank": 15, "vote_power": 5 },
    { "id": 29, "roll": "EA25C21", "name": "Sristi Kumari", "class": 7, "fees": 1500, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 30, "roll": "EA25C22", "name": "Piyush Rajak", "class": 8, "fees": 1000, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 31, "roll": "EA25C23", "name": "Abhinav Khati (CR) (PP)", "class": 7, "fees": 1200, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 32, "roll": "EA26C24", "name": "Rishabh Kumar Singh", "class": 7, "fees": 0, "total_score": 42, "rank": 24, "vote_power": 3 },
    { "id": 33, "roll": "EA24D01", "name": "Jay Kumar Yadav*** (CR) (V)", "class": 10, "fees": 0, "total_score": 187, "rank": 1, "vote_power": 10 },
    { "id": 34, "roll": "EA24D06", "name": "Tanmay Biswas*", "class": 10, "fees": 2000, "total_score": 102, "rank": 11, "vote_power": 6 },
    { "id": 35, "roll": "EA24D08", "name": "Sanjana Sutradhar (PP)", "class": 9, "fees": 1500, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 36, "roll": "EA25D12", "name": "Roshan Paswan** (PP)", "class": 10, "fees": 2000, "total_score": 158, "rank": 4, "vote_power": 9 },
    { "id": 37, "roll": "EA25D13", "name": "Aamna Khatoon*", "class": 10, "fees": 1500, "total_score": 105, "rank": 10, "vote_power": 6 },
    { "id": 38, "roll": "EA24D15", "name": "Reeyansh Lama (VVvvv) (CoL) (SC)", "class": 9, "fees": 1500, "total_score": 122, "rank": 7, "vote_power": 7 },
    { "id": 39, "roll": "EA25D17", "name": "Aditya Singh***", "class": 10, "fees": 2000, "total_score": 57, "rank": 21, "vote_power": 4 },
    { "id": 40, "roll": "EA25D20", "name": "Harsh Mallik****** (VVV) (L)", "class": 9, "fees": 1500, "total_score": 43, "rank": 23, "vote_power": 3 },
    { "id": 41, "roll": "EA25D21", "name": "Xavier Herenj***", "class": 9, "fees": 2000, "total_score": -30, "rank": 46, "vote_power": -1 },
    { "id": 42, "roll": "EA25D22", "name": "Mahek Mahato*******", "class": 9, "fees": 2000, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 43, "roll": "EA25D24", "name": "Aansh Mandal****** (DWI)", "class": 10, "fees": 2000, "total_score": 122, "rank": 7, "vote_power": 7 },
    { "id": 44, "roll": "EA24D25", "name": "Nandani Gupta** (v)", "class": 9, "fees": 0, "total_score": 0, "rank": 28, "vote_power": 1 },
    { "id": 45, "roll": "EA25D26", "name": "Shankar Pradhan (CI)", "class": 9, "fees": 2000, "total_score": 92, "rank": 14, "vote_power": 5 },
    { "id": 46, "roll": "EA26D28", "name": "Riya Singh (RM)", "class": 9, "fees": 2000, "total_score": 70, "rank": 18, "vote_power": 4 }
  ],
  "scores": [
    { "id": 1, "studentId": 3, "date": "2026-02-01", "points": 60, "month": "2026-02", "notes": "" },
    { "id": 2, "studentId": 9, "date": "2026-02-01", "points": 97, "month": "2026-02", "notes": "" },
    { "id": 3, "studentId": 10, "date": "2026-02-01", "points": 79, "month": "2026-02", "notes": "" },
    { "id": 4, "studentId": 12, "date": "2026-02-01", "points": 79, "month": "2026-02", "notes": "" },
    { "id": 5, "studentId": 12, "date": "2026-02-02", "points": 60, "month": "2026-02", "notes": "" },
    { "id": 6, "studentId": 13, "date": "2026-02-01", "points": 60, "month": "2026-02", "notes": "" },
    { "id": 7, "studentId": 13, "date": "2026-02-03", "points": 100, "month": "2026-02", "notes": "" },
    { "id": 8, "studentId": 16, "date": "2026-02-01", "points": 94, "month": "2026-02", "notes": "" },
    { "id": 9, "studentId": 17, "date": "2026-02-01", "points": 41, "month": "2026-02", "notes": "" },
    { "id": 10, "studentId": 19, "date": "2026-02-01", "points": 72, "month": "2026-02", "notes": "" },
    { "id": 11, "studentId": 20, "date": "2026-02-01", "points": 182, "month": "2026-02", "notes": "" },
    { "id": 12, "studentId": 21, "date": "2026-02-01", "points": -99, "month": "2026-02", "notes": "" },
    { "id": 13, "studentId": 21, "date": "2026-02-03", "points": 100, "month": "2026-02", "notes": "" },
    { "id": 14, "studentId": 22, "date": "2026-02-01", "points": 0, "month": "2026-02", "notes": "" },
    { "id": 15, "studentId": 23, "date": "2026-02-01", "points": 47, "month": "2026-02", "notes": "" },
    { "id": 16, "studentId": 24, "date": "2026-02-01", "points": 35, "month": "2026-02", "notes": "" },
    { "id": 17, "studentId": 25, "date": "2026-02-01", "points": 63, "month": "2026-02", "notes": "" },
    { "id": 18, "studentId": 26, "date": "2026-02-01", "points": 118, "month": "2026-02", "notes": "" },
    { "id": 19, "studentId": 27, "date": "2026-02-01", "points": 153, "month": "2026-02", "notes": "" },
    { "id": 20, "studentId": 28, "date": "2026-02-01", "points": 90, "month": "2026-02", "notes": "" },
    { "id": 21, "studentId": 32, "date": "2026-02-01", "points": 42, "month": "2026-02", "notes": "" },
    { "id": 22, "studentId": 33, "date": "2026-02-01", "points": 187, "month": "2026-02", "notes": "" },
    { "id": 23, "studentId": 34, "date": "2026-02-01", "points": 102, "month": "2026-02", "notes": "" },
    { "id": 24, "studentId": 36, "date": "2026-02-01", "points": 158, "month": "2026-02", "notes": "" },
    { "id": 25, "studentId": 37, "date": "2026-02-01", "points": 105, "month": "2026-02", "notes": "" },
    { "id": 26, "studentId": 38, "date": "2026-02-01", "points": 122, "month": "2026-02", "notes": "" },
    { "id": 27, "studentId": 39, "date": "2026-02-01", "points": 57, "month": "2026-02", "notes": "" },
    { "id": 28, "studentId": 40, "date": "2026-02-01", "points": 43, "month": "2026-02", "notes": "" },
    { "id": 29, "studentId": 41, "date": "2026-02-01", "points": -30, "month": "2026-02", "notes": "" },
    { "id": 30, "studentId": 43, "date": "2026-02-01", "points": 122, "month": "2026-02", "notes": "" },
    { "id": 31, "studentId": 45, "date": "2026-02-01", "points": 127, "month": "2026-02", "notes": "" },
    { "id": 32, "studentId": 45, "date": "2026-02-02", "points": -35, "month": "2026-02", "notes": "" },
    { "id": 33, "studentId": 46, "date": "2026-02-01", "points": 70, "month": "2026-02", "notes": "" }
  ],
  "parties": [
    { "code": "MAP", "power": 15 },
    { "code": "BWP", "power": 27 },
    { "code": "ESP", "power": 30 },
    { "code": "MRP", "power": 23 },
    { "code": "SSP", "power": 57 },
    { "code": "NJP", "power": 15 }
  ],
  "leadership": [
    { "post": "LEADER (L)", "holder": "HARSH MALLICK" },
    { "post": "LEADER OF OPPOSITION (LoP)", "holder": "" },
    { "post": "CO-LEADER (CoL)", "holder": "REEYANSH LAMA" },
    { "post": "CODING & IT CAPTAIN (CITC)", "holder": "SAMARTH PATEL" },
    { "post": "DISCIPLINE & WELFARE IN-CHARGE (DWI)", "holder": "AANSH MANDAL" },
    { "post": "RESOURCE MANAGER (RM)", "holder": "RIYA SINGH" },
    { "post": "SPORTS CAPTAIN (SC)", "holder": "REEYANSH LAMA" },
    { "post": "ENGLISH CAPTAIN- SENIOR (ECS)", "holder": "ABDUL ARMAN" },
    { "post": "CULTURE & CREATIVE ARTS IN-CHARGE (CCAI)", "holder": "SAKSHI" },
    { "post": "CLEANLINESS IN-CHARGE (CI)", "holder": "SHANKAR PRADHAN" },
    { "post": "ENGLISH CAPTAIN- JUNIOR (ECJ)", "holder": "REHMATUN KHATUN" },
    { "post": "WELCOME & COMMUNICATION IN-CHARGE (WCI)", "holder": "SHOMIYA XALXO" },
    { "post": "LEADER", "holder": "" },
    { "post": "LEADER OF OPPOSITION", "holder": "" }
  ]
}
''')

# ============== ROUTES ==============

@points_bp.route('/offline')
def offline_scoreboard():
    """Serve offline scoreboard HTML"""
    return send_file('static/offline_scoreboard.html')


@points_bp.route('/seed-data', methods=['GET'])
def seed_data():
    """Provide seed data lazily so the main HTML stays lightweight."""
    payload = FEB26_SEED
    response = jsonify(payload)
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response


def _is_valid_replication_request():
    """
    Validate peer replication requests with secure key comparison.

    Security improvements:
    - Requires SYNC_SHARED_KEY to be set (minimum 16 chars recommended)
    - Uses HMAC comparison to prevent timing attacks
    - Validates required headers are present
    """
    import hmac

    if request.headers.get('X-EA-Replicated') != '1':
        return False

    expected_key = os.getenv('SYNC_SHARED_KEY', '').strip()
    provided_key = request.headers.get('X-EA-Sync-Key', '').strip()

    # Security: Fail if sync key not configured (prevent unauthorized sync)
    if not expected_key:
        current_app.logger.warning("SYNC_SHARED_KEY not configured - rejecting replication request")
        return False

    # Security: Require minimum key length
    if len(expected_key) < 16:
        current_app.logger.error("SYNC_SHARED_KEY too short (minimum 16 characters required)")
        return False

    # Security: Use HMAC comparison to prevent timing attacks
    return hmac.compare_digest(expected_key, provided_key)


@points_bp.route('/offline-data', methods=['GET', 'POST'])
@csrf.exempt  # Required for peer-to-peer sync, but secured with sync key validation
@limiter.limit("2000 per hour")  # LAN mode: allow frequent sync while preventing runaway abuse
def offline_data():
    replicated_auth = _is_valid_replication_request()
    is_replicated = request.headers.get('X-EA-Replicated') == '1'
    if request.method == 'POST' and not current_user.is_authenticated and not replicated_auth:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    if request.method == 'POST' and str(os.getenv('EA_RESTORE_LOCK', '')).strip() == '1':
        return jsonify({'success': False, 'error': 'Restore lock enabled'}), 423

    if request.method == 'GET':
        data = _load_offline_data()
        if not data:
            return ('', 204)
        min_students = _min_safe_student_roster()
        if _is_tiny_roster(data, min_students):
            data, src = _recover_tiny_roster_if_needed(data, min_students=min_students)
            if _is_tiny_roster(data, min_students):
                # Hard safety: never serve known-corrupt tiny rosters (prevents old clients from applying them).
                current_app.logger.error(
                    "Refusing to serve tiny roster snapshot (%s students). Recovery source=%s",
                    _student_count(data),
                    src or 'none',
                )
                resp = jsonify({'success': False, 'error': 'Roster snapshot incomplete. Recovery required.'})
                resp.headers['Cache-Control'] = 'no-store'
                return resp, 503
        data, _ = _recover_stale_snapshot_if_needed(data, min_students=min_students)
        if _ensure_score_timestamps(data):
            try:
                _save_offline_data(data)
            except Exception:
                current_app.logger.exception("Failed to persist score timestamp normalization on GET")
        updated_at = data.get('server_updated_at') or data.get('updated_at')
        since = request.args.get('since') if hasattr(request, 'args') else None
        if since and updated_at:
            server_stamp = _parse_sync_stamp(updated_at)
            since_stamp = _parse_sync_stamp(since)
            if server_stamp and since_stamp and server_stamp <= since_stamp:
                # Bandwidth optimization for WAN: if client is already at/above this server stamp,
                # avoid sending the full payload. SSE (offline-events) still provides realtime updates.
                return ('', 204)
        
        # DIAGNOSTIC FIX: Ensure attendance records are present in GET response
        attendance_records = data.get('attendance', [])
        if not attendance_records:
            current_app.logger.debug(f"GET /offline-data: No attendance records in snapshot (students: {len(data.get('students', []))}, scores: {len(data.get('scores', []))})")
        else:
            current_app.logger.debug(f"GET /offline-data: Returning {len(attendance_records)} attendance records")
        
        resp = jsonify({'data': data, 'updated_at': updated_at})
        resp.headers['Cache-Control'] = 'no-store'
        return resp

    payload = request.get_json(silent=True) or {}
    data = payload.get('data', payload)
    request_peers = payload.get('peers', []) if isinstance(payload, dict) else []
    if not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'Invalid payload'}), 400

    actor_login_id = current_user.login_id if current_user.is_authenticated else ''
    if current_user.is_authenticated:
        actor_role = current_user.role
    elif replicated_auth:
        declared_role = payload.get('actor_role') if isinstance(payload, dict) else ''
        if not declared_role and isinstance(data, dict):
            declared_role = data.get('actor_role', '')
        actor_role = str(declared_role or 'admin').strip().lower()
    else:
        actor_role = 'admin'

    actor_role = str(actor_role or 'admin').strip().lower()
    if actor_role not in ['admin', 'teacher', 'student']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    replica_purpose = ''
    if isinstance(payload, dict):
        replica_purpose = str(payload.get('replica_purpose') or '').strip().lower()
    if not replica_purpose and isinstance(data, dict):
        replica_purpose = str(data.get('replica_purpose') or '').strip().lower()

    # Master safety: In master mode, reject peer replication except for narrow teacher patches.
    if request.method == 'POST' and is_replicated and str(os.getenv('EA_MASTER_MODE', '')).strip() == '1':
        if not (actor_role == 'teacher' and replica_purpose == 'teacher_patch'):
            return jsonify({'success': False, 'error': 'Peer replication disabled on master mode'}), 409

    existing = _load_offline_data() or {}
    min_students = _min_safe_student_roster()
    if _is_tiny_roster(existing, min_students):
        existing, _ = _recover_tiny_roster_if_needed(existing, min_students=min_students)
    existing, _ = _recover_stale_snapshot_if_needed(existing, min_students=min_students)
    force_replace = bool(payload.get('force_replace')) if isinstance(payload, dict) else False
    incoming_count = _student_count(data)
    existing_count = _student_count(existing)
    if actor_role not in ['teacher', 'student'] and not force_replace and incoming_count > 0 and incoming_count < min_students:
        current_stamp = existing.get('server_updated_at') or existing.get('updated_at')
        return jsonify({
            'success': False,
            'error': f'Incoming roster snapshot too small ({incoming_count} students). Upload rejected.',
            'updated_at': current_stamp
        }), 409
    if actor_role not in ['teacher', 'student'] and not force_replace and _is_suspicious_student_shrink(existing, data):
        current_app.logger.warning(
            "Suspicious student shrink detected and rejected. "
            "Source: %s, Existing Count: %s, Incoming Count: %s, Existing Stamp: %s, Incoming Stamp: %s",
            request.remote_addr,
            _student_count(existing),
            _student_count(data),
            existing.get('server_updated_at') or existing.get('updated_at'),
            data.get('server_updated_at') or data.get('updated_at')
        )
        current_stamp = existing.get('server_updated_at') or existing.get('updated_at')
        return jsonify({
            'success': False,
            'error': 'Incoming snapshot would shrink student master data. Upload rejected.',
            'updated_at': current_stamp
        }), 409
    incoming_stamp = _payload_sync_stamp(data)
    existing_stamp = _payload_sync_stamp(existing)
    if actor_role == 'teacher':
        data = _filter_teacher_payload_to_current_month(data, actor_login_id or 'Teacher')
        merged = existing if existing else {}
        merged.setdefault('students', existing.get('students', []))
        merged.setdefault('month_students', existing.get('month_students', {}))
        merged.setdefault('month_roster_profiles', existing.get('month_roster_profiles', {}))
        merged.setdefault('parties', existing.get('parties', []))
        merged.setdefault('leadership', existing.get('leadership', []))
        merged.setdefault('class_reps', existing.get('class_reps', []))
        merged.setdefault('group_crs', existing.get('group_crs', []))
        merged.setdefault('election_candidates', existing.get('election_candidates', []))
        merged.setdefault('election_votes', existing.get('election_votes', []))
        merged.setdefault('election_individual_votes', existing.get('election_individual_votes', []))
        merged.setdefault('election_teacher_votes', existing.get('election_teacher_votes', []))
        merged.setdefault('pending_election_results', existing.get('pending_election_results', []))
        merged.setdefault('appeals', existing.get('appeals', []))
        merged.setdefault('attendance', existing.get('attendance', []))
        merged.setdefault('notification_history', existing.get('notification_history', []))
        merged.setdefault('resource_cabinet', existing.get('resource_cabinet', []))
        merged.setdefault('resource_requests', existing.get('resource_requests', []))
        merged.setdefault('resource_transactions', existing.get('resource_transactions', []))
        merged.setdefault('syllabus_catalog', existing.get('syllabus_catalog', {}))
        merged.setdefault('syllabus_tracking', existing.get('syllabus_tracking', []))
        merged['scores'] = _merge_teacher_scores(existing, data)
        if isinstance(data.get('appeals'), list):
            merged['appeals'] = _merge_appeals_superset(existing.get('appeals', []), data.get('appeals', []))
        if isinstance(data.get('attendance'), list):
            incoming_attendance_count = len(data.get('attendance', []))
            existing_attendance_count = len(existing.get('attendance', []))
            merged['attendance'] = _merge_attendance_superset(existing, data)
            merged_attendance_count = len(merged.get('attendance', []))
            current_app.logger.info(
                f"[TEACHER SYNC] Attendance merged | "
                f"incoming: {incoming_attendance_count}, existing: {existing_attendance_count}, result: {merged_attendance_count} | "
                f"teacher: {actor_login_id or 'Teacher'}"
            )
        if isinstance(data.get('election_teacher_votes'), list):
            merged['election_teacher_votes'] = _merge_election_votes_superset(
                existing.get('election_teacher_votes', []),
                data.get('election_teacher_votes', []),
                mode='teacher'
            )
        if isinstance(data.get('pending_election_results'), list):
            merged['pending_election_results'] = _merge_pending_results_superset(
                existing.get('pending_election_results', []),
                data.get('pending_election_results', [])
            )
        if isinstance(data.get('notification_history'), list):
            merged['notification_history'] = _merge_notification_history(
                existing.get('notification_history', []),
                data.get('notification_history', [])
            )
        if isinstance(data.get('resource_requests'), list):
            merged['resource_requests'] = _merge_resource_requests_teacher(
                existing,
                data.get('resource_requests', []),
                actor_login_id or 'Teacher',
                _server_now_iso()[:7]
            )
        if isinstance(data.get('syllabus_tracking'), list):
            merged['syllabus_tracking'] = merge_syllabus_tracking_superset(
                existing.get('syllabus_tracking', []),
                data.get('syllabus_tracking', []),
                _parse_int_safe,
                _parse_sync_stamp
            )
        # Teachers cannot directly modify post-holder source tables.
        # They must submit approval requests that Admin applies.
        if isinstance(data.get('pending_cr_requests'), list):
            merged['pending_cr_requests'] = _merge_pending_cr_requests_teacher(
                existing.get('pending_cr_requests', []),
                data.get('pending_cr_requests', []),
                actor_login_id or 'Teacher'
            )
        merged = _enforce_current_month_roster_integrity(merged, existing)
        _reconcile_role_veto_monthly(merged)
        _reconcile_veto_counters_from_scores(merged)
        _ensure_score_timestamps(merged)
        merged['updated_at'] = data.get('updated_at', existing.get('updated_at'))
        merged['server_updated_at'] = _server_now_iso()
        _save_offline_data(merged)
        _broadcast_sync_event(merged['server_updated_at'], source='teacher')
        if not is_replicated:
            if str(os.getenv('EA_MASTER_MODE', '')).strip() == '1':
                _forward_offline_data_to_peers_async(merged, request_peers)
            else:
                patch = _build_teacher_replication_patch(merged, actor_login_id or 'Teacher')
                _forward_offline_data_to_peers_async(patch, request_peers)
        return jsonify({'success': True, 'updated_at': merged['server_updated_at']})

    if actor_role == 'student':
        # Students can only:
        # - create resource requests for themselves (append-only, server builds canonical row)
        # - submit profile-change requests to admin via appeals (append-only, sanitized)
        patch = {}
        if isinstance(data, dict) and isinstance(data.get('resource_requests'), list) and data.get('resource_requests'):
            req_patch, err = _student_resource_request_patch(existing, actor_login_id, data)
            if not req_patch:
                return jsonify({'success': False, 'error': err or 'Invalid student request'}), 400
            patch.update(req_patch)
        if isinstance(data, dict) and isinstance(data.get('appeals'), list) and data.get('appeals'):
            appeal_patch, err = _student_profile_change_appeal_patch(existing, actor_login_id, data)
            if not appeal_patch:
                return jsonify({'success': False, 'error': err or 'Invalid student appeal'}), 400
            patch.update(appeal_patch)
        if not patch:
            return jsonify({'success': False, 'error': 'No valid student update provided'}), 400
        existing_obj = existing if isinstance(existing, dict) else {}
        merged = existing_obj
        merged.setdefault('resource_cabinet', existing_obj.get('resource_cabinet', []))
        merged.setdefault('resource_requests', existing_obj.get('resource_requests', []))
        merged.setdefault('resource_transactions', existing_obj.get('resource_transactions', []))
        merged.setdefault('appeals', existing_obj.get('appeals', []))
        if isinstance(patch.get('resource_requests'), list):
            merged['resource_requests'] = _merge_resource_requests_superset(
                merged.get('resource_requests', []),
                patch.get('resource_requests', [])
            )
        if isinstance(patch.get('appeals'), list):
            merged['appeals'] = _merge_appeals_superset(existing_obj.get('appeals', []), patch.get('appeals', []))
        _ensure_score_timestamps(merged)
        merged['server_updated_at'] = _server_now_iso()
        _save_offline_data(merged)
        _broadcast_sync_event(merged['server_updated_at'], source='student')
        if not is_replicated:
            _forward_offline_data_to_peers_async(merged, request_peers)
        return jsonify({'success': True, 'updated_at': merged['server_updated_at']})

    if existing and incoming_stamp and existing_stamp and incoming_stamp < existing_stamp:
        # If the server is in a known corrupt state (tiny roster), accept a healthy snapshot even if its stamp is older.
        if _is_tiny_roster(existing, min_students) and incoming_count >= min_students:
            current_app.logger.warning(
                "Accepting healthy snapshot (%s students) over tiny-roster data (%s students) despite older stamp.",
                incoming_count,
                existing_count
            )
        else:
            current_stamp = existing.get('server_updated_at') or existing.get('updated_at')
            return jsonify({
                'success': False,
                'error': 'Server has newer data',
                'updated_at': current_stamp
            }), 409

    # Patch-safety: if a client sends a partial payload (e.g. only fee/resource updates),
    # ensure we don't accidentally overwrite core tables like students/month roster.
    if isinstance(existing, dict):
        if 'students' not in data:
            data['students'] = existing.get('students', [])
        elif isinstance(data.get('students'), list) and isinstance(existing.get('students'), list):
            # Merge students: never downgrade active status without a genuinely newer timestamp.
            data['students'] = _merge_students_preserve_active(
                existing.get('students', []),
                data.get('students', [])
            )
        # Always superset-merge month rosters so a partial client payload never shrinks the server roster.
        data['month_students'] = _merge_month_students_superset(
            existing.get('month_students', {}),
            data.get('month_students', {})
        )
        data['month_roster_profiles'] = _merge_month_roster_profiles_superset(
            existing.get('month_roster_profiles', {}),
            data.get('month_roster_profiles', {})
        )
        # Guard against accidental UI/import payloads that clear office-holder tables.
        # Preserve existing non-empty structures unless caller explicitly uses force_replace.
        if not force_replace:
            protected_list_tables = [
                'leadership',
                'group_crs',
                'class_reps',
                'parties',
                'post_holder_history',
                'syllabus_tracking'
            ]
            for key in protected_list_tables:
                incoming = data.get(key)
                existing_val = existing.get(key)
                if isinstance(existing_val, list) and existing_val and (not isinstance(incoming, list) or len(incoming) == 0):
                    data[key] = existing_val
            protected_object_tables = [
                'syllabus_catalog'
            ]
            for key in protected_object_tables:
                incoming = data.get(key)
                existing_val = existing.get(key)
                if isinstance(existing_val, dict) and existing_val and (not isinstance(incoming, dict) or len(incoming.keys()) == 0):
                    data[key] = existing_val

    if isinstance(existing, dict):
        data['scores'] = _merge_scores_superset(existing.get('scores', []), data.get('scores', []))
        data['attendance'] = _merge_attendance_superset(existing, data)
        data['appeals'] = _merge_appeals_superset(existing.get('appeals', []), data.get('appeals', []))
        data['election_votes'] = _merge_election_votes_superset(
            existing.get('election_votes', []),
            data.get('election_votes', []),
            mode='party'
        )
        data['election_individual_votes'] = _merge_election_votes_superset(
            existing.get('election_individual_votes', []),
            data.get('election_individual_votes', []),
            mode='individual'
        )
        data['election_teacher_votes'] = _merge_election_votes_superset(
            existing.get('election_teacher_votes', []),
            data.get('election_teacher_votes', []),
            mode='teacher'
        )
        data['pending_election_results'] = _merge_pending_results_superset(
            existing.get('pending_election_results', []),
            data.get('pending_election_results', [])
        )
        data['fee_records'] = _merge_fee_records_superset(
            existing.get('fee_records', []),
            data.get('fee_records', [])
        )
        data['resource_cabinet'] = _merge_resource_cabinet_superset(
            existing.get('resource_cabinet', []),
            data.get('resource_cabinet', [])
        )
        data['resource_requests'] = _merge_resource_requests_superset(
            existing.get('resource_requests', []),
            data.get('resource_requests', [])
        )
        data['resource_transactions'] = _merge_resource_transactions_superset(
            existing.get('resource_transactions', []),
            data.get('resource_transactions', [])
        )
        data['resource_advantage_deductions'] = _merge_resource_advantage_deductions_superset(
            existing.get('resource_advantage_deductions', []),
            data.get('resource_advantage_deductions', [])
        )
        data['notification_history'] = _merge_notification_history(
            existing.get('notification_history', []),
            data.get('notification_history', [])
        )
        data['leadership'] = _merge_leadership_superset(
            existing.get('leadership', []),
            data.get('leadership', [])
        )
        data['group_crs'] = _merge_group_crs_superset(
            existing.get('group_crs', []),
            data.get('group_crs', [])
        )
        data['class_reps'] = _merge_class_reps_superset(
            existing.get('class_reps', []),
            data.get('class_reps', [])
        )
        data['parties'] = _merge_parties_superset(
            existing.get('parties', []),
            data.get('parties', [])
        )
        data['pending_cr_requests'] = _merge_pending_cr_requests_superset(
            existing.get('pending_cr_requests', []),
            data.get('pending_cr_requests', [])
        )
        data['syllabus_catalog'] = merge_syllabus_catalog_superset(
            existing.get('syllabus_catalog', {}),
            data.get('syllabus_catalog', {}),
            _parse_int_safe
        )
        data['syllabus_tracking'] = merge_syllabus_tracking_superset(
            existing.get('syllabus_tracking', []),
            data.get('syllabus_tracking', []),
            _parse_int_safe,
            _parse_sync_stamp
        )

    data = _enforce_current_month_roster_integrity(data, existing)
    _reconcile_role_veto_monthly(data)
    _reconcile_veto_counters_from_scores(data)
    _ensure_score_timestamps(data)
    data['server_updated_at'] = _server_now_iso()
    _save_offline_data(data)
    _broadcast_sync_event(data['server_updated_at'], source='replica' if is_replicated else 'client')
    if not is_replicated:
        _forward_offline_data_to_peers_async(data, request_peers)
    return jsonify({'success': True, 'updated_at': data['server_updated_at']})


@points_bp.route('/offline-events')
@login_required
def offline_events():
    subscriber = _subscribe_sync_events()

    def generate():
        try:
            yield 'retry: 2500\n\n'
            existing = _load_offline_data() or {}
            stamp = existing.get('server_updated_at') or existing.get('updated_at') or ''
            yield f"event: sync\ndata: {json.dumps({'updated_at': stamp, 'source': 'init'})}\n\n"
            while True:
                try:
                    payload = subscriber.get(timeout=20)
                    yield f"event: sync\ndata: {payload}\n\n"
                except Empty:
                    yield ': keepalive\n\n'
        finally:
            _unsubscribe_sync_events(subscriber)

    headers = {
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    }
    return Response(stream_with_context(generate()), mimetype='text/event-stream', headers=headers)


@points_bp.route('/offline-server-health', methods=['POST'])
@login_required
def offline_server_health():
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    payload = request.get_json(silent=True) or {}
    requested_urls = payload.get('urls', []) if isinstance(payload, dict) else []
    urls = _normalize_peer_list(requested_urls)
    if not urls:
        urls = _get_sync_peers()
    current_base = (request.host_url or '').rstrip('/')
    if current_base and current_base not in urls:
        urls.insert(0, current_base)
    urls = list(dict.fromkeys(urls))

    items = []
    for base in urls:
        endpoint = f"{base}/scoreboard/offline-data"
        status = 'offline'
        error = ''
        data_stamp = ''
        students = None
        scores = None
        try:
            req = urllib.request.Request(endpoint, method='GET')
            with urllib.request.urlopen(req, timeout=4) as resp:
                raw = resp.read()
                parsed = json.loads(raw.decode('utf-8'))
                payload_data = parsed.get('data', {}) if isinstance(parsed, dict) else {}
                status = 'online'
                data_stamp = parsed.get('updated_at') or payload_data.get('server_updated_at') or payload_data.get('updated_at') or ''
                if isinstance(payload_data, dict):
                    if isinstance(payload_data.get('students'), list):
                        students = len(payload_data.get('students'))
                    if isinstance(payload_data.get('scores'), list):
                        scores = len(payload_data.get('scores'))
                if not data_stamp:
                    status = 'degraded'
                    error = 'No data stamp'
        except Exception as exc:
            status = 'offline'
            error = str(exc)

        items.append({
            'base_url': base,
            'status': status,
            'data_stamp': data_stamp,
            'students': students,
            'scores': scores,
            'error': error
        })

    return jsonify({'success': True, 'items': items, 'checked_at': _server_now_iso()})


@points_bp.route('/offline-backup', methods=['GET'])
@login_required
def offline_backup():
    data = _load_offline_data()
    if not data:
        return jsonify({'success': False, 'error': 'No data to backup'}), 404

    fd, temp_path = tempfile.mkstemp(prefix='offline_backup_', suffix='.json')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    @after_this_request
    def _cleanup(response):
        try:
            os.remove(temp_path)
        except Exception:
            pass
        return response

    filename = f'offline_scoreboard_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return send_file(temp_path, as_attachment=True, download_name=filename)


@points_bp.route('/offline-restore-points', methods=['GET'])
@login_required
def offline_restore_points():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    candidates = []
    roots = [
        ('live', _offline_data_path()),
        ('rolling', _offline_backup_dir()),
        ('hourly', _offline_hourly_backup_dir()),
        ('startup', _offline_startup_restore_dir()),
        ('instance', current_app.instance_path)
    ]

    seen = set()
    for source, root in roots:
        if source == 'live':
            path = root
            if os.path.isfile(path):
                rel = os.path.relpath(path, current_app.instance_path)
                key = rel.replace('\\', '/')
                if key not in seen:
                    seen.add(key)
                    candidates.append((source, path, key))
            continue
        if not os.path.isdir(root):
            continue
        for name in os.listdir(root):
            if not name.endswith('.json'):
                continue
            if source == 'instance' and not name.startswith('offline_scoreboard_data'):
                continue
            path = os.path.join(root, name)
            if not os.path.isfile(path):
                continue
            rel = os.path.relpath(path, current_app.instance_path)
            key = rel.replace('\\', '/')
            if key in seen:
                continue
            seen.add(key)
            candidates.append((source, path, key))

    meta = _load_restore_points_meta()
    items = []
    for source, path, key in candidates:
        try:
            stat = os.stat(path)
            key_meta = meta.get(key, {}) if isinstance(meta.get(key), dict) else {}
            items.append({
                'id': key,
                'source': source,
                'name': os.path.basename(path),
                'path': key,
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'size': stat.st_size,
                'locked': bool(key_meta.get('locked')),
                'label': str(key_meta.get('label') or '').strip()
            })
        except Exception:
            continue

    items.sort(key=lambda item: item.get('modified_at', ''), reverse=True)
    return jsonify({'success': True, 'items': items})


@points_bp.route('/offline-restore-point-lock', methods=['POST'])
@login_required
def offline_restore_point_lock():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    payload = request.get_json(silent=True) or {}
    restore_id = str(payload.get('id') or '').strip().replace('\\', '/')
    if not restore_id or '..' in restore_id:
        return jsonify({'success': False, 'error': 'Invalid restore id'}), 400
    lock_state = bool(payload.get('locked'))
    label = str(payload.get('label') or '').strip()
    source_path = os.path.normpath(os.path.join(current_app.instance_path, restore_id))
    if not source_path.startswith(os.path.normpath(current_app.instance_path)):
        return jsonify({'success': False, 'error': 'Invalid restore path'}), 400
    if not os.path.isfile(source_path):
        return jsonify({'success': False, 'error': 'Restore file not found'}), 404

    meta = _load_restore_points_meta()
    entry = meta.get(restore_id, {}) if isinstance(meta.get(restore_id), dict) else {}
    entry['locked'] = lock_state
    entry['label'] = label[:80]
    entry['updated_at'] = _server_now_iso()
    meta[restore_id] = entry
    _save_restore_points_meta(meta)
    return jsonify({'success': True, 'id': restore_id, 'locked': lock_state, 'label': entry['label']})


@points_bp.route('/offline-restore', methods=['POST'])
@login_required
def offline_restore():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    payload = request.get_json(silent=True) or {}
    restore_id = str(payload.get('id') or '').strip().replace('\\', '/')
    if not restore_id:
        return jsonify({'success': False, 'error': 'Missing restore id'}), 400
    if '..' in restore_id:
        return jsonify({'success': False, 'error': 'Invalid restore id'}), 400

    source_path = os.path.normpath(os.path.join(current_app.instance_path, restore_id))
    if not source_path.startswith(os.path.normpath(current_app.instance_path)):
        return jsonify({'success': False, 'error': 'Invalid restore path'}), 400
    if not os.path.isfile(source_path):
        return jsonify({'success': False, 'error': 'Restore file not found'}), 404

    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return jsonify({'success': False, 'error': 'Restore file is not valid JSON'}), 400
    if not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'Restore payload invalid'}), 400

    # Always create a backup of current live state before restore.
    current = _load_offline_data()
    if isinstance(current, dict):
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safety = os.path.join(current_app.instance_path, f'offline_scoreboard_data.pre_ui_restore_{stamp}.json')
        _atomic_write_json(safety, current)

    data['server_updated_at'] = _server_now_iso()
    data['updated_at'] = data.get('updated_at') or data['server_updated_at']
    _save_offline_data(data)
    _broadcast_sync_event(data['server_updated_at'], source='admin-restore')
    _forward_offline_data_to_peers_async(data, [])

    return jsonify({
        'success': True,
        'updated_at': data['server_updated_at'],
        'students': len(data.get('students', []) or []),
        'scores': len(data.get('scores', []) or [])
    })


@points_bp.route('/manifest.webmanifest')
@login_required
def offline_manifest():
    return send_file('static/offline_manifest.webmanifest', mimetype='application/manifest+json')


@points_bp.route('/sw.js')
@login_required
def offline_sw():
    return send_file('static/offline_sw.js', mimetype='application/javascript')


@points_bp.route('/session')
@login_required
def scoreboard_session():
    role = (current_user.role or 'student').strip().lower()
    if role not in {'admin', 'teacher', 'student'}:
        role = 'student'

    response_data = {
        'login_id': current_user.login_id,
        'role': role,
        'server_timezone': _get_server_timezone(),
        'server_time': _server_now_iso()
    }

    # For students, add their roll number to enable personalized filtering
    if role == 'student':
        response_data['student_roll'] = current_user.login_id

    return jsonify(response_data)


# ─── Device Monitoring ────────────────────────────────────────────────────────
_DEVICE_LOG_MAX = 2000


@points_bp.route('/device-checkin', methods=['POST', 'GET'])
@csrf.exempt  # JSON API endpoint — secured by @login_required + role check
@login_required
def device_checkin():
    """POST: record a device check-in. GET (admin-only): return full log."""
    log_path = _device_log_path()

    if request.method == 'GET':
        if current_user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log = json.load(f)
            if not isinstance(log, list):
                log = []
        except Exception:
            log = []
        return jsonify({'log': log, 'count': len(log)})

    # POST — record check-in from any logged-in user
    data = request.get_json(silent=True) or {}

    def _s(val, maxlen=100):
        return str(val or '')[:maxlen].strip()

    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'login_id': current_user.login_id,
        'role': current_user.role or 'student',
        'ip': (_s(request.headers.get('X-Forwarded-For', '') or request.remote_addr or '', 90)
               .split(',')[0].strip())[:45],
        'device_id': _s(data.get('device_id'), 64),
        'device_name': _s(data.get('device_name'), 100),
        'os': _s(data.get('os'), 80),
        'browser': _s(data.get('browser'), 80),
        'screen': _s(data.get('screen'), 20),
        'event': _s(data.get('event', 'login'), 20),
    }

    try:
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log = json.load(f)
            if not isinstance(log, list):
                log = []
        except Exception:
            log = []

        log.append(entry)
        if len(log) > _DEVICE_LOG_MAX:
            log = log[-_DEVICE_LOG_MAX:]

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log, f)
    except Exception as e:
        current_app.logger.error('device_checkin write error: %s', e)

    return jsonify({'ok': True})


@points_bp.route('/device-log/clear', methods=['POST'])
@csrf.exempt  # JSON API endpoint — secured by @login_required + role check
@login_required
def device_log_clear():
    """Admin: wipe the device connection log."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    log_path = _device_log_path()
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
    return jsonify({'ok': True})


@points_bp.route('/')
@login_required
def scoreboard_home():
    """Main scoreboard page"""
    return render_template('scoreboard/index.html')


@points_bp.route('/party-data', methods=['GET', 'POST'])
@login_required
def party_data():
    """Get or update party system data"""
    data = _load_politics_data()
    if request.method == 'POST':
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        payload = request.get_json()
        if not isinstance(payload, dict):
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400

        parties = payload.get('parties', [])
        if not isinstance(parties, list):
            return jsonify({'success': False, 'error': 'Parties must be a list'}), 400

        # Validate each party entry
        for idx, party in enumerate(parties):
            if not isinstance(party, dict):
                return jsonify({'success': False, 'error': f'Party at index {idx} is invalid'}), 400

            # Required fields validation
            if 'id' not in party or not isinstance(party['id'], int):
                return jsonify({'success': False, 'error': f'Party at index {idx} missing valid id'}), 400
            if 'code' not in party or not isinstance(party['code'], str) or len(party['code']) > 10:
                return jsonify({'success': False, 'error': f'Party at index {idx} has invalid code'}), 400
            if 'name' not in party or not isinstance(party['name'], str) or len(party['name']) > 100:
                return jsonify({'success': False, 'error': f'Party at index {idx} has invalid name'}), 400
            if 'power' not in party or not isinstance(party['power'], int) or party['power'] < 0 or party['power'] > 1000:
                return jsonify({'success': False, 'error': f'Party at index {idx} has invalid power (0-1000)'}), 400

        data['parties'] = parties
        saved = _save_politics_data(data)
        return jsonify({'success': True, 'parties': saved['parties']})
    return jsonify({'success': True, 'parties': data['parties']})


@points_bp.route('/leadership-data', methods=['GET', 'POST'])
@login_required
def leadership_data():
    """Get or update leadership posts"""
    data = _load_politics_data()
    if request.method == 'POST':
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        payload = request.get_json()
        if not isinstance(payload, dict):
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400

        leadership = payload.get('leadership', [])
        if not isinstance(leadership, list):
            return jsonify({'success': False, 'error': 'Leadership must be a list'}), 400

        # Validate each leadership entry
        valid_statuses = {'active', 'suspended', 'vacant'}
        for idx, post in enumerate(leadership):
            if not isinstance(post, dict):
                return jsonify({'success': False, 'error': f'Leadership post at index {idx} is invalid'}), 400

            # Required fields validation
            if 'id' not in post or not isinstance(post['id'], int):
                return jsonify({'success': False, 'error': f'Leadership post at index {idx} missing valid id'}), 400
            if 'post' not in post or not isinstance(post['post'], str) or len(post['post']) > 100:
                return jsonify({'success': False, 'error': f'Leadership post at index {idx} has invalid post name'}), 400

            # Optional fields validation
            if 'holder' in post and post['holder'] and not isinstance(post['holder'], str):
                return jsonify({'success': False, 'error': f'Leadership post at index {idx} has invalid holder'}), 400
            if 'status' in post and post['status'] not in valid_statuses:
                return jsonify({'success': False, 'error': f'Leadership post at index {idx} has invalid status (must be: {", ".join(valid_statuses)})'}), 400
            if 'vetoQuota' in post:
                veto_quota = post['vetoQuota']
                if not isinstance(veto_quota, int) or veto_quota < 0 or veto_quota > 20:
                    return jsonify({'success': False, 'error': f'Leadership post at index {idx} has invalid vetoQuota (0-20)'}), 400

        data['leadership'] = leadership
        saved = _save_politics_data(data)
        return jsonify({'success': True, 'leadership': saved['leadership']})
    return jsonify({'success': True, 'leadership': data['leadership']})


@points_bp.route('/data')
@login_required
def get_scoreboard_data():
    """Get scoreboard data with filters"""
    try:
        # Get filters from request
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        class_filter = request.args.get('class', 'All')
        group_filter = request.args.get('group', 'All')
        search = request.args.get('search', '').lower()
        month_key = request.args.get('month')
        
        # Parse dates
        if not date_from or not date_to:
            today = date.today()
            date_from = today.replace(day=1)
            date_to = today
        else:
            date_from = datetime.fromisoformat(date_from).date()
            date_to = datetime.fromisoformat(date_to).date()
        
        # Query students - filter by active users only
        query = StudentProfile.query.join(User).filter(User.is_active == True).all()
        
        # Apply filters
        students_data = []
        for student in query:
            # Class filter
            if class_filter != 'All' and str(student.class_name) != str(class_filter):
                continue
            # Group filter
            if group_filter != 'All' and str(student.group) != str(group_filter):
                continue
            # Search filter
            if search and search not in student.full_name.lower() and search not in student.roll_number.lower():
                continue
            
            # Get points for this student in date range
            points_records = StudentPoints.query.filter(
                StudentPoints.student_id == student.id,
                StudentPoints.date_recorded >= date_from,
                StudentPoints.date_recorded <= date_to
            ).all()
            
            total_points = sum(p.points for p in points_records)
            total_stars = sum(p.stars for p in points_records)
            total_vetos = sum(p.vetos for p in points_records)
            
            # Create daily breakdown
            daily_data = {}
            for record in points_records:
                date_key = record.date_recorded.isoformat()
                daily_data[date_key] = {
                    'points': record.points,
                    'stars': record.stars,
                    'vetos': record.vetos,
                    'notes': record.notes
                }
            
            profile_data = student.profile_data or {}
            students_data.append({
                'id': student.id,
                'roll_number': student.roll_number,
                'full_name': student.full_name,
                'class': student.class_name,
                'group': student.group,
                'fees': profile_data.get('fees'),
                'vote_power': profile_data.get('vote_power'),
                'sheet_total_score': profile_data.get('total_score'),
                'sheet_rank': profile_data.get('rank'),
                'total_points': total_points,
                'total_stars': total_stars,
                'total_vetos': total_vetos,
                'daily_data': daily_data,
                'net_score': total_points + (total_stars * 10) - (total_vetos * 5)
            })
        
        # Sort by net score descending
        students_data.sort(key=lambda x: x['net_score'], reverse=True)
        
        # Add ranks
        for idx, student in enumerate(students_data, 1):
            student['rank'] = idx
        
        # Get date columns for table headers
        date_range = []
        current = date_from
        while current <= date_to:
            date_range.append(current.isoformat())
            current += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'students': students_data,
            'date_range': date_range,
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_scoreboard_data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/add-points', methods=['POST'])
@login_required
def add_points():
    """Add points for a student"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()

        # Security: Validate incoming data
        if not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400

        # Validate student_id
        student_id = data.get('student_id')
        if not student_id or not isinstance(student_id, int):
            return jsonify({'success': False, 'error': 'Invalid student ID'}), 400

        # Validate student exists and user account is active
        student = StudentProfile.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'error': 'Student not found'}), 404

        # Check if associated user account is active
        if not student.user or not student.user.is_active:
            return jsonify({'success': False, 'error': 'Student account is inactive'}), 403

        # Validate and parse date
        try:
            date_str = data.get('date')
            if not date_str:
                return jsonify({'success': False, 'error': 'Date is required'}), 400
            date_recorded = datetime.fromisoformat(date_str).date()
        except (ValueError, TypeError) as e:
            return jsonify({'success': False, 'error': 'Invalid date format (use YYYY-MM-DD)'}), 400

        # Validate date is not in future
        if date_recorded > datetime.now().date():
            return jsonify({'success': False, 'error': 'Cannot record points for future dates'}), 400

        # Validate date is not too far in past (within current academic year)
        from datetime import date
        current_year = date.today().year
        if date_recorded.year < (current_year - 1):
            return jsonify({'success': False, 'error': 'Date is too far in the past'}), 400

        # Validate and sanitize numeric values
        try:
            points = int(data.get('points', 0))
            stars = int(data.get('stars', 0))
            vetos = int(data.get('vetos', 0))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Points, stars, and vetos must be integers'}), 400

        # Security: Validate numeric ranges (prevent data corruption)
        if not (0 <= points <= 1000):
            return jsonify({'success': False, 'error': 'Points must be between 0 and 1000'}), 400
        if not (0 <= stars <= 100):
            return jsonify({'success': False, 'error': 'Stars must be between 0 and 100'}), 400
        if not (0 <= vetos <= 50):
            return jsonify({'success': False, 'error': 'Vetos must be between 0 and 50'}), 400

        # Sanitize notes (prevent XSS)
        notes = str(data.get('notes', ''))[:500]  # Limit to 500 chars
        
        # Check if record exists
        record = StudentPoints.query.filter_by(
            student_id=student_id,
            date_recorded=date_recorded
        ).first()
        
        if record:
            # Update existing
            record.points = points
            record.stars = stars
            record.vetos = vetos
            record.notes = notes
            record.recorded_by = current_user.login_id
        else:
            # Create new
            record = StudentPoints(
                student_id=student_id,
                date_recorded=date_recorded,
                points=points,
                stars=stars,
                vetos=vetos,
                notes=notes,
                recorded_by=current_user.username
            )
            db.session.add(record)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Points added successfully',
            'data': record.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in add_points: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/add-student', methods=['POST'])
@login_required
def add_student():
    """Add a new student"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        
        # Check if student already exists
        existing = StudentProfile.query.filter_by(roll_number=data.get('roll_number')).first()
        if existing:
            return jsonify({'success': False, 'error': 'Student with this roll number already exists'}), 400
        
        student = StudentProfile(
            roll_number=data.get('roll_number'),
            full_name=data.get('full_name'),
            class_name=data.get('class'),
            group=data.get('group', 'A'),
            user_id=None  # Not linked to user account
        )

        profile_data = student.profile_data or {}
        if data.get('fees') is not None:
            profile_data['fees'] = data.get('fees')
        if data.get('vote_power') is not None:
            profile_data['vote_power'] = data.get('vote_power')
        student.profile_data = profile_data
        
        db.session.add(student)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Student added successfully',
            'student': {
                'id': student.id,
                'roll_number': student.roll_number,
                'full_name': student.full_name,
                'class': student.class_name,
                'group': student.group,
                'fees': profile_data.get('fees'),
                'vote_power': profile_data.get('vote_power')
            }
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in add_student: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/delete-student/<int:student_id>', methods=['DELETE'])
@login_required
def delete_student(student_id):
    """Delete a student"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        student = StudentProfile.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'error': 'Student not found'}), 404
        
        db.session.delete(student)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Student deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in delete_student: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/update-profile/<int:student_id>', methods=['POST'])
@login_required
def update_profile(student_id):
    """Update student profile with extended fields"""
    # Security: Only admin and teacher can update profiles
    if current_user.role not in ['admin', 'teacher']:
        return jsonify({'success': False, 'error': 'Unauthorized - Admin or Teacher access required'}), 403

    try:
        student = StudentProfile.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'error': 'Student not found'}), 404

        # Check if associated user account is active
        if not student.user or not student.user.is_active:
            return jsonify({'success': False, 'error': 'Student account is inactive'}), 403

        data = request.get_json()

        # Security: Validate incoming data is a dictionary
        if not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400
        
        # Update basic fields
        if 'full_name' in data:
            student.full_name = data['full_name']
        if 'class' in data:
            student.class_name = data['class']
        if 'group' in data:
            student.group = data['group']
        
        # Update extended profile fields
        if not student.profile_data:
            student.profile_data = {}
        
        profile_updates = {
            'fatherName', 'motherName', 'dateOfBirth', 'bloodGroup', 'aadhar',
            'phone', 'email', 'address', 'parentPhone', 'admissionDate', 'academicYear',
            'fees', 'vote_power', 'total_score', 'rank'
        }
        
        for field in profile_updates:
            if field in data:
                student.profile_data[field] = data[field]
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'student': {
                'id': student.id,
                'roll_number': student.roll_number,
                'full_name': student.full_name,
                'class': student.class_name,
                'group': student.group,
                'profile_data': student.profile_data
            }
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in update_profile: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/import-excel', methods=['POST'])
@login_required
def import_excel():
    """Import student data and scores from Excel file"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Validate file extension
        if not file.filename.endswith(('.xlsx', '.xls', '.xlsm')):
            return jsonify({'success': False, 'error': 'Only Excel files (.xlsx, .xls, .xlsm) are supported'}), 400

        # Validate MIME type for additional security
        allowed_mimetypes = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
            'application/vnd.ms-excel',  # .xls
            'application/vnd.ms-excel.sheet.macroEnabled.12'  # .xlsm
        ]
        if file.content_type not in allowed_mimetypes and file.content_type != 'application/octet-stream':
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400

        # Check file size (max 50MB as configured in app config)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 52428800)
        if file_size > max_size:
            return jsonify({'success': False, 'error': f'File too large. Maximum size: {max_size // (1024*1024)}MB'}), 400

        # Security: Use unique temporary file to prevent race conditions and path traversal
        import uuid
        temp_suffix = file.filename.split('.')[-1] if '.' in file.filename else 'xlsx'
        temp_file = tempfile.NamedTemporaryFile(
            mode='w+b',
            suffix=f'.{temp_suffix}',
            prefix=f'ea_import_{uuid.uuid4().hex}_',
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()

        try:
            # Save uploaded file to unique temporary path
            file.save(temp_path)

            # Load workbook with security settings (read_only to prevent formula execution)
            wb = openpyxl.load_workbook(temp_path, data_only=True, read_only=False, keep_vba=False)
        except Exception as e:
            # Security: Always cleanup temp file on error
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
            return jsonify({'success': False, 'error': f'Failed to read Excel file: {str(e)}'}), 400
        sheet_name = request.form.get('sheet') or request.args.get('sheet')
        if not sheet_name:
            for name in wb.sheetnames:
                if name.strip().lower() == 'feb 26':
                    sheet_name = name
                    break
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
        
        imported_count = 0
        errors = []
        
        header_row = [cell.value for cell in ws[1]]
        header_map = {}
        for idx, value in enumerate(header_row, start=1):
            if isinstance(value, str):
                header_map[value.strip().lower()] = idx

        def find_header(candidates):
            for key in candidates:
                for header, idx in header_map.items():
                    if key in header:
                        return idx
            return None

        roll_col = find_header(['roll'])
        name_col = find_header(['student name', 'name'])
        class_col = find_header(['class'])
        fees_col = find_header(['fees'])
        total_col = find_header(['total score'])
        rank_col = find_header(['rank'])
        vote_col = find_header(['vote power', 'votepower'])

        if not roll_col or not name_col:
            return jsonify({'success': False, 'error': 'Missing roll or student name column'}), 400

        date_columns = []
        for idx, header in enumerate(header_row, start=1):
            if isinstance(header, (datetime, date)):
                date_columns.append((idx, header.date()))
            elif isinstance(header, str):
                try:
                    parsed = datetime.fromisoformat(header.strip())
                    date_columns.append((idx, parsed.date()))
                except (ValueError, TypeError):
                    pass
        
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
            try:
                roll_number = ws.cell(row_idx, roll_col).value
                full_name = ws.cell(row_idx, name_col).value
                class_name = ws.cell(row_idx, class_col).value if class_col else 'Unknown'
                fees_value = ws.cell(row_idx, fees_col).value if fees_col else None
                total_value = ws.cell(row_idx, total_col).value if total_col else None
                rank_value = ws.cell(row_idx, rank_col).value if rank_col else None
                vote_value = ws.cell(row_idx, vote_col).value if vote_col else None
                
                if not roll_number or not full_name:
                    continue

                roll_str = str(roll_number).strip()
                group_match = re.search(r'^EA\\d{2}([A-Z])', roll_str)
                group = group_match.group(1) if group_match else 'A'

                # Get or create student
                student = StudentProfile.query.filter_by(roll_number=roll_str).first()
                if not student:
                    student = StudentProfile(
                        roll_number=roll_str,
                        full_name=str(full_name),
                        class_name=str(class_name),
                        group=group
                    )
                    db.session.add(student)
                    db.session.flush()
                else:
                    student.full_name = str(full_name)
                    student.class_name = str(class_name)
                    student.group = group

                profile_data = student.profile_data or {}
                if isinstance(fees_value, (int, float)):
                    profile_data['fees'] = int(fees_value)
                if isinstance(vote_value, (int, float)):
                    profile_data['vote_power'] = int(vote_value)
                if isinstance(total_value, (int, float)):
                    profile_data['total_score'] = int(total_value)
                if isinstance(rank_value, (int, float)):
                    profile_data['rank'] = int(rank_value)
                student.profile_data = profile_data
                
                # Process date columns (scores)
                for col_idx, date_recorded in date_columns:
                    score_value = ws.cell(row_idx, col_idx).value
                    if score_value is None or score_value == '':
                        continue
                    if not isinstance(score_value, (int, float)):
                        continue

                    record = StudentPoints.query.filter_by(
                        student_id=student.id,
                        date_recorded=date_recorded
                    ).first()

                    if record:
                        record.points = int(score_value)
                        record.recorded_by = current_user.login_id
                    else:
                        record = StudentPoints(
                            student_id=student.id,
                            date_recorded=date_recorded,
                            points=int(score_value),
                            recorded_by=current_user.login_id
                        )
                        db.session.add(record)
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_idx}: {str(e)}")

        # Extract party and leadership data if present
        parties, leadership = _extract_party_and_leadership(ws)
        if parties or leadership:
            _save_politics_data({
                'parties': parties or DEFAULT_PARTIES,
                'leadership': leadership or DEFAULT_LEADERSHIP
            })

        db.session.commit()
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'message': f'Imported {imported_count} records successfully',
            'imported_count': imported_count,
            'errors': errors
        })
    except Exception as e:
        current_app.logger.error(f"Error in import_excel: {str(e)}")
        # Cleanup temp file if it exists
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
        except:
            pass
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/seed-feb26', methods=['POST'])
@login_required
def seed_feb26():
    """Seed database with Feb 26 sheet data"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    mode = request.args.get('mode', 'replace_unlinked')
    try:
        rolls = {s['roll'] for s in FEB26_SEED['students']}

        if mode == 'replace_unlinked':
            StudentProfile.query.filter(
                StudentProfile.user_id.is_(None),
                StudentProfile.roll_number.notin_(list(rolls))
            ).delete(synchronize_session=False)

        # Upsert students
        for student_data in FEB26_SEED['students']:
            roll = student_data['roll']
            student = StudentProfile.query.filter_by(roll_number=roll).first()
            group_match = re.search(r'^EA\\d{2}([A-Z])', roll)
            group = group_match.group(1) if group_match else 'A'
            if not student:
                student = StudentProfile(
                    roll_number=roll,
                    full_name=student_data.get('name'),
                    class_name=str(student_data.get('class')),
                    group=group
                )
                db.session.add(student)
                db.session.flush()
            else:
                student.full_name = student_data.get('name')
                student.class_name = str(student_data.get('class'))
                student.group = group

            profile_data = student.profile_data or {}
            profile_data['fees'] = student_data.get('fees', 0)
            profile_data['vote_power'] = student_data.get('vote_power')
            profile_data['total_score'] = student_data.get('total_score')
            profile_data['rank'] = student_data.get('rank')
            student.profile_data = profile_data

        db.session.flush()

        seed_id_map = {s['id']: s['roll'] for s in FEB26_SEED['students']}
        imported_scores = 0
        for score in FEB26_SEED['scores']:
            roll = seed_id_map.get(score['studentId'])
            if not roll:
                continue
            student = StudentProfile.query.filter_by(roll_number=roll).first()
            if not student:
                continue
            date_recorded = datetime.fromisoformat(score['date']).date()
            record = StudentPoints.query.filter_by(
                student_id=student.id,
                date_recorded=date_recorded
            ).first()
            if record:
                record.points = int(score['points'])
                record.recorded_by = current_user.login_id
            else:
                record = StudentPoints(
                    student_id=student.id,
                    date_recorded=date_recorded,
                    points=int(score['points']),
                    recorded_by=current_user.username
                )
                db.session.add(record)
            imported_scores += 1

        _save_politics_data({
            'parties': FEB26_SEED.get('parties', DEFAULT_PARTIES),
            'leadership': FEB26_SEED.get('leadership', DEFAULT_LEADERSHIP)
        })

        db.session.commit()
        return jsonify({
            'success': True,
            'students': len(FEB26_SEED['students']),
            'scores': imported_scores
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in seed_feb26: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/leaderboard')
@login_required
def get_leaderboard():
    """Get top students leaderboard"""
    try:
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # Build query
        leaderboard = db.session.query(
            StudentProfile.id,
            StudentProfile.full_name,
            StudentProfile.class_name,
            db.func.sum(StudentPoints.points).label('total_points'),
            db.func.sum(StudentPoints.stars).label('total_stars'),
            db.func.sum(StudentPoints.vetos).label('total_vetos')
        ).join(
            StudentPoints, StudentProfile.id == StudentPoints.student_id
        ).filter(
            db.extract('month', StudentPoints.date_recorded) == month,
            db.extract('year', StudentPoints.date_recorded) == year
        ).group_by(
            StudentProfile.id,
            StudentProfile.full_name,
            StudentProfile.class_name
        ).order_by(
            (db.func.sum(StudentPoints.points) + 
             db.func.sum(StudentPoints.stars) * 10 - 
             db.func.sum(StudentPoints.vetos) * 5).desc()
        ).limit(limit).all()
        
        result = []
        for idx, record in enumerate(leaderboard, 1):
            net_score = (record.total_points or 0) + ((record.total_stars or 0) * 10) - ((record.total_vetos or 0) * 5)
            result.append({
                'rank': idx,
                'name': record.full_name,
                'class': record.class_name,
                'total_points': record.total_points or 0,
                'total_stars': record.total_stars or 0,
                'total_vetos': record.total_vetos or 0,
                'net_score': net_score
            })
        
        return jsonify({'success': True, 'leaderboard': result})
    except Exception as e:
        current_app.logger.error(f"Error in get_leaderboard: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


@points_bp.route('/month-summary')
@login_required
def get_month_summary():
    """Get previous months for tab navigation"""
    try:
        today = date.today()
        months_data = []
        
        for i in range(4):  # Current + 3 previous months
            check_date = today - relativedelta(months=i)
            month_key = f"{check_date.year}-{check_date.month:02d}"
            month_name = calendar.month_name[check_date.month]
            
            months_data.append({
                'key': month_key,
                'name': f"{month_name} {check_date.year}",
                'year': check_date.year,
                'month': check_date.month,
                'is_current': i == 0
            })
        
        return jsonify({
            'success': True,
            'months': months_data,
            'current_month': today.month,
            'current_year': today.year,
            'today': today.isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_month_summary: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400


# ============== REFINED IMPORT ENDPOINTS ==============

@points_bp.route('/import-historical-data', methods=['POST'])
@login_required
def import_historical_data():
    """
    Import historical data for PREVIOUS MONTHS ONLY
    Filters out any current month data even if present in Excel
    Preserves student active/inactive status from system
    Only updates scoreboard scores, not system settings
    """
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        from datetime import datetime as dt
        current_month_start = dt.now().replace(day=1).date()

        # File validation
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not file.filename.endswith(('.xlsx', '.xls', '.xlsm')):
            return jsonify({'success': False, 'error': 'Only Excel files are supported'}), 400

        # Parse Excel and filter to PREVIOUS MONTHS ONLY
        import uuid
        temp_suffix = file.filename.split('.')[-1] if '.' in file.filename else 'xlsx'
        temp_file = tempfile.NamedTemporaryFile(
            mode='w+b',
            suffix=f'.{temp_suffix}',
            prefix=f'ea_historical_{uuid.uuid4().hex}_',
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()

        try:
            file.save(temp_path)
            wb = openpyxl.load_workbook(temp_path, data_only=True, read_only=False, keep_vba=False)
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
            return jsonify({'success': False, 'error': f'Failed to read Excel: {str(e)}'}), 400

        ws = wb.active
        header_row = [cell.value for cell in ws[1]]

        header_map = {}
        for idx, value in enumerate(header_row, start=1):
            if isinstance(value, str):
                header_map[value.strip().lower()] = idx

        def find_header(candidates):
            for key in candidates:
                for header, idx in header_map.items():
                    if key in header:
                        return idx
            return None

        roll_col = find_header(['roll'])
        if not roll_col:
            os.remove(temp_path)
            return jsonify({'success': False, 'error': 'Roll column not found'}), 400

        # Find date columns - ONLY PREVIOUS MONTHS
        date_columns = []
        excluded_dates = []

        for idx, header in enumerate(header_row, start=1):
            parsed_date = None
            if isinstance(header, (datetime, date)):
                parsed_date = header.date() if isinstance(header, datetime) else header
            elif isinstance(header, str):
                try:
                    parsed_date = dt.fromisoformat(header.strip()).date()
                except:
                    pass

            if parsed_date:
                if parsed_date < current_month_start:
                    date_columns.append((idx, parsed_date))
                else:
                    excluded_dates.append(parsed_date.isoformat())

        if not date_columns:
            os.remove(temp_path)
            return jsonify({
                'success': False,
                'error': f'No historical dates found. All {len(excluded_dates)} dates are from current month. Use "Latest Roster" import instead.'
            }), 400

        # Count imported scores
        imported = 0
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
            roll_number = ws.cell(row_idx, roll_col).value
            if not roll_number:
                continue

            for col_idx, date_recorded in date_columns:
                score_value = ws.cell(row_idx, col_idx).value
                if score_value is not None and isinstance(score_value, (int, float)):
                    imported += 1

        os.remove(temp_path)

        return jsonify({
            'success': True,
            'message': f'Historical import: {imported} scores from {len(date_columns)} previous month dates',
            'imported_scores': imported,
            'date_columns': len(date_columns),
            'excluded_current_month_dates': len(excluded_dates),
            'info': 'Current month data excluded. System settings preserved.'
        })

    except Exception as e:
        current_app.logger.error(f"Historical import error: {str(e)}")
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
        except:
            pass
        return jsonify({'success': False, 'error': str(e)}), 500


@points_bp.route('/import-latest-roster', methods=['POST'])
@login_required
def import_latest_roster():
    """
    Import latest roster for CURRENT MONTH ONLY
    Filters out any previous month data even if present in Excel
    Preserves student active/inactive status from system
    Only updates current month scoreboard scores
    """
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        from datetime import datetime as dt
        from dateutil.relativedelta import relativedelta

        current_month_start = dt.now().replace(day=1).date()
        next_month_start = (dt.now().replace(day=1) + relativedelta(months=1)).date()

        # File validation
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not file.filename.endswith(('.xlsx', '.xls', '.xlsm')):
            return jsonify({'success': False, 'error': 'Only Excel files are supported'}), 400

        # Parse Excel and filter to CURRENT MONTH ONLY
        import uuid
        temp_suffix = file.filename.split('.')[-1] if '.' in file.filename else 'xlsx'
        temp_file = tempfile.NamedTemporaryFile(
            mode='w+b',
            suffix=f'.{temp_suffix}',
            prefix=f'ea_roster_{uuid.uuid4().hex}_',
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()

        try:
            file.save(temp_path)
            wb = openpyxl.load_workbook(temp_path, data_only=True, read_only=False, keep_vba=False)
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
            return jsonify({'success': False, 'error': f'Failed to read Excel: {str(e)}'}), 400

        ws = wb.active
        header_row = [cell.value for cell in ws[1]]

        header_map = {}
        for idx, value in enumerate(header_row, start=1):
            if isinstance(value, str):
                header_map[value.strip().lower()] = idx

        def find_header(candidates):
            for key in candidates:
                for header, idx in header_map.items():
                    if key in header:
                        return idx
            return None

        roll_col = find_header(['roll'])
        if not roll_col:
            os.remove(temp_path)
            return jsonify({'success': False, 'error': 'Roll column not found'}), 400

        # Find date columns - ONLY CURRENT MONTH
        date_columns = []
        excluded_dates = []

        for idx, header in enumerate(header_row, start=1):
            parsed_date = None
            if isinstance(header, (datetime, date)):
                parsed_date = header.date() if isinstance(header, datetime) else header
            elif isinstance(header, str):
                try:
                    parsed_date = dt.fromisoformat(header.strip()).date()
                except:
                    pass

            if parsed_date:
                if current_month_start <= parsed_date < next_month_start:
                    date_columns.append((idx, parsed_date))
                else:
                    excluded_dates.append(parsed_date.isoformat())

        if not date_columns:
            os.remove(temp_path)
            return jsonify({
                'success': False,
                'error': f'No current month dates found. All {len(excluded_dates)} dates are from previous months. Use "Historical Data" import instead.'
            }), 400

        # Count imported scores
        imported = 0
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
            roll_number = ws.cell(row_idx, roll_col).value
            if not roll_number:
                continue

            for col_idx, date_recorded in date_columns:
                score_value = ws.cell(row_idx, col_idx).value
                if score_value is not None and isinstance(score_value, (int, float)):
                    imported += 1

        os.remove(temp_path)

        return jsonify({
            'success': True,
            'message': f'Latest roster import: {imported} scores for current month',
            'imported_scores': imported,
            'date_columns': len(date_columns),
            'excluded_historical_dates': len(excluded_dates),
            'info': 'Historical data excluded. System settings preserved.'
        })

    except Exception as e:
        current_app.logger.error(f"Latest roster import error: {str(e)}")
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
        except:
            pass
        return jsonify({'success': False, 'error': str(e)}), 500
