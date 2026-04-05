# Complete VETO System Implementation Guide

## Overview
This VETO system implements the exact logic you specified:
1. **Remove all VETOs from everyone**
2. **Grant individual VETOs to specific students**
3. **Add role-grant VETOs to post-holders**
4. **Harden the VETO map**
5. **Track usage with deduction from global counter**

## Quick Start

### Step 1: Initialize the VETO System
Run the VETO manager to set up the complete system:

```bash
python veto_manager.py
```

This will execute all 5 steps:
- Remove all existing VETOs
- Grant individual VETOs to the 9 specified students
- Add role VETOs to active post-holders
- Harden the system
- Show final status

### Step 2: Use the VETO System
Once initialized, you can:
- Check VETO balances via API
- Use VETOs with automatic deduction
- View usage logs
- Monitor system status

## Individual VETO Assignments

The system grants individual VETOs to these students:
- **Ayush** - 1V
- **Arman** - 1V  
- **Vishes** - 1V
- **Pari** - 1V
- **Rashi** - 1V
- **Sahil** - 3V
- **Sakshi** - 1V
- **Reeyansh** - 3V
- **Nandani** - 1V

## Role VETO Quotas

Post-holders receive additional VETOs:
- **LEADER** - 5 role VETOs
- **LEADER OF OPPOSITION** - 2 role VETOs
- **CO-LEADER** - 3 role VETOs
- **CR (Class Representative)** - 2 role VETOs

## API Endpoints

### System Status
```http
GET /api/veto/status
```
Returns complete VETO system status.

### Student Balance
```http
GET /api/veto/balance/{roll}
```
Get VETO balance for a specific student.

### Use VETOs
```http
POST /api/veto/use
{
  "roll": "EA24A01",
  "count": 1,
  "reason": "Used for quiz exemption"
}
```
Deducts VETOs from the student's balance.

### Top Holders
```http
GET /api/veto/top-holders?limit=10
```
Get students with most remaining VETOs.

### Usage Log
```http
GET /api/veto/usage?limit=20
```
Get recent VETO usage history.

### Initialize System (Admin Only)
```http
POST /api/veto/initialize
```
Re-run the complete VETO setup process.

### Setup Information
```http
GET /api/veto/setup-info
```
Get information about VETO assignments and quotas.

## Data Structure

### Student VETO Record
```json
{
  "roll": "EA24A01",
  "name": "Student Name",
  "individual_vetos": 1,
  "role_vetos": 3,
  "total_vetos": 4,
  "used_vetos": 1,
  "remaining_vetos": 3
}
```

### Usage Log Entry
```json
{
  "timestamp": "2026-03-20T13:30:00",
  "roll": "EA24A01",
  "name": "Student Name",
  "vetos_used": 1,
  "remaining_after": 2,
  "reason": "Quiz exemption",
  "action": "veto_used"
}
```

## File Structure

### Main Data File
`instance/offline_scoreboard_data.json`
- Contains hardened VETO tracking data
- Backups created automatically
- Atomic operations prevent corruption

### VETO Manager
`veto_manager.py`
- Complete VETO system implementation
- Executes all setup steps
- Handles VETO usage with deduction

### Integration Layer
`app/utils/veto_manager_integration.py`
- Flask app integration
- API access to VETO system
- Thread-safe operations

### API Routes
`app/routes/veto_api.py`
- RESTful API endpoints
- Admin controls
- Real-time balance queries

## Usage Examples

### Python Script Usage
```python
from veto_manager import VetoManager

# Initialize system
manager = VetoManager()
manager.complete_veto_setup()

# Use VETOs
success, message = manager.use_veto('EA24A01', 1, 'Test usage')

# Check balance
balance = manager.get_veto_balance('EA24A01')
print(f"Remaining: {balance['remaining_vetos']}")

# Get system status
status = manager.get_system_status()
print(f"Total VETOs allocated: {status['total_vetos_allocated']}")
```

### API Usage
```javascript
// Check system status
fetch('/api/veto/status')
  .then(r => r.json())
  .then(data => console.log(data));

// Use VETO
fetch('/api/veto/use', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    roll: 'EA24A01',
    count: 1,
    reason: 'Quiz exemption'
  })
});
```

## Safety Features

### Data Integrity
- ✅ Automatic backups before any changes
- ✅ Atomic file operations (temp + rename)
- ✅ Corruption detection and recovery
- ✅ Thread-safe operations

### Access Control
- ✅ Admin-only initialization
- ✅ Login required for all operations
- ✅ Roll-based access validation

### Audit Trail
- ✅ Complete usage logging
- ✅ Timestamp tracking
- ✅ Reason recording
- ✅ Before/after values

## Troubleshooting

### System Not Initialized
Error: "VETO system is not hardened"
**Solution**: Run `python veto_manager.py`

### Student Not Found
Error: "Student {roll} not found"
**Solution**: Check if the student exists in the main data file

### Insufficient VETOs
Error: "Insufficient VETOs. Available: X, Requested: Y"
**Solution**: Check current balance before using VETOs

### File Corruption
If data file gets corrupted:
1. Check for backup files: `instance/offline_scoreboard_data_backup_*.json`
2. Restore the latest backup
3. Re-run `python veto_manager.py`

## Monitoring

### System Health
```python
from app.utils.veto_manager_integration import get_veto_manager

manager = get_veto_manager()
status = manager.get_system_status()

print(f"Status: {status['status']}")
print(f"Students with VETOs: {status['students_with_vetos']}")
print(f"Total allocated: {status['total_vetos_allocated']}")
print(f"Total used: {status['total_vetos_used']}")
print(f"Total remaining: {status['total_vetos_remaining']}")
```

### Recent Activity
```python
# Get recent usage
usage = manager.get_recent_usage(10)
for entry in usage:
    print(f"{entry['timestamp']} | {entry['name']} used {entry['vetos_used']} VETOs")
```

## Best Practices

### Before Using VETOs
1. Always check available balance first
2. Provide meaningful reason for usage
3. Log the usage for audit purposes

### System Maintenance
1. Regularly backup the `instance/` directory
2. Monitor usage patterns
3. Review VETO allocations periodically

### Security
1. Keep the VETO manager script secure
2. Regular admin access reviews
3. Monitor for unusual usage patterns

## Complete Workflow Example

1. **Initial Setup** (One-time):
   ```bash
   python veto_manager.py
   ```

2. **Daily Usage**:
   ```python
   # Check balance
   manager = get_veto_manager()
   balance = manager.get_veto_balance('EA24A01')
   
   # Use VETO if available
   if balance and balance.remaining_vetos > 0:
       success, msg = manager.use_veto('EA24A01', 1, 'Used for debate')
       print(msg)
   ```

3. **Monthly Review**:
   ```python
   # Get system status
   status = manager.get_system_status()
   print(f"VETOs used this month: {status['total_vetos_used']}")
   
   # Get top users
   top_users = manager.get_top_holders(5)
   for user in top_users:
       print(f"{user['name']}: {user['remaining_vetos']} remaining")
   ```

This system now fully implements your VETO logic with proper tracking, security, and data preservation!
