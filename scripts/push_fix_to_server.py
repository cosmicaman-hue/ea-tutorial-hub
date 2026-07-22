#!/usr/bin/env python3
"""Push the fixed data to the local server so it propagates to cloud snapshots."""
import urllib.request, json

# Read the fixed data
with open('C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Update timestamp so server accepts it
from datetime import datetime, timezone, timedelta
ist = timezone(timedelta(hours=5, minutes=30))
data['server_updated_at'] = datetime.now(ist).isoformat()
data['updated_at'] = datetime.now(ist).isoformat()

payload = json.dumps({
    'data': data,
    'force_replace': True,
    'authoritative_master_push': True
}).encode('utf-8')
sync_key = 'EA_SYNC_KEY_917511_2026'
req = urllib.request.Request(
    'http://127.0.0.1:5000/scoreboard/offline-data',
    data=payload,
    method='POST',
    headers={
        'Content-Type': 'application/json',
        'X-EA-Replicated': '1',
        'X-EA-Sync-Key': sync_key,
    }
)

try:
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read().decode())
    print(f"Server response: success={result.get('success')}, updated_at={result.get('updated_at','')[:19]}")
except urllib.error.HTTPError as e:
    body = e.read().decode()[:300]
    print(f"HTTP {e.code}: {body}")
except Exception as e:
    print(f"Error: {e}")
