# Public academy site

The legacy LAN app remains the authority for official academy data. The public shell is served at https://ea-tutorial-hub.pages.dev by Pages project `ea-scoreboard`. Svelte and Android are separate from this flow.

## Required production settings

- Production branch: `main`
- Build command: `python3 scripts/build_secure_academy_site.py`
- Build output: `rebuild/out/secure_academy_site`
- Pages service binding: `PORTAL_API` to `project-ea-private-portal-staging`

The builder exports allowlisted files. The count changes with published resources; verify the manifest instead of assuming a fixed count. Never publish all of `public_site`, the legacy SPA, or private staging output. Root `wrangler.toml` belongs to private staging. An ad-hoc config using `../site` can overwrite the public destination and break later Git builds. Use controlled Git builds and verify settings after each release.

## Separate delivery paths

Scoreboard, public Ranking, Chess, Information, Results and Study Notes are static published projections. Their update time is the snapshot's time. Relevant tabs fetch static data with no-store semantics. An already-open page may need refreshing after deployment.

My Profile and protected party views use the authenticated Worker and D1. The LAN connector delivers sanitized projections through durable outboxes and receives student requests. Only Admin-managed/activated profiles are published by default. An old public Ranking does not establish that the private connector is offline.

Official Rules publish through the signed LAN connector. Cloud discussions cannot change official rules. Student browser admission is enforced by the Worker: two registrations are allowed; later registrations await LAN Admin approval. LAN login policy is unchanged.

General login and secure My Profile login have separate account/session paths. General credentials are managed in the LAN Admin Control Panel and delivered directly to the Worker. The builder does not export password verifiers; `/credentials.json` is explicitly denied. Removing the current file cannot make older downloads or historical releases secret. Password replacement is a separate Admin decision.

Static scoreboard/resource files remain downloadable. Their visual login gate does not make those files private. Private profiles, Rules interactions and protected party records require server authorization.

## Publish from LAN

Policies & Notices is a public tab and a standalone register at `/policies/`.
It lists issue/effective dates and links to typewritten PDF notices. The
canonical register is `app/static/policies/catalog.json`; run
`scripts/build_policy_notices.py` after adding a dated notice. The normal LAN
publication copies these assets, and the secure builder explicitly allowlists
them. Add amendments as new entries; do not overwrite an earlier notice.

1. Save pending LAN changes normally.
2. As Admin, click Force Publish. The repaired backend captures a canonical server snapshot and queues publication without rewriting the ledger.
3. Publishing status displays a durable receipt, source revision, export, GitHub delivery, Rules result and hosted-content verification.
4. A partial result identifies a separate failed stage. GitHub success alone is not a hosting receipt. Interrupted jobs resume on LAN startup.
5. Refresh the public page after verified delivery. The repaired local backend needs the normal LAN restart to activate installed source changes.

Internet outages delay cloud delivery independently of LAN operation. Do not clear browser queues or edit the live ledger to repair public publication.

## Recovery and manual fallback

The PowerShell fallback pushes existing exported files; it does not regenerate the snapshot. Review intended paths before `-Push`. It requires `main` and excludes the legacy SPA and password file.

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/publish_public_scoreboard.ps1 -Push
node --use-system-ca scripts/public_cloud_delivery.mjs inspect
node --use-system-ca scripts/public_cloud_delivery.mjs logs <deployment-id>
```

For wrong public build settings, `configure` saves a private local backup and restores the required command/output. Retry requires a reviewed full main commit SHA and refuses if remote main changed:

```powershell
node --use-system-ca scripts/public_cloud_delivery.mjs configure
node --use-system-ca scripts/public_cloud_delivery.mjs retry <reviewed-40-character-commit>
node --use-system-ca scripts/public_cloud_delivery.mjs verify <isolated-sanitized-build-folder>
```

Wait for deployment success; compare the sanitized `scores.json` hash to live bytes. Protected academy access must return 401, connector access through Pages 404, and the old credential-file URL 404. Raw source formatting can differ from sanitized output.

## Helpdesk

The public generic `/api/feedback` intake is not deployed. An unconfirmed submission is retained as a browser-only draft and explicitly labelled as not delivered. Use the visible WhatsApp option to send it. Receipt is reported only when an API returns success with a receipt ID. Authenticated student requests retain their separate Worker/LAN flow. Browser drafts are not silently converted into student requests or cloud records.
