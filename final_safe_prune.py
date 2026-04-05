import json
import os

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'

def final_safe_prune():
    if not os.path.exists(DATA_PATH): return
    
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Prune scores: Keep only 2025-2026, OR 2024-08 for our fixed IDs
    original_count = len(data.get('scores', []))
    pruned_scores = []
    for s in data.get('scores', []):
        m = str(s.get('month', ''))
        sid = int(s.get('studentId', 0))
        # Keep recent history (2025 onwards) OR our critical August 2024 repair
        if m >= '2025-01' or (m == '2024-08' and sid in [900, 901]):
            pruned_scores.append(s)
    
    data['scores'] = pruned_scores
    print(f"Scores pruned: {original_count} -> {len(pruned_scores)}")

    # 2. Re-bind students and rosters to ensure 900/901 dominance
    students = data.get('students', [])
    data['students'] = [s for s in students if s.get('id') in [900, 901] or (int(s.get('id',0)) > 4)]
    
    # Ensure IDs 900/901 exist
    if not any(s.get('id') == 900 for s in data['students']):
        data['students'].append({"id":900,"roll":"EA24B15","name":"Ayush Gupta (CR)","base_name":"Ayush Gupta","class":12,"active":True})
    if not any(s.get('id') == 901 for s in data['students']):
        data['students'].append({"id":901,"roll":"EA24B16","name":"Tanu Sinha","base_name":"Tanu Sinha","class":12,"active":True})

    # 3. Bump version and force fresh pull
    data['server_version'] = 9999
    data['server_updated_at'] = '2026-04-05T12:20:00Z'
    data['month_roster_profiles'] = {} # Full clear to save space - HTML re-renders from Students + history

    # 4. Atomic Write (Ensures no stale trailing data)
    with open(DATA_PATH + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
    
    os.replace(DATA_PATH + '.tmp', DATA_PATH)
    
    fsize = os.path.getsize(DATA_PATH)
    print(f"Final File Size: {fsize/1024/1024:.2f} MB")

if __name__ == '__main__':
    final_safe_prune()
