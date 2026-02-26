#!/usr/bin/env python3
"""
Data Reconciliation Script for EA Tutorial Hub
Fixes the scoreboard active student count from 54 to 45

This script:
1. Backs up the current offline_scoreboard_data.json
2. Loads FEB26_SEED as the source of truth
3. Marks students NOT in FEB26_SEED as inactive
4. Preserves all other data (scores, profiles, etc.)
5. Validates the result
"""

import json
import os
import shutil
from datetime import datetime

def main():
    print("=" * 80)
    print("EA TUTORIAL HUB - SCOREBOARD DATA RECONCILIATION")
    print("=" * 80)
    print()

    # Paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    offline_data_path = os.path.join(project_root, 'instance', 'offline_scoreboard_data.json')
    scoreboard_py_path = os.path.join(project_root, 'app', 'routes', 'scoreboard.py')
    backup_dir = os.path.join(project_root, 'instance', 'offline_scoreboard_backups')

    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)

    # Step 1: Backup current data
    print("Step 1: Creating backup...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'offline_scoreboard_before_fix_{timestamp}.json')

    if os.path.exists(offline_data_path):
        shutil.copy2(offline_data_path, backup_path)
        print(f"✓ Backup created: {backup_path}")
    else:
        print(f"✗ Error: {offline_data_path} not found!")
        return

    # Step 2: Load FEB26_SEED from scoreboard.py
    print("\nStep 2: Loading FEB26_SEED (source of truth)...")

    with open(scoreboard_py_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract FEB26_SEED JSON
    start = content.find('FEB26_SEED = json.loads(r\'\'\'')
    if start == -1:
        print("✗ Error: FEB26_SEED not found in scoreboard.py!")
        return

    start = content.find('{', start)
    brace_count = 0
    end = start
    for i in range(start, len(content)):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end = i + 1
                break

    seed_data = json.loads(content[start:end])
    seed_students = seed_data.get('students', [])
    seed_rolls = {s['roll'] for s in seed_students}

    print(f"✓ FEB26_SEED loaded: {len(seed_students)} students")

    # Step 3: Load current offline data
    print("\nStep 3: Loading current offline data...")

    with open(offline_data_path, 'r', encoding='utf-8') as f:
        offline_data = json.load(f)

    offline_students = offline_data.get('students', [])
    print(f"✓ Offline data loaded: {len(offline_students)} total students")

    # Step 4: Identify and fix discrepancies
    print("\nStep 4: Reconciling active status...")

    active_before = sum(1 for s in offline_students if s.get('active', True))
    students_to_deactivate = []

    for student in offline_students:
        roll = student.get('roll')
        is_currently_active = student.get('active', True)
        should_be_active = roll in seed_rolls

        # Special case: EA25D21 (Xavier Herenj) should be inactive even though in seed
        if roll == 'EA25D21':
            should_be_active = False

        if is_currently_active and not should_be_active:
            students_to_deactivate.append(student)
            student['active'] = False

    active_after = sum(1 for s in offline_students if s.get('active', True))

    print(f"\n✓ Reconciliation complete:")
    print(f"  - Students deactivated: {len(students_to_deactivate)}")
    print(f"  - Active before: {active_before}")
    print(f"  - Active after: {active_after}")

    if students_to_deactivate:
        print(f"\n  Deactivated students:")
        for student in students_to_deactivate:
            roll = student.get('roll', 'N/A')
            name = student.get('name', 'N/A')
            cls = student.get('class', 'None')
            print(f"    • {roll:<15} {name:<40} Class: {cls}")

    # Step 5: Validate result
    print("\nStep 5: Validating result...")

    expected_active = len(seed_students) - 1  # 46 - 1 (Xavier Herenj) = 45

    if active_after == expected_active:
        print(f"✓ VALIDATION PASSED: Active count is {active_after} (expected {expected_active})")
    else:
        print(f"✗ VALIDATION FAILED: Active count is {active_after} (expected {expected_active})")
        print("  Rolling back changes...")
        shutil.copy2(backup_path, offline_data_path)
        print("  Backup restored. Please review the script.")
        return

    # Step 6: Save updated data
    print("\nStep 6: Saving updated data...")

    # Update server timestamp
    offline_data['server_updated_at'] = datetime.now().isoformat()

    with open(offline_data_path, 'w', encoding='utf-8') as f:
        json.dump(offline_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Data saved to: {offline_data_path}")

    # Final summary
    print("\n" + "=" * 80)
    print("RECONCILIATION COMPLETE!")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  • Backup location: {backup_path}")
    print(f"  • Students in system: {len(offline_students)}")
    print(f"  • Active students: {active_after} (was {active_before})")
    print(f"  • Inactive students: {len(offline_students) - active_after}")
    print(f"  • Changes made: {len(students_to_deactivate)} students deactivated")
    print(f"\n✓ Scoreboard will now show {active_after} active students")
    print()

if __name__ == '__main__':
    main()
