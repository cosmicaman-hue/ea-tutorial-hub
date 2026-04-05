import json
import os

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'

def prune_and_repair():
    if not os.path.exists(DATA_PATH):
        print("File not found")
        return

    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. PRUNE: Remove huge historical roster profiles to fit in localStorage.
    # Keep only 2026-02 onwards as authoritative. Fallback to students list for earlier.
    rosters = data.get('month_roster_profiles', {})
    pruned_rosters = {m: p for m, p in rosters.items() if m >= '2026-02'}
    data['month_roster_profiles'] = pruned_rosters
    print(f"Pruned rosters: {len(rosters)} -> {len(pruned_rosters)}")

    # 2. PRUNE: Remove long redundant notes in scores
    scores = data.get('scores', [])
    for s in scores:
        if len(str(s.get('notes', ''))) > 100:
            s['notes'] = s['notes'][:100] + "..."
    
    # 3. ENSURE ID 900 AND 901 ARE CORRECT (Ayush & Tanu)
    students = data.get('students', [])
    # Re-check and re-bind if anything shifted
    ayush = next((s for s in students if s.get('id') == 900), None)
    tanu = next((s for s in students if s.get('id') == 901), None)
    
    if not ayush:
        students.append({
            "id": 900, "roll": "EA24B15", "name": "Ayush Gupta (CR)", "base_name": "Ayush Gupta",
            "class": 12, "active": True, "stars": 15, "veto_count": 6
        })
    if not tanu:
        students.append({
            "id": 901, "roll": "EA24B16", "name": "Tanu Sinha", "base_name": "Tanu Sinha",
            "class": 12, "active": True
        })
    data['students'] = students

    # 4. BUMP VERSION TO FORCE RE-SYNC
    data['server_version'] = data.get('server_version', 0) + 500 # Big jump
    data['server_updated_at'] = '2026-04-05T12:10:00Z'

    output_path = DATA_PATH
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':')) # No whitespace to minimize size
    
    final_size = os.path.getsize(output_path)
    print(f"SUCCESS: Final database size: {final_size/1024/1024:.2f} MB")

if __name__ == '__main__':
    prune_and_repair()
