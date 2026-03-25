# Public Scoreboard (Static Host)

This folder contains only public files for static hosting.

## Files
- `index.html` - public read-only scoreboard UI
- `scores.json` - exported scoreboard snapshot

## Publish (from project root)

Export latest LAN data into `public_site/scores.json`:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\publish_public_scoreboard.ps1 -PublicRepoPath .\public_site
```

Export + push (when `public_site` is a Git repo with remote configured):

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\publish_public_scoreboard.ps1 -PublicRepoPath .\public_site -Push
```

## Cloudflare Pages settings
- Framework preset: `None`
- Build command: *(empty)*
- Build output directory: `/`

Keep admin/LAN app private; host only this folder publicly.
