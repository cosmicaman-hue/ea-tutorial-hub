import os
from app import create_app, db
from app.models import User, StudentProfile, Notes, Quiz, QuizQuestion, QuizAnswer, ActivityLog

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'StudentProfile': StudentProfile,
        'Notes': Notes,
        'Quiz': Quiz,
        'QuizQuestion': QuizQuestion,
        'QuizAnswer': QuizAnswer,
        'ActivityLog': ActivityLog
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
