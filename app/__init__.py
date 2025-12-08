import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ea_tutorial.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Create upload folder if not exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.admin import admin_bp
    from app.routes.notes import notes_bp
    from app.routes.quiz import quiz_bp
    from app.routes.quiz_ai import quiz_ai_bp
    from app.routes.profile_viewer import profile_viewer_bp
    from app.routes.scoreboard import points_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(quiz_ai_bp)
    app.register_blueprint(profile_viewer_bp)
    app.register_blueprint(points_bp)
    
    # User loader
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return app
