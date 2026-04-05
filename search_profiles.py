import json

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'

def search_profiles():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    profiles = data.get('month_roster_profiles', {})
    for m, list_m in profiles.items():
        for p in list_m:
            name = str(p.get('name', '')).upper()
            base_name = str(p.get('base_name', '')).upper()
            if 'EA24A01' in name or 'EA24A01' in base_name:
                print(f"Month {m}: Name literal EA24A01 found: {p}")

if __name__ == '__main__':
    search_profiles()
