import json
from datetime import datetime

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'

def repair():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    changed = False

    # 1. Purge duplicates and fix main records
    students = data.get('students', [])
    new_students = []
    ayush = None
    tanu = None

    # Identify Ayush (1) and Tanu (4)
    for s in students:
        sid = int(s.get('id', 0))
        if sid == 1:
            ayush = s
        elif sid == 4:
            tanu = s

    # If they don't exist, we have a bigger problem, but let's assume they do.
    # If they are missing, we should find them by name.
    if not ayush:
        ayush = next((s for s in students if 'AYUSH GUPTA' in str(s.get('name','')).upper()), None)
        if ayush: ayush['id'] = 1
    if not tanu:
        tanu = next((s for s in students if 'TANU SINHA' in str(s.get('name','')).upper()), None)
        if tanu: tanu['id'] = 4

    # Now filter out anyone else claiming their rolls or IDs
    protected_rolls = {'EA24A01', 'EA24B15', 'EA24A04', 'EA24B16'}
    for s in students:
        sid = int(s.get('id', 0))
        roll = str(s.get('roll', '')).upper()
        name = str(s.get('name', '')).upper()
        
        # Don't keep ghost records
        if sid in {1, 4}:
            if sid == 1:
                s['roll'] = 'EA24B15' # Force current roll
                s['name'] = 'Ayush Gupta (CR)'
                s['base_name'] = 'Ayush Gupta'
                s['active'] = True
            if sid == 4:
                s['roll'] = 'EA24B16' # Force current roll
                s['name'] = 'Tanu Sinha'
                s['base_name'] = 'Tanu Sinha'
                s['active'] = True
            new_students.append(s)
            continue
        
        # If it's a different ID but has their rolls or names, skip it (it's a duplicate)
        if roll in protected_rolls:
            print(f"Purging duplicate student ID {sid} with roll {roll}")
            changed = True
            continue
        if 'AYUSH GUPTA' in name or 'TANU SINHA' in name:
            print(f"Purging duplicate student ID {sid} with name {name}")
            changed = True
            continue
            
        new_students.append(s)

    data['students'] = new_students

    # 2. Fix Month Roster Profiles
    profiles = data.get('month_roster_profiles', {})
    for month, p_list in profiles.items():
        for p in p_list:
            roll = str(p.get('roll', '')).upper()
            if roll == 'EA24A01' or roll == 'EA24B15':
                if p.get('studentId') != 1:
                    p['studentId'] = 1
                    p['name'] = 'Ayush Gupta'
                    print(f"Fixed Ayush profile in {month}")
                    changed = True
            elif roll == 'EA24A04' or roll == 'EA24B16':
                if p.get('studentId') != 4:
                    p['studentId'] = 4
                    p['name'] = 'Tanu Sinha'
                    print(f"Fixed Tanu profile in {month}")
                    changed = True

    # 3. Fix Scores
    scores = data.get('scores', [])
    for s in scores:
        sid = s.get('studentId')
        # If studentId is a roll or wrong ID
        if sid == 'EA24A01' or sid == 'EA24B15' or (isinstance(sid, int) and sid != 1 and str(s.get('notes', '')).lower().startswith('excel') and 'Ayush' in str(s.get('notes', ''))):
            s['studentId'] = 1
            changed = True
        elif sid == 'EA24A04' or sid == 'EA24B16':
            s['studentId'] = 4
            changed = True

    # 4. Roll History
    # We want to ensure that for all months until 2026-03, their rolls were A01/A04
    history = data.get('roll_history', [])
    # Clean up existing Ayush/Tanu history to avoid duplicates
    history = [h for h in history if int(h.get('student_id', 0)) not in {1, 4}]
    
    # Add definitive history
    history.append({
        "student_id": 1,
        "old_roll": "EA24A01",
        "new_roll": "EA24B15",
        "effective_month": "2026-04",
        "reason": "Promotion/Roll Update",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    history.append({
        "student_id": 4,
        "old_roll": "EA24A04",
        "new_roll": "EA24B16",
        "effective_month": "2026-04",
        "reason": "Promotion/Roll Update",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    data['roll_history'] = history
    changed = True

    # Update timestamp
    data['server_updated_at'] = datetime.utcnow().isoformat() + "Z"
    data['server_version'] = data.get('server_version', 0) + 1

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print("Repair complete.")

if __name__ == '__main__':
    repair()
