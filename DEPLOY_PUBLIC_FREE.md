# Public Deployment (No Play Store, No Paid Domain)

This project can be publicly accessible as a web app (PWA) using a free subdomain.

## What You Get
- Public URL like `https://project-ea.onrender.com`
- Installable on phones/desktops from browser (Add to Home Screen)
- No Play Store listing needed
- No custom domain purchase required

## Files Already Added
- `render.yaml`
- `Procfile`
- `wsgi.py`
- `runtime.txt`
- Production dependencies in `requirements.txt` (`gunicorn`, `psycopg2-binary`)

## Deploy on Render (Free)
1. Push this repo to GitHub.
2. Go to Render dashboard and create a new Blueprint deploy.
3. Select this repo.
4. Render auto-detects `render.yaml`.
5. Set required env values during deploy:
   - `ADMIN_PASSWORD`
   - `TEACHER_PASSWORD`
   - `SYNC_SHARED_KEY` (long random string)
6. Deploy.

## If Postgres Free Tier Is Unavailable
- In `render.yaml`, change DB service plan:
  - `project-ea-db` -> `plan: starter`
- Re-deploy Blueprint.
- `DATABASE_URL` mapping is already configured automatically from DB service to web service.

## Important Data Note
- If you use default SQLite (`DATABASE_URL` not set), filesystem on free plans can reset and you can lose saved data.
- For public real usage, connect a persistent PostgreSQL database by setting `DATABASE_URL`.

## Suggested Safe Minimum for Public Use
- Keep this web service on Render.
- Use managed PostgreSQL (`DATABASE_URL`).
- Keep periodic JSON backups from the Tools/backup flows.

## Post-Deploy Checks
1. Open deployed URL and login as admin.
2. Confirm Students, Scoreboard, Leadership, Parties load.
3. Add one test score entry, refresh in another device/browser.
4. Confirm sync status shows online and data remains after restart/redeploy.
