#!/usr/bin/env python3
"""
Diagnose why Ayush appears on top of Feb 2026 instead of Rehmetun.
Check AWF column configuration and deduction logic.
"""
import json

# Load data
with open('instance/offline_scoreboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 70)
print("FEB 2026 ORDERING DIAGNOSIS")
print("=" * 70)

# Check Feb 2026 extra columns
feb_extra_cols = data.get('month_extra_columns', {}).get('2026-02', [])
print("\nFeb 2026 Extra Columns:")
print(f"  Count: {len(feb_extra_cols)}")
for col in feb_extra_cols:
    print(f"  - Key: {col.get('key')}, Label: {col.get('label')}")

# Check if AWF column exists
awf_col_exists = any(col.get('key', '').lower() == 'awf' for col in feb_extra_cols)
print(f"\n  AWF Column Present: {'✓ YES' if awf_col_exists else '✗ NO'}")

# Check Feb 2026 student extras
feb_extras = data.get('month_student_extras', {}).get('2026-02', {})
print("\nFeb 2026 Student Extras (AWF flags):")
print(f"  Total students with extras: {len(feb_extras)}")

ayush_extras = feb_extras.get('EA24A01', {})
tanu_extras = feb_extras.get('EA24A04', {})
rehmetun_extras = feb_extras.get('EA25B13', {})

print(f"\n  Ayush (EA24A01):")
print(f"    Extras: {ayush_extras}")
print(f"    Has AWF: {'✓ YES' if ayush_extras.get('awf') else '✗ NO'}")

print(f"\n  Tanu (EA24A04):")
print(f"    Extras: {tanu_extras}")
print(f"    Has AWF: {'✓ YES' if tanu_extras.get('awf') else '✗ NO'}")

print(f"\n  Rehmetun (EA25B13):")
print(f"    Extras: {rehmetun_extras}")
print(f"    Has AWF: {'✓ YES' if rehmetun_extras.get('awf') else '✗ NO'}")

# Calculate expected totals
print("\n" + "=" * 70)
print("EXPECTED TOTALS (with AWF deduction)")
print("=" * 70)

ayush_scores = [s for s in data['scores'] 
                if (s.get('month') == '2026-02' or s.get('date', '')[:7] == '2026-02')
                and s.get('studentId') == 1]
ayush_total = sum(s.get('points', 0) for s in ayush_scores)
ayush_with_awf = ayush_total - 75 if ayush_extras.get('awf') else ayush_total

rehmetun_scores = [s for s in data['scores'] 
                   if (s.get('month') == '2026-02' or s.get('date', '')[:7] == '2026-02')
                   and s.get('studentId') == 80]
rehmetun_total = sum(s.get('points', 0) for s in rehmetun_scores)

print(f"\nAyush:")
print(f"  Raw points: {ayush_total}")
print(f"  AWF deduction: {75 if ayush_extras.get('awf') else 0}")
print(f"  Final total: {ayush_with_awf}")

print(f"\nRehmetun:")
print(f"  Raw points: {rehmetun_total}")
print(f"  AWF deduction: 0")
print(f"  Final total: {rehmetun_total}")

print(f"\nExpected order:")
if ayush_with_awf < rehmetun_total:
    print(f"  #1: Rehmetun ({rehmetun_total})")
    print(f"  #2: Ayush ({ayush_with_awf})")
else:
    print(f"  #1: Ayush ({ayush_with_awf})")
    print(f"  #2: Rehmetun ({rehmetun_total})")

# Diagnosis
print("\n" + "=" * 70)
print("DIAGNOSIS")
print("=" * 70)

if not awf_col_exists:
    print("\n⚠️  ISSUE FOUND: AWF column is missing from Feb 2026 extra_columns!")
    print("   The frontend cannot find the AWF flag because the column isn't defined.")
    print("\n   SOLUTION: Add AWF column to Feb 2026 month_extra_columns")
else:
    print("\n✓ AWF column is defined in Feb 2026")
    print("  The issue might be in the lookup logic or case sensitivity")

if ayush_extras.get('awf'):
    print("\n✓ Ayush has AWF flag in data")
    if not awf_col_exists:
        print("  But the column is missing, so frontend can't apply the deduction")
else:
    print("\n✗ Ayush does NOT have AWF flag in data")
    print("  This is unexpected - check if AWF was supposed to be set")
