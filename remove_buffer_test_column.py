#!/usr/bin/env python3
"""
Remove Buffer/Test Column from January 2026 Scoreboard
Safely removes the column without affecting other data
"""

import json
import os
import shutil
from datetime import datetime

def main():
    print("=" * 80)
    print("REMOVE BUFFER/TEST COLUMN - JANUARY 2026 SCOREBOARD")
    print("=" * 80)
    print()

    project_root = os.path.dirname(os.path.abspath(__file__))
    offline_data_path = os.path.join(project_root, 'instance', 'offline_scoreboard_data.json')
    backup_dir = os.path.join(project_root, 'instance', 'offline_scoreboard_backups')

    # Create backup
    print("Step 1: Creating backup...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'before_buffer_test_removal_{timestamp}.json')

    if os.path.exists(offline_data_path):
        shutil.copy2(offline_data_path, backup_path)
        print(f"✓ Backup created: {backup_path}")
    else:
        print(f"✗ Error: {offline_data_path} not found!")
        return

    # Load data
    print("\nStep 2: Loading offline scoreboard data...")
    with open(offline_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("✓ Data loaded successfully")

    # Remove Buffer/Test column definition
    print("\nStep 3: Removing Buffer/Test column from month_extra_columns...")
    extra_cols = data.get('month_extra_columns', {})
    jan_2026_cols = extra_cols.get('2026-01', [])

    original_col_count = len(jan_2026_cols)

    # Filter out buffer_test column
    jan_2026_cols_new = [col for col in jan_2026_cols if col.get('key') != 'buffer_test']

    if original_col_count == len(jan_2026_cols_new):
        print("⚠ Buffer/Test column not found in month_extra_columns")
    else:
        extra_cols['2026-01'] = jan_2026_cols_new
        data['month_extra_columns'] = extra_cols
        print(f"✓ Removed Buffer/Test column")
        print(f"  Original columns: {original_col_count}")
        print(f"  Remaining columns: {len(jan_2026_cols_new)}")
        for col in jan_2026_cols_new:
            print(f"    - {col.get('label')} ({col.get('key')})")

    # Remove buffer_test data from student extras
    print("\nStep 4: Removing buffer_test data from student records...")
    student_extras = data.get('month_student_extras', {})
    jan_students = student_extras.get('2026-01', {})

    students_with_buffer_test = 0
    students_processed = 0

    for student_roll, extras in jan_students.items():
        if 'buffer_test' in extras:
            students_with_buffer_test += 1
            del extras['buffer_test']
            students_processed += 1

    if students_processed > 0:
        print(f"✓ Removed buffer_test data from {students_processed} student records")
    else:
        print("⚠ No buffer_test data found in student records")

    # Update timestamp
    data['server_updated_at'] = datetime.now().isoformat()

    # Save updated data
    print("\nStep 5: Saving updated data...")
    with open(offline_data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ Data saved to: {offline_data_path}")

    # Summary
    print("\n" + "=" * 80)
    print("REMOVAL COMPLETE!")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  • Backup: {backup_path}")
    print(f"  • Column removed: Buffer/Test (buffer_test)")
    print(f"  • Students updated: {students_processed}")
    print(f"  • Remaining Jan 2026 columns: {len(jan_2026_cols_new)}")
    print(f"\n✓ The Buffer/Test column has been removed from January 2026 scoreboard")
    print()

if __name__ == '__main__':
    main()
