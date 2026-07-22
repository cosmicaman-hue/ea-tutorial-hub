#!/usr/bin/env python3
"""Push the fixed data to the local server via admin login session."""
import urllib.request, json, http.cookiejar

# Read the fixed data
with open('C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

from datetime import datetime, timezone, timedelta
ist = timezone(timedelta(hours=5, minutes=30))
now_iso = datetime.now(ist).isoformat()
data['server_updated_at'] = now_iso
data['updated_at'] = now_iso

base = 'http://127.0.0.1:5000'
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Step 1: GET login page to get CSRF token
try:
    resp = opener.open(f'{base}/auth/login', timeout=10)
    html = resp.read().decode('utf-8', errors='replace')
except Exception as e:
    print(f"Error fetching login page: {e}")
    exit(1)

# Extract CSRF token
import re
csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
if not csrf_match:
    csrf_match = re.search(r'<input[^>]*id="csrf_token"[^>]*value="([^"]+)"', html)
csrf_token = csrf_match.group(1) if csrf_match else ''
print(f"CSRF token: {csrf_token[:20]}...")

# Step 2: POST login
login_data = urllib.parse.urlencode({
    'csrf_token': csrf_token,
    'login_id': 'admin',
    'password': 'admin123',
}).encode()

# Get the session cookie from login
import urllib.parse
resp2 = opener.open(urllib.request.Request(
    f'{base}/auth/login',
    data=login_data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    method='POST'
), timeout=10)
print(f"Login response status: {resp2.status}")
print(f"Cookies: {[c.name for c in cj]}")

# Step 3: Push data
payload = json.dumps({'data': data, 'force_replace': True}).encode('utf-8')
req = urllib.request.Request(
    f'{base}/scoreboard/offline-data',
    data=payload,
    method='POST',
    headers={'Content-Type': 'application/json'}
)

try:
    resp3 = opener.open(req, timeout=120)
    result = json.loads(resp3.read().decode())
    print(f"Push result: success={result.get('success')}, updated_at={result.get('updated_at','')[:19]}")
except urllib.error.HTTPError as e:
    body = e.read().decode()[:500]
    print(f"HTTP {e.code}: {body}")
except Exception as e:
    print(f"Error: {e}")
