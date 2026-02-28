import os
from run import app, initialize_runtime

# Ensure startup initialization also runs under Gunicorn (non-__main__ path).
if str(os.getenv('EA_INIT_ON_BOOT', '1')).strip().lower() in ('1', 'true', 'yes', 'on'):
    try:
        initialize_runtime(app)
    except Exception:
        pass  # App must boot even if DB init fails; routes handle DB errors gracefully

