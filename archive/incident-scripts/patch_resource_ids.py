"""
Patch resource_transactions, resource_requests, and resource_advantage_deductions
to fix studentId mismatches caused by restored data having different IDs.

Strategy: Use student_roll in each row to find the correct studentId in current data.
"""
import json, os, shutil, sys
from datetime import datetime

DATA = os.path.join(os.path.dirname(__file__), '..', 'instance', 'offline_scoreboard_data.json')

def load():
    return json.load(open(DATA, 'r', encoding='utf-8'))

def save(d):
    backup = DATA + f'.bak-resource-id-fix-{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy2(DATA, backup)
    print(f"Backup: {backup}")
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, separators=(',', ':'))
    print("Saved.")

def build_maps(students):
    id_to_roll = {}
    id_to_name = {}
    roll_to_id = {}
    roll_to_name = {}
    for s in students:
        sid = s['id']
        name = s.get('name', '?')
        roll = str(s.get('roll', '')).strip().upper()
        id_to_roll[sid] = roll
        id_to_name[sid] = name
        if roll:
            roll_to_id[roll] = sid
            roll_to_name[roll] = name
    return id_to_roll, id_to_name, roll_to_id, roll_to_name

def find_mismatches(rows, id_to_roll, id_to_name, roll_to_id, roll_to_name, table_name):
    patches = []
    for row in rows:
        sid = row.get('studentId')
        row_roll = str(row.get('student_roll', '')).strip().upper()
        if not row_roll or sid is None:
            continue
        current_roll = id_to_roll.get(sid, '')
        if row_roll != current_roll:
            correct_id = roll_to_id.get(row_roll)
            if correct_id is not None and correct_id != sid:
                patches.append({
                    'table': table_name,
                    'row_id': row.get('id'),
                    'roll': row_roll,
                    'old_id': sid,
                    'old_name': id_to_name.get(sid, '?'),
                    'new_id': correct_id,
                    'new_name': roll_to_name.get(row_roll, '?'),
                })
    return patches

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'list'
    d = load()
    students = d.get('students', [])
    id_to_roll, id_to_name, roll_to_id, roll_to_name = build_maps(students)

    all_patches = []
    for table in ['resource_transactions', 'resource_requests', 'resource_advantage_deductions']:
        rows = d.get(table, [])
        patches = find_mismatches(rows, id_to_roll, id_to_name, roll_to_id, roll_to_name, table)
        all_patches.extend(patches)

    # Print summary by unique roll mapping
    print("=" * 80)
    print(f"RESOURCE ID PATCH PLAN — {len(all_patches)} rows to fix")
    print("=" * 80)
    
    # Group by roll
    by_roll = {}
    for p in all_patches:
        key = p['roll']
        if key not in by_roll:
            by_roll[key] = p
            by_roll[key]['count'] = 0
            by_roll[key]['tables'] = set()
        by_roll[key]['count'] += 1
        by_roll[key]['tables'].add(p['table'])

    print(f"\n{'Roll':<12} {'Old ID':>6} {'Old Name':<30} {'New ID':>6} {'New Name':<30} {'Rows':>4} Tables")
    print("-" * 120)
    for roll in sorted(by_roll):
        p = by_roll[roll]
        tables = ', '.join(sorted(p['tables']))
        print(f"{roll:<12} {p['old_id']:>6} {p['old_name']:<30} {p['new_id']:>6} {p['new_name']:<30} {p['count']:>4} {tables}")

    print(f"\nTotal: {len(all_patches)} rows across {len(by_roll)} students")

    if mode == 'patch':
        print("\nApplying patches...")
        patched = 0
        for table in ['resource_transactions', 'resource_requests', 'resource_advantage_deductions']:
            rows = d.get(table, [])
            for row in rows:
                sid = row.get('studentId')
                row_roll = str(row.get('student_roll', '')).strip().upper()
                if not row_roll or sid is None:
                    continue
                current_roll = id_to_roll.get(sid, '')
                if row_roll != current_roll:
                    correct_id = roll_to_id.get(row_roll)
                    if correct_id is not None and correct_id != sid:
                        row['studentId'] = correct_id
                        patched += 1
        print(f"Patched {patched} rows.")
        save(d)
    else:
        print("\nRun with 'patch' argument to apply fixes.")

if __name__ == '__main__':
    main()
