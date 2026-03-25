# Public Scoreboard (Static Host)

This folder contains only public files for static hosting.

## Files
- `index.html` - public read-only scoreboard UI
- `scores.json` - exported scoreboard snapshot
- `_headers` - cache-control rules (keeps `scores.json` fresh on Cloudflare)

## Publish flow (Cloudflare Pages)

Primary path:
- In LAN admin app, use `Force Publish`.
- Server writes `public_site/scores.json` (Top 15 full details, remaining masked) and auto-pushes if enabled.

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
