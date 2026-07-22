#!/usr/bin/env python3
"""
reconcile_stars.py — diff / restore star counts against a known-good backup.

Why this exists
---------------
The JavaScript `repairMonthCounterCarryForward()` function used to silently
recompute `student.stars` from month-profile snapshots on every admin login
and after every score mutation. Because Star→VETO conversions, admin edits,
and late-month awards were not visible to that carry-forward math, the
function would overwrite valid stars with stale derived values. That path is
now disabled — `student.stars` is the sole authoritative balance.

This script helps you recover from past corruption by diffing the current
`student.stars` against a backup snapshot and optionally restoring them.

Usage
-----
    # Compare current state to a specific backup (dry-run)
    python scripts/reconcile_stars.py --backup instance/<backup>.json

    # Same, but restrict to one or more rolls
    python scripts/reconcile_stars.py --backup <path> --roll EA24A01 EA24B02

    # After reviewing the diff, actually apply the backup's star values
    python scripts/reconcile_stars.py --backup <path> --apply

The script never touches VETO counts, scores, or month_roster_profiles. It
only writes to `student.stars` in the current data file, and only under
`--apply`. A pre-change backup of the current file is written to the
`offline_scoreboard_backups/` directory before any apply.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import data_paths directly without triggering app/__init__.py (which pulls
# Flask). This script only needs path helpers, not the Flask app.
import importlib.util as _ilu
_dp_spec = _ilu.spec_from_file_location(
    'ea_data_paths', _project_root / 'app' / 'utils' / 'data_paths.py'
)
_dp_mod = _ilu.module_from_spec(_dp_spec)
assert _dp_spec.loader is not None
_dp_spec.loader.exec_module(_dp_mod)
get_backup_dir = _dp_mod.get_backup_dir
get_data_path = _dp_mod.get_data_path


def _load(path: Path) -> dict:
    with path.open('r', encoding='utf-8') as handle:
        return json.load(handle)


def _index_students_by_roll(data: dict) -> dict:
    out: dict = {}
    for student in data.get('students', []) or []:
        roll = str(student.get('roll') or '').strip()
        if roll:
            out[roll] = student
    return out


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', required=True, help='Path to backup JSON to compare against')
    parser.add_argument('--apply', action='store_true', help='Write backup star values to current data')
    parser.add_argument('--roll', nargs='+', default=None, help='Restrict to these rolls')
    parser.add_argument(
        '--current',
        default=None,
        help='Override current data path (defaults to configured data path)',
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    current_path = Path(args.current) if args.current else Path(get_data_path())
    backup_path = Path(args.backup)

    if not current_path.exists():
        print(f"❌ Current data file not found: {current_path}")
        return 2
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_path}")
        return 2

    print(f"Current : {current_path}")
    print(f"Backup  : {backup_path}")
    print()

    current_data = _load(current_path)
    backup_data = _load(backup_path)

    current_by_roll = _index_students_by_roll(current_data)
    backup_by_roll = _index_students_by_roll(backup_data)

    roll_filter = {r.strip().upper() for r in (args.roll or [])} or None

    diffs: list[tuple[str, str, int, int]] = []
    for roll, current_student in current_by_roll.items():
        if roll_filter and roll.upper() not in roll_filter:
            continue
        backup_student = backup_by_roll.get(roll)
        if not backup_student:
            continue
        try:
            current_stars = int(current_student.get('stars') or 0)
            backup_stars = int(backup_student.get('stars') or 0)
        except (TypeError, ValueError):
            continue
        if current_stars != backup_stars:
            name = str(current_student.get('base_name') or current_student.get('name') or '')
            diffs.append((roll, name, current_stars, backup_stars))

    if not diffs:
        print("✅ No star differences between current and backup.")
        return 0

    diffs.sort(key=lambda row: row[0])
    print(f"{'Roll':<10} {'Name':<28} {'Current':>8} {'Backup':>8} {'Delta':>7}")
    print('-' * 64)
    for roll, name, current, backup in diffs:
        name_display = (name[:26] + '..') if len(name) > 28 else name
        print(f"{roll:<10} {name_display:<28} {current:>8} {backup:>8} {backup - current:>+7}")
    print('-' * 64)
    print(f"{len(diffs)} student(s) differ.")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to restore backup values.")
        return 0

    # Persist a pre-change backup before applying anything.
    backup_dir = Path(get_backup_dir())
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pre_change_path = backup_dir / f'offline_scoreboard_data.pre_reconcile_stars_{stamp}.json'
    shutil.copy2(current_path, pre_change_path)
    print(f"\nPre-change backup written: {pre_change_path}")

    applied = 0
    for roll, _name, _current_stars, backup_stars in diffs:
        student = current_by_roll.get(roll)
        if not student:
            continue
        student['stars'] = max(0, int(backup_stars))
        applied += 1

    tmp_path = current_path.with_suffix(current_path.suffix + '.tmp')
    with tmp_path.open('w', encoding='utf-8') as handle:
        json.dump(current_data, handle, indent=2, ensure_ascii=False)
    tmp_path.replace(current_path)
    print(f"✅ Restored star counts for {applied} student(s). Current file updated.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
