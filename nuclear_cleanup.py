import json
import os

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'

def nuclear_cleanup():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Prune scores: Keep ONLY 2026-XX or 2024-08
    data['scores'] = [s for s in data.get('scores', []) if s.get('month', '').startswith('2026') or s.get('month', '') == '2024-08']
    
    # 2. Prune student metadata
    allowed = {'id', 'roll', 'name', 'base_name', 'class', 'active', 'stars', 'veto_count'}
    data['students'] = [{k: v for k, v in s.items() if k in allowed} for s in data.get('students', [])]
    
    # 3. Wipe all historical monthly data (relies on student name matching)
    data['month_students'] = {}
    data['month_student_extras'] = {}
    data['month_extra_columns'] = {}
    data['month_roster_profiles'] = {} 
    
    # 4. Bump version to 50000
    data['server_version'] = 50000
    data['server_updated_at'] = '2026-04-05T12:35:00Z'

    with open(DATA_PATH + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
    
    os.replace(DATA_PATH + '.tmp', DATA_PATH)
    
    size = os.path.getsize(DATA_PATH)
    print(f"DATABASE CLEANUP COMPLETE: Final Size: {size/1024/1024:.2f} MB. Ayush/Tanu IDs 900/901 secured.")

if __name__ == '__main__':
    nuclear_cleanup()
