import json
import os

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'

def final_nuclear_prune():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    keep_months = ['2026-01', '2026-02', '2026-03', '2026-04', '2024-08']
    
    # 1. Prune scores aggressively
    pruned_scores = []
    for s in data.get('scores', []):
        m = str(s.get('month', ''))
        sid = int(s.get('studentId', 0))
        if m in ['2026-01', '2026-02', '2026-03', '2026-04'] or (m == '2024-08' and sid in [900, 901]):
            pruned_scores.append(s)
    data['scores'] = pruned_scores
    
    # 2. Prune students to core fields only
    allowed_student_keys = {'id', 'roll', 'name', 'base_name', 'class', 'active', 'stars', 'veto_count'}
    pruned_students = []
    for s in data.get('students', []):
        pruned_s = {k: v for k, v in s.items() if k in allowed_student_keys}
        pruned_students.append(pruned_s)
    data['students'] = pruned_students
    
    # 3. Clear all rosters and extras completely
    data['month_students'] = {}
    data['month_student_extras'] = {}
    data['month_extra_columns'] = {}
    data['month_roster_profiles'] = {} 
    data['fee_records'] = []

    # 4. Bump version to 30000
    data['server_version'] = 30000
    data['server_updated_at'] = '2026-04-05T12:30:00Z'

    with open(DATA_PATH + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
    
    os.replace(DATA_PATH + '.tmp', DATA_PATH)
    
    size = os.path.getsize(DATA_PATH)
    print(f"NUCLEAR PRUNE SUCCESS. Final Size: {size/1024/1024:.2f} MB. Keeping {len(pruned_scores)} scores.")

if __name__ == '__main__':
    final_nuclear_prune()
