EA Project Archive
==================

This folder holds one-off maintenance material that is not part of the running app.

- incident-scripts/  Historical Python and PowerShell fixes/diagnostics (Feb 2026 rolls,
  frozen month, etc.). Do not run unless you intend to modify data; back up instance/ first.
  Run from the project root if a script expects paths relative to the repo root.

- artifacts/         Exported reports (e.g. CSV discrepancies).

- helpers/             Optional HTML helpers (e.g. cache clear), not served by Flask.

- session-notes/       Fix summaries, architecture notes, and analysis markdown from
  development sessions. Safe to read or ignore; not used at runtime.

Active maintenance tools remain under scripts/ (see scripts/README.md).
