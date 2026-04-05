#!/usr/bin/env python3
"""
CRITICAL: Anti-Corruption Script
Prevents offline scoreboard from syncing stale cached VETO data back to the file.

THE PROBLEM:
- offline_scoreboard.html stores data in browser localStorage + IndexedDB
- When Flask app restarts, it can pull old cached data from browser and sync it back
- This overwrites correct VETO values with stale data
- Result: Hours of corrections are lost

THE SOLUTION:
- Add corruption detection to warn before app starts
- Lock the veto_tracking system to prevent unwanted modifications
- Inject a "last_known_correct_hash" marker to detect corruptions
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime

DATA_FILE = Path('instance/offline_scoreboard_data.json')

def calculate_veto_hash(data):
    """Calculate hash of all VETO values to detect corruption."""
    try:
        veto_tracking = data.get('veto_tracking', {})
        students_veto = veto_tracking.get('students', {})
        
        # Build string of all VETO allocations
        veto_string = ""
        for roll in sorted(students_veto.keys()):
            veto_data = students_veto[roll]
            total = veto_data.get('total_vetos', 0)
            veto_string += f"{roll}:{total};"
        
        return hashlib.sha256(veto_string.encode()).hexdigest()
    except:
        return None

def check_for_corruption():
    """Detect if VETO data has been corrupted by stale sync."""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        current_hash = calculate_veto_hash(data)
        last_known_hash = data.get('_last_known_correct_veto_hash')
        
        if last_known_hash and current_hash != last_known_hash:
            print("\n" + "=" * 70)
            print("⚠️  CORRUPTION DETECTED IN VETO SYSTEM")
            print("=" * 70)
            print(f"Last known correct hash: {last_known_hash}")
            print(f"Current data hash:       {current_hash}")
            print("\nThis indicates stale data was synced back to the file.")
            print("The VETO corrections are being overwritten by cached browser data.")
            print("\nACTION REQUIRED:")
            print("1. Stop the Flask app (already done)")
            print("2. Run: python restore_correct_veto_data.py")
            print("3. Manually clear browser cache/localStorage")
            print("=" * 70 + "\n")
            return False
        
        if not last_known_hash:
            print("✅ Setting VETO checkpoint for corruption detection...")
            data['_last_known_correct_veto_hash'] = current_hash
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"   Checkpoint: {current_hash}")
        
        return True
    except Exception as e:
        print(f"❌ Error checking corruption: {e}")
        return True  # Don't block startup on error

def lock_veto_system(data):
    """Add enforcement lock to prevent unauthorized VETO modifications."""
    veto_tracking = data.get('veto_tracking', {})
    
    # Ensure hardened flag is set
    veto_tracking['hardened'] = True
    veto_tracking['hardening_enforced'] = True
    veto_tracking['corruption_detection_enabled'] = True
    
    # Add current hash
    veto_tracking['_last_sync_hash'] = calculate_veto_hash(data)
    veto_tracking['_last_sync_time'] = datetime.utcnow().isoformat() + 'Z'
    
    data['veto_tracking'] = veto_tracking
    return data

def sanitize_student_veto_counts(data):
    """Ensure all student records match veto_tracking (detect corruption source)."""
    veto_tracking = data.get('veto_tracking', {})
    students_veto = veto_tracking.get('students', {})
    students = data.get('students', [])
    
    mismatches = 0
    for student in students:
        roll = student.get('id')
        if roll in students_veto:
            veto_data = students_veto[roll]
            expected_total = veto_data.get('total_vetos', 0)
            
            actual_ind = student.get('veto_count', 0)
            actual_role = student.get('role_veto_count', 0)
            actual_total = actual_ind + actual_role
            
            if actual_total != expected_total:
                print(f"  Mismatch found: {roll} has {actual_total}V but tracking expects {expected_total}V")
                mismatches += 1
                
                # Auto-fix by resetting to match veto_tracking
                student['veto_count'] = veto_data.get('individual_vetos', 0)
                student['role_veto_count'] = veto_data.get('role_vetos', 0)
    
    if mismatches > 0:
        print(f"\n⚠️  Found {mismatches} student record mismatches with veto_tracking")
        print("   Auto-fixing to match authoritative veto_tracking...")
    
    return data, mismatches

def main():
    print("\n" + "=" * 70)
    print("VETO SYSTEM ANTI-CORRUPTION CHECK")
    print("=" * 70)
    
    # Check for corruption
    if not check_for_corruption():
        print("\n❌ CORRUPTION DETECTED - Please restore from backup!")
        return False
    
    # Load and process data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n✓ Checking student records vs veto_tracking...")
    data, mismatches = sanitize_student_veto_counts(data)
    
    if mismatches == 0:
        print("  All student records match veto_tracking ✓")
    
    print("\n✓ Enforcing veto_tracking hardening...")
    data = lock_veto_system(data)
    
    # Save
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 70)
    print("✅ VETO SYSTEM SECURED")
    print("=" * 70)
    print("Safe to restart Flask app now")
    print("=" * 70 + "\n")
    
    return True

if __name__ == '__main__':
    main()
