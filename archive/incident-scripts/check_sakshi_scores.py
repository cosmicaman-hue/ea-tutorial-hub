import json

DB_PATH = r'c:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'

with open(DB_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

scores = data.get('scores', [])

print('Scores for EA24C06 (old roll):')
for s in scores:
    if s.get('roll') == 'EA24C06':
        print(f"  Month: {s.get('month')}, Stars: {s.get('stars')}, StudentId: {s.get('studentId')}")

print('\nScores for EA24D32 (new roll):')
for s in scores:
    if s.get('roll') == 'EA24D32':
        print(f"  Month: {s.get('month')}, Stars: {s.get('stars')}, StudentId: {s.get('studentId')}")

print('\nScores for student id 98 (new roll student):')
for s in scores:
    if s.get('studentId') == 98:
        print(f"  Roll: {s.get('roll')}, Month: {s.get('month')}, Stars: {s.get('stars')}")
