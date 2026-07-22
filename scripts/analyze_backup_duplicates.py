import json
from collections import defaultdict

with open(r'instance\BACKUP_FEB_APR_2026_20260405_134210.json', 'r', encoding='utf-8') as f:
    backup = json.load(f)

# Check for duplicate rolls
rolls = defaultdict(list)
for s in backup['students']:
    rolls[s.get('roll', '')].append(s.get('name', ''))

duplicates = {r: names for r, names in rolls.items() if len(names) > 1}

print(f"Total students in backup: {len(backup['students'])}")
print(f"Duplicate rolls: {len(duplicates)}\n")

if duplicates:
    print("Duplicate roll examples:")
    for roll, names in list(duplicates.items())[:10]:
        print(f"  {roll}: {names}")

# Check active/inactive split
active = sum(1 for s in backup['students'] if s.get('active') != False)
inactive = len(backup['students']) - active
print(f"\nActive: {active}, Inactive: {inactive}")

# Check roll prefixes
ea24 = sum(1 for s in backup['students'] if str(s.get('roll', '')).startswith('EA24'))
ea25 = sum(1 for s in backup['students'] if str(s.get('roll', '')).startswith('EA25'))
ea26 = sum(1 for s in backup['students'] if str(s.get('roll', '')).startswith('EA26'))
other = len(backup['students']) - ea24 - ea25 - ea26
print(f"\nRoll prefixes: EA24={ea24}, EA25={ea25}, EA26={ea26}, Other={other}")
