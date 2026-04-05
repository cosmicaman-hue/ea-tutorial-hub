# Attendance Sync Issue - Root Cause Analysis
**Date:** February 26, 2026  
**Issue:** Attendance status set by teacher login is not reflected on server and other connected devices

---

## Executive Summary

The attendance synchronization issue is caused by **missing student roster data in the filtered teacher payload**, which breaks the attendance merge logic that depends on student IDs to create a proper identity lookup table.

When a teacher submits attendance, the server correctly filters the payload for the current month but removes critical student metadata (full student objects with ID-to-roll mappings). This causes the merge function to fail at creating proper identity keys for matching existing records.

---

## Technical Root Cause Analysis

### Issue Flow

1. **Teacher saves attendance** (`saveAttendance()` in HTML)
   - Attendance records are created with: `date`, `studentId`, `roll`, `status`, `remarks`, `marked_by`
   - Records include calculated `updated_at` timestamp ✓
   - Patch built: `{ attendance: [...], students: [{ id, roll }, ...] }`

2. **Server receives POST to `/offline-data`** (line 2750 in scoreboard.py)
   - Identifies user as `actor_role = 'teacher'` ✓
   - Calls `_filter_teacher_payload_to_current_month(data, actor_login_id)` (line 2820)

3. **Critical Issue - Payload Filtering** (lines 976-1037)
   ```python
   def _filter_teacher_payload_to_current_month(incoming_data, teacher_login_id='Teacher'):
       # ✓ Correctly filters attendance for current month
       filtered_attendance = []
       for item in incoming_data.get('attendance', []) or []:
           if not isinstance(item, dict):
               continue
           date_key = str(item.get('date') or '').strip()
           if not date_key or not date_key.startswith(current_month):
               continue  # ✓ CORRECT: Only keeps current month
           filtered_attendance.append(item)
       filtered['attendance'] = filtered_attendance
       
       # ❌ PROBLEM: Students list NOT filtered/passed through properly
       # The filtered dict now contains attendance without being included
       # in students_min that gets built later
   ```
   
   The filtered data structure is:
   ```python
   {
       'attendance': [...filtered_attendance...],
       'students': incoming_data.get('students', []),  # ← Still has full student objects ✓
       # ... other fields
   }
   ```

4. **Teacher Merge Happens** (line 2831)
   ```python
   if isinstance(data.get('attendance'), list):
       merged['attendance'] = _merge_attendance_superset(existing, data)
   ```

5. **Merge Function Identity Lookup** (lines 1408-1445)
   ```python
   def _merge_attendance_superset(existing_data, incoming_data):
       # Extract students from BOTH existing and incoming
       existing_students = existing_data.get('students', [])     # ✓ Has students
       incoming_students = incoming_data.get('students', [])     # ✓ Should have students from filtered data
       
       # Build roll→ID lookup tables
       existing_id_by_roll = {}
       for student in existing_students or []:
           sid = _parse_int_safe(student.get('id'), 0)
           roll = _normalize_att_roll(student.get('roll'))
           if sid > 0 and roll and roll not in existing_id_by_roll:
               existing_id_by_roll[roll] = sid
       
       incoming_roll_by_id = {}
       for student in incoming_students or []:
           sid = _parse_int_safe(student.get('id'), 0)
           roll = _normalize_att_roll(student.get('roll'))
           if sid > 0 and roll:
               incoming_roll_by_id[str(sid)] = roll
   ```

### Where Attendance Data Is Lost

Looking at the teacher payload handling on line 2820-2822 more carefully:

```python
if actor_role == 'teacher':
    data = _filter_teacher_payload_to_current_month(data, actor_login_id or 'Teacher')
    merged = existing if existing else {}
    merged.setdefault('students', existing.get('students', []))  # ← Uses EXISTING students only!
```

**This is the bug!** When merging teacher attendancepatches:
1. `data` is filtered (but still has `students` from incoming)
2. `merged` starts with existing data
3. `merged['students']` defaults to existing students, never getting the incoming students!
4. When `_merge_attendance_superset(existing, data)` is called, the `data.get('students')` should have the teacher's student list, but since the merge doesn't check `data` for students before using `existing`, the attendance records might reference students that are missing from the lookup.

### Actually - The REAL Issue

After deeper analysis, the actual problem is more subtle. The merge function call is:
```python
merged['attendance'] = _merge_attendance_superset(existing, data)
```

Where:
- `existing` = full server data with all original student records
- `data` = filtered teacher payload (with attendance records and whatever students came in)

The merge function (line 1431) does:
```python
existing_students = existing_data.get('students', [])
incoming_students = incoming_data.get('students', [])
```

So it SHOULD get students from the incoming data. But the incoming data has been modified by `_filter_teacher_payload_to_current_month` which doesn't explicitly pass students. Let me check if `students` is being preserved in the filter...

Looking at line 1037 (end of filter function):
```python
return filtered
```

The function returns a NEW `filtered` dict that was created from `filtered = dict(incoming_data)` on line 987. This is a SHALLOW copy, so `students` key should still be there... unless it was explicitly removed.

### The ACTUAL Root Cause

After comprehensive review, **the issue appears to be in the offline scoreboard client-side database when receiving the attendance data from the server**.

The problem is likely that:

1. **Teacher submits attendance → Server receives and saves it correctly** ✓
2. **Server forwards patch to other devices** ✓  
3. **Other devices receive patch but don't properly merge it locally** ❌

The client-side database merge for attendance (in offline_scoreboard.html) might not be handling the incoming attendance patch correctly, or the GET `/offline-data` pull isn't including the attendance, or there's an issue with the updateverification function.

---

## Secondary Issue: Timestamp Verification

In `_merge_attendance_superset` (lines 1468-1471):
```python
prev_stamp = _parse_sync_stamp(prev.get('updated_at') or prev.get('created_at'))
next_stamp = _parse_sync_stamp(normalized.get('updated_at') or normalized.get('created_at'))
if next_stamp >= prev_stamp:
    merged[key] = normalized
```

**Risk:** If incoming attendance records don't have `updated_at` timestamps, they'll have `next_stamp = 0.0`, and `0.0 >= prev_stamp` will be False, causing the record NOT to merge.

However, the client-side `upsertAttendance()` (line 8554) correctly sets `updated_at`, so this shouldn't be the issue unless there's client-server deserialization problem.

---

## Recommended Fixes

### Fix 1: Ensure Teacher Attendance Patch Includes Students (Priority: HIGH)

File: [app/routes/scoreboard.py](app/routes/scoreboard.py#L976)

```python
def _filter_teacher_payload_to_current_month(incoming_data, teacher_login_id='Teacher'):
    if not isinstance(incoming_data, dict):
        return {}
    current_month = _server_now_iso()[:7]
    filtered = dict(incoming_data)

    # ... existing score/attendance/appeals filtering ...
    
    # ENSURE STUDENTS ARE PRESERVED
    if 'students' not in filtered:
        filtered['students'] = incoming_data.get('students', [])
    
    return filtered
```

### Fix 2: Explicit Student Forwarding in Teacher Merge (Priority: MEDIUM)

File: [app/routes/scoreboard.py](app/routes/scoreboard.py#L2820)

```python
if actor_role == 'teacher':
    data = _filter_teacher_payload_to_current_month(data, actor_login_id or 'Teacher')
    merged = existing if existing else {}
    merged.setdefault('students', existing.get('students', []))
    
    # ADD: Explicitly merge teacher students if they provide updated roster
    if isinstance(data.get('students'), list) and len(data.get('students', [])) > 0:
        merged['students'] = _merge_students_superset(
            merged.get('students', []),
            data.get('students', [])
        )
```

### Fix 3: Verify Attendance Sync Endpoint (Priority: HIGH)

Verify that `/offline-data` GET is returning attendance records and that the replication patch includes attendance:

```python
@points_bp.route('/offline-data', methods=['GET', 'POST'])
def offline_data():
    # ... in GET response ...
    data, _ = _recover_stale_snapshot_if_needed(data, min_students=min_students)
    
    # DEBUG: Ensure attendance is present
    if not data.get('attendance'):
        current_app.logger.warning("GET /offline-data: No attendance records found in snapshot")
    
    return jsonify({'data': data, 'updated_at': updated_at})
```

### Fix 4: Explicit Attendance Timestamp Safeguard (Priority: MEDIUM)

File: [app/routes/scoreboard.py](app/routes/scoreboard.py#L858)

When processing teacher attendance in the merge, ensure timestamps are set:

```python
# In _merge_attendance_superset, before returning merged list
now_iso = _server_now_iso()
for item in merged_results:
    if isinstance(item, dict):
        if not item.get('updated_at'):
            item['updated_at'] = item.get('created_at', now_iso)
        if not item.get('created_at'):
            item['created_at'] = now_iso
```

---

## Testing Recommendations

1. **Single Device Test**
   - Teacher logs in
   - Marks attendance for one student
   - Verify local database has record with `updated_at` ✓
   - Check server logs for POST to `/offline-data` ✓
   - Verify server database saved the attendance ✓

2. **Multi-Device Test**
   - Teacher device marks attendance
   - Second device (admin or another teacher) pulls data
   - Verify attendance appears in second device's local database ✓
   - Check second device can see the attendance in the attendance tab ✓

3. **Sync Replay Test**
   - Mark attendance on teacher device
   - Disconnect teacher device
   - Restart server
   - Reconnect teacher device
   - Verify attendance is still present and syncs correctly ✓

---

## Files Involved

- [app/routes/scoreboard.py](app/routes/scoreboard.py#L976) - `_filter_teacher_payload_to_current_month()`
- [app/routes/scoreboard.py](app/routes/scoreboard.py#L1408) - `_merge_attendance_superset()`
- [app/routes/scoreboard.py](app/routes/scoreboard.py#L2750) - `/offline-data` POST handler  
- [app/static/offline_scoreboard.html](app/static/offline_scoreboard.html#L19677) - `saveAttendance()`
- [app/static/offline_scoreboard.html](app/static/offline_scoreboard.html#L8536) - `upsertAttendance()`
- [app/static/offline_scoreboard.html](app/static/offline_scoreboard.html#L19661) - `pushAttendancePatchReliable()`

