# Live Deployment Checklist (School Rollout)

Use this checklist when moving from local LAN usage to public WAN usage.

## 1. Pre-Launch Snapshot (Mandatory)
1. Create a full restore point of live data file:
   - `instance/offline_scoreboard_data.json`
2. Export one manual backup from Tools tab.
3. Verify restore-point file exists in `instance/` with timestamp.

## 2. Environment Setup (Render)
1. Deploy using `render.yaml`.
2. Confirm web service is healthy (`200` on homepage).
3. Confirm database attached (`DATABASE_URL` set from `project-ea-db`).
4. Set strong secrets:
   - `SECRET_KEY` (auto-generated)
   - `SYNC_SHARED_KEY` (long random string)
   - `ADMIN_PASSWORD`
   - `TEACHER_PASSWORD`

## 3. Master/Backup Role Policy
1. Keep only one writer node as master:
   - `EA_MASTER_MODE=1` on master
2. Backup node:
   - `EA_MASTER_MODE=0`
   - `SYNC_PEERS=<master-url>`
3. Confirm backup pulls from master only (not bi-directional conflict).

## 4. Data Integrity Smoke Test
1. Login as Admin and verify:
   - Scoreboard loads expected Feb roster visibility.
   - Leadership tab has saved posts.
   - Post Holders / Group CR / Party President data visible.
2. Login as Teacher and verify:
   - Current-month score entry works.
   - Current-month attendance update works.
3. Login as Student and verify:
   - Roll-based login works.
   - Allowed tabs/features only.

## 5. Cross-Device Sync Test
1. Device A (Admin): add a test score for current month.
2. Device B (Teacher): refresh and verify score appears.
3. Device C (Student): verify scoreboard reflects update.
4. End/suspend one test postholder and confirm:
   - Suffix updates across tabs
   - Post-related VETO effect recalculates correctly

## 6. Resources Module Test
1. Create one student request (normal).
2. Create one urgent admin request.
3. Approve and verify transaction row color:
   - Completed/settled = green
   - Pending/unsettled = non-green
4. Verify pending/return amounts compute and persist.

## 7. Daily Operations SOP
1. Start-of-day:
   - Confirm sync status online
   - Confirm latest backup timestamp visible
2. Mid-day:
   - Export one manual backup after major updates
3. End-of-day:
   - Export backup
   - Save copy off-server (external/cloud folder)

## 8. Incident Recovery Drill (Weekly)
1. Simulate stale snapshot issue on test environment.
2. Restore from latest known-good backup.
3. Re-validate:
   - Scoreboard tally
   - Leadership/Postholders/Party data
   - Fees and attendance consistency
4. Record restore time and data-loss window (target: near-zero).

## 9. Browser/PWA Reliability
1. Force refresh after new release:
   - `Ctrl+F5` (desktop)
2. Verify service worker cache version updated.
3. Confirm Edge/Chrome both load scoreboard quickly.

## 10. Go-Live Gate (Do Not Skip)
Go live only if all are true:
1. No missing leadership/post-holder records.
2. Scoreboard count matches expected active roster.
3. Sync works on at least 3 devices.
4. Latest restore point + manual backup both available.

