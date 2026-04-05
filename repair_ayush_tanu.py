"""
Final definitive fix for Ayush and Tanu scoreboard data corruption.

This script:
1. Ensures students are correctly configured (roll, active status)
2. Ensures roll_history is populated for bridging old→new rolls
3. Aligns month_students rosters
4. Bumps server_version and server_updated_at to force ALL browsers to pull fresh
5. Removes the _app_schema_version so browsers re-run schema migrations
"""
import json
import shutil
from datetime import datetime, timezone

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'
BACKUP_PATH = DATA_PATH + f'.bak_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

def normalize_roll(r):
    return str(r or '').upper().strip()

OLD_AYUSH_ROLL = "EA24A01"
NEW_AYUSH_ROLL = "EA24B15"
OLD_TANU_ROLL  = "EA24A04"
NEW_TANU_ROLL  = "EA24B16"
AYUSH_ID = 1
TANU_ID  = 4

def repair():
    print(f"Loading data...")
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    shutil.copy2(DATA_PATH, BACKUP_PATH)
    print(f"Backup saved to {BACKUP_PATH}")

    # ── 1. Student records ────────────────────────────────────────────────────
    students = data.get('students', [])
    ayush = next((s for s in students if s.get('id') == AYUSH_ID), None)
    tanu  = next((s for s in students if s.get('id') == TANU_ID),  None)

    if ayush:
        ayush['roll']   = NEW_AYUSH_ROLL
        ayush['active'] = True
        ayush.pop('deactivation_reason', None)
        ayush.pop('retired_reason', None)
        print(f"  Ayush (ID {AYUSH_ID}): roll={NEW_AYUSH_ROLL}, active=True")
    else:
        print("  ERROR: Ayush (ID 1) not found!")

    if tanu:
        tanu['roll']   = NEW_TANU_ROLL
        tanu['active'] = True
        tanu.pop('deactivation_reason', None)
        tanu.pop('retired_reason', None)
        print(f"  Tanu  (ID {TANU_ID}):  roll={NEW_TANU_ROLL}, active=True")
    else:
        print("  ERROR: Tanu (ID 4) not found!")

    # ── 2. Roll history (idempotent) ──────────────────────────────────────────
    if 'roll_history' not in data:
        data['roll_history'] = []

    def has_history(old, new):
        return any(
            normalize_roll(h.get('old_roll')) == old and normalize_roll(h.get('new_roll')) == new
            for h in data['roll_history']
        )

    if not has_history(OLD_AYUSH_ROLL, NEW_AYUSH_ROLL):
        data['roll_history'].append({
            "old_roll": OLD_AYUSH_ROLL, "new_roll": NEW_AYUSH_ROLL,
            "effective_month": "2026-04", "reason": "Batch Re-assignment", "student_id": AYUSH_ID
        })
        print(f"  Roll history: {OLD_AYUSH_ROLL} → {NEW_AYUSH_ROLL}")

    if not has_history(OLD_TANU_ROLL, NEW_TANU_ROLL):
        data['roll_history'].append({
            "old_roll": OLD_TANU_ROLL, "new_roll": NEW_TANU_ROLL,
            "effective_month": "2026-04", "reason": "Batch Re-assignment", "student_id": TANU_ID
        })
        print(f"  Roll history: {OLD_TANU_ROLL} → {NEW_TANU_ROLL}")

    # ── 3. Month rosters ──────────────────────────────────────────────────────
    month_students = data.get('month_students', {})
    for month, roster in month_students.items():
        if not isinstance(roster, list):
            continue
        if month < "2026-04":
            # Historical: must have OLD rolls, not new ones
            changed_ayush = changed_tanu = False
            if NEW_AYUSH_ROLL in roster:
                roster.remove(NEW_AYUSH_ROLL)
                if OLD_AYUSH_ROLL not in roster:
                    roster.append(OLD_AYUSH_ROLL)
                changed_ayush = True
            if NEW_TANU_ROLL in roster:
                roster.remove(NEW_TANU_ROLL)
                if OLD_TANU_ROLL not in roster:
                    roster.append(OLD_TANU_ROLL)
                changed_tanu = True
            if changed_ayush or changed_tanu:
                print(f"  Fixed month_students[{month}]: reverted to old rolls")
        else:
            # Current/future: must have NEW rolls
            changed_ayush = changed_tanu = False
            if OLD_AYUSH_ROLL in roster:
                roster.remove(OLD_AYUSH_ROLL)
                if NEW_AYUSH_ROLL not in roster:
                    roster.append(NEW_AYUSH_ROLL)
                changed_ayush = True
            if OLD_TANU_ROLL in roster:
                roster.remove(OLD_TANU_ROLL)
                if NEW_TANU_ROLL not in roster:
                    roster.append(NEW_TANU_ROLL)
                changed_tanu = True
            if changed_ayush or changed_tanu:
                print(f"  Fixed month_students[{month}]: promoted to new rolls")

    # ── 4. Month roster profiles: ensure studentId is set ────────────────────
    month_profiles = data.get('month_roster_profiles', {})
    for month, profiles in month_profiles.items():
        if not isinstance(profiles, list):
            continue
        for p in profiles:
            if not isinstance(p, dict):
                continue
            r = normalize_roll(p.get('roll'))
            if r == OLD_AYUSH_ROLL:
                p['studentId'] = AYUSH_ID
            elif r == NEW_AYUSH_ROLL:
                p['studentId'] = AYUSH_ID
            elif r == OLD_TANU_ROLL:
                p['studentId'] = TANU_ID
            elif r == NEW_TANU_ROLL:
                p['studentId'] = TANU_ID

    # ── 5. Force browsers to re-pull: bump server_version + server_updated_at ─
    current_version = int(data.get('server_version') or 0)
    data['server_version'] = current_version + 10   # big bump so any cached version is stale
    new_stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
    data['server_updated_at'] = new_stamp
    data['updated_at'] = new_stamp
    print(f"\n  server_version: {current_version} → {data['server_version']}")
    print(f"  server_updated_at: {new_stamp}")

    # ── 6. Remove browser schema version so migrations re-run on all devices ──
    # This forces schema v8 migration (added below) to execute on every browser
    data.pop('_app_schema_version', None)

    # ── 7. Save ───────────────────────────────────────────────────────────────
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("\nFinal repair completed successfully.")
    print(f"Backed up original to: {BACKUP_PATH}")

    # ── Verification summary ──────────────────────────────────────────────────
    print("\n── VERIFICATION ──")
    ayush_v = next((s for s in data['students'] if s['id'] == AYUSH_ID), {})
    tanu_v  = next((s for s in data['students'] if s['id'] == TANU_ID),  {})
    print(f"  Ayush: roll={ayush_v.get('roll')}, active={ayush_v.get('active')}")
    print(f"  Tanu:  roll={tanu_v.get('roll')},  active={tanu_v.get('active')}")
    print(f"  roll_history entries: {len(data['roll_history'])}")
    for h in data['roll_history']:
        print(f"    {h}")
    r2604 = month_students.get('2026-04', [])
    r2510 = month_students.get('2025-10', [])
    print(f"  2026-04 roster: EA24B15={NEW_AYUSH_ROLL in r2604}, EA24B16={NEW_TANU_ROLL in r2604}")
    print(f"  2025-10 roster: EA24A01={OLD_AYUSH_ROLL in r2510}, EA24A04={OLD_TANU_ROLL in r2510}")

    from collections import Counter
    score_months = Counter()
    for s in data.get('scores', []):
        if s.get('studentId') == AYUSH_ID:
            score_months[s.get('month', '?')] += 1
    print(f"\n  Ayush scores across {len(score_months)} months:")
    for m in sorted(score_months):
        print(f"    {m}: {score_months[m]} entries")

if __name__ == '__main__':
    repair()
