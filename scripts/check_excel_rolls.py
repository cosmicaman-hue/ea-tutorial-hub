import json, re, sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
from app.utils.data_paths import get_data_path

DB_PATH = get_data_path()
BACKUP_PATH = r'instance\BACKUP_FEB_APR_2026_20260405_134210.json'

with open(DB_PATH, 'r', encoding='utf-8') as f:
    db = json.load(f)

with open(BACKUP_PATH, 'r', encoding='utf-8') as f:
    backup = json.load(f)

db_rolls = set(s['roll'] for s in db['students'] if s.get('roll'))
backup_unique_rolls = set(s['roll'] for s in backup['students'] if s.get('roll'))

print(f"DB students: {len(db['students'])} | unique rolls: {len(db_rolls)}")
print(f"Backup unique rolls: {len(backup_unique_rolls)}")

only_in_backup = backup_unique_rolls - db_rolls
only_in_db = db_rolls - backup_unique_rolls
in_both = db_rolls & backup_unique_rolls

print(f"\nIn both: {len(in_both)}")
print(f"Only in DB (not in backup): {len(only_in_db)} → {sorted(only_in_db)}")
print(f"\nOnly in backup (missing from DB): {len(only_in_backup)}")
for r in sorted(only_in_backup):
    bname = next((s.get('name','') for s in backup['students'] if s.get('roll')==r), '')
    print(f"  {r}: {bname}")
