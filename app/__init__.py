import os
from flask import Flask, redirect, url_for, request, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True
    }
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
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Setup global error handlers and logging
    from app.utils.error_handler import register_error_handlers, setup_logging
    setup_logging(app)
    register_error_handlers(app)
    
    # Create upload folder if not exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.scoreboard import points_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(points_bp)

    @app.route('/')
    def home():
        return redirect(url_for('points.public_scoreboard'))

    @app.route('/ea')
    def ea_shortlink():
        return redirect(url_for('points.public_scoreboard'))

    @app.route('/login')
    def login_shortlink():
        return redirect(url_for('auth.login'))
    
    @app.before_request
    def check_default_password():
        if current_user.is_authenticated and current_user.login_id == 'Admin':
            # Use a known default password that is unlikely to be chosen by a user
            if current_user.check_password('admin123'):
                flash('CRITICAL: You are using the default admin password ("admin123"). Please change it immediately for security reasons.', 'danger')

    # User loader
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return app

# Provide a direct WSGI entrypoint for platforms that use "gunicorn app:app".
# This avoids Render misconfiguration issues when it targets the package name.
app = create_app()
if str(os.getenv('EA_INIT_ON_BOOT', '1')).strip().lower() in ('1', 'true', 'yes', 'on'):
    try:
        from run import initialize_runtime
        initialize_runtime(app)
    except Exception:
        # Fallback: app should still load even if runtime init fails here.
        pass
