# Cloudflare Two-Way Sync — Status & Future Work

**Last assessed:** 2026-07-14

This document audits the completion status of all Cloudflare sync layers in Project EA, identifies pending gaps, and recommends prioritized next steps. The system has six distinct sync layers, all with code implemented but with varying levels of operational readiness.

---

## Executive Summary

The codebase contains a fully-architected Cloudflare integration spanning tunnel access, static hosting, cross-origin authentication, publish flow, bidirectional data sync, and offline queueing. **All six layers have working code**, but operational readiness depends on infrastructure configuration (env vars, Cloudflare Pages deployment, git credentials) that cannot be verified from code alone. Three functional gaps remain: no auto-refresh of auth tokens, no scheduled auto-publish, and SSE is unavailable in cross-origin mode (polling fallback only).

---

## Layer-by-Layer Status

| # | Layer | Code Status | Key Files | Gaps |
|---|---|---|---|---|
| 1 | Cloudflare Named Tunnel | Complete | `docs/WAN_TUNNEL_SETUP.md`, `cloudflared.exe`, `app/__init__.py:45-80` | Tunnel must be running as Windows Service; `EA_TUNNEL_ORIGIN` must be set |
| 2 | Cloudflare Pages (static hosting) | Complete | `public_site/`, `scoreboard.py:654-874`, `scripts/publish_public_scoreboard.ps1` | Pages deployment + git push pipeline must be configured |
| 3 | Cross-origin SPA auth | Complete | `auth.py:711-828`, `__init__.py:45-80,656-708`, `offline_scoreboard.html:105-141,1297-1320` | No auto-refresh; 7-day token expiry requires manual re-login |
| 4 | Force Publish (LAN → Pages) | Complete | `scoreboard.py:7177-7372`, `offline_scoreboard.html:18790-18921` | No scheduled auto-publish; fully manual admin action |
| 5 | Cross-origin data sync (pull/push) | Complete | `offline_scoreboard.html:18151-18884`, `scoreboard.py:1187-1376` | SSE disabled cross-origin; polling fallback only |
| 6 | WAL offline queue | Complete | `offline_scoreboard.html:7699,8025-8029,18651-18668` | Single-entry only (last failed push); not a multi-change queue |

---

## Detailed Layer Analysis

### 1. Cloudflare Named Tunnel (WAN Access to LAN Backend)

**What it does:** Exposes the local Flask server (port 5000) to the internet via an outgoing-only Cloudflare tunnel, eliminating port forwarding.

**Implemented:**
- Full setup guide at `docs/WAN_TUNNEL_SETUP.md` (144 lines, 7 steps)
- `cloudflared.exe` binary present in project root
- `_is_trusted_cors_origin()` in `app/__init__.py:45` validates tunnel domain via `EA_TUNNEL_ORIGIN` env var (exact hostname match)
- `*.trycloudflare.com` quick-tunnel domains also whitelisted
- Tunnel URL injected into published SPA via `<meta name="ea-backend-url">` tag in `_sync_spa_to_public_site()` (`scoreboard.py:670-681`)

**Pending:**
- [ ] Verify tunnel is installed as Windows Service and running
- [ ] Verify `EA_TUNNEL_ORIGIN` env var is set on the classroom PC (e.g., `sync.yourdomain.com`)
- [ ] Confirm tunnel config.yml points to `http://localhost:5000`
- [ ] Test external access to tunnel URL from a non-LAN device

### 2. Cloudflare Pages (Static Public Site Hosting)

**What it does:** Hosts a read-only public scoreboard on Cloudflare Pages, deployed via git push from the LAN server.

**Implemented:**
- `public_site/` directory with `index.html`, `scores.json`, `_headers`, `README.md`
- `_headers` file configures cache-control (no-store for scores.json, max-age=3600 for CSS)
- `_sync_spa_to_public_site()` copies `offline_scoreboard.html` + CSS into `public_site/` and injects tunnel URL meta tag
- `_publish_public_site_snapshot()` writes `scores.json` and optionally git commits + pushes (`scoreboard.py:785-874`)
- `EA_PUBLIC_SITE_AUTO_PUSH` env var controls auto-push (default: enabled)
- Manual fallback: `scripts/publish_public_scoreboard.ps1 -Push`
- Cloudflare Pages settings documented in `public_site/README.md` (build output: `public_site`, branch: `main`, no build command)

**Pending:**
- [ ] Verify Cloudflare Pages project is created and linked to git repo
- [ ] Verify `EA_CLOUDFLARE_PAGES_ORIGIN` env var is set (custom domain for CORS)
- [ ] Decide whether to set `EA_ALLOW_PAGES_DEV=1` for `*.pages.dev` preview deployments
- [ ] Confirm git push credentials are configured on the classroom PC
- [ ] Test end-to-end: Force Publish → git push → Cloudflare Pages auto-deploy → public site loads

### 3. Cross-Origin SPA Authentication

**What it does:** Allows the SPA served from Cloudflare Pages to authenticate against the tunnel backend without session cookies (SameSite=Lax cookies can't cross origins).

**Implemented:**
- `/auth/api-login` (`auth.py:711`) — JSON-based login returning a token stored in `user.login_code`
- `/auth/api-logout` (`auth.py:813`) — clears token via header-based auth
- `_token_auth_for_cross_origin()` before_request handler (`__init__.py:656`) — logs user in programmatically when `X-EA-Login-ID` + `X-EA-Login-Code` headers are present on trusted-origin requests
- `add_cors_headers()` after_request (`__init__.py:695`) — sets `Access-Control-Allow-Origin`, `Allow-Credentials`, allowed headers/methods for trusted origins only
- `_is_trusted_cors_origin()` (`__init__.py:45`) — exact-match hostname validation (fixed from bypassable substring checks)
- Cross-origin login modal in SPA (`offline_scoreboard.html:1297-1320`) with Login ID + Password fields
- `submitCrossOriginLogin()` (`offline_scoreboard.html:16540`) — calls `/auth/api-login`, stores token in localStorage
- `eaFetch()` interceptor (`offline_scoreboard.html:105-141`) — injects `X-EA-Login-ID` + `X-EA-Login-Code` headers from localStorage on every cross-origin request
- Token expiry handling: 401 response clears stale tokens and re-opens login modal (`offline_scoreboard.html:16401-16406`)
- Rate limiting: 10 login attempts per minute on `/auth/api-login`

**Pending:**
- [ ] **No auto-refresh of auth tokens** — tokens expire after 7 days (`login_code_expires_at`). Users must manually re-login when the token expires. Consider implementing a refresh-token flow or auto-renewal on 401.
- [ ] No token revocation UI for admin (admin can't see which devices have active cross-origin sessions)

### 4. Force Publish Flow (LAN → Cloudflare Pages)

**What it does:** Admin clicks "Force Publish" in the LAN SPA → server writes `public_site/scores.json`, syncs SPA files, and git pushes to trigger Cloudflare Pages deployment.

**Implemented:**
- `forcePublishNow()` (`offline_scoreboard.html:18822`) — sends POST to `/scoreboard/offline-force-publish` with `cloudflare_only: true`
- `offline-force-publish` route (`scoreboard.py:7177`) — handles `cloudflare_only` mode separately from peer replication
- `_publish_public_site_snapshot()` (`scoreboard.py:785`) — orchestrates: VETO resync → client snapshot validation → fallback server rebuild → atomic write → SPA sync → git add/commit/push
- `buildPublicSnapshotFromLAN()` (`offline_scoreboard.html:18790`) — builds public snapshot (top 15 students, recent 3 months, names masked beyond rank 15)
- `_sanitize_client_public_snapshot()` (`scoreboard.py:295`) — server-side validation of client-provided snapshot
- `_build_public_site_payload()` (`scoreboard.py:614`) — server-side fallback rebuild if client snapshot is incomplete
- `_public_snapshot_has_useful_rows()` (`scoreboard.py:337`) — sanity check before accepting client snapshot
- Guard: blocks publish if locked historical scores not yet loaded (`offline_scoreboard.html:18832-18841`)
- Async git push in background thread when `wait_for_results` is false (`scoreboard.py:7236-7244`)
- Result reporting: shows Cloudflare public site status (PUSHED/WRITE_ONLY/UP_TO_DATE) to admin

**Pending:**
- [ ] **No scheduled/auto Force Publish** — publish is a manual admin action. Consider a cron job or interval timer to auto-publish every N hours.
- [ ] Git push failure handling is graceful (writes locally, reports error) but doesn't retry — admin must manually re-publish
- [ ] No webhook from Cloudflare Pages back to LAN server to confirm successful deployment

### 5. Cross-Origin Data Sync (SPA ↔ Backend)

**What it does:** Bidirectional data sync between the Cloudflare Pages SPA and the tunnel backend — pull latest scores, push local edits.

**Implemented:**
- `pullFromServer()` (`offline_scoreboard.html:18354`) — fetches full or delta snapshot from backend via `eaFetch()` with auth headers
- `pushToServer()` (`offline_scoreboard.html:18151`) — pushes local data to backend via `eaFetch()` with auth headers
- `scheduleServerPush()` (`offline_scoreboard.html:16670`) — debounced push after local edits
- `startMinimalSyncPolling()` (`offline_scoreboard.html:16709`) — periodic pull on visibility change / interval (replaces SSE in cross-origin mode)
- Cross-origin offline banner (`offline_scoreboard.html:1322-1327`) — shows when backend unreachable, with Retry button
- `showCrossOriginOfflineBanner()` / `hideCrossOriginOfflineBanner()` (`offline_scoreboard.html:16454-16465`)
- `retryCrossOriginConnectivity()` (`offline_scoreboard.html:16467`) — retries session check + pull
- Tunnel URL prepended to sync base URLs in cross-origin mode (`offline_scoreboard.html:8749-8754`)
- History-aware merge prevents stale server data from overwriting newer local edits (`mergeScoreRowsSuperset` with `_getLastHistoryStamp()`)

**Pending:**
- [ ] **SSE disabled in cross-origin mode** — `EventSource` can't send custom auth headers, so `startRealtimeSync()` returns false (`offline_scoreboard.html:18696-18698`). Falls back to polling. Consider implementing SSE with query-string auth token or a CORS proxy.
- [ ] Polling interval (`MINIMAL_SYNC_POLL_INTERVAL_MS`) may need tuning for cross-origin usage to balance freshness vs. tunnel bandwidth
- [ ] No conflict resolution UI — merge conflicts are resolved silently by timestamp/history-stamp comparison

### 6. WAL (Write-Ahead Log) Offline Queue

**What it does:** When a push to the backend fails (offline/unreachable), the payload is saved to localStorage. On next successful pull, the WAL is replayed so offline changes reach the server.

**Implemented:**
- `WAL_KEY = 'ea_sync_wal'` (`offline_scoreboard.html:7699`)
- WAL replay in `pullFromServer()` after successful pull (`offline_scoreboard.html:18651-18668`) — removes WAL before push to avoid replay loops
- WAL preserved across page reloads (intentionally not cleared on load, `offline_scoreboard.html:8025-8029`)
- WAL cleared on extreme localStorage quota pressure (`offline_scoreboard.html:8269-8271`)
- LZ-string compression applied to WAL key (along with other large localStorage keys)

**Pending:**
- [ ] **WAL is single-entry** — only the last failed push payload is retained. If a user makes multiple edits while offline, earlier changes are overwritten by the latest push attempt. Consider a multi-entry queue with sequential replay.
- [ ] No WAL size limit — a large WAL payload could consume significant localStorage quota
- [ ] No user-visible indicator that changes are pending sync (only the offline banner shows)

---

## Pending Items Summary

### Infrastructure / Configuration (must verify on classroom PC)

| Item | Env Var / Setting | Status |
|---|---|---|
| Cloudflare Tunnel running as Windows Service | — | Unknown |
| Tunnel origin domain | `EA_TUNNEL_ORIGIN` | Unknown |
| Cloudflare Pages project created | — | Unknown |
| Pages custom domain for CORS | `EA_CLOUDFLARE_PAGES_ORIGIN` | Unknown |
| Allow pages.dev preview | `EA_ALLOW_PAGES_DEV` | Unknown (default: 0) |
| Auto-push on Force Publish | `EA_PUBLIC_SITE_AUTO_PUSH` | Default: 1 (enabled) |
| Git push credentials on classroom PC | — | Unknown |
| Cloudflare Pages build settings | Output: `public_site`, Branch: `main` | Documented, unverified |

### Code / Feature Gaps

| Priority | Item | Description |
|---|---|---|
| High | No auto-refresh of auth tokens | 7-day expiry requires manual re-login; no refresh-token flow |
| High | No scheduled auto-publish | Force Publish is manual only; public site can go stale |
| Medium | SSE unavailable cross-origin | EventSource can't send auth headers; polling fallback only |
| Medium | WAL is single-entry | Only last failed push retained; multi-edit offline scenarios lose earlier changes |
| Medium | No reverse sync from Pages | `scores.json` on Cloudflare Pages is write-only; no mechanism to pull it back to LAN |
| Low | No WAL size limit | Large WAL could consume localStorage quota |
| Low | No conflict resolution UI | Merge conflicts resolved silently by timestamp |
| Low | No admin token revocation UI | Admin can't view/revoke active cross-origin sessions |
| Low | No Pages deployment webhook | No confirmation back to LAN that Cloudflare deployed successfully |

### Carried Over from Prior Audit (15-item list)

| # | Item | Status |
|---|---|---|
| 12 | DEFAULT_PARTIES/DEFAULT_LEADERSHIP duplication (backend) | Pending — out of scope for frontend |
| 13 | `scoreboard.py` use SafeFileWriter | Pending — only `veto_manager_unified.py` uses atomic writes |
| 14 | `askPostHolderVetoRole()` always returns 'individual' | Pending — stub code, modal not implemented |
| 15 | Consolidate DOMContentLoaded listeners | Pending — 6+ listeners, low priority, risky due to timing deps |

### Security Considerations

| Item | Status |
|---|---|
| CORS origin validation | Fixed — exact hostname match, no substring checks |
| Anonymous GET `/offline-data` | Fixed — returns sanitized 3-month snapshot, no private data |
| Token-based auth | Uses `login_code` field, same as cookie-based, delivered via header |
| Rate limiting on `/auth/api-login` | 10/min — adequate |
| Replication peer auth | `X-EA-Replicated: 1` + `X-EA-Sync-Key` required for full ledger |
| Full-ledger snapshot guard | `is_full_ledger_snapshot()` refuses sanitized/clipped payloads |

---

## Recommended Next Steps (Prioritized)

1. **Verify infrastructure** — Confirm tunnel is running, `EA_TUNNEL_ORIGIN` is set, Cloudflare Pages is deployed, and git push works end-to-end. This is the critical path — all code is ready but the pipeline may not be wired up.

2. **Implement auto-refresh of auth tokens** — Add a refresh endpoint or auto-renew `login_code` on 401 with stored credentials. This is the highest-impact user experience gap for cross-origin users.

3. **Add scheduled auto-publish** — A simple cron job or interval timer on the server that calls `_publish_public_site_snapshot()` every N hours ensures the public site doesn't go stale when admin forgets to Force Publish.

4. **Upgrade WAL to multi-entry queue** — Store an array of pending payloads instead of a single entry. Replay sequentially on reconnect. Cap at a reasonable limit (e.g., 50 entries).

5. **Consider SSE with query-string auth** — Pass auth token as a query parameter on the EventSource URL (e.g., `/scoreboard/offline-events?token=XXX`) to enable real-time sync in cross-origin mode. Validate token server-side.

6. **Add admin token management UI** — List active cross-origin sessions (login_id, last_login, expires_at) with revoke button.

7. **Address prior-audit items 12-15** — Low priority but should be tracked for codebase health.

---

## Environment Variable Checklist

```ini
# Cloudflare Tunnel
EA_TUNNEL_ORIGIN=sync.yourdomain.com

# Cloudflare Pages CORS
EA_CLOUDFLARE_PAGES_ORIGIN=yourdomain.pages.dev
EA_ALLOW_PAGES_DEV=0

# Auto-push on Force Publish (default: 1)
EA_PUBLIC_SITE_AUTO_PUSH=1

# Peer sync (if using master/backup replication)
EA_MASTER_MODE=1
SYNC_PEERS=https://backup-server.example.com
SYNC_SHARED_KEY=your_shared_key
```
