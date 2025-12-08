from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.notes import notes_bp
from app.routes.quiz import quiz_bp
from app.routes.quiz_ai import quiz_ai_bp
from app.routes.admin import admin_bp
from app.routes.profile_viewer import profile_viewer_bp
from app.routes.scoreboard import points_bp

__all__ = [
    'auth_bp', 'dashboard_bp', 'notes_bp', 'quiz_bp',
    'quiz_ai_bp', 'admin_bp', 'profile_viewer_bp', 'points_bp'
]
