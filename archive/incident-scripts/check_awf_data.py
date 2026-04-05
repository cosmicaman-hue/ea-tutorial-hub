import json

# Load current data
with open('instance/offline_scoreboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check Feb 2026 month_student_extras for AWF flags
feb_extras = data.get('month_student_extras', {}).get('2026-02', {})

print("=" * 60)
print("FEB 2026 STUDENT EXTRAS (AWF FLAGS)")
print("=" * 60)

# Find Ayush
students = [s for s in data['students'] if 'ayush' in s.get('name', '').lower()]
ayush_roll = students[0].get('roll') if students else None
print(f"\nAyush current roll: {ayush_roll}")

# Check for AWF in extras
awf_students = []
for key, value in feb_extras.items():
    if isinstance(value, dict) and value.get('AWF'):
        awf_students.append((key, value.get('AWF')))
        print(f"\nRoll: {key}")
        print(f"  AWF: {value.get('AWF')}")
        print(f"  Full data: {value}")

print(f"\n\nTotal students with AWF in Feb 2026: {len(awf_students)}")

# Check if Ayush has AWF under any roll number
ayush_awf_found = False
for key, awf_val in awf_students:
    if 'ayush' in key.lower() or 'ea24a01' in key.lower() or 'ea24b16' in key.lower():
        print(f"\n✓ AYUSH FOUND with AWF: Roll key = {key}, AWF = {awf_val}")
        ayush_awf_found = True

if not ayush_awf_found:
    print("\n✗ AYUSH NOT FOUND in AWF list - this is the problem!")
    print("\nChecking all keys for Ayush-related entries:")
    for key in feb_extras.keys():
        if 'a01' in key.lower() or 'b16' in key.lower():
            print(f"  Key: {key}, Data: {feb_extras[key]}")
