# Public Scoreboard (Static Host)

This folder contains public files for static hosting on Cloudflare Pages.

## Files
- `index.html` - public read-only scoreboard UI
- `scores.json` - exported scoreboard snapshot
- `offline_scoreboard.html` - full SPA scoreboard (cross-origin mode via meta tag)
- `static/css/offline-scoreboard.css` - SPA stylesheet
- `_headers` - cache-control rules (keeps `scores.json` and SPA fresh on Cloudflare)

## Cross-Origin Mode (Cloudflare Pages → Tunnel Backend)

When `offline_scoreboard.html` is served from Cloudflare Pages, a `<meta name="ea-backend-url">` tag is injected by the publish flow. This activates cross-origin mode:

- All API calls are rewritten to the tunnel backend URL (set via `EA_TUNNEL_ORIGIN` env var)
- Auth headers (`X-EA-Login-ID`, `X-EA-Login-Code`) are injected from localStorage
- An offline banner appears when the backend is unreachable; changes queue in a WAL for replay on reconnect
- `lz-string.min.js` and `json-parse-worker.js` are inlined — no external `/static/js/` dependencies

## Environment Variables (Backend)

- `EA_TUNNEL_ORIGIN` - Cloudflare Named Tunnel domain (e.g. `sync.yourdomain.com`). Used to inject the meta tag and validate CORS.
- `EA_CLOUDFLARE_PAGES_ORIGIN` - Cloudflare Pages custom domain for CORS validation.
- `EA_ALLOW_PAGES_DEV` - Set to `1` to allow `*.pages.dev` preview deployments in CORS.
- `EA_PUBLIC_SITE_AUTO_PUSH` - Set to `1` (default) to auto-push public_site changes on Force Publish.

## Publish flow (Cloudflare Pages)

Primary path:
- In LAN admin app, use `Force Publish`.
- Server writes `public_site/scores.json`, syncs SPA files, and auto-pushes if enabled.

Manual fallback (from project root):

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\publish_public_scoreboard.ps1 -Push
```

This fallback only commits/pushes existing `public_site` files. It does not regenerate `scores.json`.

## Cloudflare Pages settings
- Production branch: `main`
- Framework preset: `None`
- Build command: *(empty)*
- Build output directory: `public_site`

Keep admin/LAN app private; host only this folder publicly.
