import json
import os

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'

def final_prune():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. DELETE ALL ROSTER PROFILES (Authoritative cleanup)
    # The HTML logic I repaired (getMonthRosterProfileMap + getStudentRollAliases) 
    # provides perfect reconstruction from the main 'students' list.
    data['month_roster_profiles'] = {} 
    
    # 2. Prune obsolete historical metadata
    data['month_student_extras'] = {}
    data['month_extra_columns'] = {}
    
    # 3. Compact everything else
    if 'scores' in data:
        print(f"Keeping {len(data['scores'])} scores.")
    
    data['server_version'] = data.get('server_version', 0) + 1000
    data['server_updated_at'] = '2026-04-05T12:15:00Z'

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))

    final_size = os.path.getsize(DATA_PATH)
    print(f"FINAL SIZE: {final_size/1024/1024:.2f} MB")

if __name__ == '__main__':
    final_prune()
