#!/usr/bin/env python3
"""
Cache-Buster Injection Script
Adds cache-busting mechanism so offline scoreboard auto-clears stale localStorage
when server data is updated by admin scripts.
"""

import json
from pathlib import Path
from datetime import datetime

DATA_FILE = Path('instance/offline_scoreboard_data.json')

def inject_cache_buster():
    """Add cache-bust timestamp to trigger localStorage refresh in browser."""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add cache-bust timestamp - this will trigger browser localStorage invalidation
        cache_bust_version = datetime.now().isoformat()
        data['_cache_bust_version'] = cache_bust_version
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Cache-buster injected: {cache_bust_version}")
        print("   Browser will auto-refresh localStorage on next sync")
        return True
    except Exception as e:
        print(f"❌ Error injecting cache-buster: {e}")
        return False

if __name__ == '__main__':
    inject_cache_buster()
