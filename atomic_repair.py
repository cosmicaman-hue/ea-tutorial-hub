import json
import os
from datetime import datetime

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'
AYUSH_NEW_ID = 900
TANU_NEW_ID = 901

def atomic_repair():
    if not os.path.exists(DATA_PATH):
        print("Data file not found!")
        return

    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    students = data.get('students', [])
    scores = data.get('scores', [])
    rosters = data.get('month_roster_profiles', {})
    
    # 1. DELETE ALL TRACES OF OLD AYUSH/TANU FROM STUDENTS LIST
    # (Including duplicates)
    students = [s for s in students if int(s.get('id', 0)) not in [1, 4, AYUSH_NEW_ID, TANU_NEW_ID]]
    
    # 2. ADD FRESH REPAIRED IDENTITIES
    students.append({
        "id": AYUSH_NEW_ID, "roll": "EA24B15", "name": "Ayush Gupta (CR)", "base_name": "Ayush Gupta",
        "class": 12, "group": "A", "active": True, "stars": 15, "veto_count": 6
    })
    students.append({
        "id": TANU_NEW_ID, "roll": "EA24B16", "name": "Tanu Sinha", "base_name": "Tanu Sinha",
        "class": 12, "group": "B", "active": True, "stars": 0, "veto_count": 0
    })
    data['students'] = students

    # 3. REBIND ALL SCORES IN HISTORY
    count_ayush = 0
    count_tanu = 0
    for s in scores:
        sid = int(s.get('studentId', 0))
        roll = str(s.get('roll', '')).upper()
        notes = str(s.get('notes', '')).lower()
        
        # If it's ID 1 OR it mentions Ayush OR it's his old roll
        if sid == 1 or roll == 'EA24A01' or 'ayush' in notes:
            s['studentId'] = AYUSH_NEW_ID
            s['roll'] = 'EA24A01' if s.get('month', '') < '2026-04' else 'EA24B15'
            count_ayush += 1
        elif sid == 4 or roll == 'EA24A04' or 'tanu' in notes:
            s['studentId'] = TANU_NEW_ID
            s['roll'] = 'EA24A04' if s.get('month', '') < '2026-04' else 'EA24B16'
            count_tanu += 1
    
    print(f"Rebound {count_ayush} scores to Ayush (900) and {count_tanu} to Tanu (901).")

    # 4. REBIND ALL ROSTER PROFILES
    for month, profiles in rosters.items():
        new_profiles = []
        for p in profiles:
            sid = int(p.get('studentId', 0))
            roll = str(p.get('roll', '')).upper()
            
            if sid == 1 or roll == 'EA24A01' or 'AYUSH' in str(p.get('name','')).upper():
                p['studentId'] = AYUSH_NEW_ID
                p['name'] = 'Ayush Gupta'
                p['roll'] = 'EA24A01' if month < '2026-04' else 'EA24B15'
            elif sid == 4 or roll == 'EA24A04' or 'TANU' in str(p.get('name','')).upper():
                p['studentId'] = TANU_NEW_ID
                p['name'] = 'Tanu Sinha'
                p['roll'] = 'EA24A04' if month < '2026-04' else 'EA24B16'
        
    # 5. FIX ROLL HISTORY FOR NEW IDs
    data['roll_history'] = [h for h in data.get('roll_history', []) if int(h.get('student_id', 0)) not in [1, 4, AYUSH_NEW_ID, TANU_NEW_ID]]
    data['roll_history'].append({
        "student_id": AYUSH_NEW_ID, "old_roll": "EA24A01", "new_roll": "EA24B15",
        "effective_month": "2026-04", "reason": "System Re-roll", "timestamp": "2026-04-05T00:00:00Z"
    })
    data['roll_history'].append({
        "student_id": TANU_NEW_ID, "old_roll": "EA24A04", "new_roll": "EA24B16",
        "effective_month": "2026-04", "reason": "System Re-roll", "timestamp": "2026-04-05T00:00:00Z"
    })

    # 6. FORCE RE-SYNC
    data['server_version'] = data.get('server_version', 0) + 100
    data['server_updated_at'] = datetime.utcnow().isoformat() + "Z"

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print("ATOMIC ID REPAIR SUCCESSFUL. Ayush is now ID 900. Tanu is now ID 901.")

if __name__ == '__main__':
    atomic_repair()
