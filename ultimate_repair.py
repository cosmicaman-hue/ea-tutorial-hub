import json
import os
from datetime import datetime

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'

def final_repair():
    if not os.path.exists(DATA_PATH):
        print("Data file not found!")
        return

    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. FIX AYUSH AND TANU RECORDS ONCE AND FOR ALL
    students = data.get('students', [])
    # Find them
    ayush = next((s for s in students if int(s.get('id', 0)) == 1), None)
    tanu = next((s for s in students if int(s.get('id', 0)) == 4), None)
    
    # Force their current metadata
    if ayush:
        ayush['roll'] = 'EA24B15'
        ayush['name'] = 'Ayush Gupta (CR)'
        ayush['active'] = True
    if tanu:
        tanu['roll'] = 'EA24B16'
        tanu['name'] = 'Tanu Sinha'
        tanu['active'] = True

    # 2. FIX ROLL HISTORY
    # Ensure ID 1 and ID 4 have historical rolls mapped
    data['roll_history'] = [h for h in data.get('roll_history', []) if int(h.get('student_id', 0)) not in [1, 4]]
    data['roll_history'].append({
        "student_id": 1, "old_roll": "EA24A01", "new_roll": "EA24B15",
        "effective_month": "2026-04", "reason": "System Re-roll", "timestamp": "2026-04-05T00:00:00Z"
    })
    data['roll_history'].append({
        "student_id": 4, "old_roll": "EA24A04", "new_roll": "EA24B16",
        "effective_month": "2026-04", "reason": "System Re-roll", "timestamp": "2026-04-05T00:00:00Z"
    })

    # 3. RESTORE MISSING ROSTERS (Crucial for visibility)
    # If a month roster has only a few students, it's corrupted. We'll fill it from all student IDs.
    all_rolls = [s.get('roll') for s in students if s.get('roll')]
    all_active_rolls = [s.get('roll') for s in students if s.get('active') is not False]
    
    historical_months = [
        '2024-08', '2024-09', '2024-10', '2024-11', '2024-12',
        '2025-01', '2025-02', '2025-03', '2025-04', '2025-05', '2025-06',
        '2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12',
        '2026-01', '2026-02', '2026-03'
    ]
    
    if 'month_students' not in data: data['month_students'] = {}
    
    for m in historical_months:
        roster = data['month_students'].get(m, [])
        if len(roster) < 20: # Arbitrary threshold for "broken"
            print(f"Repairing broken roster for {m} (Current size: {len(roster)})")
            # For A-series months, we must ensure EA24A01 etc are in the roster
            # We'll just put all rolls in.
            data['month_students'][m] = list(set(roster + all_active_rolls + ['EA24A01', 'EA24A04']))

    # 4. FIX MONTH ROSTER PROFILES (Authoritative mapping)
    if 'month_roster_profiles' not in data: data['month_roster_profiles'] = {}
    for m in historical_months:
        profiles = data['month_roster_profiles'].get(m, [])
        # Ensure Ayush profile exists and is correctly bound to ID 1
        found_ayush = False
        for p in profiles:
            roll = str(p.get('roll', '')).upper()
            if roll == 'EA24A01' or roll == 'EA24B15':
                p['studentId'] = 1
                p['name'] = 'Ayush Gupta'
                found_ayush = True
        if not found_ayush:
            profiles.append({
                "studentId": 1, "roll": "EA24A01", "name": "Ayush Gupta",
                "month_star_count": 0, "month_veto_count": 0, "month_designations": [], "locked": True
            })
        data['month_roster_profiles'][m] = profiles

    # 5. FIX SCORES (ID binding)
    scores = data.get('scores', [])
    for s in scores:
        sid = s.get('studentId')
        # If studentId is missing or wrong for Ayush scores
        notes = str(s.get('notes', '')).lower()
        if 'ayush' in notes or str(s.get('roll', '')).upper() == 'EA24A01':
            s['studentId'] = 1
        elif 'tanu' in notes or str(s.get('roll', '')).upper() == 'EA24A04':
            s['studentId'] = 4

    # FINAL: Force version jump
    data['server_version'] = data.get('server_version', 0) + 10
    data['server_updated_at'] = datetime.utcnow().isoformat() + "Z"

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print("ULTIMATE REPAIR SUCCESSFUL.")

if __name__ == '__main__':
    final_repair()
