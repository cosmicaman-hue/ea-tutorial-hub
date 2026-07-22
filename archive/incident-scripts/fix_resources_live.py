"""
Copy restored resource data from instance/ into the LIVE database at C:/var/data/ea_tutorial_hub/.
Creates a backup of the live file first.
"""
import json, os, shutil
from datetime import datetime

LIVE_PATH = 'C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json'
INSTANCE_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'offline_scoreboard_data.json')

# Backup live file
stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup = LIVE_PATH.replace('.json', f'.pre_resource_fix_{stamp}.json')
shutil.copy2(LIVE_PATH, backup)
print(f"Backup: {backup}")

# Load both
with open(LIVE_PATH, 'r', encoding='utf-8') as f:
    live = json.load(f)
with open(INSTANCE_PATH, 'r', encoding='utf-8') as f:
    inst = json.load(f)

KEYS = ['resource_cabinet', 'resource_requests', 'resource_transactions', 'resource_advantage_deductions']

print("\nBefore:")
for k in KEYS:
    print(f"  live {k}: {len(live.get(k, []))}")
    print(f"  inst {k}: {len(inst.get(k, []))}")

# Copy resource data from instance to live
for k in KEYS:
    src = inst.get(k, [])
    if src:
        live[k] = src

live['updated_at'] = datetime.now().isoformat()

with open(LIVE_PATH, 'w', encoding='utf-8') as f:
    json.dump(live, f, ensure_ascii=False)

print("\nAfter:")
for k in KEYS:
    print(f"  live {k}: {len(live.get(k, []))}")

print(f"\nDone. Resource data copied to live database.")
