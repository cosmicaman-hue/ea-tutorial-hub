import json

# Load current data
with open('instance/offline_scoreboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 60)
print("CURRENT ROLL NUMBERS")
print("=" * 60)

# Check Ayush
ayush = [s for s in data['students'] if 'ayush' in s.get('name', '').lower()]
if ayush:
    print(f"\nAyush:")
    print(f"  ID: {ayush[0]['id']}")
    print(f"  Current Roll: {ayush[0].get('roll')}")
    print(f"  Name: {ayush[0].get('name')}")
    print(f"  Target Roll: EA24A01")
    print(f"  Status: {'✓ CORRECT' if ayush[0].get('roll') == 'EA24A01' else '✗ NEEDS RESTORATION'}")

# Check Tanu
tanu = [s for s in data['students'] if 'tanu' in s.get('name', '').lower()]
if tanu:
    print(f"\nTanu:")
    print(f"  ID: {tanu[0]['id']}")
    print(f"  Current Roll: {tanu[0].get('roll')}")
    print(f"  Name: {tanu[0].get('name')}")
    print(f"  Target Roll: EA24A04")
    print(f"  Status: {'✓ CORRECT' if tanu[0].get('roll') == 'EA24A04' else '✗ NEEDS RESTORATION'}")

# Check Feb 2026 profiles
print("\n" + "=" * 60)
print("FEB 2026 PROFILES")
print("=" * 60)

feb_profiles = data.get('month_roster_profiles', {}).get('2026-02', [])

ayush_feb = [p for p in feb_profiles if 'ayush' in p.get('name', '').lower()]
if ayush_feb:
    print(f"\nAyush Feb 2026:")
    print(f"  Roll: {ayush_feb[0].get('roll')}")
    print(f"  Status: {'✓ CORRECT' if ayush_feb[0].get('roll') == 'EA24A01' else '✗ WRONG'}")

tanu_feb = [p for p in feb_profiles if 'tanu' in p.get('name', '').lower()]
if tanu_feb:
    print(f"\nTanu Feb 2026:")
    print(f"  Roll: {tanu_feb[0].get('roll')}")
    print(f"  Status: {'✓ CORRECT' if tanu_feb[0].get('roll') == 'EA24A04' else '✗ WRONG'}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

ayush_ok = ayush and ayush[0].get('roll') == 'EA24A01' and ayush_feb and ayush_feb[0].get('roll') == 'EA24A01'
tanu_ok = tanu and tanu[0].get('roll') == 'EA24A04' and tanu_feb and tanu_feb[0].get('roll') == 'EA24A04'

if ayush_ok and tanu_ok:
    print("\n✓ Both students already have correct original roll numbers!")
    print("  No restoration needed.")
else:
    print("\n✗ Restoration needed for:")
    if not ayush_ok:
        print(f"  - Ayush (current: {ayush[0].get('roll') if ayush else 'NOT FOUND'})")
    if not tanu_ok:
        print(f"  - Tanu (current: {tanu[0].get('roll') if tanu else 'NOT FOUND'})")
