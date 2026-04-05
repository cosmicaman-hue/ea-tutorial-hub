import json
import os

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'

def final_aggressive_prune():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    keep_months = ['2026-01', '2026-02', '2026-03', '2026-04', '2024-08']
    
    # Prune Scores
    pruned_scores = [s for s in data.get('scores', []) if s.get('month') in keep_months]
    data['scores'] = pruned_scores
    
    # Prune other per-month garbage
    for key in ['month_students', 'month_student_extras', 'month_extra_columns', 'month_roster_profiles']:
        if key in data:
            data[key] = {m: v for m, v in data[key].items() if m in keep_months} if isinstance(data[key], dict) else {}

    data['server_version'] = 20000 # Critical jump
    data['server_updated_at'] = '2026-04-05T12:25:00Z'

    with open(DATA_PATH + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
    
    os.replace(DATA_PATH + '.tmp', DATA_PATH)
    
    size = os.path.getsize(DATA_PATH)
    print(f"ULTRA PRUNE SUCCESS. Final Size: {size/1024/1024:.2f} MB. Keeping {len(pruned_scores)} scores.")

if __name__ == '__main__':
    final_aggressive_prune()
