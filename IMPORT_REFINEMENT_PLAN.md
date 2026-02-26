# Import Refinement Plan

## Current Issues:
1. Single import endpoint handles all data (historical + current)
2. No separation between historical data and latest roster
3. Student active/inactive status can be overwritten
4. Import can affect system settings and logic

## Requirements:
1. **Historical Data Import**: Previous months ONLY (exclude current month)
2. **Latest Roster Import**: Current month ONLY (exclude previous months)
3. **Preserve Student Status**: Active/inactive status from system takes precedence
4. **Scoreboard Tally Only**: Excel only updates scores, not settings/logic
5. **Data Isolation**: Two import types must not interfere with each other

## Implementation Plan:

### 1. Create Separate Import Functions:
- `import_historical_data()` - for previous months
- `import_latest_roster()` - for current month roster

### 2. Date Filtering Logic:
```python
current_month_start = datetime.now().replace(day=1).date()

# Historical: date < current_month_start
# Latest Roster: date >= current_month_start
```

### 3. Student Status Preservation:
```python
# Load existing offline data
existing_data = load_offline_scoreboard_data()
existing_students = {s['roll']: s for s in existing_data.get('students', [])}

# For each imported student:
if student_roll in existing_students:
    # Preserve active status from system
    student_data['active'] = existing_students[student_roll].get('active', True)
else:
    # New student - default to active
    student_data['active'] = True
```

### 4. Scoreboard Tally Only:
- Only update: scores, points, dates
- Never update: active status, system settings, configurations
- Preserve: student metadata, preferences, all system logic

### 5. Two-Endpoint Approach:
- `/import-historical-data` - Historical import
- `/import-latest-roster` - Current month roster
- Both use parameter `import_type` to distinguish
