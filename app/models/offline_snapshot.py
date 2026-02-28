from app import db


class OfflineSnapshot(db.Model):
    """
    Persistent store for the offline scoreboard JSON blob.
    Used as a fallback when Render's ephemeral filesystem wipes
    the JSON file on redeploy — the database survives restarts
    as long as a persistent backend (e.g. Supabase PostgreSQL) is
    configured via DATABASE_URL.
    Only the single most-recent healthy snapshot is kept (id=1).
    """
    __tablename__ = 'offline_snapshot'

    id = db.Column(db.Integer, primary_key=True)
    data_json = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.String(64), default='')
    student_count = db.Column(db.Integer, default=0)
