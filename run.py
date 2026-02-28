import os
import json
import re
import urllib.request
import urllib.error
import atexit
from datetime import datetime
from pathlib import Path
from app import create_app, db
from app.models import User, StudentProfile, ActivityLog

app = create_app()
_SERVER_LOCK_FD = None


def create_startup_restore_point(flask_app, keep=200):
    """Write a startup restore snapshot of offline scoreboard data."""
    instance_dir = Path(flask_app.instance_path)
    source = instance_dir / 'offline_scoreboard_data.json'
    if not source.exists():
        return
    restore_dir = instance_dir / 'startup_restore_points'
    restore_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    target = restore_dir / f'offline_scoreboard_startup_{stamp}.json'
    try:
        data = json.loads(source.read_text(encoding='utf-8'))
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        return

    backups = sorted(restore_dir.glob('offline_scoreboard_startup_*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[keep:]:
        try:
            old.unlink()
        except Exception:
            pass


def _pid_is_running(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def acquire_single_instance_lock(flask_app):
    """Ensure a single run.py writer process per machine."""
    global _SERVER_LOCK_FD
    lock_path = Path(flask_app.instance_path) / '.server_main.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    this_pid = os.getpid()

    # Clear stale lock if previous PID is gone.
    if lock_path.exists():
        try:
            existing_pid = int(lock_path.read_text(encoding='utf-8').strip())
        except Exception:
            existing_pid = 0
        if existing_pid and _pid_is_running(existing_pid):
            print(f'Another server instance is already running (pid {existing_pid}). Exiting duplicate launcher.')
            return False
        try:
            lock_path.unlink()
        except Exception:
            pass

    try:
        _SERVER_LOCK_FD = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(_SERVER_LOCK_FD, str(this_pid).encode('utf-8'))
        os.fsync(_SERVER_LOCK_FD)
    except FileExistsError:
        print('Another server instance is already running. Exiting duplicate launcher.')
        return False

    def _release():
        global _SERVER_LOCK_FD
        try:
            if _SERVER_LOCK_FD is not None:
                os.close(_SERVER_LOCK_FD)
        except Exception:
            pass
        _SERVER_LOCK_FD = None
        try:
            if lock_path.exists():
                lock_path.unlink()
        except Exception:
            pass

    atexit.register(_release)
    return True


def _parse_sync_peers():
    raw = os.getenv('SYNC_PEERS', '') or os.getenv('SYNC_PEER', '')
    peers = []
    for token in re.split(r'[,;\s]+', str(raw).strip()):
        item = token.strip()
        if not item:
            continue
        if not re.match(r'^https?://', item, re.I):
            item = f'http://{item}'
        peers.append(item.rstrip('/'))
    return list(dict.fromkeys(peers))


def _load_json_file(path_obj):
    try:
        return json.loads(path_obj.read_text(encoding='utf-8'))
    except Exception:
        return None


def _student_count(payload):
    if not isinstance(payload, dict):
        return 0
    students = payload.get('students', [])
    return len(students) if isinstance(students, list) else 0


def maybe_bootstrap_backup_from_master(flask_app):
    """
    On backup server startup, optionally pull latest full offline snapshot from master.
    Safety rules:
    - Never run in master mode.
    - Only replace local snapshot if remote appears newer and has a larger/equal roster.
    - Always keep a pre-pull restore copy.
    """
    if str(os.getenv('EA_MASTER_MODE', '')).strip() == '1':
        return
    if str(os.getenv('EA_BACKUP_BOOTSTRAP', '1')).strip().lower() in ('0', 'false', 'no', 'off'):
        return

    peers = _parse_sync_peers()
    if not peers:
        return

    instance_dir = Path(flask_app.instance_path)
    local_path = instance_dir / 'offline_scoreboard_data.json'
    local_data = _load_json_file(local_path) if local_path.exists() else None
    local_count = _student_count(local_data)
    local_stamp = str((local_data or {}).get('server_updated_at') or (local_data or {}).get('updated_at') or '')

    best_remote = None
    best_stamp = ''
    best_count = 0
    for peer in peers:
        url = f'{peer}/scoreboard/offline-data'
        try:
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=4) as resp:
                payload = json.loads(resp.read().decode('utf-8'))
            remote = payload.get('data', {}) if isinstance(payload, dict) else {}
            if not isinstance(remote, dict):
                continue
            remote_count = _student_count(remote)
            remote_stamp = str(payload.get('updated_at') or remote.get('server_updated_at') or remote.get('updated_at') or '')
            if remote_count <= 0:
                continue
            if (remote_stamp, remote_count) >= (best_stamp, best_count):
                best_remote = remote
                best_stamp = remote_stamp
                best_count = remote_count
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
            continue

    if not isinstance(best_remote, dict):
        return

    # Replace only when clearly better/newer than local.
    should_replace = False
    if local_count == 0 and best_count > 0:
        should_replace = True
    elif best_count >= max(local_count, 25) and best_stamp >= local_stamp:
        should_replace = True
    elif best_count >= (local_count + 5):
        should_replace = True

    if not should_replace:
        return

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if local_path.exists():
        pre = instance_dir / f'offline_scoreboard_data.pre_backup_bootstrap_{stamp}.json'
        try:
            pre.write_text(local_path.read_text(encoding='utf-8'), encoding='utf-8')
        except Exception:
            pass
    try:
        local_path.write_text(json.dumps(best_remote, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        return

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'StudentProfile': StudentProfile,
        'ActivityLog': ActivityLog
    }


def initialize_runtime(flask_app):
    """Idempotent runtime bootstrap for both dev and production servers."""
    if flask_app.config.get('_EA_RUNTIME_INIT_DONE'):
        return
    with flask_app.app_context():
        db.create_all()
        maybe_bootstrap_backup_from_master(flask_app)
        create_startup_restore_point(flask_app)
        # Ensure default Admin and Teacher accounts exist
        # Passwords are read from environment variables for security
        admin_password = os.getenv('ADMIN_PASSWORD', 'ChangeAdminPass123!')
        teacher_password = os.getenv('TEACHER_PASSWORD', 'ChangeTeacherPass123!')
        defaults = [
            {'login_id': 'Admin', 'role': 'admin', 'password': admin_password},
            {'login_id': 'Teacher', 'role': 'teacher', 'password': teacher_password}
        ]
        for item in defaults:
            user = User.query.filter_by(login_id=item['login_id']).first()
            if not user:
                user = User(login_id=item['login_id'], role=item['role'], first_login=False)
                user.set_password(item['password'])
                db.session.add(user)
            else:
                # Ensure core accounts remain usable on every server node.
                user.role = item['role']
                user.is_active = True
        db.session.commit()
    flask_app.config['_EA_RUNTIME_INIT_DONE'] = True
    # Start background thread that keeps Render awake and syncs data every 30 s.
    # Only activates when EA_MASTER_MODE=1 and SYNC_PEERS is configured (local server).
    try:
        from app.routes.scoreboard import start_peer_sync_background
        start_peer_sync_background(flask_app)
    except Exception:
        pass

if __name__ == '__main__':
    if not acquire_single_instance_lock(app):
        raise SystemExit(0)
    initialize_runtime(app)
    port_value = os.getenv('PORT') or os.getenv('BACKUP_PORT') or '5000'
    try:
        port = int(port_value)
    except (TypeError, ValueError):
        port = 5000
    debug = str(os.getenv('FLASK_DEBUG', '0')).strip().lower() in ('1', 'true', 'yes', 'on')
    # Integrity safety: avoid Flask reloader double-process mode on server PCs,
    # which can create duplicate writers and race-prone startup side effects.
    use_reloader = str(os.getenv('FLASK_USE_RELOADER', '0')).strip().lower() in ('1', 'true', 'yes', 'on')
    prefer_waitress = str(os.getenv('EA_USE_WAITRESS', '1')).strip().lower() in ('1', 'true', 'yes', 'on')
    if prefer_waitress:
        try:
            from waitress import serve
            threads = int(os.getenv('WAITRESS_THREADS', '16'))
            serve(app, host='0.0.0.0', port=port, threads=max(4, threads))
            raise SystemExit(0)
        except Exception:
            pass
    app.run(debug=debug, use_reloader=use_reloader, host='0.0.0.0', port=port)
