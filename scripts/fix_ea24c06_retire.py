#!/usr/bin/env python3
"""Remove active_from_month from EA24C06 (id=88, Sakshi) - she correctly moved to EA24D32."""
import json
from pathlib import Path

LIVE_PATH = Path("C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json")
data_path = LIVE_PATH if LIVE_PATH.exists() else Path("instance/offline_scoreboard_data.json")

with open(data_path, 'r', encoding='utf-8') as f:
    d = json.load(f)

for s in d.get('students', []):
    if s.get('roll') == 'EA24C06' and s.get('id') == 88:
        old = s.get('active_from_month')
        s.pop('active_from_month', None)
        print(f"EA24C06 (id=88, Sakshi): removed active_from_month (was '{old}')")
    # Confirm the other fixes are still in place
    if s.get('roll') == 'EA24A03' and s.get('id') == 11:
        print(f"EA24A03 (Ayat): active_from_month={s.get('active_from_month')}")
    if s.get('roll') == 'EA24A05' and s.get('id') == 39:
        print(f"EA24A05 (Rashi): active_from_month={s.get('active_from_month')}")

with open(data_path, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
print(f"Saved to {data_path}")
