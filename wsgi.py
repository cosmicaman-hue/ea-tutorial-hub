import os
from run import app, initialize_runtime

# Ensure startup initialization also runs under Gunicorn (non-__main__ path).
if str(os.getenv('EA_INIT_ON_BOOT', '1')).strip().lower() in ('1', 'true', 'yes', 'on'):
    initialize_runtime(app)

