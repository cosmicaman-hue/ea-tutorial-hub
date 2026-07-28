import os
import ipaddress
import re
from time import perf_counter
from urllib.parse import urlsplit
from flask import Flask, redirect, url_for, request, flash, session
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, UserMixin
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


class EphemeralUser(UserMixin):
    """Fallback session user used when DB ORM user loading is unavailable."""

    def __init__(self, user_id, login_id, role, active=True):
        self.id = int(user_id)
        self.login_id = str(login_id or '')
        self.role = str(role or 'student')
        self._active = bool(active)

    @property
    def is_active(self):
        return self._active


def _is_trusted_cors_origin(origin):
    """
    Exact-match validation of cross-origin callers.

    Trusted: file:// and null origins (offline SPA copies / Android WebView),
    localhost/loopback, private LAN IPs (192.168.x.x, 10.x.x.x, etc.) and
    *.trycloudflare.com tunnels. Substring checks were previously used and
    were bypassable (e.g. an attacker origin http://192.168.evil.com contained
    the string '192.168.'); this parses the hostname and matches it exactly.
    """
    if not origin:
        return False
    if origin == 'null' or origin.startswith('file://'):
        return True
    try:
        host = (urlsplit(origin).hostname or '').strip().lower()
    except Exception:
        return False
    if not host:
        return False
    if host == 'localhost' or host.endswith('.localhost'):
        return True
    if host == 'trycloudflare.com' or host.endswith('.trycloudflare.com'):
        return True
    # Cloudflare Named Tunnel domain (e.g. sync.yourdomain.com)
    tunnel_origin = str(os.getenv('EA_TUNNEL_ORIGIN', '') or '').strip().lower()
    if tunnel_origin and host == tunnel_origin:
        return True
    # Cloudflare Pages custom domain or project domain
    pages_origin = str(os.getenv('EA_CLOUDFLARE_PAGES_ORIGIN', '') or '').strip().lower()
    if pages_origin and host == pages_origin:
        return True
    # Allow *.pages.dev for Cloudflare Pages preview deployments
    if str(os.getenv('EA_ALLOW_PAGES_DEV', '0')).strip().lower() in ('1', 'true', 'yes', 'on'):
        if host.endswith('.pages.dev'):
            return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback
    except ValueError:
        return False


def make_ephemeral_user(role):
    role_key = str(role or '').strip().lower()
    if role_key == 'admin':
        return EphemeralUser(-1, 'Admin', 'admin', True)
    if role_key == 'teacher':
        return EphemeralUser(-2, 'Teacher', 'teacher', True)
    return None


def _configured_process_workers(environ=None):
    env = os.environ if environ is None else environ
    counts = []
    for name in ('WEB_CONCURRENCY', 'GUNICORN_WORKERS'):
        try:
            counts.append(int(str(env.get(name, '') or '').strip()))
        except (TypeError, ValueError):
            pass
    gunicorn_args = str(env.get('GUNICORN_CMD_ARGS', '') or '')
    match = re.search(r'(?:--workers(?:=|\s+)|-w\s+)(\d+)', gunicorn_args)
    if match:
        counts.append(int(match.group(1)))
    return max([1, *counts])


def _migrate_notebook_schema(app):
    """Recreate notebook_checks with roll_number schema; create other notebook tables."""
    with app.app_context():
        try:
            from sqlalchemy import inspect, text as sa_text
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            # Drop and recreate notebook_checks if it has the old student_id FK schema
            if 'notebook_checks' in tables:
                cols = [c['name'] for c in inspector.get_columns('notebook_checks')]
                if 'student_id' in cols:  # old schema — no data yet, safe to drop
                    with db.engine.connect() as conn:
                        conn.execute(sa_text('DROP TABLE IF EXISTS notebook_subject_checks'))
                        conn.execute(sa_text('DROP TABLE IF EXISTS notebook_checks'))
                        conn.commit()

            db.create_all()  # creates all missing tables with current schema

            # Add entry_type to student_points if missing
            if 'student_points' in tables:
                sp_cols = [c['name'] for c in inspector.get_columns('student_points')]
                if 'entry_type' not in sp_cols:
                    with db.engine.connect() as conn:
                        conn.execute(sa_text(
                            "ALTER TABLE student_points ADD COLUMN entry_type VARCHAR(30) DEFAULT 'manual'"
                        ))
                        conn.commit()

            # Add grade column to notebook_subject_checks if missing
            existing_tables = inspector.get_table_names()
            if 'notebook_subject_checks' in existing_tables:
                nsc_cols = [c['name'] for c in inspector.get_columns('notebook_subject_checks')]
                if 'grade' not in nsc_cols:
                    with db.engine.connect() as conn:
                        conn.execute(sa_text(
                            'ALTER TABLE notebook_subject_checks ADD COLUMN grade VARCHAR(30)'
                        ))
                        conn.commit()

            # Add missing columns to student_profiles if missing
            if 'student_profiles' in existing_tables:
                sp_cols = [c['name'] for c in inspector.get_columns('student_profiles')]
                with db.engine.connect() as conn:
                    if 'full_name' not in sp_cols:
                        conn.execute(sa_text(
                            'ALTER TABLE student_profiles ADD COLUMN full_name VARCHAR(300)'
                        ))
                    if 'group' not in sp_cols:
                        conn.execute(sa_text(
                            'ALTER TABLE student_profiles ADD COLUMN "group" VARCHAR(5) DEFAULT \'A\''
                        ))
                    if 'profile_data' not in sp_cols:
                        conn.execute(sa_text(
                            'ALTER TABLE student_profiles ADD COLUMN profile_data TEXT DEFAULT \'{}\''
                        ))
                    conn.commit()

            # Sync offline JSON ledger to SQLite on startup
            _sync_json_ledger_to_sqlite(app)

        except Exception:
            app.logger.exception(
                'Notebook/database schema migration failed; application startup will continue',
                extra={'event_type': 'schema_migration_failure'}
            )


def _sync_json_ledger_to_sqlite(app):
    """Synchronize the offline scoreboard JSON ledger to SQLite tables on startup."""
    with app.app_context():
        started_at = perf_counter()
        metrics = {
            'status': 'running',
            'source_students': 0,
            'source_scores': 0,
            'rolls_backfilled': 0,
            'users_created': 0,
            'students_created': 0,
            'students_updated': 0,
            'scores_created': 0,
            'scores_updated': 0,
            'rows_skipped': 0,
        }
        try:
            from datetime import datetime, date
            from app.utils.data_paths import load_json_data_cached
            from app.models.student_profile import StudentProfile
            from app.models.points import StudentPoints
            from app.models import User
            
            data = load_json_data_cached()
            if not data or not isinstance(data, dict):
                metrics['status'] = 'skipped_no_ledger'
                metrics['duration_ms'] = round((perf_counter() - started_at) * 1000, 2)
                app.logger.info(
                    'JSON-to-SQL reconciliation skipped because no ledger was available',
                    extra={'event_type': 'json_sql_reconciliation', 'metrics': metrics}
                )
                return
            students = data.get('students', [])
            scores = data.get('scores', [])
            metrics['source_students'] = len(students) if hasattr(students, '__len__') else 0
            metrics['source_scores'] = len(scores) if hasattr(scores, '__len__') else 0

            # 0. Propagate User.login_id to StudentProfile.roll_number for existing null-roll profiles
            for s in StudentProfile.query.filter((StudentProfile.roll_number.is_(None)) | (StudentProfile.roll_number == '')).all():
                if s.user_id:
                    u = User.query.get(s.user_id)
                    if u and u.login_id and u.login_id.upper().startswith('EA'):
                        s.roll_number = u.login_id.upper()
                        metrics['rolls_backfilled'] += 1
            db.session.commit()

            # 1. Sync students
            roll_to_sqlite_student = {}
            for s in students:
                roll = s.get('roll')
                if not roll:
                    metrics['rows_skipped'] += 1
                    continue
                
                # Check if student exists in SQL
                student = StudentProfile.query.filter_by(roll_number=roll).first()
                if not student:
                    user = User.query.filter_by(login_id=roll).first()
                    if not user:
                        user = User(
                            login_id=roll,
                            role='student',
                            first_login=True,
                            is_active=True
                        )
                        user.set_password(roll)
                        db.session.add(user)
                        db.session.flush()
                        metrics['users_created'] += 1
                    name_parts = (s.get('name') or s.get('base_name') or roll).strip().split(' ')
                    first_name = name_parts[0]
                    second_name = name_parts[1] if len(name_parts) > 1 else ''
                    third_name = ' '.join(name_parts[2:]) if len(name_parts) > 2 else ''
                    
                    dob = None
                    try:
                        dob_str = s.get('profile_data', {}).get('dateOfBirth', '')
                        if dob_str:
                            dob = date.fromisoformat(dob_str)
                    except Exception:
                        pass
                    if not dob:
                        dob = date(2000, 1, 1)

                    student = StudentProfile(
                        roll_number=roll,
                        first_name=first_name,
                        second_name=second_name,
                        third_name=third_name,
                        full_name=s.get('name') or s.get('base_name') or roll,
                        class_name=str(s.get('class', '5')),
                        group=s.get('group', 'A'),
                        user_id=user.id,
                        date_of_birth=dob,
                        gender='Unknown',
                        religion='Unknown',
                        nationality='India',
                        school_name='Unknown',
                        section='A',
                        contact_number_1='',
                        contact_number_2='',
                        email=None,
                        village_area='',
                        post_office='',
                        district='',
                        state='',
                        pin_code='',
                        hobbies='',
                        improvement_areas='',
                        father_name='',
                        mother_name='',
                        guardian_name='',
                        guardian_contact='',
                        blood_group='',
                        aadhar_number='',
                        profile_data=s.get('profile_data') or {}
                    )
                    db.session.add(student)
                    db.session.flush()
                    metrics['students_created'] += 1
                else:
                    next_name = s.get('name') or s.get('base_name') or student.full_name
                    next_class = str(s.get('class', student.class_name))
                    next_group = s.get('group', student.group)
                    if (
                        student.full_name != next_name
                        or student.class_name != next_class
                        or student.group != next_group
                    ):
                        metrics['students_updated'] += 1
                    student.full_name = next_name
                    student.class_name = next_class
                    student.group = next_group
                
                roll_to_sqlite_student[roll] = student
            
            db.session.commit()
            
            # Create a mapping of JSON student ID to roll
            json_id_to_roll = {s.get('id'): s.get('roll') for s in students if s.get('id') and s.get('roll')}
            
            # 2. Sync scores (only for active students in SQL)
            # Query all existing StudentPoints to memory to avoid 12000 SELECT statements
            existing_points = StudentPoints.query.all()
            existing_map = {}
            for ep in existing_points:
                key = (ep.student_id, ep.date_recorded.isoformat(), ep.entry_type)
                existing_map[key] = ep
                
            for sc in scores:
                json_sid = sc.get('studentId')
                roll = json_id_to_roll.get(json_sid)
                if not roll:
                    metrics['rows_skipped'] += 1
                    continue
                
                student_db = roll_to_sqlite_student.get(roll)
                if not student_db:
                    metrics['rows_skipped'] += 1
                    continue
                
                date_str = sc.get('date')
                if not date_str:
                    metrics['rows_skipped'] += 1
                    continue
                
                notes = sc.get('notes', '')
                entry_type = 'manual'
                if '[NOTEBOOK:SCHOOL]' in notes:
                    entry_type = 'notebook_school'
                elif '[NOTEBOOK:TUITION]' in notes:
                    entry_type = 'notebook_tuition'
                
                key = (student_db.id, date_str, entry_type)
                points = sc.get('points', 0)
                stars = sc.get('stars', 0)
                vetos = sc.get('vetos', 0)
                recorded_by = sc.get('recorded_by') or 'system'
                
                if key in existing_map:
                    points_record = existing_map[key]
                    if (points_record.points != points or 
                        points_record.stars != stars or 
                        points_record.vetos != vetos or 
                        points_record.notes != notes):
                        points_record.points = points
                        points_record.stars = stars
                        points_record.vetos = vetos
                        points_record.notes = notes
                        points_record.recorded_by = recorded_by
                        metrics['scores_updated'] += 1
                else:
                    try:
                        date_recorded = datetime.fromisoformat(date_str).date()
                    except Exception:
                        metrics['rows_skipped'] += 1
                        continue
                    points_record = StudentPoints(
                        student_id=student_db.id,
                        date_recorded=date_recorded,
                        points=points,
                        stars=stars,
                        vetos=vetos,
                        notes=notes,
                        recorded_by=recorded_by,
                        entry_type=entry_type
                    )
                    db.session.add(points_record)
                    metrics['scores_created'] += 1
            
            db.session.commit()
            metrics['status'] = 'completed'
            metrics['duration_ms'] = round((perf_counter() - started_at) * 1000, 2)
            app.logger.info(
                'JSON-to-SQL reconciliation completed',
                extra={'event_type': 'json_sql_reconciliation', 'metrics': metrics}
            )
            
        except Exception:
            db.session.rollback()
            metrics['status'] = 'failed'
            metrics['duration_ms'] = round((perf_counter() - started_at) * 1000, 2)
            app.logger.exception(
                'JSON-to-SQL reconciliation failed; application startup will continue',
                extra={'event_type': 'json_sql_reconciliation_failure', 'metrics': metrics}
            )



def _bootstrap_auth_defaults(app):
    """
    Ensure auth tables and core users exist even when booted via Gunicorn/Wsgi entrypoints.
    This prevents login 500s on fresh/misaligned production databases.
    """
    from app.models import User

    with app.app_context():
        db.create_all()
        admin_password = os.getenv('ADMIN_PASSWORD', 'ChangeAdminPass123!')
        teacher_password = os.getenv('TEACHER_PASSWORD', 'ChangeTeacherPass123!')
        defaults = (
            ('Admin', 'admin', admin_password),
            ('Teacher', 'teacher', teacher_password),
        )
        for login_id, role, password in defaults:
            user = User.query.filter_by(login_id=login_id).first()
            if not user:
                user = User(login_id=login_id, role=role, first_login=False, is_active=True)
                user.set_password(password)
                db.session.add(user)
            else:
                user.role = role
                user.is_active = True
        db.session.commit()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    database_url = os.getenv('DATABASE_URL', 'sqlite:///ea_tutorial.db')
    # Many managed platforms still provide postgres://; SQLAlchemy needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
    engine_options = {
        'pool_pre_ping': True
    }
    if database_url.startswith('sqlite'):
        engine_options['connect_args'] = {'timeout': 15}
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options
    # LAN deployment: allow unlimited/repeated requests from classroom devices.
    # Set ENABLE_RATE_LIMITING=1 in environment if you want throttling again.
    app.config['RATELIMIT_ENABLED'] = str(os.getenv('ENABLE_RATE_LIMITING', '0')).strip().lower() in ('1', 'true', 'yes', 'on')

    # Session security configuration
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_COOKIE_SECURE'] = str(os.getenv('SESSION_COOKIE_SECURE', 'False')).lower() in ('true', '1', 'yes')
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    app.config['REMEMBER_COOKIE_SECURE'] = str(os.getenv('SESSION_COOKIE_SECURE', 'False')).lower() in ('true', '1', 'yes')
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
    
    # Initialize extensions
    db.init_app(app)
    if database_url.startswith('sqlite'):
        from sqlalchemy import event as _sa_event
        with app.app_context():
            @_sa_event.listens_for(db.engine, 'connect')
            def _set_sqlite_pragmas(dbapi_conn, _record):
                cursor = dbapi_conn.cursor()
                try:
                    cursor.execute('PRAGMA journal_mode=WAL')
                    cursor.execute('PRAGMA busy_timeout=15000')
                    cursor.execute('PRAGMA synchronous=NORMAL')
                finally:
                    cursor.close()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)
    limiter.init_app(app)
    Compress(app)  # gzip/brotli for HTML, JSON, CSS, JS
    
    # Setup global error handlers and logging
    from app.utils.logger import setup_logging, log_request_info, log_response_info
    from app.utils.error_handler import register_error_handlers
    try:
        setup_logging(app)
    except Exception as e:
        # Fallback if new logging fails
        print(f"Warning: New logging system failed to initialize: {e}")
        import logging
        logging.basicConfig(level=logging.INFO)
    register_error_handlers(app)

    process_workers = _configured_process_workers()
    if process_workers > 1:
        app.logger.critical(
            'File-ledger deployment configured with %s worker processes; use one process to prevent lost updates',
            process_workers,
            extra={
                'event_type': 'unsafe_worker_configuration',
                'configured_process_workers': process_workers,
            }
        )
    
    # Add request/response logging middleware — but skip noisy paths (static
    # assets, favicon, health checks). Each structured-log entry involves a
    # synchronous JSON serialize + rotating-file write; logging every static
    # request during a page load added dozens of disk writes per tab switch.
    def _should_skip_access_log():
        try:
            p = request.path or ''
        except Exception:
            return False
        if p.startswith('/static/'):
            return True
        if p == '/favicon.ico' or p.endswith('/favicon.ico'):
            return True
        if p == '/healthz' or p == '/health':
            return True
        return False

    def _log_request_filtered():
        if _should_skip_access_log():
            return
        log_request_info()

    def _log_response_filtered(response):
        if _should_skip_access_log():
            return response
        return log_response_info(response)

    app.before_request(_log_request_filtered)
    app.after_request(_log_response_filtered)

    # Force browsers to always re-fetch HTML pages (never serve from cache).
    # This ensures inline CSS/JS changes in templates (e.g. sidebar checkbox hack)
    # are picked up immediately, even on mobile browsers that aggressively cache.
    @app.after_request
    def _no_store_html(response):
        # Safety net for Jinja pages that set no Cache-Control of their own.
        # Routes with an explicit policy (e.g. /scoreboard/offline's ETag
        # revalidation) are left untouched.
        ct = response.content_type or ''
        if 'text/html' in ct and 'Cache-Control' not in response.headers:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    # Trust Railway / Render / any single reverse-proxy hop so Flask sees
    # the real HTTPS scheme and host (fixes Secure cookie + redirect URLs).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Create upload folder if not exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.scoreboard import points_bp
    from app.routes.veto_api import veto_bp
    from app.routes.star_validation import star_bp
    from app.routes.favicon import favicon_bp
    from app.routes.notebook import notebook_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(points_bp)
    app.register_blueprint(veto_bp)
    app.register_blueprint(star_bp)
    app.register_blueprint(favicon_bp)
    app.register_blueprint(notebook_bp)

    @app.route('/')
    def home():
        return redirect(url_for('points.public_scoreboard'))

    @app.route('/ea')
    def ea_shortlink():
        return redirect(url_for('points.public_scoreboard'))

    @app.route('/login')
    def login_shortlink():
        return redirect(url_for('auth.login'))

    @app.context_processor
    def _inject_static_v():
        """Append file mtime as ?v= to bust browser caches when assets change."""
        def static_v(filename):
            filepath = os.path.join(app.static_folder, filename)
            try:
                mtime = str(int(os.path.getmtime(filepath)))
            except OSError:
                mtime = '0'
            return url_for('static', filename=filename) + '?v=' + mtime
        return dict(static_v=static_v)

    @app.before_request
    def check_default_password():
        if current_user.is_authenticated and current_user.login_id == 'Admin':
            # bcrypt verification costs ~100-300ms; cache the result per session
            # instead of re-hashing on EVERY admin request. The flag resets on
            # login/logout (new session), so a password change is re-detected.
            cached = session.get('_admin_default_pw')
            if cached is None:
                try:
                    cached = bool(current_user.check_password('admin123'))
                except Exception:
                    cached = False
                session['_admin_default_pw'] = cached
            if cached:
                flash('CRITICAL: You are using the default admin password ("admin123"). Please change it immediately for security reasons.', 'danger')

    # User loader
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            uid = int(str(user_id))
        except Exception:
            return None

        if uid == -1:
            return make_ephemeral_user('admin')
        if uid == -2:
            return make_ephemeral_user('teacher')

        try:
            return User.query.get(uid)
        except Exception:
            db.session.rollback()
            # ORM can fail on partially migrated schemas; use raw fallback to keep sessions usable.
            try:
                with db.engine.connect() as conn:
                    row = conn.execute(
                        text("SELECT * FROM users WHERE id = :id LIMIT 1"),
                        {'id': uid}
                    ).mappings().first()
                if not row:
                    return None
                login_id = str(row.get('login_id') or '')
                role = str(row.get('role') or 'student')
                active_val = row.get('is_active')
                is_active = True if active_val is None else bool(active_val)
                return EphemeralUser(uid, login_id, role, is_active)
            except Exception:
                return None

    # Defensive bootstrap for production entrypoints (Render/Gunicorn).
    if str(os.getenv('EA_DB_AUTO_INIT', '1')).strip().lower() in ('1', 'true', 'yes', 'on'):
        try:
            _bootstrap_auth_defaults(app)
        except SQLAlchemyError:
            # Keep app booting; auth route has additional DB guards.
            app.logger.exception(
                'Authentication database bootstrap failed; application startup will continue',
                extra={'event_type': 'auth_bootstrap_failure'}
            )
        try:
            _migrate_notebook_schema(app)
        except Exception:
            app.logger.exception(
                'Schema bootstrap failed; application startup will continue',
                extra={'event_type': 'schema_bootstrap_failure'}
            )
    
    @app.before_request
    def _token_auth_for_cross_origin():
        """Authenticate cross-origin SPA requests via X-EA-Login-ID / X-EA-Login-Code headers.

        When a trusted cross-origin request carries valid token headers, log the
        user in programmatically so @login_required and current_user work without
        session cookies. This is a no-op for same-origin requests (which use
        cookies) and for requests that are already authenticated.
        """
        if current_user.is_authenticated:
            return
        origin = request.headers.get('Origin', '')
        if not origin or not _is_trusted_cors_origin(origin):
            return
        if request.method == 'OPTIONS':
            return  # preflight handled by handle_options_preflight below
        login_id = request.headers.get('X-EA-Login-ID', '').strip()
        login_code = request.headers.get('X-EA-Login-Code', '').strip()
        if not login_id or not login_code:
            return
        from app.models import User
        from datetime import datetime as _dt
        try:
            user = User.query.filter_by(login_id=login_id).first()
            if user and user.is_active and user.login_code == login_code:
                expires_at = user.login_code_expires_at
                if expires_at is None or expires_at > _dt.utcnow():
                    login_manager.login_user(user, remember=False)
                    session.permanent = False
                    return
        except Exception:
            db.session.rollback()

    @app.before_request
    def handle_options_preflight():
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            return response

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if _is_trusted_cors_origin(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-EA-Login-ID, X-EA-Login-Code, X-EA-Replicated, X-EA-Sync-Key'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            existing_vary = response.headers.get('Vary')
            response.headers['Vary'] = f'{existing_vary}, Origin' if existing_vary else 'Origin'
        # Untrusted origins get NO CORS grant. Same-origin requests (the normal
        # LAN/tunnel SPA usage) never need CORS headers at all. The previous
        # fallback of '*' combined with Allow-Credentials was spec-invalid and
        # the substring origin checks were bypassable.
        return response

    return app

# Provide a direct WSGI app object for platforms that target "app:app".
# Runtime initialization is handled by wsgi.py / app.py / run.py entrypoints.
app = create_app()
