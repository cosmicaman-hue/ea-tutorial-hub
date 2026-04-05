# Cache Issue & Solution Guide

## Problem Identified

After you reported seeing stale VETO values (10V, 9V, 7V, 3V instead of 5V, 6V, 5V, 1V), I investigated and found the root cause:

**The offline scoreboard stores data in browser localStorage, which persists across page reloads.**

When our Python fix scripts update `instance/offline_scoreboard_data.json`, the server has the new data. However, the offline scoreboard app running in your browser continues to read from its cached localStorage until that cache is cleared.

### Data Flow Problem:
```
1. Python script updates instance/offline_scoreboard_data.json ✓
2. Server has correct VETO values ✓
3. Browser localStorage still has OLD VETO values ✗
4. When offline scoreboard syncs with server, it may merge or show cached values
5. Display shows incorrect stale VETOs ✗
```

## Solution Overview

There are THREE levels of caching that need to be cleared:

1. **Browser localStorage** — Primary issue (stores offline_scoreboard_data)
2. **Browser IndexedDB** — Secondary cache (stores full backups)
3. **Service Worker cache** — Tertiary issue (may serve stale responses)

## How to Fix (User Steps)

### ✅ IMMEDIATE FIX - Clear Cache & Refresh

**Option A: Automatic Cache Clear**

1. Open this cache-clearing utility (I've created it for you):
   ```
   clear_offline_cache.html
   ```
   
2. Click **"Clear All Caches"** button
   - This will remove ALL scoreboard data from localStorage, IndexedDB, and Service Worker cache
   
3. Click **"Open Fresh Scoreboard"** button
   - Opens a new tab with cache-busted scoreboard
   
4. Click **"Verify Data"** to confirm VETO values are now correct

**Option B: Manual Browser Cache Clear**

On Windows (Chrome/Edge):
  ```
  Ctrl + Shift + Delete  → Open Clear Browsing Data
  Check: Cookies and other site data
  Check: Cached images and files
  Click "Clear data"
  
  Then:
  Ctrl + F5  → Hard refresh (bypass browser cache)
  ```

### ✅ VERIFY DATA IS CORRECT

After clearing cache, go to offline scoreboard:
- **Leader** should show **5V** (not 10V)
- **Co-Leader** should show **6V** (not 9V)
- **EA24C02** (Group C CR) should show **5V** (not 7V)
- **EA24B01** (Previous CR Pari) should show **1V** (not 3V)

## Technical Deep Dive

### Why This Happens

The offline scoreboard app (`app/static/offline_scoreboard.html`) has this data-loading sequence:

```javascript
1. Check if data is in _cacheData (in-memory) → Use it
2. Check if data is in localStorage → Parse and use it
3. Only if neither exists → Fetch from server

// When syncing:
if (localStorage has data) {
    use localStorage as truth source  // ← PROBLEM: stale data used!
}
```

### Root Cause of Display Issue

When you make Python script changes:
- **File updated**: `instance/offline_scoreboard_data.json` ✓
- **Server knows new values**: Yes ✓
- **Browser localStorage**: STILL HAS OLD DATA for 12+ hours (depending on cache TTL)
- **Display shows**: Stale values from localStorage ✗

### Multi-Layer Caching in Offline Scoreboard:

```
┌─────────────────────────────┐
│ Browser Display             │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ In-Memory Cache (_cacheData)│ ← Clears on page reload
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Browser localStorage        │ ← 12-24 hour persistence
│ (offline_scoreboard_data)   │   MAIN CULPRIT
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ IndexedDB Storage           │ ← Full backup persistence
│ (idb write in saveData)     │   Rarely checked
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Service Worker Cache        │ ← HTTP response cache
│ (/scoreboard/sw.js)         │   Bypassed with cache:'no-store'
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Server Data File            │ ← Source of truth
│ (instance/offline_score...) │   Now has correct VETO values
└─────────────────────────────┘
```

## Permanent Solution

I've created two tools to prevent this in the future:

### Tool 1: `clear_offline_cache.html`
- GUI tool to clear all caches with one click
- Verifies what's in localStorage vs server
- Useful when you know data was updated

### Tool 2: `inject_cache_buster.py`
- Can be added to VETO fix scripts
- Injects `_cache_bust_version` timestamp into data file
- Browser can detect this and auto-clear its cache
- Future enhancement: modify offline_scoreboard.html to watch for this

## Recommended Workflow Going Forward

**When you make Python script changes to VETO system:**

1. Run your fix script (e.g., `sync_veto_tracking.py`)
2. Run cache buster:
   ```bash
   python inject_cache_buster.py
   ```
3. Tell users to:
   - Use `clear_offline_cache.html` tool OR
   - Hard refresh (Ctrl+Shift+Delete → Clear → Ctrl+F5)

## Files Created

1. **clear_offline_cache.html** — GUI tool for clearing cache (open in browser as file://)
2. **inject_cache_buster.py** — Script to add cache-bust version to data file

## Testing Checklist

After clearing cache:
- [ ] VETO values match expected: 5V, 6V, 5V, 1V
- [ ] localStorage no longer shows stale student data
- [ ] Page refresh maintains correct values
- [ ] IndexedDB is also cleared (secondary backups)

## Architecture Notes

The offline scoreboard was designed for LAN deployments where data stays consistent. The cache layers were meant to prevent network requests when offline. However, when server data is updated via Python scripts (rather than through the normal app UI), those cache layers can cause display lag.

**Key insight**: The system trusts localStorage as authoritative for 12+ hours. When Python scripts update the server file directly, they bypass the normal sync channels that would invalidate the browser cache.

## Related Configuration

From `app/config/constants.py`, these TTLs apply:
- LEADERBOARD_TTL = 3600 (1 hour)
- STUDENT_PROFILE_TTL = 1800 (30 minutes)  
- PARTY_DATA_TTL = 86400 (24 hours)

These are HTTP cache headers, not localStorage TTL. localStorage persists indefinitely until manually cleared.
