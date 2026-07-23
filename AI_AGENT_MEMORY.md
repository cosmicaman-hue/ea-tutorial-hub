# AI AGENT MEMORY — Project EA (READ THIS FIRST)

> **THIS FILE IS THE SINGLE FIRST STOP FOR EVERY AI AGENT WORKING ON THIS REPO.**
> Read it before exploring the codebase. It maps every feature, bug area and data flow
> to exact files and line anchors so you can jump straight to the code instead of re-digging.

---

## 0. AMENDMENT PROTOCOL (MANDATORY FOR ALL FUTURE AGENTS)

1. **After ANY code change**, update the affected section(s) of this file in the SAME session:
   - If you moved/added/removed functions, refresh the line anchors of the section you touched.
   - If you fixed a bug, add a one-line entry to §10 (Known Root-Caused Bugs) with: date, symptom, root cause, fix location.
   - If you added a feature/tab/route, add it to the relevant index table.
2. **Do NOT restructure this file.** Keep the section numbering. Append inside existing sections.
3. **Line anchors drift.** All line numbers are labeled with their snapshot date. When a section's
   numbers are stale, re-anchor by searching the **function name** (names are stable; numbers are hints).
   Refresh numbers only for sections you touch — do not mass-renumber.
4. **Never delete history entries** in §10; they explain why defensive code exists.
5. Regenerate the full function index anytime with the one-liners in §12.
6. Line anchors below were captured **2026-07-02** (`offline_scoreboard.html` = 50,402 lines,
   `scoreboard.py` = 10,499+ lines). Rules system anchors updated **2026-07-11** (file now ~53,300 lines). If a target file changed by ±200 lines since, trust names over numbers.

---

## 1. SYSTEM OVERVIEW

**Project EA** is a tuition-center management system ("EA Tutorial Hub"): scores, stars, VETOs,
attendance, fees, elections/politics, notebooks, resources, syllabus — for students grouped A–D.

- **Backend:** Flask app factory in `app/__init__.py` (blueprints: auth, scoreboard/points, veto, star, favicon, notebook).
- **Frontend:** ONE giant single-file SPA — `app/static/offline_scoreboard.html` (~50.4k lines: HTML + CSS + JS).
  Served by route `/scoreboard/offline`. This file is where ~90% of feature work happens.
- **Primary datastore:** a JSON ledger file `offline_scoreboard_data.json` (NOT SQLite). Resolved by
  `app/utils/data_paths.py` → priority: `EA_STORAGE_ROOT` → `RENDER_DISK_PATH` → `/var/data/ea_tutorial_hub`
  (on Windows server PC this is `C:/var/data/ea_tutorial_hub/`) → Flask `instance_path` → project `instance/`.
  **The LIVE production DB is `C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json`, not `instance/`.**
- **Secondary datastore:** SQLite (`ea_data.db` / `DATABASE_URL`) for auth users, notebook checks,
  fee transactions, governance tables. JSON ledger is synced INTO SQLite at startup
  (`_sync_json_ledger_to_sqlite`, `app/__init__.py:115`).
- **Client storage:** browser `localStorage` (LZ-string compressed, key `ea_scoreboard_data`) + IndexedDB
  (`ea_scoreboard_idb`) as full uncompressed backup. See §7.
- **Roles:** `admin` (full), `teacher` (current-month window), `student` (read + self views). Session comes
  from Flask (`/scoreboard/session`) and is mirrored into the SPA (`loadSessionContext`).

---

## 2. REPO MAP (what matters, what doesn't)

| Path | Purpose |
|---|---|
| `app/__init__.py` | App factory, extensions, CORS, cache headers, user loader, bootstrap (535 lines) |
| `app/routes/scoreboard.py` | **Backend brain.** Blueprint `points_bp` (`/scoreboard/*`). All sync/merge/publish logic (~10.5k lines) |
| `app/routes/auth.py` | Login/register/change-password/logout, join codes, device sessions |
| `app/routes/notebook.py` | Notebook checking API (SQLite-backed), writes scores into JSON ledger too |
| `app/routes/veto_api.py` | `/api/veto/*` — thin wrapper over `veto_manager_unified` |
| `app/routes/star_validation.py` | `/api/stars/*` — star balance validation endpoints |
| `app/routes/favicon.py` | favicon/webmanifest |
| `app/static/offline_scoreboard.html` | **THE frontend.** Entire SPA (see §6–§8) |
| `app/static/js/lz-string.min.js` | localStorage compression lib |
| `app/utils/data_paths.py` | Single source of truth for data file path + response cache |
| `app/utils/score_balance.py` | AUTHORITATIVE star/veto balance formulas (`compute_star_balance`, `compute_veto_balance`) |
| `app/utils/star_calculator.py` | Delegates to score_balance (do not re-implement formulas here) |
| `app/utils/veto_manager_unified.py` | Unified veto manager (uses SafeFileWriter) |
| `app/utils/file_operations.py` | `SafeFileWriter`/`SafeFileReader` (atomic writes). scoreboard.py has its own `_atomic_write_json` |
| `app/utils/fee_pdf.py` | Monthly fee PDF reports (reportlab) |
| `app/utils/logger.py`, `error_handler.py` | Structured logging, error pages/JSON |
| `app/utils/secrets_manager.py` | Admin/Teacher password provider |
| `app/utils/student_roster.py`, `helpers.py`, `syllabus_helpers.py` | Small shared helpers |
| `app/models/` | SQLite ORM: `user.py` (User, ActivityLog), `student_profile.py`, `points.py` (StudentPoints, StudentLeaderboard, MonthlyPointsSummary), `fees.py` (FeeTransaction), `notebook.py` (5 tables), `governance.py` (UserAccessWindow, DeviceSession, AccountAction, JoinCode, StudentTransfer, Proposal*, ScoreAdjustmentAction) |
| `app/config/constants.py` | VETO_QUOTAS, DEFAULT_PARTIES/LEADERSHIP (⚠ duplicated w/ scoreboard.py), limits |
| `app/templates/` | Jinja pages: auth, notebook, scoreboard public, errors, base |
| `run.py` | **Main entrypoint** (Waitress). Single-instance lock, startup restore points, backup bootstrap, peer-sync thread |
| `wsgi.py` / `app.py` | Gunicorn/Railway entrypoints |
| `public_site/` | Static public scoreboard (index.html + scores.json) published by `_publish_public_site_snapshot` |
| `scripts/` | Maintenance CLIs (all use `get_data_path()`) |
| `tests/` | pytest: attendance sync, calculation, teacher sync |
| `archive/` | Old incident scripts + session notes. **Read-only reference, never import from here** |
| `migrations/` | credential migration only |
| `ea_android_app/`, `jdk-17*`, `mini-quiz-app/` | Android WebView wrapper + unrelated side projects — usually ignore |
| Root `*.md` files | Historical docs; may be stale. THIS file supersedes them for code navigation |

---

## 3. BACKEND — `app/__init__.py` (anchors @2026-07-02)

- `EphemeralUser` L27 — fallback user (-1 Admin, -2 Teacher) when ORM broken.
- `_migrate_notebook_schema` L50, `_sync_json_ledger_to_sqlite` L115 (JSON→SQLite student/score sync at boot).
- `_bootstrap_auth_defaults` L293 — ensures Admin/Teacher users.
- `create_app` L319: rate-limit disabled by default (`ENABLE_RATE_LIMITING`), 7-day sessions,
  no-store on all HTML L401, ProxyFix L412, blueprints L418-430, `/`→public scoreboard L432,
  `static_v` cache-buster L444, user loader L466, CORS after_request L517 (allows file://, trycloudflare, 192.168.*).
- Module-level `app = create_app()` L534 (for `app:app` targets).

---

## 4. BACKEND — `app/routes/scoreboard.py` FUNCTION INDEX (anchors @2026-07-02)

Blueprint `points_bp`, url_prefix `/scoreboard`. Layout is roughly: paths/helpers → public-site publish →
peer/cloud sync → load/save → merge engine → routes.

### 4.1 Storage & helpers
| Line | Function |
|---|---|
| 56–73 | **`_LEDGER_WRITE_LOCK` (RLock) + `_ledger_write_guard`** — serializes all ledger read-merge-write requests (added 2026-07-02; decorates ~20 mutating routes) |
| 106–138 | `_storage_root_path`, `_offline_data_path`, backup dirs, `_device_log_path` (⚠ anchors below drifted ~+120 after 2026-07-02 fixes — trust names) |
| 121–140 | restore-points meta, `_get_server_timezone` (Asia/Kolkata), `_server_now_iso` |
| 150–212 | `_roll_key`, `_name_key`, `_safe_int/float`, `_parse_stamp`, attendance status/penalty |
| 1380 | `_atomic_write_json` (temp+rename) |
| 1402 / 1430 | `_backup_offline_file` (keep 50) / `_backup_offline_hourly_immutable` (keep 720) |
| 1479 | **`_load_offline_data`** — the canonical read (cached via data_paths) |
| 1631 | **`_save_offline_data`** — acquires `_LEDGER_WRITE_LOCK`, delegates to `_save_offline_data_locked` (strips `sync_scope`/`allowed_months` view-markers, atomic write, backups, gist push) |
| 1574–1601 | SSE pub/sub: `_subscribe/_unsubscribe/_broadcast_sync_event` |
| 1630–1663 | sync-op dedupe (`_is_duplicate_sync_op`, `_record_sync_op`) |
| 1699–1746 | anti-shrink guards: `_is_suspicious_student_shrink`, `_is_tiny_roster` |
| 1810–2049 | snapshot recovery: `_iter_offline_recovery_candidate_paths`, `_best_local_snapshot`, `_best_peer_snapshot`, `_recover_tiny_roster_if_needed`, `_recover_stale_snapshot_if_needed` |

### 4.2 Public-site publish (static hosting)
| Line | Function |
|---|---|
| 212–608 | public payload builders (`_public_month_keys`, `_build_public_month_rows`) |
| 608–810 | `_build_public_site_payload`, `_publish_public_site_snapshot` (writes `public_site/scores.json`, optional git push via `_run_git`; flag `_auto_push_public_site_enabled`) |
| ~3721 | **`_sanitize_anonymous_snapshot`** — public/display-safe view for unauthenticated GET `/offline-data` (recent 3 months, no fees/appeals/logs/profile_data; marked `sync_scope='anonymous-public'`) |

### 4.3 Peer / cloud replication
| Line | Function |
|---|---|
| 811–971 | LAN peers: `_get_sync_peers` (SYNC_PEERS env), `_forward_offline_data_to_peers[_async]`, `_resolve_sync_shared_key` |
| 978–1116 | Supabase snapshot push/fetch (`_supabase_*`) |
| 1117–1213 | GitHub Gist snapshot push/fetch (`_gist_*`) |
| 1214–1379 | `_do_peer_sync_cycle`, `start_peer_sync_background` (30s thread; only when `EA_MASTER_MODE=1` + SYNC_PEERS) |

### 4.4 Balances / veto / roles
| Line | Function |
|---|---|
| 2114–2180 | leadership role type / veto quota / tenure helpers |
| 2196–2535 | `_compute_active_role_veto_quotas`, `_reconcile_role_veto_monthly`, veto consumption from scores, `_reconcile_veto_tracking_from_data`, `_reconcile_veto_counters_from_scores` |
| 2536/2541 | `_compute_student_star_balance` / `_compute_student_veto_balance` (delegate to `app/utils/score_balance.py`) |

### 4.5 THE MERGE ENGINE (heart of sync — edit with extreme care)
| Line | Function |
|---|---|
| 2546 | `_merge_teacher_scores` (teacher pushes; 50-pt ceiling, GCB floor -20; **no clamping guardrails — removed on purpose, see §10.3**) |
| 2694–2772 | teacher edit window: `_non_admin_edit_window_bounds`, `_filter_teacher_payload_to_edit_window` |
| 2773 | `_build_teacher_replication_patch` |
| 2850–2911 | month_students / month_roster_profiles supersets |
| 2916–2993 | **`_locked_month_keys`, `_preserve_locked_historical_window`** (locked months = Aug 2024–Feb 2026; protects history on every save) |
| 2994 | `_apply_admin_historical_score_ops` (admin queued historical edits) |
| 3086 | `_merge_students_preserve_active` |
| 3283 | **`_merge_scores_superset`** — history-aware: uses `_get_last_history_stamp` (L1674) so a row with newer real edit history wins over newer-but-synthetic `updated_at` |
| 3354–4820 | all other domain supersets: notifications, records, activity log, elections, attendance, fees, resources, leadership, parties, CRs, syllabus (via `syllabus_helpers`) |
| 5151 | `_enforce_current_month_roster_integrity` |

### 4.6 Month/permission scoping
| Line | Function |
|---|---|
| 3518–3682 | `_month_key_from_date_like`, `_allowed_months_for_user`, `_clip_payload_to_allowed_months` (students only get roster months; teachers get access windows) |

### 4.7 Routes (all prefixed `/scoreboard`)
| Line | Route | Notes |
|---|---|---|
| 5371 | GET `/balances` | star/veto balances |
| 5412 | POST `/validate-action` | pre-validate star/veto spend |
| 5471 | POST `/record-roll-change` | roll promotions (roll_history) |
| 5761 | GET `/offline` | **serves the SPA** (no-store + hash `_get_offline_html_hash` L5746) |
| 5773 | GET `/public` | public Jinja scoreboard |
| ~6147 | GET/POST **`/offline-data`** | **THE sync endpoint.** GET: full payload for admin/replication-key callers, month-clipped for teacher/student, SANITIZED for anonymous (env escape hatch `EA_ALLOW_ANON_FULL_SYNC=1`); delta filters by `updated_at` first. POST merges by role, serialized by `_ledger_write_guard` |
| 6747 | GET `/offline-events` | SSE stream |
| 6774 | GET `/activity-log` | filtered log rows |
| 6801/6858 | `/offline-server-health`, `/supabase-health` | |
| 6930 | POST `/offline-force-publish` | admin force local→server snapshot |
| 7127 | GET `/offline-backup` | download server JSON |
| 7150–7550 | fees: `_validate_and_sanitize_fee_updates`, `/fee-update`, `/api/fees/reconstruct`, report gen/download |
| 7554–7710 | restore points list/lock/restore |
| 7712/7718 | `/manifest.webmanifest`, `/sw.js` |
| 7752 | `_get_request_user` (session OR `X-EA-Login-ID`/`X-EA-Login-Code` headers) |
| 7779 | GET `/session` | role for SPA |
| 7809–7884 | device check-in/log |
| 7892/7930/7975 | party-data, leadership-data, election-results |
| 7992 | GET `/data` | Jinja scoreboard data |
| 8096–8272 | proposals + votes + messages |
| 8273 | GET `/allowed-months` |
| 8295–8549 | admin control panel: join-code, account-action, access-window, reset-login-codes |
| 8550 | `/auth/check-updates` |
| 8596 | `/student-transfers` |
| 8768/8874/9017 | add-points, leader-adjust-score, award-gcb |
| 9062–9199 | add/delete-student, update-profile |
| 9201 | POST `/import-excel` |
| 9412 | POST `/seed-feb26` |
| 9502/9553 | leaderboard, month-summary |
| 9665 | POST `/import-historical-data` (**`HISTORY_CUTOFF = '2026-02'` at L9681**) |
| 10092 | POST `/import-latest-roster` |
| 10227 | POST `/transfer-points` |
| 10462 | `/__debug_cache_status` |

---

## 5. BACKEND — other routes (anchors @2026-07-02)

**auth.py** (`auth_bp`): fallback login `_try_secure_fallback_login` L29 (works even if DB broken → EphemeralUser),
schema self-heal `_ensure_auth_schema_and_defaults` L50, join-code validation L264, device sessions L325,
`login` L455 (student login = roll number, validated against JSON roster L416), `register` L591,
`change_password` L645, `logout` L679.

**notebook.py** (`notebook_bp`, `/notebook`): dual-writes — SQLite tables AND JSON ledger scores with
note markers `[NOTEBOOK:SCHOOL]` / `[NOTEBOOK:TUITION]` (`_add_score_to_json` L78, `_remove_score_from_json` L126).
Save endpoint `save_check` L384. Subject configs / exemptions / score-settings CRUD below that.

**veto_api.py** (`/api/veto/*`) and **star_validation.py** (`/api/stars/*`): thin JSON APIs; formulas live in
`app/utils/score_balance.py` — **never fork the formula**.

---

## 6. FRONTEND — `offline_scoreboard.html` FILE LAYOUT (anchors @2026-07-02, 50,402 lines; rules @2026-07-11, ~53,300 lines)

| Lines | Content |
|---|---|
| 1–330 | Head scripts: AndroidBridge shim (L11–100), boot/loader (`boot` L646 → DOMContentLoaded), SW kill, cache-bust, **LZ-string localStorage compression wrapper** (L269–325: transparent compress/decompress with BOM marker on keys `ea_scoreboard_data`, `ea_scoreboard_backups`, `ea_offline_data_v2`) |
| 326–630 | Base CSS |
| 666–760 | Sidebar nav buttons (`data-tab=...`) |
| 1321–6360 | **All tab HTML** (see §6.1) |
| 6361–49757 | **THE main `<script>`** (~43k lines of JS) |
| 49767–50400 | Small trailing scripts: scroll perf, CR badge polish, sidebar collapse/hover, `patchSwitchTab` |

### 6.1 Tab HTML anchor table (`<div id="X-tab" class="tab-content">`)
| Tab id | HTML line | Loader function (JS) |
|---|---|---|
| scoreboard | 1321 | `loadScoreboard` 18744 / `loadMonthScoreboard` 18954 |
| my-dashboard | 1442 | `loadMyDashboard` 23828 |
| add-score (Record Score) | 1495 | `initScoreForm` 19390, `loadRecordStudentTable` 20899 |
| students | 1750 | `loadStudents` 24459 |
| fees | 1998 | `loadFeesTab` 41649 |
| resources | 2079 | `loadResourcesTab` 44338 |
| excel-mela | 2406 | `loadExcelMelaTab` 44358 |
| syllabus | 2803 | `loadSyllabusTab` 46051 |
| rules | 3274 | `loadRulesTab` 48990 |
| information | 3135 | `loadInformationTab` 46932 |
| ranking | 3203 | `loadRankings` 26359 |
| group-scoreboard | 3238 | `loadGroupScoreboard` 26391 |
| team-competition | 3309 | `loadTeamCompetitionTab` 27479 |
| gr (Class Rep) | 3445 | `loadCRTab` 30355 |
| party | 3544 | `loadParties` 30698 |
| leadership | 3665 | `loadLeadership` 31244 |
| leadership-selection | 3756 | `loadLeadershipSelectionTab` 29208 (state in localStorage `ea_leadership_selection_state`) |
| office (Post Holders) | 4018 | `loadOfficeHolders` 31634 |
| settings | 4135 | `loadSettingsTab` 32024 |
| voting | 4235 | `loadVotingTab` 34093 |
| teachers | 4448 | `loadTeachersTab` 34110 |
| teacher-voting | 4499 | `loadTeacherVotingTab` 34320 |
| appeals | 4596 | `loadAppealsTab` 38791 |
| notifications | 4706 | `loadNotificationsTab` 33035 |
| proposals | 4752 | `loadProposalsTab` 33100 |
| activity-log | 4826 | `loadActivityLogTab` 33842 |
| attendance | 4890 | `loadAttendanceTab` 39735 |
| profile | 5137 | `loadProfileTab` 40327 |
| good-conduct | 5205 | `computeGoodConductData` 48242 |
| reports | 5299 | `loadReportsTab` 33315 |
| awf (Academy Welfare Fund) | 5380 | `loadAwfTab` 22173 |
| notebooks | 5450 | `loadNotebooksTab` 22374 (`nb*` functions 22259–23343; sub-tabs: entry, records, notifications, settings, **summary** added 2026-07-02) |
| tools | 5776 | server endpoints, import/export, restore points, device log, admin panel |

Tab switching: `switchTab` 12880 (with `_safeRender` 12858, render-versioning `_tabRenderVer`);
role gating: `isTabAccessibleForCurrentRole` 14818, `applyRolePermissions` 14864
(**contains sidebar-element early-return fix — do not remove**, see §10.7).

---

## 7. FRONTEND — DATA LAYER (`ScoreboardDB` class, L10164–12857)

`const db = new ScoreboardDB()` at **L12831**. Global singleton.

| Anchor | Member | Notes |
|---|---|---|
| 10165 | `constructor` | `storageKey='ea_scoreboard_data'`, `_cacheData` in-memory truth, `_monthScoresCache`/`_scoreboardCache` memos |
| 10182–10315 | IndexedDB layer | `ea_scoreboard_idb` v2: stores `snapshots` (full mirror) + `rolling_snapshots` (max 10, ≥5s apart). Fire-and-forget write-through |
| 10316 | `getDefaultData` | **THE JSON SCHEMA** — every top-level key of the ledger (students, scores, month_students, month_roster_profiles, parties, leadership, election_*, attendance, fee_records, resource_*, syllabus_*, appeals, activity_log, proposals, rule_*, app_settings, postholder_tickets, postholder_ticket_log…). Schema v15 adds ticket fields. |
| 10366/10399 | `init` / `_asyncPreParse` | localStorage → `_cacheData` (worker-parsed if large) |
| 10409 | `ensureSchema` | fills missing keys, migrations (~500 lines) |
| 10926 | `getData()` | returns `_cacheData` (localStorage fallback) |
| 10965 | **`saveData(data, options)`** | THE write path. Options: `system`, `allowHistoricalWrite`, `skipShrinkCheck`, `skipBackup`, `preserveTimestamp`, `skipSync`. Flow: permission check → historical-edit guard → **shrink-detection confirm** → `preserveHistoricalMonthSnapshots` → localStorage (`buildLocalStorageSnapshot` strips locked-month scores for quota!) → IDB full write → backups → `scheduleServerPush` |
| 11199 | `addScore` (merges history), 11266 `getScore`, 11271 `deleteScore` (leaves roster intact — by design) |
| 11286–11794 | CRUD: students, parties, leadership, election posts, class reps, candidates, votes, teachers, pending results, appeals |
| 11801/11805 | attendance get/upsert |
| 11850–11910 | syllabus + fee records |
| 11919 | `applyElectionOutcome` |
| 12066 | **`getMonthlyScoreboard(month)`** — the score rendering engine. `scorePoints` vs `displayPoints` split (§10.1); Excel-history cutoff `< '2026-02'` L12173; star-bonus rules `>= '2026-02'`; VETO days zero score; AWF logic L12557 |
| 12592 | `deleteStudent` (moves to `deleted_students` + scrubs month maps), 12716 `restoreDeletedStudent` |
| 12813 | `clearAll` |

**Persistence invariants:**
- `buildLocalStorageSnapshot` (L7085) intentionally strips locked-month scores from localStorage; the FULL
  dataset lives only in `_cacheData` + IndexedDB. Any code reading raw localStorage misses history.
- `preserveHistoricalMonthSnapshots` (L13555) computes historical scores as a **superset of previous AND next**
  (`mergeScoreRowsSuperset`) — this prevents locked-month wipes. Never weaken it (§10.4).
- Two-tier IDB startup recovery lives in the main DOMContentLoaded (L49464–49565): Tier 1 full replace when
  localStorage is corrupt; Tier 2 merges only locked-month data into `_cacheData` without rewriting localStorage.

---

## 8. FRONTEND — SYNC ENGINE (client side)

| Anchor | Function | Role |
|---|---|---|
| 6367 | `SERVER_SYNC` config | enabled when served over http(s) or AndroidBridge |
| 6391 | `TEMP_DISABLE_AUTO_SYNC_LOOPS = true` | **permanent**: no polling/SSE loops. Sync = admin push after edits + pull on load/focus |
| 15168 | `scheduleServerPush` | debounce → `pushToServer` |
| 15399/15409 | `_getLastHistoryStamp` / **`mergeScoreRowsSuperset`** | history-aware merge (mirror of backend §4.5); uses `parseFloat` for points |
| 15516/15566 | `mergeScoreRowsWithHistoricalLocalGuard` / `mergeScoreRowsForAuthoritativePull` |
| 15593–16463 | all domain merge functions (mirror backend supersets) |
| 16465 | **`applyRemoteSnapshot`** | merges server payload into local, saves with `allowHistoricalWrite:true` |
| 16579 | **`pushToServer`** | POST `/scoreboard/offline-data` (admin full snapshot; teacher/student patches) |
| 16772 | **`pullFromServer(silent, forceFull)`** | startup always `forceFull=true` (delta misses edited old rows) |
| 17092 | `startRealtimeSync` (SSE — disabled by flag) |
| 17222/17340 | `forcePublishNow`, `maybeAutoPublishAdminSnapshot` |
| 15328 | `assessSnapshotHealth` | returns `{score, healthy, strippedLockedMonths, studentCount, scoreCount}` |
| 49381 | **MAIN STARTUP HANDLER** (DOMContentLoaded): overlay → restore tab → IDB recovery (49464) → `loadSessionContext` → `pullFromServer(false,true)` (49584) → admin batched repairs `persist:false` + single save (49590–49619) → overlay removal + rerender (49634) |

**Admin startup repairs (49596–49607):** `pruneVotingHistoryToCurrentMonth`, `repairMonthRosterProfileVetoCarries`,
`reconcileApprovedElectionOutcomes`, `reconcilePendingElectionApprovals`, `syncPostHolderHistory`,
`applyMonthlyRoleVetoGrants`, `repairLeaderDirectAppointmentState`, `collapseDuplicateStudentRecords`,
`reconcileClassValuesToCurrentMonthRoster`, `reconcilePostHolderTickets`. All run with `persist:false`, one batched `saveData({system:true,...})`.
⚠ Any NEW startup repair MUST follow this pattern (or pass `allowHistoricalWrite:true`) — see §10.4.

---

## 9. DOMAIN LOGIC QUICK-JUMP (frontend anchors @2026-07-02)

| Domain | Key functions (line) |
|---|---|
| Month/roster identity | `isStudentVisibleForMonth` 13740, `getMonthRosterProfileMap` 14434, `getStudentRollForMonth` 14530, `resolveCanonicalStudentRecord` 14269, roll-change/superseded 14077–14195, `autoCreateNewMonthRosterIfNeeded` 18547, `repairMonthCounterCarryForward` 18736 (⚠ §10.6) |
| Historical months | `isHistoricalMonthKey` 13283, `isExplicitlyLockedMonthKey` 13289, admin historical edit mode 13343–13444, hist editor 24240–24457 |
| Record score | `saveRecordScoreRow` 21531, `saveScore` 21856, drafts 21130–21207, `getRecordScoreStudentCandidates` 17494 (must keep `isStudentVisibleForMonth` filter — §10.8), cell menu/edit/pardon/penalty 23109–23434, delete/undo star/veto 23453–23661 |
| Stars/VETO | `getAvailableStarsForMonth` 49192, `validateStarAvailability` 49223, `smartStarCounter` 21342, star transfer 20118, star→veto convert 20622, points→star 20765, veto workflow `promptVetoUsageWorkflow` 19609 / `applyVetoWorkflowDatabaseChanges` 19786, role veto quotas 18192–18461, `applyPostHolderVeto` 49370 |
| Elections/voting | posts manager 31150–31243, candidates 35488, student voting 35333–38430, teacher voting 34320–34734, pending approvals 34742–34989, tie-break 37454–37684, winner reveal 37783 |
| Leadership/posts | `saveLeadershipPost` 31294, suspend/reactivate 9705/9751, suffixes (`getLeadershipSuffix` 9513, `syncStudentPostHolderSuffixes` 9826), tenure 17980–18098, auto-suspend 18795–18953, post-holder history 37052, name rendering `getStudentRenderState` 9842 |
| Parties/CR | parties 30698–31149, group CRs 30355–30697, class reps 31713–32119 |
| Attendance | drafts 39089–39151, `saveAttendance` 39979 (reliable patch push 39950–39978), bulk 39220–39606, reports 40056–40246, prize module 35910–36730 |
| Fees | `normalizeFeeRecord` 40378, pay/partial/history modals 41032–41435, PDF reports 41437–41563, `loadFeesTab` 41649 |
| Resources/Mela | cabinet/requests/transactions 41785–44337, cash pricing 43406–43483, mela cart 44843–45152, advantage deductions 41857+, admin fixes 41950–42074, **free quota system** (helpers ~43100–43178, `renderFreeQuotaCounter` 43178, `updateResourceContext` 43440, `submitResourceRequest` 45166, `adminApproveResourceRequest` 45446, `loadResourcesTab` calls `renderFreeQuotaCounter`) |
| Syllabus | catalog/tracking 6845–7067 (shared shape) + UI 45210–46070 |
| Notebooks (client) | `nb*` 22259–23073 |
| Good Conduct (GCB) | formula config 48044–48193, `awardGCB` 48216, `computeGoodConductData` 48242 |
| Team competition | 26519–27858 |
| Leadership Selection | 27859–30293 (state in `ea_leadership_selection_state`) |
| Notifications | `buildSystemNotifications` 32691, history 32794–33062 |
| Academy Rules | `ACADEMY_RULE_SECTIONS_TEMPLATE` 48566, `_migrateRuleItem` 48762, `_migrateRuleSections` 48780, `getRuleSectionsStore` 48800, `_flattenSectionRules` 48815, `_renderRulesSectionCard` 48871, `openRulesHome` 48885, `openRulesSection` 48922, `loadRulesTab` 48990, `createRulesSection` 49005, `_findRuleById` 49045, `editRulesSectionHeading` 49052, `editRuleText` 49072, `editRuleMetadata` 49102, `addRuleToSection` 49127, `openRuleModal` 49141, `closeRuleModal` 49182, `saveRuleFromModal` 49187, `deleteRuleText` 49262 |
| Appeals | 38631–39073, teacher score adjustments 21281–21341 |
| Reports/exports | reports tab 33315–33835, Excel import `parseWorkbook` 47348 / `importExcel` 47577, export 47636–47706 |
| Modals/UI utils | `openModal` 48784, `openConfirmModal` 49238, `showAlert` 48899, score history modal 48924–49066, undo snapshots 48833 |
| Postholder Tickets | `TICKET_ALLOCATION_BY_ROLE` 43596, `getTicketRoleForStudent` 43607, `getStudentTickets`/`setStudentTickets`/`logTicketAction` 43639, `grantPostHolderTickets` 43670, `getAllStudentsWithTickets` 43690, `transferTickets` 43700, `useHalfDeductionTicket` 43720, `useEraseTicket` 43740, `reconcilePostHolderTickets` 43791, cell menu `_cellMenuTicket` 24838, office tab panel `renderTicketManagementPanel` 43990/`executeTicketTransfer` 44064, frontend merge `mergePostholderTickets`/`mergePostholderTicketLog` 17104, backend merge `_merge_postholder_tickets`/`_merge_postholder_ticket_log` (scoreboard.py 4813), CSS `.ph-head-purple`/`.ticket-btn`/`.ticket-half-cell`/`.ticket-erase-cell` (offline-scoreboard.css 5019) |
| Tools | restore points 48439–48559, device log 47707–47902, admin control panel 47903–48030 |

---

## 10. KNOWN ROOT-CAUSED BUGS & INVARIANTS (never regress these)

1. **scorePoints vs displayPoints split** (`getMonthlyScoreboard` ~L12066+): star-usage days zero only the
   *display*, never the total. VETO days zero BOTH by design. Don't merge these variables back.
2. **No variable shadowing in getMonthlyScoreboard**: a `let points`/`const points` collision once killed all JS.
3. **Backend merge guardrails REMOVED on purpose** (`_merge_scores_superset`, `_merge_teacher_scores`):
   old clamps (±30 pts, Δ15) corrupted legitimate admin scores (e.g., -99 → -30). Only the teacher 50-pt
   ceiling and GCB immunity floor (-20) remain. **Do not re-add clamping.**
4. **Locked-month wipe class of bugs**: `buildLocalStorageSnapshot` strips locked-month scores; any
   `saveData()` without `allowHistoricalWrite:true` that reads a stripped snapshot could wipe history.
   Fixed by superset merge in `preserveHistoricalMonthSnapshots` (13555) + two-tier IDB recovery (49464).
   locked_months = 2024-08 … 2026-02 (19 months); backend mirror `_preserve_locked_historical_window` (2935).
5. **History-aware merge**: both `mergeScoreRowsSuperset` (fe 15409) and `_merge_scores_superset` (be 3283)
   compare last-history-entry stamps, not just `updated_at` (sync ops bump `updated_at` artificially).
6. **`repairMonthCounterCarryForward` (18736)**: the `isSeedMonth` special case was removed — always use
   computed `prevFinalStars` carry-forward. Re-adding it makes prior-month star awards vanish on refresh.
7. **`applyRolePermissions` (14864)**: teacher/student blanket `disabled=true` loops MUST keep the early
   return for `.app-sidebar` / `.mobile-topbar` / `.sidebar-overlay` elements (mobile nav broke without it).
8. **`getRecordScoreStudentCandidates` (17494)** must filter by `isStudentVisibleForMonth` (deactivated
   students were appearing in Record Score).
9. **Excel-history cutoff is FIXED** `'2026-02'` (fe L12173, be `HISTORY_CUTOFF` L9681) — never derive it
   from "now".
10. **Star formula single source**: `score_balance.compute_star_balance` (with `max(..., global_stars)` floor).
    `star_calculator` delegates to it. Frontend equivalent: `getAvailableStarsForMonth` 49192.
11. **Service workers are unconditionally killed** (head + L49679). PWA install prompt removed. Don't re-add
    SW caching without solving historical-data staleness.
12. **`TEMP_DISABLE_AUTO_SYNC_LOOPS = true` is permanent** (L6391). Sync model: push-after-edit + pull-on-load.
13. **Dual-database trap**: Flask reads `C:/var/data/ea_tutorial_hub/` (via data_paths), NOT `instance/`.
    Scripts must use `get_data_path()` — never hardcode either path.
14. **ID generation**: use `generateUniqueId()` (6495), never raw `Date.now()` (collision bugs).
15. **`saveData` shrink-check**: non-system saves prompt on student/score count shrink. System saves must pass
    `{system:true}` and follow the batched-repair pattern (§8).
16. **deleteScore leaves month roster entries** — intentional (roster ≠ scores).
17. **`_ayush_scores_*.json` root files** are incident artifacts; ledger repair history in `archive/session-notes/`.
18. **2026-07-02 — anonymous full-ledger exposure — FIXED**: unauthenticated GET `/offline-data` was treated as
    admin and served the full ledger (fees, profile data, logs) over LAN/tunnel. Now anonymous callers get
    `_sanitize_anonymous_snapshot` (recent 3 months, private collections stripped). Replication peers/backups
    authenticate with `X-EA-Replicated: 1` + `X-EA-Sync-Key` (updated in `_fetch_peer_offline_payload`,
    `_do_peer_sync_cycle`, and `run.py maybe_bootstrap_backup_from_master`). All three fetchers REFUSE payloads
    carrying `sync_scope`/`allowed_months` (never persist a clipped view as a full ledger); `_save_offline_data`
    strips those markers so they can never round-trip into the canonical ledger. Escape hatch: `EA_ALLOW_ANON_FULL_SYNC=1`.
19. **2026-07-02 — CORS origin bypass — FIXED**: substring origin checks (`'192.168.' in origin`) were bypassable
    (e.g. `http://192.168.evil.com`) and the `*` fallback was combined with `Allow-Credentials: true` (spec-invalid).
    Now `_is_trusted_cors_origin` in `app/__init__.py` parses the hostname and exact-matches localhost/loopback,
    private IPs (via `ipaddress`), `*.trycloudflare.com`, file:// and null. Untrusted origins get NO CORS headers.
20. **2026-07-02 — lost-update race on concurrent syncs — FIXED**: multi-threaded Waitress allowed two concurrent
    mutating requests to read→merge→write the ledger and silently drop one merge. `_LEDGER_WRITE_LOCK` (RLock) now
    serializes: all ~20 mutating routes via `@_ledger_write_guard` (GETs skip the lock) and `_save_offline_data`
    itself. NOTE: in-process lock only — correct for Waitress single-process; do NOT deploy multi-process gunicorn
    workers against the same ledger file without adding a cross-process `FileLock`.
21. **2026-07-02 — delta sync missed edits to old rows — FIXED**: GET `?since=` delta filtered scores by
    `date`/`created_at` only, so edits to historical rows never appeared in deltas. Filter now checks
    `updated_at` first (superset-safe). Frontend startup still uses `forceFull=true` — keep it.
22. **2026-07-02 — per-request bcrypt on admin — FIXED**: `check_default_password` in `app/__init__.py` ran a
    bcrypt verify on EVERY admin request (~100-300ms). Result now cached in the session (`_admin_default_pw`).

23. **2026-07-02 — Notebooks dark mode CSS broken (~37 selectors missing `.nb-` prefix) — FIXED**: `dark_mode.css` lines 391–581 had selectors like `.type-pill`, `.nb-table`, `.grade-select` instead of `.nb-type-pill`, `.nb-table`, `.nb-grade-select`. All selectors corrected + new dark mode overrides added for grade pills, next-student btn, last-check indicator, summary sub-tab. Also replaced grade `<select>` dropdown with color-coded quick-grade pill buttons (`.nb-grade-pill` + `NB_GRADES` array, `nbGradePillsHtml`, `nbGetSelectedGrade`, `nbSetGrade`, `nbOnPillClick`). Added: Next Student button (`nbNextStudent`), last check indicator (`nbLoadLastCheck`), Summary sub-tab (`nbLoadSummary`), keyboard shortcuts (1-8 grades, Enter save, ArrowRight next, Space toggle). Line anchors: `nbGradePillsHtml` ~22642, `nbOnPillClick` ~22765, `nbNextStudent` ~23227, `nbLoadLastCheck` ~23241, `nbLoadSummary` ~23261.

24. **2026-07-03 — Free Quota System added**: Students get a monthly ₹ quota from the Academy for resource purchases,
    varying by post-holder role: Leader ₹50, Co-Leader(s) ₹35 (shared combined), LoP ₹30, RM ₹25, GR (excl. PP) ₹20,
    all others ₹15. Mode `free_quota` in resource requests/transactions. Helper functions: `getStudentFreeQuotaRole`,
    `getStudentFreeQuotaAmount`, `getStudentFreeQuotaUsed` (sums `free_quota_amount` from transactions for the month),
    `getStudentFreeQuotaRemaining`. `renderFreeQuotaCounter` shows a color-gradient utilization bar per student.
    `adminApproveResourceRequest` checks quota remaining at approval time (blocks unless admin veto). Transaction rows
    store `free_quota_amount` field. `isCompleted()` returns `true` for `free_quota` mode (always settled — no cash due).
    UI labels show "Free Quota" instead of raw mode string in requests and transactions tables.

25. **2026-07-10 — duplicated runtime/config/persistence infrastructure — FIXED**: `run.py` constructed a second Flask
    app after importing the package-level app; peer URL/key/private-network logic was duplicated across startup and
    scoreboard sync; scoreboard and startup had separate JSON replacement implementations; operational politics defaults
    lived in the route monolith. `run.py` now reuses `app.app`; `app/utils/sync_config.py` owns peer normalization, shared-key
    resolution, private-peer classification and full-ledger markers; `app/utils/file_operations.py::atomic_write_json`
    owns locked same-filesystem replace + flush/fsync + optional backup; operational defaults live in
    `app/config/constants.py`. Existing route behavior and helper contracts remain unchanged.
26. **2026-07-10 — explicit JSON read fallback lost — FIXED**: `SafeFileReader.read_json(path, default=None)` returned `{}`
    because it used `default or {}`. That defeated `data_paths.load_json_data_cached` failure detection and could replace a
    valid in-memory ledger cache with an empty dict after corruption/read failure. An internal sentinel now distinguishes
    an omitted default from explicit `None`; regression coverage is in `tests/test_file_operations.py`.

27. **2026-07-10 — silent startup failures and unsafe worker configuration visibility — FIXED**: schema/auth
    bootstrap failures now use structured exception logs while preserving boot-continuation behavior;
    `_sync_json_ledger_to_sqlite` logs duration and source/create/update/skip counters; `_configured_process_workers`
    parses `WEB_CONCURRENCY`, `GUNICORN_WORKERS`, and Gunicorn `-w`/`--workers` arguments and emits a non-blocking
    critical warning above one process. Test discovery is side-effect-safe: the live attendance diagnostic opts out of
    pytest collection, the calculation diagnostic runs only under `__main__`, and the ambiguous admin-vote case is
    explicitly skipped until vote records encode actor role. `unittest discover` passes 18 tests with one skip.

28. **2026-07-10 — WAN replication payload sanitization coupled to route monolith — FIXED**:
    `payload_for_external_replication` now lives in `app/utils/sync_payloads.py`; scoreboard peer, Supabase, Gist,
    background sync, and force-publish paths call the shared pure function. Exact-output tests verify fee removal,
    source immutability, invalid inputs, and the legacy shallow-copy fallback when deep copy fails. Automated discovery
    now passes 21 tests with one intentional voting-schema skip; guardrail and offline HTTP smoke checks pass.

29. **2026-07-11 — Academy Rules system redesigned from string list to structured table — NEW FEATURE**:
    Rules data model migrated from flat string arrays to rich objects with metadata fields: `text`, `penalty`,
    `in_charge`, `severity` (info/minor/major/critical), `applicable_to` (All/Students/Prefects/Boarders/Day Scholars/Class 11-12/Class 6-10),
    `status` (active/review/repealed), `updated_at`. `ACADEMY_RULE_SECTIONS_TEMPLATE` expanded to 12 sections (A–L) with ~100 pre-seeded rules.
    **Migration**: `_migrateRuleItem` (48762) converts old string items → objects on load via `_migrateRuleSections` (48780) called from
    `getRuleSectionsStore` (48800). **Flattening**: `_flattenSectionRules` (48815) produces flat row objects with composite IDs (`{key}-B{n}-R{n}`).
    **UI**: `openRulesSection` (48922) renders a `<table class="rules-table">` with columns: #, Rule, Penalty, In-Charge, Severity, For, Status, Votes, Actions.
    Severity/status rendered as colored badges via `_severityBadge` (48910) / `_statusBadge` (48916).
    **Admin actions**: `addRuleToSection` (49127) opens modal, `editRuleText` (49072) edits text inline, `editRuleMetadata` (49102) opens modal for metadata fields,
    `deleteRuleText` (49262) removes with confirm, `saveRuleFromModal` (49187) handles both add/edit modes.
    **Modal**: `openRuleModal` (49141) / `closeRuleModal` (49182) manage a form overlay (`#ruleModal` at HTML line 3459).
    **CSS**: scoped `<style>` block at line 3275 inside rules-tab — includes `.rules-table`, `.rule-badge.severity-*`, `.rule-badge.status-*`,
    `.rule-modal-overlay`, mobile responsive card layout at ≤480px using `data-label` attributes on `<td>`s.
    `editRuleText` and `deleteRuleText` updated to work with object items via `_migrateRuleItem` normalization before field access.

30. **2026-07-23 — Phase 1 ledger reliability hardening**: `run.py::_pid_is_running` now uses the Win32 process API and rejects a PID reused by a non-Python executable, while conservatively treating access-denied processes as live; this prevents duplicate JSON-ledger writers on Windows. SQLite now uses WAL, `busy_timeout=15000`, `synchronous=NORMAL`, and a 15-second connection timeout. Ledger recovery, background peer sync, and backup failures now emit logs instead of failing silently; backup copies undergo a source-size verification and invalid copies are removed. Regression coverage: `tests/test_ledger_reliability.py`. **Test safety:** it overrides `EA_STORAGE_ROOT` and resets `data_paths` storage/cache state before exercising `_save_offline_data` so it never touches live ledger data.

31. **2026-07-23 — Phases 2–5: sync speed, smooth saves, multi-tab, UX polish**:
    - **Phase 2 (ETag/304):** Backend `GET /offline-data` admin full-sync now checks `If-None-Match` and returns `304 Not Modified` when the ledger hasn't changed (saves ~18 MB bandwidth per repeat pull). Frontend `pullFromServer` sends `If-None-Match` with the stored ETag and handles `304` same as `204`. ETag stored in `localStorage['ea_last_server_etag']`, invalidated on `pushToServer`. Anchors: backend `scoreboard.py` ~L6539, frontend `offline_scoreboard.html` ~L7965 (`_lastServerETag`/`_saveServerETag`), ~L18741 (conditional GET in pull), ~L18500 (ETag invalidation on push).
    - **Phase 3 (debounced saves):** `ScoreboardDB.saveData` no longer writes localStorage synchronously on every call. New `_scheduleDeferredLocalWrite` (300 ms debounce) coalesces rapid edits into one `JSON.stringify` + LZ compress + `localStorage.setItem`. `_flushDeferredLocalWrite` handles the full fallback chain (reclaim → emergency → IDB). `beforeunload` handler flushes any pending write to prevent data loss on tab close. Anchors: `offline_scoreboard.html` ~L11709 (`_scheduleDeferredLocalWrite`/`_flushDeferredLocalWrite`), ~L12574 (saveData deferral), ~L53994 (beforeunload flush).
    - **Phase 4 (multi-tab):** `BroadcastChannel('ea-scoreboard')` notifies other tabs on save; receiver pulls from server to get the merged result instead of clobbering localStorage. Anchor: ~L7971 (`_eaBroadcastChannel`/`_broadcastSave`), ~L12676 (`_broadcastSave` call in saveData).
    - **Phase 5 (UX):** Startup overlay now shows progress steps: "Restoring local backup..." → "Checking session..." → "Syncing data..." → "Preparing dashboard...". Anchor: `_updateStartupStep` ~L53762, calls at ~L53788, ~L53881, ~L53947.

*(append new entries here as: date — symptom — root cause — fix anchor)*

---

## 11. DEPLOYMENT / OPS

- **Local server PC (primary):** `run.py` via Waitress (port 5000; `EA_USE_WAITRESS=1` default). Single-instance
  lock `instance/.server_main.lock`. Startup: restore point snapshot (keep 200), backup bootstrap from master
  peers, default accounts, optional peer-sync thread (`EA_MASTER_MODE=1` + `SYNC_PEERS`).
- **Batch launchers:** `run_server.bat`, `run_server_dev.bat`, `start_cluster_server.*`, `launcher.py/ps1`,
  backup tasks (`daily_backup.ps1`, `setup_daily_backup_task.ps1`), `cloudflared.exe` for WAN tunnel
  (`docs/WAN_TUNNEL_SETUP.md`).
- **Cloud (Railway/Render):** `wsgi.py`/`app.py` with gunicorn (1 worker/1 thread). Keep background work off.
- **Static public site:** `public_site/` (scores.json) published by backend `_publish_public_site_snapshot`
  or `scripts/publish_public_scoreboard.ps1 [-Push]`.
- **Cloud snapshot mirrors:** Supabase + GitHub Gist (env-driven, §4.3).
- **Env vars of note:** `EA_STORAGE_ROOT`, `RENDER_DISK_PATH`, `DATABASE_URL`, `SECRET_KEY`, `ADMIN_PASSWORD`,
  `TEACHER_PASSWORD`, `SYNC_PEERS`, `EA_MASTER_MODE`, `SYNC_SHARED_KEY` (replication key; falls back to
  SECRET_KEY then a hardcoded default — all peers must resolve the SAME key or backup bootstrap skips),
  `EA_ALLOW_ANON_FULL_SYNC` (legacy open GET), `ENABLE_RATE_LIMITING`, `EA_DB_AUTO_INIT`, `EA_BACKUP_BOOTSTRAP`,
  `EA_SKIP_STARTUP_RESTORE`, `EA_RESTORE_LOCK`, `PORT`.

## 12. REGENERATING INDEXES (PowerShell, repo root)

```powershell
# Backend function/route map
Select-String -Path "app/routes/scoreboard.py" -Pattern '^(def |class |@points_bp\.route)' |
  ForEach-Object { "$($_.LineNumber): $($_.Line)" }

# Frontend named-function map (~1,270 entries)
Select-String -Path "app/static/offline_scoreboard.html" -Pattern '^\s*(async\s+)?function\s+([A-Za-z_$][\w$]*)' |
  ForEach-Object { "$($_.LineNumber): $($_.Matches[0].Groups[2].Value)" }

# Tab HTML anchors
Select-String -Path "app/static/offline_scoreboard.html" -Pattern 'class="tab-content'
```

## 13. TESTS & VERIFICATION

- `tests/test_attendance_sync.py`, `tests/test_calculation.py`, `tests/test_teacher_sync*.py` — run with
  `python -m pytest tests/ -q` (venv: recreate; `.venv_broken_from_old_pc_20260214` is dead).
- `test_guardrail.py` (root) — merge guardrail regression checks.
- `scripts/anti_corruption_check.py` and other `scripts/*` for ledger integrity (all path-safe via `get_data_path()`).
- Manual smoke: start server → `/scoreboard/offline` → check startup overlay clears, scoreboard renders
  locked months (e.g., 2024-09) with non-zero scores, and admin push/pull round-trips.
