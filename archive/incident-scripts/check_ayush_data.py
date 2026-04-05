import json

# Load current data
with open('instance/offline_scoreboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find Ayush
students = [s for s in data['students'] if 'ayush' in s.get('name', '').lower()]
print("=" * 60)
print("AYUSH CURRENT DATA:")
print("=" * 60)
for s in students:
    print(f"ID: {s['id']}, Roll: {s.get('roll')}, Name: {s.get('name')}")

# Check Feb 2026 profile
feb_profiles = data.get('month_roster_profiles', {}).get('2026-02', [])
ayush_feb = [p for p in feb_profiles if 'ayush' in p.get('name', '').lower()]
print("\nAYUSH FEB 2026 PROFILE:")
print("=" * 60)
for p in ayush_feb:
    print(f"Roll: {p.get('roll')}, Name: {p.get('name')}")

# Check Feb 2026 scores for Ayush
ayush_id = students[0]['id'] if students else None
if ayush_id:
    feb_scores = [s for s in data['scores'] 
                  if (s.get('month') == '2026-02' or s.get('date', '')[:7] == '2026-02')
                  and s.get('studentId') == ayush_id]
    print(f"\nAYUSH FEB 2026 SCORES: {len(feb_scores)} scores")
    total_points = sum(s.get('points', 0) for s in feb_scores)
    print(f"Total points: {total_points}")

# Find Rehmetun
rehmetun = [s for s in data['students'] if 'rehmetun' in s.get('name', '').lower()]
print("\n" + "=" * 60)
print("REHMETUN CURRENT DATA:")
print("=" * 60)
for s in rehmetun:
    print(f"ID: {s['id']}, Roll: {s.get('roll')}, Name: {s.get('name')}")

# Check Rehmetun Feb 2026 scores
if rehmetun:
    rehmetun_id = rehmetun[0]['id']
    feb_scores = [s for s in data['scores'] 
                  if (s.get('month') == '2026-02' or s.get('date', '')[:7] == '2026-02')
                  and s.get('studentId') == rehmetun_id]
    print(f"\nREHMETUN FEB 2026 SCORES: {len(feb_scores)} scores")
    total_points = sum(s.get('points', 0) for s in feb_scores)
    print(f"Total points: {total_points}")

# Check month_students for Feb 2026
feb_students = data.get('month_students', {}).get('2026-02', [])
print("\n" + "=" * 60)
print(f"FEB 2026 MONTH_STUDENTS: {len(feb_students)} students")
print("=" * 60)
print("Sample rolls:", feb_students[:10] if len(feb_students) > 10 else feb_students)
