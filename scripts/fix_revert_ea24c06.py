#!/usr/bin/env python3
"""Revert the incorrect active_from_month fix on EA24C06 (id=88, Sakshi).
EA24C06 was correctly retired — Sakshi moved to EA24D32 from Apr 2026.
Only EA24A05 and EA24A03 need the active_from_month fix."""
import json, shutil
from pathlib import Path
from datetime import datetime

LIVE_PATH = Path("C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json")
data_path = LIVE_PATH if LIVE_PATH.exists() else Path("instance/offline_scoreboard_data.json")

# Backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = data_path.parent / f"{data_path.stem}.bak-revert-c06-{timestamp}.json"
shutil.copy2(data_path, backup_path)
print(f"Backup: {backup_path}")

with open(data_path, 'r', encoding='utf-8') as f:
    d = json.load(f)

students = d.get('students', [])

for s in students:
    roll = s.get('roll', '')
    sid = s.get('id')
    
    if roll == 'EA24C06' and sid == 88:
        old_afm = s.get('active_from_month')
        # Remove active_from_month so roll_history check hides this student
        # (EA24C06 was retired, Sakshi moved to EA24D32)
        s.pop('active_from_month', None)
        print(f"  ✓ Reverted EA24C06 (id=88, Sakshi): removed active_from_month (was '{old_afm}')")
    
    # Confirm EA24A05 and EA24A03 still have their fixes
    if roll == 'EA24A03' and sid == 11:
        print(f"  EA24A03 (Ayat): active_from_month={s.get('active_from_month')} ✓")
    if roll == 'EA24A05' and sid == 39:
        print(f"  EA24A05 (Rashi): active_from_month={s.get('active_from_month')} ✓")

with open(data_path, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print(f"\n✓ Data saved to {data_path}")
