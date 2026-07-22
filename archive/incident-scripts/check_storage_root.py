"""Check which storage root Flask uses and compare resource data."""
import os, json

paths = {
    'C:/var/data/ea_tutorial_hub': 'C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json',
    'instance': 'instance/offline_scoreboard_data.json',
}

for label, path in paths.items():
    exists = os.path.exists(path)
    print(f"\n=== {label} ===")
    print(f"  Path: {path}")
    print(f"  Exists: {exists}")
    if exists:
        with open(path, 'r', encoding='utf-8') as f:
            d = json.load(f)
        print(f"  students: {len(d.get('students', []))}")
        print(f"  scores: {len(d.get('scores', []))}")
        print(f"  resource_cabinet: {len(d.get('resource_cabinet', []))}")
        print(f"  resource_requests: {len(d.get('resource_requests', []))}")
        print(f"  resource_transactions: {len(d.get('resource_transactions', []))}")
        print(f"  resource_advantage_deductions: {len(d.get('resource_advantage_deductions', []))}")
        print(f"  updated_at: {d.get('updated_at', 'N/A')}")

# Also check if C:/var/data/ea_tutorial_hub directory exists
var_path = 'C:/var/data/ea_tutorial_hub'
print(f"\n=== Directory check ===")
print(f"  {var_path} exists: {os.path.isdir(var_path)}")
if os.path.isdir(var_path):
    files = os.listdir(var_path)
    print(f"  Files: {len(files)}")
    for f in sorted(files)[:10]:
        size = os.path.getsize(os.path.join(var_path, f))
        print(f"    {f} ({size:,} bytes)")
