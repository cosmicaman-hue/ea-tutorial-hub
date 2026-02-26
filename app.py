import os
from run import app, initialize_runtime

# Compatibility entrypoint for platforms that use "gunicorn app:app".
# Keep behavior aligned with wsgi.py so runtime bootstraps consistently.
if str(os.getenv('EA_INIT_ON_BOOT', '1')).strip().lower() in ('1', 'true', 'yes', 'on'):
    initialize_runtime(app)

