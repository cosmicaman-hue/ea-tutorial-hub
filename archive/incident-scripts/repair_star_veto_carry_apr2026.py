"""
repair_star_veto_carry_apr2026.py

Fixes star and VETO carry values for all students across Jan–Mar 2026,
then sets student.stars and student.veto_count to the correct April 2026 carry.

What was broken:
  - month_star_count and month_veto_count were 0 in all Feb/Mar 2026 profiles
  - Jan 2026 carries were only stored in decorated names (e.g. "Jay** (V)")
  - student.stars did not reflect the true cumulative carry into April 2026

What this script does:
  1. Backs up the live JSON with a timestamp
  2. Extracts Jan 2026 star/veto carries from decorated names
  3. Chains carry forward: Feb carry_in = Jan carry_in + Jan net activity
     Mar carry_in = Feb carry_in + Feb net activity
  4. Writes corrected month_star_count / month_veto_count into Feb and Mar profiles
  5. Sets student.stars and student.veto_count = Mar carry_out for each student

Safe to re-run: only updates carry fields and student counters. Score rows are untouched.
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

DATA_FILE = Path("instance/offline_scoreboard_data.json")
BACKUP_DIR = Path("instance/manual_restore_safety")
MONTHS = ["2026-01", "2026-02", "2026-03"]


def make_backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / f"offline_scoreboard_data.pre_carry_fix_{ts}.json"
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DATA_FILE, dst)
    print(f"Backup: {dst}")
    return dst


def extract_name_carries(name: str):
    """Count * for stars; count V/v chars inside veto-only parens for vetos."""
    name = name or ""
    stars = name.count("*")
    # Only match parenthesised groups that contain exclusively V or v chars
    veto_groups = re.findall(r"\(([Vv]+)\)", name)
    vetos = sum(len(g) for g in veto_groups)
    return stars, vetos


def safe_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def month_key(v):
    s = str(v or "").strip()
    if len(s) >= 7:
        return s[:7]
    return ""


def get_profiles(data, mo):
    """Return the roster profile list for a month (always as a list of dicts)."""
    raw = (data.get("month_roster_profiles") or {}).get(mo) or {}
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return [v for v in raw.values() if isinstance(v, dict)]
    return []


def build_score_index(scores):
    """Build {(studentId, YYYY-MM): {awards, used, veto_awards, veto_used}}."""
    idx = {}
    for r in (scores or []):
        sid = safe_int(r.get("studentId"), 0)
        mo = month_key(r.get("month") or r.get("date"))
        if not sid or not mo:
            continue
        key = (sid, mo)
        if key not in idx:
            idx[key] = dict(star_awards=0, star_used=0, veto_awards=0, veto_used=0)
        s = safe_int(r.get("stars"), 0)
        v = safe_int(r.get("vetos"), 0)
        if s > 0:
            idx[key]["star_awards"] += s
        elif s < 0:
            idx[key]["star_used"] += abs(s)
        if v > 0:
            idx[key]["veto_awards"] += v
        elif v < 0:
            idx[key]["veto_used"] += abs(v)
    return idx


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    make_backup()

    scores = data.get("scores") or []
    students = data.get("students") or []
    score_idx = build_score_index(scores)

    # Build a quick student lookup by ID
    stu_by_id = {safe_int(s.get("id"), 0): s for s in students}

    # ── Step 1: extract Jan 2026 carries from decorated names ─────────────
    jan_profiles = get_profiles(data, "2026-01")
    jan_carry = {}  # {studentId: (stars, vetos)}
    for p in jan_profiles:
        sid = safe_int(p.get("studentId") or p.get("student_id"), 0)
        if not sid:
            continue
        s_carry, v_carry = extract_name_carries(p.get("name", ""))
        jan_carry[sid] = (s_carry, v_carry)
        # Write into the Jan profile so it's consistent
        p["month_star_count"] = s_carry
        p["month_veto_count"] = v_carry

    print(f"\nJan 2026 carries extracted for {len(jan_carry)} students")
    for sid, (sc, vc) in sorted(jan_carry.items()):
        if sc or vc:
            name = (stu_by_id.get(sid) or {}).get("name", "")[:35]
            print(f"  ID {sid:3d} ({name}): stars={sc}, vetos={vc}")

    # ── Step 2 & 3: chain Feb and Mar, then compute April carry ──────────
    # running_carry[sid] = (star_carry_into_month, veto_carry_into_month)
    # Start from Jan carry_in, then at end of Jan compute Jan carry_out = Jan carry_in + Jan net
    running = {}
    for sid, (sc, vc) in jan_carry.items():
        act = score_idx.get((sid, "2026-01"), {})
        star_out = max(0, sc + act.get("star_awards", 0) - act.get("star_used", 0))
        veto_out = max(0, vc + act.get("veto_awards", 0) - act.get("veto_used", 0))
        running[sid] = (star_out, veto_out)

    changes = {"2026-02": 0, "2026-03": 0, "student.stars": 0}

    for mo in ["2026-02", "2026-03"]:
        profiles = get_profiles(data, mo)
        for p in profiles:
            sid = safe_int(p.get("studentId") or p.get("student_id"), 0)
            if not sid or sid not in running:
                continue
            carry_in_s, carry_in_v = running[sid]

            old_s = safe_int(p.get("month_star_count"), 0)
            old_v = safe_int(p.get("month_veto_count"), 0)

            p["month_star_count"] = carry_in_s
            p["month_veto_count"] = carry_in_v

            if old_s != carry_in_s or old_v != carry_in_v:
                changes[mo] += 1
                name = (stu_by_id.get(sid) or {}).get("name", "")[:30]
                print(f"  {mo} ID {sid:3d} ({name}): stars {old_s}→{carry_in_s}, vetos {old_v}→{carry_in_v}")

            # Advance running carry using this month's activity
            act = score_idx.get((sid, mo), {})
            star_out = max(0, carry_in_s + act.get("star_awards", 0) - act.get("star_used", 0))
            veto_out = max(0, carry_in_v + act.get("veto_awards", 0) - act.get("veto_used", 0))
            running[sid] = (star_out, veto_out)

    # ── Step 4: write April carry into student.stars / student.veto_count ─
    print("\nSetting student.stars for April 2026 carry:")
    for sid, (apr_s, apr_v) in sorted(running.items()):
        stu = stu_by_id.get(sid)
        if not stu:
            continue
        old_s = safe_int(stu.get("stars"), 0)
        old_v = safe_int(stu.get("veto_count"), 0)
        if old_s != apr_s or old_v != apr_v:
            name = stu.get("name", "")[:35]
            print(f"  ID {sid:3d} ({name}): stars {old_s}→{apr_s}, veto_count {old_v}→{apr_v}")
            stu["stars"] = apr_s
            stu["veto_count"] = apr_v
            changes["student.stars"] += 1

    # ── Save ──────────────────────────────────────────────────────────────
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Feb profiles updated: {changes['2026-02']}, "
          f"Mar profiles updated: {changes['2026-03']}, "
          f"student records updated: {changes['student.stars']}")


if __name__ == "__main__":
    main()
