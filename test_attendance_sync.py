#!/usr/bin/env python3
"""
Attendance Sync Verification Test
Tests the teacher attendance marking and sync to server and other devices
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
SERVER_URL = "http://localhost:5000"
TEACHER_LOGIN = "Teacher"
TEACHER_PASSWORD = "teacher123"

def log(message: str, level: str = "INFO"):
    """Print formatted log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def test_teacher_attendance_sync():
    """Test complete flow: teacher marks attendance -> server saves -> other devices receive"""
    
    log("=" * 80)
    log("ATTENDANCE SYNC VERIFICATION TEST")
    log("=" * 80)
    
    session = requests.Session()
    
    # Step 1: Teacher Login
    log("\n[STEP 1] Teacher Login")
    login_response = session.post(
        f"{SERVER_URL}/auth/login",
        data={"login_id": TEACHER_LOGIN, "password": TEACHER_PASSWORD}
    )
    
    if login_response.status_code == 302:  # Redirect means successful login
        log(f"✓ Teacher login successful", "SUCCESS")
    else:
        log(f"✗ Teacher login failed: {login_response.status_code}", "ERROR")
        return False
    
    # Step 2: Get current server data
    log("\n[STEP 2] Fetching Current Server Data")
    get_response = session.get(f"{SERVER_URL}/offline-data")
    
    if get_response.status_code != 200:
        log(f"✗ Failed to get server data: {get_response.status_code}", "ERROR")
        return False
    
    server_data = get_response.json().get('data', {})
    log(f"✓ Retrieved server data", "SUCCESS")
    log(f"  - Students: {len(server_data.get('students', []))}")
    log(f"  - Scores: {len(server_data.get('scores', []))}")
    log(f"  - Current Attendance Records: {len(server_data.get('attendance', []))}")
    
    # Step 3: Prepare test attendance data
    log("\n[STEP 3] Preparing Test Attendance Data")
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    test_student_id = 3  # Use first student from server data
    
    # Find student from server data
    students = server_data.get('students', [])
    test_student = next((s for s in students if s.get('id') == test_student_id), None)
    
    if not test_student:
        log(f"✗ Test student ID {test_student_id} not found in server data", "ERROR")
        return False
    
    log(f"✓ Test student selected: {test_student.get('roll')} - {test_student.get('name')}", "SUCCESS")
    
    # Create attendance record
    attendance_record = {
        'date': current_date,
        'studentId': test_student_id,
        'roll': test_student.get('roll', ''),
        'status': 'present',
        'remarks': 'Test attendance record - automated test',
        'marked_by': TEACHER_LOGIN,
        'updated_at': datetime.now().isoformat(),
        'created_at': datetime.now().isoformat()
    }
    
    log(f"✓ Attendance record created: {json.dumps(attendance_record, indent=2)}")
    
    # Step 4: Send attendance patch to server
    log("\n[STEP 4] Sending Attendance Patch to Server")
    
    attendancePatch = {
        'attendance': [attendance_record],
        'students': [{'id': test_student_id, 'roll': test_student.get('roll')}]
    }
    
    sync_response = session.post(
        f"{SERVER_URL}/offline-data",
        json=attendancePatch,
        headers={'Content-Type': 'application/json'}
    )
    
    if sync_response.status_code == 200:
        response_data = sync_response.json()
        log(f"✓ Attendance patch sent successfully", "SUCCESS")
        log(f"  - Server response: {response_data}")
    else:
        log(f"✗ Failed to send attendance patch: {sync_response.status_code}", "ERROR")
        log(f"  - Response: {sync_response.text}", "ERROR")
        return False
    
    # Step 5: Verify attendance on server
    log("\n[STEP 5] Verifying Attendance on Server")
    time.sleep(1)  # Give server time to process
    
    verify_response = session.get(f"{SERVER_URL}/offline-data")
    
    if verify_response.status_code != 200:
        log(f"✗ Failed to verify attendance: {verify_response.status_code}", "ERROR")
        return False
    
    verified_data = verify_response.json().get('data', {})
    attendance_records = verified_data.get('attendance', [])
    
    # Find our test record
    test_record_found = False
    for record in attendance_records:
        if (record.get('date') == current_date and 
            record.get('studentId') == test_student_id):
            test_record_found = True
            log(f"✓ Test attendance record found on server!", "SUCCESS")
            log(f"  - Date: {record.get('date')}")
            log(f"  - Student ID: {record.get('studentId')}")
            log(f"  - Status: {record.get('status')}")
            log(f"  - Updated At: {record.get('updated_at')}")
            break
    
    if not test_record_found:
        log(f"✗ Test attendance record NOT found on server", "ERROR")
        log(f"  - Total attendance records: {len(attendance_records)}")
        log(f"  - Expected: date={current_date}, studentId={test_student_id}")
        return False
    
    # Step 6: Check server logs for diagnostics
    log("\n[STEP 6] Verification Summary")
    log("✓ All checks passed!", "SUCCESS")
    log("\nExpected server logs should show:")
    log("  - [TEACHER SYNC] Attendance merged | incoming: 1, existing: X, result: X+1")
    log("  - GET /offline-data: Returning X attendance records")
    
    return True

def test_attendance_client_sync():
    """Test that attendance updates sync across multiple client instances"""
    log("\n\n" + "=" * 80)
    log("CLIENT-SIDE ATTENDANCE SYNC TEST")
    log("=" * 80)
    
    log("\nThis test requires manual verification on client side:")
    log("1. Open offline scoreboard in Browser 1 (Teacher)")
    log("2. Mark attendance for a student")
    log("3. Open offline scoreboard in Browser 2 (Admin)")
    log("4. Verify the attendance appears in Browser 2")
    log("\nExpected behavior:")
    log("✓ Browser 1 marks attendance -> syncs to server instantly")
    log("✓ Browser 2 pulls from server -> shows same attendance")
    log("✓ Check browser console (F12) for sync logs")
    
    return True

if __name__ == '__main__':
    try:
        result = test_teacher_attendance_sync()
        
        if result:
            log("\n" + "=" * 80)
            log("✓ ALL TESTS PASSED", "SUCCESS")
            log("=" * 80)
            exit(0)
        else:
            log("\n" + "=" * 80)
            log("✗ TESTS FAILED", "ERROR")
            log("=" * 80)
            exit(1)
            
    except Exception as e:
        log(f"\n✗ Test execution error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        exit(1)
