import json

DB_PATH = r'c:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'

with open(DB_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

ms = data.get('month_students', {})
mrp = data.get('month_roster_profiles', {})

print('month_students keys:', list(ms.keys()))
print('\nEA24C06 in month_students:')
for k, v in ms.items():
    if 'EA24C06' in v:
        print(f'  {k}: {v}')

print('\nEA24D32 in month_students:')
for k, v in ms.items():
    if 'EA24D32' in v:
        print(f'  {k}: {v}')

print('\nmonth_roster_profiles keys:', list(mrp.keys()))
print('\nEA24C06 in month_roster_profiles:')
for k, v in mrp.items():
    rolls = [p['roll'] for p in v if p.get('roll') == 'EA24C06']
    if rolls:
        print(f'  {k}: {rolls}')

print('\nEA24D32 in month_roster_profiles:')
for k, v in mrp.items():
    rolls = [p['roll'] for p in v if p.get('roll') == 'EA24D32']
    if rolls:
        print(f'  {k}: {rolls}')
