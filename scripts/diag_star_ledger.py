#!/usr/bin/env python3
"""diag_star_ledger.py — dump a student's full star ledger to diagnose balance drift.

Why this exists
---------------
The displayed current-month star balance is `student.stars` (the global ledger —
single source of truth per score_balance.compute_star_balance). When a student
claims the balance is wrong (e.g. "should be 11, shows 8"), the discrepancy is
almost always caused by one of:

  1. Stale-sync overwrite: mergeStudentsSuperset / _merge_students_preserve_active
     take the side with the newer `updated_at`, but sync ops bump `updated_at`
     artificially — so a stale snapshot with fewer stars can silently win.
  2. Cross-month duplicate score rows: merge keys include `month`, but
     db.addScore / deleteScore look up by (studentId, date) only, so duplicates
     with different month strings confuse the delta math.
  3. A historical repair/recompute that overwrote student.stars from a raw sum
     of score.stars (ignoring transfers/conversions).

This script prints everything needed to pinpoint which of those happened for a
given student: the ledger value, every score row, duplicate detection, a
recomputed current-month balance, month-profile carries, and the corruption
checkpoint hashes.

Usage
-----
    python scripts/diag_star_ledger.py                       # defaults to EA25H05
    python scripts/diag_star_ledger.py --roll EA24B15
    python scripts/diag_star_ledger.py --roll EA25H05 --current path/to/data.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import data_paths directly without triggering app/__init__.py (which pulls Flask).
import importlib.util as _ilu
_dp_spec = _ilu.spec_from_file_location(
    'ea_data_paths', _project_root / 'app' / 'utils' / 'data_paths.py'
)
_dp_mod = _ilu.module_from_spec(_dp_spec)
assert _dp_spec.loader is not None
_dp_spec.loader.exec_module(_dp_mod)
get_data_path = _dp_mod.get_data_path


def _safe_int(value, default=0):
    try:
        if value is None or value == '':
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_stamp(value):
    if not value:
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    # Accept ISO 8601 (Z or offset) and fall back to float epoch.
    try:
        if text.endswith('Z'):
            return datetime.fromisoformat(text[:-1] + '+00:00').timestamp()
        return datetime.fromisoformat(text).timestamp()
    except (ValueError, TypeError):
        try:
            return float(text)
        except (TypeError, ValueError):
            return 0.0


def _load(path: Path) -> dict:
    with path.open('r', encoding='utf-8') as handle:
        return json.load(handle)


def _find_student_by_roll(data: dict, roll: str):
    roll_norm = roll.strip().upper()
    for student in data.get('students', []) or []:
        if str(student.get('roll') or '').strip().upper() == roll_norm:
            return student
    return None


def _current_month_key() -> str:
    return datetime.now().strftime('%Y-%m')


def _month_key(value):
    if not value:
        return ''
    text = str(value).strip()
    if len(text) >= 7 and text[:4].isdigit() and text[4] == '-' and text[5:7].isdigit():
        return text[:7]
    return ''


def _print_section(title: str) -> None:
    print('\n' + '=' * 72)
    print(title)
    print('=' * 72)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--roll', default='EA25H05', help='Student roll to inspect (default: EA25H05)')
    parser.add_argument(
        '--current',
        default=None,
        help='Override current data path (defaults to configured data path)',
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    roll = args.roll.strip().upper()
    current_path = Path(args.current) if args.current else Path(get_data_path())
    if not current_path.exists():
        print(f"Current data file not found: {current_path}")
        return 2

    print(f"Data file : {current_path}")
    print(f"Target    : {roll}")
    data = _load(current_path)

    student = _find_student_by_roll(data, roll)
    if not student:
        print(f"Student with roll {roll} not found in data['students'].")
        return 1

    sid = _safe_int(student.get('id'))
    current_month = _current_month_key()

    # ── 1. Ledger snapshot ───────────────────────────────────────────────
    _print_section('1. STUDENT LEDGER (authoritative for current month)')
    print(f"  id              : {student.get('id')}")
    print(f"  roll            : {student.get('roll')}")
    print(f"  base_name       : {student.get('base_name') or student.get('name')}")
    print(f"  stars           : {_safe_int(student.get('stars'))}   <- displayed current-month balance")
    print(f"  stars_updated_at: {student.get('stars_updated_at') or '(not set)'}")
    print(f"  updated_at      : {student.get('updated_at') or '(not set)'}")
    print(f"  created_at      : {student.get('created_at') or '(not set)'}")
    print(f"  veto_count      : {_safe_int(student.get('veto_count'))}")
    print(f"  role_veto_count : {_safe_int(student.get('role_veto_count'))}")
    print(f"  active          : {student.get('active', True)}")

    # ── 2. Score rows ────────────────────────────────────────────────────
    _print_section('2. SCORE ROWS (every entry for this student)')
    scores = data.get('scores', []) or []
    mine = [s for s in scores if isinstance(s, dict) and _safe_int(s.get('studentId')) == sid]
    print(f"  Total score rows for studentId={sid}: {len(mine)}")
    if not mine:
        print("  (no score rows — ledger value is independent of scores)")
    else:
        print()
        print(f"  {'date':<12}{'month':<8}{'stars':>7}{'vetos':>7}{'usg_n':>7}{'usg_d':>7}{'tr_out':>8}{'tr_in':>7}  {'updated_at':<28}notes")
        print('  ' + '-' * 110)
        mine_sorted = sorted(mine, key=lambda r: (str(r.get('date') or ''), str(r.get('month') or '')))
        for s in mine_sorted:
            date = str(s.get('date') or '')
            month = str(s.get('month') or '')[:7]
            stars = _safe_int(s.get('stars'))
            vetos = _safe_int(s.get('vetos'))
            usg_n = _safe_int(s.get('star_usage_normal'))
            usg_d = _safe_int(s.get('star_usage_disciplinary'))
            tr_out = _safe_int(s.get('star_transfer_out'))
            tr_in = _safe_int(s.get('star_transfer_in'))
            stamp = str(s.get('updated_at') or s.get('created_at') or '')[:27]
            notes = str(s.get('notes') or '')[:60]
            print(f"  {date:<12}{month:<8}{stars:>7}{vetos:>7}{usg_n:>7}{usg_d:>7}{tr_out:>8}{tr_in:>7}  {stamp:<28}{notes}")

    # ── 3. Duplicate (studentId, date) detection ─────────────────────────
    _print_section('3. DUPLICATE (studentId, date) CHECK — different month strings trip db.addScore')
    by_date = defaultdict(list)
    for s in mine:
        by_date[str(s.get('date') or '')].append(s)
    dup_dates = {d: rows for d, rows in by_date.items() if len(rows) > 1}
    if not dup_dates:
        print("  No duplicate (studentId, date) rows found. Clean.")
    else:
        print(f"  Found {len(dup_dates)} date(s) with multiple rows:")
        for date, rows in sorted(dup_dates.items()):
            months = sorted({str(r.get('month') or '')[:7] for r in rows})
            star_values = [_safe_int(r.get('stars')) for r in rows]
            print(f"    {date}: {len(rows)} rows, months={months}, stars values={star_values}")
            for r in rows:
                print(f"      month={r.get('month')!r} stars={_safe_int(r.get('stars'))} "
                      f"updated_at={r.get('updated_at')!r} id={r.get('id')!r}")
            print("      -> db.addScore would update only the FIRST match; the rest are ghosts.")

    # ── 4. Recompute current-month derived balance vs ledger ─────────────
    _print_section(f'4. DERIVED BALANCE FOR CURRENT MONTH ({current_month}) vs LEDGER')
    month_rows = [s for s in mine if _month_key(s.get('month') or s.get('date')) == current_month]
    awards = sum(_safe_int(s.get('stars')) for s in month_rows if _safe_int(s.get('stars')) > 0)
    used = sum(abs(_safe_int(s.get('stars'))) for s in month_rows if _safe_int(s.get('stars')) < 0)
    transfer_out = sum(_safe_int(s.get('star_transfer_out')) for s in month_rows)
    transfer_in = sum(_safe_int(s.get('star_transfer_in')) for s in month_rows)
    ledger = _safe_int(student.get('stars'))
    print(f"  Current-month awards (stars>0)      : {awards}")
    print(f"  Current-month usage   (stars<0)     : {used}")
    print(f"  Current-month transfer_out          : {transfer_out}")
    print(f"  Current-month transfer_in           : {transfer_in}")
    print(f"  Net score.stars sum for month       : {awards - used}")
    print(f"  Ledger student.stars                : {ledger}")
    print(f"  Ledger is authoritative for current month — derived sum is informational only.")
    print(f"  If ledger < derived-sum, a stale sync likely overwrote a higher correct value.")

    # ── 5. Month roster profile carries ──────────────────────────────────
    _print_section('5. MONTH ROSTER PROFILES (historical carry-in fields)')
    profiles = data.get('month_roster_profiles', {}) or {}
    roll_norm = roll.strip().upper()
    found_any = False
    for month in sorted(profiles.keys()):
        rows = profiles[month] or []
        match = None
        for r in rows:
            if not isinstance(r, dict):
                continue
            if str(r.get('roll') or '').strip().upper() == roll_norm:
                match = r
                break
            if _safe_int(r.get('studentId')) == sid:
                match = r
                break
        if match:
            found_any = True
            print(f"  {month}: month_star_count={_safe_int(match.get('month_star_count'))} "
                  f"month_veto_count={_safe_int(match.get('month_veto_count'))} "
                  f"studentId={match.get('studentId')!r}")
    if not found_any:
        print("  No month_roster_profiles entries found for this student.")

    # ── 6. Corruption checkpoint hashes ──────────────────────────────────
    _print_section('6. CORRUPTION CHECKPOINT HASHES (anti_corruption_check.py)')
    last_star = data.get('_last_known_correct_star_hash')
    print(f"  _last_known_correct_star_hash : {last_star or '(not set)'}")
    print(f"  _last_known_correct_veto_hash : {data.get('_last_known_correct_veto_hash') or '(not set)'}")
    if last_star:
        print("  Run scripts/anti_corruption_check.py to compare against current state.")
    else:
        print("  No checkpoint has been seeded yet — drift cannot be detected until one is set.")

    # ── 7. Diagnosis hints ───────────────────────────────────────────────
    _print_section('7. DIAGNOSIS HINTS')
    if dup_dates:
        print("  [FOUND] Cross-month duplicate score rows — see section 3.")
        print("          These confuse db.addScore delta math and deleteScore restore math.")
    if ledger < (awards - used) and month_rows:
        print("  [FOUND] Ledger is LOWER than the current-month derived sum.")
        print("          Strong signal of a stale-sync overwrite (mergeStudentsSuperset took")
        print("          a stale snapshot with a bumped updated_at over the correct value).")
        print("          Recovery: scripts/reconcile_stars.py --backup <known-good>.json --roll " + roll)
    if not student.get('stars_updated_at'):
        print("  [INFO] stars_updated_at is not set on this student record.")
        print("         After applying the mergeStudentsSuperset hardening fix, the first star")
        print("         mutation will populate it; until then merges fall back to updated_at.")
    print()
    print("  If none of the above flags fired, inspect the score rows in section 2 manually")
    print("  for unexpected star deltas (e.g. a single -2 where -1 was intended).")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
