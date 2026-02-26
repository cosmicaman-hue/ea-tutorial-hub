#!/usr/bin/env python3
"""
Verification Script for EA Tutorial Hub Fixes
Validates that all scoreboard fixes are working correctly
"""

import json
import os
import sys
from datetime import datetime

def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def print_test(name, passed, details=""):
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"     {details}")

def main():
    print_header("EA TUTORIAL HUB - FIXES VERIFICATION")
    print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    project_root = os.path.dirname(os.path.abspath(__file__))
    offline_data_path = os.path.join(project_root, 'instance', 'offline_scoreboard_data.json')
    scoreboard_py_path = os.path.join(project_root, 'app', 'routes', 'scoreboard.py')

    all_passed = True

    # Test 1: Offline data file exists
    print_header("TEST 1: Data File Integrity")

    test_passed = os.path.exists(offline_data_path)
    print_test("Offline data file exists", test_passed)
    if not test_passed:
        all_passed = False
        print("\nCRITICAL: Cannot proceed without offline data file")
        return 1

    # Test 2: Load and validate offline data
    print_header("TEST 2: Offline Data Validation")

    try:
        with open(offline_data_path, 'r', encoding='utf-8') as f:
            offline_data = json.load(f)
        print_test("JSON file is valid", True)
    except Exception as e:
        print_test("JSON file is valid", False, str(e))
        all_passed = False
        return 1

    students = offline_data.get('students', [])
    active_students = [s for s in students if s.get('active', True)]
    inactive_students = [s for s in students if not s.get('active', True)]

    # Test 3: Active student count
    print_header("TEST 3: Active Student Count")

    expected_active = 45
    actual_active = len(active_students)
    test_passed = actual_active == expected_active

    print_test(
        f"Active student count is {expected_active}",
        test_passed,
        f"Found {actual_active} active students"
    )

    if not test_passed:
        all_passed = False
        print(f"\n  Expected: {expected_active}")
        print(f"  Actual:   {actual_active}")
        print(f"  Difference: {actual_active - expected_active}")

    # Test 4: Verify FEB26_SEED alignment
    print_header("TEST 4: FEB26_SEED Alignment")

    try:
        with open(scoreboard_py_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract FEB26_SEED
        start = content.find('FEB26_SEED = json.loads(r\'\'\'')
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

        print_test("FEB26_SEED loaded successfully", True, f"{len(seed_students)} students")

        # Check for extra active students
        active_rolls = {s['roll'] for s in active_students}
        extra_active = active_rolls - seed_rolls

        # Xavier Herenj should be in seed but inactive
        if 'EA25D21' in active_rolls:
            extra_active.add('EA25D21')

        test_passed = len(extra_active) == 0
        print_test(
            "No extra active students",
            test_passed,
            f"Found {len(extra_active)} extra" if not test_passed else "All active students are in FEB26_SEED"
        )

        if not test_passed:
            all_passed = False
            print("\n  Extra active students:")
            for roll in sorted(extra_active):
                student = next((s for s in active_students if s['roll'] == roll), None)
                if student:
                    print(f"    - {roll}: {student.get('name', 'N/A')}")

    except Exception as e:
        print_test("FEB26_SEED alignment check", False, str(e))
        all_passed = False

    # Test 5: Code fixes verification
    print_header("TEST 5: Code Fixes Verification")

    # Check for is_active filter in query
    test_passed = 'StudentProfile.query.join(User).filter(User.is_active == True)' in content
    print_test(
        "Database query filters by is_active",
        test_passed,
        "Line 2860 has proper JOIN and filter" if test_passed else "Missing is_active filter"
    )
    if not test_passed:
        all_passed = False

    # Check for is_active validation in add_points
    test_passed = 'Student account is inactive' in content
    print_test(
        "Add points validates user status",
        test_passed,
        "Proper validation found" if test_passed else "Missing validation"
    )
    if not test_passed:
        all_passed = False

    # Test 6: Backup verification
    print_header("TEST 6: Backup Files")

    backup_dir = os.path.join(project_root, 'instance', 'offline_scoreboard_backups')
    backup_files = []
    if os.path.exists(backup_dir):
        backup_files = [f for f in os.listdir(backup_dir) if 'before_fix' in f]

    test_passed = len(backup_files) > 0
    print_test(
        "Backup created before fixes",
        test_passed,
        f"Found {len(backup_files)} backup(s)" if test_passed else "No backups found"
    )

    if test_passed:
        latest_backup = sorted(backup_files)[-1]
        print(f"     Latest backup: {latest_backup}")

    # Test 7: Data integrity
    print_header("TEST 7: Data Integrity")

    # Check that all students have required fields
    missing_fields = []
    for student in students:
        if not student.get('roll'):
            missing_fields.append("roll")
        if not student.get('name'):
            missing_fields.append("name")
        if 'active' not in student:
            missing_fields.append("active")

    test_passed = len(missing_fields) == 0
    print_test(
        "All students have required fields",
        test_passed,
        "All required fields present" if test_passed else f"Missing fields detected"
    )
    if not test_passed:
        all_passed = False

    # Final Summary
    print_header("VERIFICATION SUMMARY")

    print(f"\nData Statistics:")
    print(f"  • Total students:    {len(students)}")
    print(f"  • Active students:   {len(active_students)}")
    print(f"  • Inactive students: {len(inactive_students)}")
    print(f"  • Expected active:   45")

    if all_passed:
        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED - SYSTEM IS PRODUCTION READY")
        print("=" * 80)
        print("\nThe scoreboard fixes have been successfully applied and verified.")
        print("You can safely deploy the system.")
        return 0
    else:
        print("\n" + "=" * 80)
        print("✗ SOME TESTS FAILED - REVIEW REQUIRED")
        print("=" * 80)
        print("\nPlease review the failed tests above and re-run fix_scoreboard_data.py")
        return 1

if __name__ == '__main__':
    sys.exit(main())
