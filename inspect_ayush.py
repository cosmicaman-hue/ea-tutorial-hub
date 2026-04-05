import json

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'

def inspect():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ayush_id = 1
    ayush_id_str = str(ayush_id)
    
    # Check 1: Student Record
    student_list = data.get('students', [])
    ayush = next((s for s in student_list if str(s.get('id')) == ayush_id_str), None)
    print(f"AYUSH STUDENT RECORD: {ayush}")

    # Check 2: Month Roster Profiles
    months = ['2024-08', '2024-10', '2025-10', '2026-01', '2026-02', '2026-03', '2026-04']
    print("\n--- ROSTER PROFILES ---")
    profiles_map = data.get('month_roster_profiles', {})
    for m in months:
        m_profiles = profiles_map.get(m, [])
        p_by_id = next((p for p in m_profiles if str(p.get('studentId') or p.get('student_id')) == ayush_id_str), None)
        p_by_roll = next((p for p in m_profiles if str(p.get('roll','')).upper() in ['EA24A01', 'EA24B15']), None)
        
        display_name = p_by_id.get('name', 'NO_NAME') if p_by_id else 'NO_PROFILE'
        display_roll = p_by_id.get('roll', 'NO_ROLL') if p_by_id else 'NO_PROFILE'
        print(f"Month {m}: ID Match: Roll={display_roll}, Name={display_name}")
        if p_by_roll and (not p_by_id or p_by_roll.get('roll') != p_by_id.get('roll')):
            print(f"      - Found DIFFERENT Profile by Roll: {p_by_roll.get('roll')} (ID={p_by_roll.get('studentId') or p_by_roll.get('student_id')})")

    # Check 3: Roll History
    print("\n--- ROLL HISTORY ---")
    history = [h for h in data.get('roll_history', []) if str(h.get('student_id') or h.get('studentId')) == ayush_id_str]
    for h in history:
        print(f"  {h}")

    # Check 4: Scores (Sample)
    print("\n--- SCORES CHECK ---")
    scores = data.get('scores', [])
    for m in months:
        m_scores = [s for s in scores if str(s.get('studentId')) == ayush_id_str and (s.get('month') == m or (not s.get('month') and str(s.get('date',''))[:7] == m))]
        print(f"  Month {m}: Score Count = {len(m_scores)}")

if __name__ == '__main__':
    inspect()
