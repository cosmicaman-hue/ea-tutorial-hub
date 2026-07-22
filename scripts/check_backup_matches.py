import json
import re
import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
from app.utils.data_paths import get_data_path

def canonical_name(raw):
    if not raw:
        return ""
    name = str(raw)
    name = re.sub(r'\*+', '', name)
    name = re.sub(r'\s*\([^)]*\)\s*', ' ', name)
    name = re.sub(r'(?<!\w)[vV]+(?!\w)', ' ', name)
    name = re.sub(r'[/\\]+', ' ', name)
    name = re.sub(r'\d+', '', name)
    name = re.sub(r'[^\w\s]', '', name)
    return re.sub(r'\s+', ' ', name).strip().lower()

# Load current database (after rebuild)
with open(get_data_path(), 'r', encoding='utf-8') as f:
    db = json.load(f)

# Load backup
with open(r'instance\BACKUP_FEB_APR_2026_20260405_134210.json', 'r', encoding='utf-8') as f:
    backup = json.load(f)

# Build canonical map from rebuilt DB
rebuilt_canonical = {}
for s in db['students']:
    cname = canonical_name(s.get('name', '') or s.get('base_name', ''))
    if cname:
        rebuilt_canonical[cname] = s

# Check backup students
matched = 0
unmatched = []
for bs in backup['students']:
    cname = canonical_name(bs.get('name', '') or bs.get('base_name', ''))
    if cname in rebuilt_canonical:
        matched += 1
    else:
        unmatched.append({
            'name': bs.get('name', ''),
            'base_name': bs.get('base_name', ''),
            'roll': bs.get('roll', ''),
            'canonical': cname,
            'active': bs.get('active', True)
        })

print(f"Backup students: {len(backup['students'])}")
print(f"Matched to rebuilt DB: {matched}")
print(f"Unmatched: {len(unmatched)}\n")

if unmatched:
    print("First 20 unmatched students:")
    for u in unmatched[:20]:
        print(f"  {u['name']} ({u['roll']}) → canonical: '{u['canonical']}' | active: {u['active']}")
