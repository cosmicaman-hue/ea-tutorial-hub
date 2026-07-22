import json, re, sys, os
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
from app.utils.data_paths import get_data_path

DB_PATH = get_data_path()

with open(DB_PATH, 'r', encoding='utf-8') as f:
    db = json.load(f)

def base_name(raw):
    """Strip Option B decorations for clean display."""
    s = re.sub(r'\*\d+', '', str(raw or ''))   # remove *N
    s = re.sub(r'\bV\d+\b', '', s)             # remove V1, V2 etc.
    s = re.sub(r'(?<!\w)[vV]+(?!\w)', '', s)   # remove standalone v/V
    s = re.sub(r'\([^)]*\)', '', s)             # remove (...) suffixes
    return re.sub(r'\s+', ' ', s).strip()

students = db['students']
active   = sorted([s for s in students if s.get('active', True)],  key=lambda x: x.get('roll',''))
inactive = sorted([s for s in students if not s.get('active', True)], key=lambda x: x.get('roll',''))

COL = {'no':4, 'roll':10, 'name':32, 'class':6, 'month':14}
HDR = f"{'#':>{COL['no']}}  {'Roll':<{COL['roll']}}  {'Name':<{COL['name']}}  {'Class':^{COL['class']}}  {'Effective From':<{COL['month']}}"
SEP = '-' * (sum(COL.values()) + 8)

# ── ACTIVE ──────────────────────────────────────────────────────────────────
print(f"\n{'='*len(SEP)}")
print(f"  ACTIVE STUDENTS ({len(active)})  —  present in Jan 2026, continuing to Feb 2026+")
print(f"{'='*len(SEP)}")
print(HDR)
print(SEP)
for i, s in enumerate(active, 1):
    name  = base_name(s.get('base_name') or s.get('name') or s.get('roll',''))[:COL['name']]
    roll  = s.get('roll', 'N/A')
    cls   = str(s.get('class', '') or '-')
    month = s.get('active_from_month') or s.get('last_month_appeared') or '2024-08'
    print(f"{i:>{COL['no']}}  {roll:<{COL['roll']}}  {name:<{COL['name']}}  {cls:^{COL['class']}}  {month:<{COL['month']}}")

# ── INACTIVE ─────────────────────────────────────────────────────────────────
print(f"\n{'='*len(SEP)}")
print(f"  INACTIVE / DEACTIVATED STUDENTS ({len(inactive)})  —  left before Feb 2026")
print(f"{'='*len(SEP)}")
HDR2 = f"{'#':>{COL['no']}}  {'Roll':<{COL['roll']}}  {'Name':<{COL['name']}}  {'Class':^{COL['class']}}  {'Inactive From':<{COL['month']}}"
print(HDR2)
print(SEP)
for i, s in enumerate(inactive, 1):
    name  = base_name(s.get('base_name') or s.get('name') or s.get('roll',''))[:COL['name']]
    roll  = s.get('roll', 'N/A')
    cls   = str(s.get('class', '') or '-')
    month = s.get('deactivation_month', '?')
    print(f"{i:>{COL['no']}}  {roll:<{COL['roll']}}  {name:<{COL['name']}}  {cls:^{COL['class']}}  {month:<{COL['month']}}")

print(f"\n{'='*len(SEP)}")
print(f"  Total: {len(students)}  |  Active: {len(active)}  |  Inactive: {len(inactive)}")
print(f"{'='*len(SEP)}\n")
