"""Diagnose resource transaction studentId mismatches vs current student rolls."""
import json, os

DATA = os.path.join(os.path.dirname(__file__), '..', 'instance', 'offline_scoreboard_data.json')
d = json.load(open(DATA, 'r', encoding='utf-8'))

txns = d.get('resource_transactions', [])
students = d.get('students', [])

id_to_name = {s['id']: s.get('name', '?') for s in students}
id_to_roll = {s['id']: str(s.get('roll', '')).strip().upper() for s in students}
roll_to_id = {}
roll_to_name = {}
for s in students:
    r = str(s.get('roll', '')).strip().upper()
    if r:
        roll_to_id[r] = s['id']
        roll_to_name[r] = s.get('name', '?')

mismatches = []
for t in txns:
    sid = t.get('studentId')
    txn_roll = str(t.get('student_roll', '')).strip().upper()
    current_roll = id_to_roll.get(sid, '')
    if txn_roll and current_roll and txn_roll != current_roll:
        correct_id = roll_to_id.get(txn_roll)
        correct_name = roll_to_name.get(txn_roll, '?')
        mismatches.append({
            'txn_id': t.get('id'),
            'txn_roll': txn_roll,
            'old_sid': sid,
            'old_name': id_to_name.get(sid, '?'),
            'correct_sid': correct_id,
            'correct_name': correct_name,
            'item': t.get('item_name', ''),
            'month': t.get('month', ''),
        })

print(f"Total txns: {len(txns)}, Mismatches: {len(mismatches)}")
print()

# Deduplicated mapping
seen = set()
for m in mismatches:
    key = (m['txn_roll'], m['old_sid'], m['correct_sid'])
    if key not in seen:
        seen.add(key)
        print(f"  Roll {m['txn_roll']}: ID {m['old_sid']} ({m['old_name']}) -> should be ID {m['correct_sid']} ({m['correct_name']})")

print()
print("=== All mismatched transactions ===")
for m in mismatches:
    print(f"  TxnID={m['txn_id']}  Roll={m['txn_roll']}  Month={m['month']}  Item={m['item']}  OldID={m['old_sid']}({m['old_name']}) -> NewID={m['correct_sid']}({m['correct_name']})")

# Also check resource_requests and resource_advantage_deductions
for table_name in ['resource_requests', 'resource_advantage_deductions']:
    rows = d.get(table_name, [])
    table_mismatches = 0
    for row in rows:
        sid = row.get('studentId')
        row_roll = str(row.get('student_roll', '')).strip().upper()
        current_roll = id_to_roll.get(sid, '')
        if row_roll and current_roll and row_roll != current_roll:
            table_mismatches += 1
    print(f"\n{table_name}: {len(rows)} rows, {table_mismatches} ID mismatches")
