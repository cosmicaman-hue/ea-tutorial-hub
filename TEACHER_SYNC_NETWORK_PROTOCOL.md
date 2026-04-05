# Teacher Data Sync - Network Protocol Reference

## HTTP Endpoints

### 1. Teacher Login
```
POST /auth/login
Content-Type: application/x-www-form-urlencoded

login_id=Teacher&password=ChangeTeacherPass123!

Response 302 (Redirect to /points/offline)
Set-Cookie: session=...
Location: /points/offline
```

### 2. Get Latest Data (GET)
```
GET /points/offline-data
Accept: application/json
Cookie: session=...

Response 200 OK
Content-Type: application/json
Cache-Control: no-store

{
  "data": {
    "students": [...],
    "scores": [...],
    "attendance": [...],
    "appeals": [...],
    "server_updated_at": "2026-04-04T12:34:56.789Z",
    "server_version": 42,
    ...
  },
  "updated_at": "2026-04-04T12:34:56.789Z"
}
```

### 3. Push Teacher Changes (POST)
```
POST /points/offline-data
Content-Type: application/json
Cookie: session=...

{
  "data": {
    "students": [...],
    "scores": [
      {
        "student_id": "EA24A01",
        "month": "2026-04",
        "date": "2026-04-04",
        "points": 5,
        "reason": "Good participation",
        "recordedBy": "Teacher",
        "timestamp": "2026-04-04T12:30:00.000Z"
      },
      ...
    ],
    "attendance": [
      {
        "student_id": "EA24A01",
        "date": "2026-04-04",
        "status": "present",
        "timestamp": "2026-04-04T12:31:00.000Z"
      }
    ],
    "server_updated_at": "2026-04-04T12:00:00.000Z",
    "server_version": 41,
    ...
  },
  "op_id": "sync_op_1712235600000",
  "base_version": 41,
  "peers": ["http://server2:5000"]
}

Response 200 OK
Content-Type: application/json

{
  "success": true,
  "updated_at": "2026-04-04T12:35:00.000Z",
  "server_version": 42
}
```

### 4. Server-Sent Events (SSE)
```
GET /points/offline-events
Accept: text/event-stream
Cookie: session=...

Response 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache

retry: 2500

event: sync
data: {"updated_at": "2026-04-04T12:35:00.000Z", "source": "init"}

event: sync
data: {"updated_at": "2026-04-04T12:35:30.000Z", "source": "teacher"}

event: sync
data: {"updated_at": "2026-04-04T12:36:00.000Z", "source": "replica"}
```

---

## Response Status Codes

### Success (200)
```json
{
  "success": true,
  "updated_at": "2026-04-04T12:35:00.000Z",
  "server_version": 42
}
```
Teacher changes accepted, merged, and saved.

### No Content (204)
```
GET /points/offline-data?since=2026-04-04T12:30:00.000Z

(empty response body)
```
Optimization: client is already at/above server timestamp.

### Conflict (409)
```json
{
  "success": false,
  "error": "Version conflict",
  "code": "stale_base_version",
  "updated_at": "2026-04-04T12:35:00.000Z",
  "server_version": 42
}
```
**Action**: Client should:
1. Pull fresh data (GET /offline-data)
2. Re-merge locally
3. Re-POST with new base_version

### Unauthorized (401)
```json
{
  "success": false,
  "error": "Unauthorized"
}
```
**Action**: Re-login (POST /auth/login)

### Forbidden (403)
```json
{
  "success": false,
  "error": "Only Admin/Teacher can create proposals"
}
```
Wrong role or insufficient permissions.

### Bad Request (400)
```json
{
  "success": false,
  "error": "Invalid payload"
}
```
Malformed JSON or missing required fields.

### Restore Lock (423)
```json
{
  "success": false,
  "error": "Restore lock enabled"
}
```
Server is in maintenance mode. Wait for restore to complete.

### Service Unavailable (503)
```json
{
  "success": false,
  "error": "Roster snapshot incomplete. Recovery required."
}
```
Server data is corrupted. Recovery in progress.

---

## Request/Response Payloads

### Teacher Scores (POST body)
```json
{
  "scores": [
    {
      "student_id": "EA24A01",
      "month": "2026-04",
      "date": "2026-04-04",
      "points": 5,
      "reason": "Excellent homework",
      "recordedBy": "Teacher",
      "timestamp": "2026-04-04T10:30:00.000Z"
    },
    {
      "student_id": "EA24A02",
      "month": "2026-04",
      "date": "2026-04-04",
      "points": -2,
      "reason": "Late submission",
      "recordedBy": "Teacher",
      "timestamp": "2026-04-04T10:31:00.000Z"
    }
  ]
}
```

### Attendance Records
```json
{
  "attendance": [
    {
      "student_id": "EA24A01",
      "date": "2026-04-04",
      "status": "present",
      "recordedBy": "Teacher",
      "timestamp": "2026-04-04T08:00:00.000Z"
    },
    {
      "student_id": "EA24A02",
      "date": "2026-04-04",
      "status": "absent",
      "reason": "Sick leave",
      "recordedBy": "Teacher",
      "timestamp": "2026-04-04T08:00:00.000Z"
    }
  ]
}
```

### Appeals
```json
{
  "appeals": [
    {
      "id": "appeal_123456",
      "student_id": "EA24A01",
      "type": "score_dispute",
      "title": "Score correction request",
      "description": "I believe my points are incorrect",
      "status": "pending",
      "createdBy": "Teacher",
      "timestamp": "2026-04-04T09:00:00.000Z"
    }
  ]
}
```

---

## Merge Strategy (Server-Side)

When teacher POSTs changes, server merges with existing data using **superset merge**:

### Scores
```python
existing_scores = [
  {id: 1, student: "EA24A01", points: 10, timestamp: "2026-04-03T10:00Z"},
  {id: 2, student: "EA24A02", points: 5, timestamp: "2026-04-03T11:00Z"}
]

incoming_scores = [
  {student: "EA24A01", points: 15, timestamp: "2026-04-04T10:00Z"},  # update
  {student: "EA24A03", points: 8, timestamp: "2026-04-04T10:05Z"}   # new
]

merged_scores = [
  {id: 1, student: "EA24A01", points: 15, timestamp: "2026-04-04T10:00Z"},  # newer timestamp wins
  {id: 2, student: "EA24A02", points: 5, timestamp: "2026-04-03T11:00Z"},   # preserved
  {student: "EA24A03", points: 8, timestamp: "2026-04-04T10:05Z"}           # added
]
```

### Attendance
```python
# Similar superset merge for attendance records
# Newer timestamp takes precedence
# All records preserved unless explicitly older
```

### Protected Tables (Never modified by teacher)
```
- leadership
- class_reps
- group_crs
- parties
- post_holder_history

# These are copied as-is from server to merged data
# Teacher changes to these are silently dropped
merged['leadership'] = existing['leadership']
```

---

## Edit Window Filter

Teacher changes to dates outside the **edit window** are dropped:

```
Current Date: 2026-04-04
Edit Window: N = 7 days

Allowed Window: 2026-03-28 to 2026-04-04

Requests:
✓ Date 2026-04-04 → KEPT (today)
✓ Date 2026-04-03 → KEPT (yesterday, 1 day ago)
✓ Date 2026-03-28 → KEPT (7 days ago, edge)
✗ Date 2026-03-27 → DROPPED (8 days ago, outside window)
✗ Date 2025-04-04 → DROPPED (1 year ago)
```

**Server Code**: `_filter_teacher_payload_to_edit_window()` at line 2285

---

## Operation ID (op_id) - Deduplication

Prevents duplicate POSTs when network is flaky:

```
Request 1:
POST /offline-data
{
  "data": {...},
  "op_id": "sync_op_1712235600000"
}
→ Response: 200 OK, processed

Request 2 (duplicate, due to network retry):
POST /offline-data
{
  "data": {...},
  "op_id": "sync_op_1712235600000"  // SAME op_id
}
→ Response: 200 OK, deduped
  {
    "success": true,
    "dedup": true,
    "updated_at": "2026-04-04T12:35:00.000Z"
  }

Result: Data processed only once, response returned immediately
```

---

## SSE Event Flow

Teacher sync generates sync events that propagate to all connected clients:

```
Timeline:
1. T0: Device 1 sends POST /offline-data
2. T0 + 50ms: Server saves data, broadcasts SSE event
3. T0 + 100ms: Device 2 receives SSE event via /offline-events
4. T0 + 100ms: Device 2 sees: {updated_at: "...", source: "teacher"}
5. T0 + 150ms: Device 2 auto-pulls GET /offline-data
6. T0 + 200ms: Device 2 has fresh data with changes from Device 1
```

---

## Error Scenarios

### Scenario: Version Conflict
```
Time    Device 1                    Server                      Device 2
────    ────────                    ──────                      ────────
  0     GET /offline-data
        received version: 41
  
  50    Makes local changes
        
  100                               Admin pushes new data
                                    version: 42
  
  150   POST with base_version: 41
        (base_version != 42)        
                                    409 Conflict response
  
  200   Receives 409
        Pulls fresh data
        GET /offline-data
                                    Returns version: 42
  
  250   Merges locally
        Re-POSTs with base_version: 42
        
  300                               Merges and returns 200 OK
                                    version: 43
  
  350   Device 1 synced                                         Still has version 42
  
  400                                                           Auto-sync triggered
                                                                GET /offline-data
                                                                
  450                                                          Receives version: 43
```

### Scenario: Network Timeout
```
Device 1 sends POST /offline-data
↓
Network timeout (no response)
↓
Device 1 retries with SAME op_id
↓
Server receives retry
↓
Server checks: is op_id in dedup table?
↓
Yes → Return cached response (no reprocessing)
No → Process and cache
```

---

## Headers Reference

### Request Headers (Teacher POST)
```
POST /points/offline-data HTTP/1.1
Host: server:5000
Content-Type: application/json
Content-Length: 45678
Accept: application/json
Cookie: session=abc123def456
Connection: keep-alive
User-Agent: Mozilla/5.0...
```

### Response Headers (Success)
```
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 234
Cache-Control: no-store
Set-Cookie: session=abc123def456; Path=/; HttpOnly; SameSite=Lax
Date: Fri, 04 Apr 2026 12:35:00 GMT
```

### Response Headers (Conflict)
```
HTTP/1.1 409 Conflict
Content-Type: application/json; charset=utf-8
Cache-Control: no-store
Date: Fri, 04 Apr 2026 12:35:00 GMT
```

---

## Testing with cURL

### Login
```bash
curl -c cookies.txt -X POST http://localhost:5000/auth/login \
  -d "login_id=Teacher&password=ChangeTeacherPass123!"
```

### Get Data
```bash
curl -b cookies.txt http://localhost:5000/points/offline-data \
  -H "Accept: application/json" | jq '.data | keys'
```

### Push Changes
```bash
curl -b cookies.txt -X POST http://localhost:5000/points/offline-data \
  -H "Content-Type: application/json" \
  -d @payload.json | jq '.'
```

### Watch SSE
```bash
curl -b cookies.txt -N http://localhost:5000/points/offline-events
```

---

## Monitoring Checklist

- [ ] POST requests complete within 5 seconds
- [ ] Response always includes `updated_at` and `server_version`
- [ ] SSE stream connects and receives events
- [ ] Version numbers increment monotonically
- [ ] No 409 conflicts on normal operation
- [ ] No 403/401 after initial login
- [ ] No 503 errors (data corruption)
- [ ] Cache-Control headers prevent stale data
- [ ] Session cookies persist across restarts

