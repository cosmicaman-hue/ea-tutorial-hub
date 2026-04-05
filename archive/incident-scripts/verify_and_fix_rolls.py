#!/usr/bin/env python3
"""
Verify Ayush and Tanu have correct original rolls.
If they're already correct, no action needed.
If they're wrong, fix them directly in the data file.
"""
import json
from datetime import datetime

# Load data
with open('instance/offline_scoreboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Define target rolls
TARGET_ROLLS = {
    'ayush': 'EA24A01',
    'tanu': 'EA24A04'
}

print("=" * 70)
print("ROLL NUMBER VERIFICATION & FIX")
print("=" * 70)

# Find students
students_to_fix = {}
for student in data.get('students', []):
    name_lower = student.get('name', '').lower()
    for target_name, target_roll in TARGET_ROLLS.items():
        if target_name in name_lower:
            current_roll = student.get('roll', '')
            students_to_fix[target_name] = {
                'id': student['id'],
                'name': student.get('name'),
                'current_roll': current_roll,
                'target_roll': target_roll,
                'needs_fix': current_roll != target_roll
            }

# Report status
print("\nCURRENT STATUS:")
print("-" * 70)

all_correct = True
for name, info in students_to_fix.items():
    status = "✓ CORRECT" if not info['needs_fix'] else "✗ NEEDS FIX"
    print(f"\n{name.upper()}:")
    print(f"  ID: {info['id']}")
    print(f"  Current Roll: {info['current_roll']}")
    print(f"  Target Roll: {info['target_roll']}")
    print(f"  Status: {status}")
    if info['needs_fix']:
        all_correct = False

if all_correct:
    print("\n" + "=" * 70)
    print("✓ ALL STUDENTS ALREADY HAVE CORRECT ROLLS!")
    print("=" * 70)
    print("\nNo changes needed. The rolls are already correct.")
    print("\nIf you're unable to edit through the UI, it's because:")
    print("1. The rolls are already at their target values")
    print("2. The UI validation prevents 'no change' edits")
    print("\nThe data is correct. Feb 2026 should display properly.")
    exit(0)

# If we get here, we need to fix rolls
print("\n" + "=" * 70)
print("FIXING INCORRECT ROLLS")
print("=" * 70)

# Create backup
backup_file = f"instance/offline_scoreboard_data.pre_roll_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(backup_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"\nBackup created: {backup_file}")

# Fix students
for name, info in students_to_fix.items():
    if info['needs_fix']:
        # Find and update student
        for student in data.get('students', []):
            if student['id'] == info['id']:
                old_roll = student.get('roll')
                student['roll'] = info['target_roll']
                print(f"\n✓ Fixed {name.upper()}:")
                print(f"  {old_roll} → {info['target_roll']}")

# Save fixed data
with open('instance/offline_scoreboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 70)
print("✓ ROLLS FIXED AND SAVED")
print("=" * 70)
print("\nNext steps:")
print("1. Hard refresh browser (Ctrl+Shift+R)")
print("2. Navigate to Feb 2026 scoreboard")
print("3. Verify Rehmetun is on top (not Ayush)")
