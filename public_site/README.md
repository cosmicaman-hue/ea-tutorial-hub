# Public Scoreboard (Static Host)

This folder contains public files for static hosting on Cloudflare Pages.

## Files
- `index.html` - public read-only scoreboard UI (client-side login gate + scoreboard/info rendering)
- `scores.json` - exported scoreboard snapshot (scoreboard + `public_information`)
- `credentials.json` - per-student salted SHA-256 login credentials (manually maintained)
- `offline_scoreboard.html` - full SPA scoreboard (cross-origin mode via meta tag; no longer linked from the public UI)
- `static/css/offline-scoreboard.css` - SPA stylesheet
- `_headers` - cache-control rules (keeps `scores.json`, `credentials.json`, and SPA fresh on Cloudflare)

## Client-side login gate

The Scoreboard and Information tabs are locked behind a login dialog that runs
entirely in the browser. There is **no server and no routing to the local SPA**:

1. The user clicks **Login** (header button or a locked tab).
2. A modal prompts for **Roll No.** and **Password**.
3. The browser fetches `credentials.json`, finds the matching roll, and computes
   `SHA-256(salt + password)` (UTF-8) via Web Crypto.
4. On a hash match, the tabs unlock and render directly from `scores.json`.
5. The login is remembered in `localStorage`; **Logout** clears it.

This is a **soft gate only**. `credentials.json` is a public static file — anyone
can download it and brute-force the hashes offline. Use strong, unique passwords
and never reuse passwords that protect sensitive accounts. This model hides the
scoreboard from casual visitors; it is **not** real security.

### Managing credentials

Credentials are **manually maintained** in `credentials.json` with this schema:

```json
{
  "credentials": [
    { "roll": "EA24B15", "salt": "<16-hex-chars>", "hash": "<sha256(salt+password) hex>" }
  ]
}
```

Use the helper script from the project root to add/update/list/remove entries
(the script uses the exact same salted SHA-256 / UTF-8 encoding as the browser):

```bash
# Add or update one student (prompts for the password, hidden):
python scripts/generate_credentials.py EA24B15

# Bulk import from a CSV (columns: roll,password):
python scripts/generate_credentials.py --csv students_passwords.csv

# List configured rolls:
python scripts/generate_credentials.py --list

# Remove a student:
python scripts/generate_credentials.py --remove EA24B15
```

To generate a hash manually (must match the browser's UTF-8 SHA-256):

```python
import hashlib, secrets
salt = secrets.token_hex(8)
password = "your-password"
print(salt, hashlib.sha256((salt + password).encode("utf-8")).hexdigest())
```

Edits to `credentials.json` are deployed to Cloudflare Pages automatically on the
next **Force Publish** (it is included in the publish git-add list). The file is
served with `no-store` so credential changes/revocations propagate immediately.


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
