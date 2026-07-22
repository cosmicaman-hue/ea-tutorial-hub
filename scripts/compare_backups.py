"""
Compare backup files vs current DB.
Reports: student-list mismatches, missing scores (Mar 27 – Apr 4, 2026).
Read-only – no writes.
"""
import json, sqlite3, os, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
from app.utils.data_paths import get_data_path

CURRENT_DB   = get_data_path()
JSON_BACKUPS = [
    r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\ops_daily_backups\json\offline_scoreboard_data_20260401_092140.json',
    r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\ops_daily_backups\json\offline_scoreboard_data_20260404_085247.json',
]
DB_BACKUPS = [
    r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\ops_daily_backups\db\ea_tutorial_20260401_221505.db',
    r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\ops_daily_backups\db\ea_tutorial_20260404_221507.db',
]
SCORE_RANGE_START = '2026-03-27'
SCORE_RANGE_END   = '2026-04-04'

# ── helpers ───────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def student_key(s):
    """Stable identifier for comparison: prefer (id, roll, base_name)."""
    return (int(s.get('id') or 0), str(s.get('roll') or ''), str(s.get('base_name') or s.get('name') or ''))

def student_summary(s):
    return f"id={s.get('id')}  roll={s.get('roll')}  name={s.get('base_name') or s.get('name')}  active={s.get('active')}  deact={s.get('deactivation_month')}"

def scores_in_range(scores):
    return [sc for sc in scores
            if SCORE_RANGE_START <= str(sc.get('date', '')) <= SCORE_RANGE_END]

def student_map_from_list(lst):
    """id → student dict"""
    return {int(s.get('id') or 0): s for s in lst if s.get('id')}

def score_set(scores):
    """Set of (studentId, date, points) for quick diff."""
    return {(int(sc.get('studentId') or 0), str(sc.get('date', '')), int(sc.get('points') or 0))
            for sc in scores}

# ── load current ──────────────────────────────────────────────────────────────
print("=" * 70)
print("CURRENT DB:", CURRENT_DB)
current = load_json(CURRENT_DB)
curr_students = current.get('students', [])
curr_scores   = current.get('scores', [])
curr_smap     = student_map_from_list(curr_students)
curr_range_scores = scores_in_range(curr_scores)
print(f"  Students: {len(curr_students)}   Total scores: {len(curr_scores)}")
print(f"  Scores in {SCORE_RANGE_START}–{SCORE_RANGE_END}: {len(curr_range_scores)}")

# ── process each JSON backup ──────────────────────────────────────────────────
for path in JSON_BACKUPS:
    label = os.path.basename(path)
    print("\n" + "=" * 70)
    print(f"JSON BACKUP: {label}")
    if not os.path.exists(path):
        print("  FILE NOT FOUND"); continue
    bk = load_json(path)
    bk_students = bk.get('students', [])
    bk_scores   = bk.get('scores', [])
    bk_smap     = student_map_from_list(bk_students)
    bk_range    = scores_in_range(bk_scores)

    print(f"  Students: {len(bk_students)}   Total scores: {len(bk_scores)}")
    print(f"  Scores in {SCORE_RANGE_START}–{SCORE_RANGE_END}: {len(bk_range)}")

    # --- student diff ---
    curr_ids = set(curr_smap.keys())
    bk_ids   = set(bk_smap.keys())
    in_curr_not_bk = curr_ids - bk_ids
    in_bk_not_curr = bk_ids   - curr_ids

    if in_curr_not_bk:
        print(f"\n  Students in CURRENT but NOT in backup ({len(in_curr_not_bk)}):")
        for sid in sorted(in_curr_not_bk):
            print(f"    {student_summary(curr_smap[sid])}")
    else:
        print("  No students missing from backup (vs current) by ID.")

    if in_bk_not_curr:
        print(f"\n  Students in BACKUP but NOT in current ({len(in_bk_not_curr)}):")
        for sid in sorted(in_bk_not_curr):
            print(f"    {student_summary(bk_smap[sid])}")
    else:
        print("  No extra students in backup (vs current) by ID.")

    # --- check active/deactivation differences for matching IDs ---
    common = curr_ids & bk_ids
    field_diffs = []
    for sid in sorted(common):
        cs, bs = curr_smap[sid], bk_smap[sid]
        for field in ('active', 'deactivation_month', 'active_from_month', 'roll', 'base_name'):
            cv, bv = cs.get(field), bs.get(field)
            if cv != bv:
                field_diffs.append((sid, cs.get('base_name') or cs.get('name'), field, bv, cv))
    if field_diffs:
        print(f"\n  Field differences on matching students ({len(field_diffs)}):")
        for sid, name, field, bv, cv in field_diffs:
            print(f"    id={sid} ({name})  {field}: backup={bv!r}  current={cv!r}")
    else:
        print("  No field differences on matching students.")

    # --- score range diff ---
    curr_rset = score_set(curr_range_scores)
    bk_rset   = score_set(bk_range)
    in_bk_not_curr_s = bk_rset - curr_rset
    in_curr_not_bk_s = curr_rset - bk_rset
    if in_bk_not_curr_s:
        print(f"\n  Scores in BACKUP range NOT in current ({len(in_bk_not_curr_s)}):")
        for (sid, date, pts) in sorted(in_bk_not_curr_s):
            name = (bk_smap.get(sid) or {}).get('base_name') or (bk_smap.get(sid) or {}).get('name') or '?'
            print(f"    studentId={sid} ({name})  date={date}  pts={pts}")
    else:
        print(f"  All backup range scores are in current.")
    if in_curr_not_bk_s:
        print(f"\n  Scores in CURRENT range NOT in backup ({len(in_curr_not_bk_s)}):")
        for (sid, date, pts) in sorted(in_curr_not_bk_s):
            name = (curr_smap.get(sid) or {}).get('base_name') or (curr_smap.get(sid) or {}).get('name') or '?'
            print(f"    studentId={sid} ({name})  date={date}  pts={pts}")
    else:
        print(f"  All current range scores are in backup.")

# ── process each SQLite backup ────────────────────────────────────────────────
for path in DB_BACKUPS:
    label = os.path.basename(path)
    print("\n" + "=" * 70)
    print(f"SQLITE BACKUP: {label}")
    if not os.path.exists(path):
        print("  FILE NOT FOUND"); continue
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # List tables
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"  Tables: {tables}")

    # Try to read scoreboard data from the db – it's stored in a key-value table
    data = None
    for tname in tables:
        try:
            cols = [r[1] for r in cur.execute(f"PRAGMA table_info({tname})").fetchall()]
            if 'value' in cols and 'key' in cols:
                row = cur.execute(f"SELECT value FROM {tname} WHERE key='scoreboard_data' LIMIT 1").fetchone()
                if row:
                    data = json.loads(row[0])
                    print(f"  Found scoreboard_data in table '{tname}'")
                    break
            # Also try to find a blob/text column named 'data' or 'json'
            for ccol in ('data', 'json', 'content'):
                if ccol in cols:
                    row = cur.execute(f"SELECT {ccol} FROM {tname} LIMIT 1").fetchone()
                    if row and row[0] and isinstance(row[0], str) and row[0].startswith('{'):
                        try:
                            data = json.loads(row[0])
                            if 'students' in data:
                                print(f"  Found scoreboard_data in table '{tname}', col '{ccol}'")
                                break
                        except Exception:
                            pass
            if data:
                break
        except Exception as e:
            print(f"  Error reading {tname}: {e}")

    if data is None:
        # Dump first few rows of each table for inspection
        print("  Could not locate scoreboard_data. Showing table row counts:")
        for tname in tables:
            try:
                cnt = cur.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
                print(f"    {tname}: {cnt} rows")
                # Show column names
                cols = [r[1] for r in cur.execute(f"PRAGMA table_info({tname})").fetchall()]
                print(f"      columns: {cols}")
                # Show a sample
                rows = cur.execute(f"SELECT * FROM {tname} LIMIT 3").fetchall()
                for rr in rows:
                    safe = {k: (str(v)[:80] + '…' if isinstance(v, str) and len(str(v)) > 80 else v)
                            for k, v in dict(rr).items()}
                    print(f"      sample: {safe}")
            except Exception as e:
                print(f"    {tname}: error {e}")
        con.close()
        continue

    bk_students = data.get('students', [])
    bk_scores   = data.get('scores', [])
    bk_smap     = student_map_from_list(bk_students)
    bk_range    = scores_in_range(bk_scores)

    print(f"  Students: {len(bk_students)}   Total scores: {len(bk_scores)}")
    print(f"  Scores in {SCORE_RANGE_START}–{SCORE_RANGE_END}: {len(bk_range)}")

    curr_ids = set(curr_smap.keys())
    bk_ids   = set(bk_smap.keys())
    in_curr_not_bk = curr_ids - bk_ids
    in_bk_not_curr = bk_ids   - curr_ids

    if in_curr_not_bk:
        print(f"\n  Students in CURRENT but NOT in backup ({len(in_curr_not_bk)}):")
        for sid in sorted(in_curr_not_bk):
            print(f"    {student_summary(curr_smap[sid])}")
    else:
        print("  No students missing from backup (vs current) by ID.")

    if in_bk_not_curr:
        print(f"\n  Students in BACKUP but NOT in current ({len(in_bk_not_curr)}):")
        for sid in sorted(in_bk_not_curr):
            print(f"    {student_summary(bk_smap[sid])}")
    else:
        print("  No extra students in backup (vs current) by ID.")

    common = curr_ids & bk_ids
    field_diffs = []
    for sid in sorted(common):
        cs, bs = curr_smap[sid], bk_smap[sid]
        for field in ('active', 'deactivation_month', 'active_from_month', 'roll', 'base_name'):
            cv, bv = cs.get(field), bs.get(field)
            if cv != bv:
                field_diffs.append((sid, cs.get('base_name') or cs.get('name'), field, bv, cv))
    if field_diffs:
        print(f"\n  Field differences on matching students ({len(field_diffs)}):")
        for sid, name, field, bv, cv in field_diffs:
            print(f"    id={sid} ({name})  {field}: backup={bv!r}  current={cv!r}")
    else:
        print("  No field differences on matching students.")

    curr_rset = score_set(curr_range_scores)
    bk_rset   = score_set(bk_range)
    in_bk_not_curr_s = bk_rset - curr_rset
    in_curr_not_bk_s = curr_rset - bk_rset
    if in_bk_not_curr_s:
        print(f"\n  Scores in BACKUP range NOT in current ({len(in_bk_not_curr_s)}):")
        for (sid, date, pts) in sorted(in_bk_not_curr_s):
            name = (bk_smap.get(sid) or {}).get('base_name') or (bk_smap.get(sid) or {}).get('name') or '?'
            print(f"    studentId={sid} ({name})  date={date}  pts={pts}")
    else:
        print(f"  All backup range scores are in current.")
    if in_curr_not_bk_s:
        print(f"\n  Scores in CURRENT range NOT in backup ({len(in_curr_not_bk_s)}):")
        for (sid, date, pts) in sorted(in_curr_not_bk_s):
            name = (curr_smap.get(sid) or {}).get('base_name') or (curr_smap.get(sid) or {}).get('name') or '?'
            print(f"    studentId={sid} ({name})  date={date}  pts={pts}")
    else:
        print(f"  All current range scores are in backup.")

    con.close()

print("\n" + "=" * 70)
print("DONE.")
