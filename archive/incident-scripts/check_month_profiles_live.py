import json

LIVE_PATH = r'C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json'

with open(LIVE_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

mrp = data.get('month_roster_profiles', {})

print('EA24C06 in month_roster_profiles:')
for month, profiles in mrp.items():
    for p in profiles:
        if p.get('roll') == 'EA24C06':
            print(f'  {month}: roll={p.get("roll")}, name={p.get("name")}, studentId={p.get("studentId")}')

print('\nEA24D32 in month_roster_profiles:')
for month, profiles in mrp.items():
    for p in profiles:
        if p.get('roll') == 'EA24D32':
            print(f'  {month}: roll={p.get("roll")}, name={p.get("name")}, studentId={p.get("studentId")}')
