#!/usr/bin/env python
"""
Dual-workbook merger for EA scoreboard.

Usage:
  python smart_excel_dual_merge.py "old_data.xlsm" "active_roster.xlsx" -o merged.json --month 2026-02

What it does:
- Extracts visible data from both workbooks
- Preserves all historical month data from old workbook
- Applies active roster workbook to one target month
- Ensures exactly one active profile per roll for target month
- Keeps historical scores untouched; prunes target-month scores to active roster only
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from smart_excel_extractor import extract_workbook


def norm(value: object) -> str:
    return str(value or "").strip().upper()


def choose_target_month(active_month_students: Dict[str, List[str]], explicit: str | None) -> str:
    if explicit:
        return explicit
    keys = sorted(active_month_students.keys(), reverse=True)
    if keys:
        return keys[0]
    return datetime.now().strftime("%Y-%m")


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge historical workbook with latest active roster workbook.")
    parser.add_argument("historical_workbook", help="Path to old/historical workbook")
    parser.add_argument("active_workbook", help="Path to latest active roster workbook")
    parser.add_argument("-o", "--out", default="smart_dual_merge_output.json", help="Output JSON path")
    parser.add_argument("--month", default=None, help="Target month (YYYY-MM). Defaults to latest month in active workbook")
    args = parser.parse_args()

    historical_path = Path(args.historical_workbook)
    active_path = Path(args.active_workbook)

    if not historical_path.exists():
        raise SystemExit(f"Historical workbook not found: {historical_path}")
    if not active_path.exists():
        raise SystemExit(f"Active roster workbook not found: {active_path}")

    hist = extract_workbook(historical_path)
    active = extract_workbook(active_path)

    target_month = choose_target_month(active.month_students, args.month)

    students_by_roll: Dict[str, dict] = {}
    next_id = 1

    for student in hist.students:
        roll = norm(student.get("roll"))
        if not roll:
            continue
        copy = dict(student)
        copy["id"] = next_id
        next_id += 1
        copy["active"] = False
        students_by_roll[roll] = copy

    active_profiles = []
    for student in active.students:
        roll = norm(student.get("roll"))
        name = str(student.get("name") or "").strip()
        if not roll or not name:
            continue
        class_value = student.get("class")
        profile = {
            "roll": roll,
            "name": name,
            "base_name": name,
            "class": class_value if isinstance(class_value, int) else None,
        }
        active_profiles.append(profile)

        if roll not in students_by_roll:
            students_by_roll[roll] = {
                "id": next_id,
                "roll": roll,
                "name": name,
                "base_name": name,
                "raw_name": name,
                "class": profile["class"],
                "fees": None,
                "total_score": None,
                "rank": None,
                "vote_power": None,
                "stars": 0,
                "veto_count": 0,
                "active": True,
            }
            next_id += 1
        else:
            students_by_roll[roll]["name"] = name
            students_by_roll[roll]["base_name"] = name
            students_by_roll[roll]["raw_name"] = name
            if profile["class"] is not None:
                students_by_roll[roll]["class"] = profile["class"]

    active_rolls = {norm(p["roll"]) for p in active_profiles}
    for roll, student in students_by_roll.items():
        student["active"] = roll in active_rolls

    id_by_roll = {roll: student["id"] for roll, student in students_by_roll.items()}

    scores: List[dict] = []
    score_id = 1
    for score in hist.scores:
        student_id = score.get("studentId")
        hist_student = next((s for s in hist.students if s.get("id") == student_id), None)
        if not hist_student:
            continue
        roll = norm(hist_student.get("roll"))
        if not roll or roll not in id_by_roll:
            continue
        mapped_id = id_by_roll[roll]
        month = str(score.get("month") or "")
        if month == target_month and roll not in active_rolls:
            continue
        copy = dict(score)
        copy["id"] = score_id
        copy["studentId"] = mapped_id
        scores.append(copy)
        score_id += 1

    month_students = {k: list(v) for k, v in hist.month_students.items()}
    month_students[target_month] = sorted(active_rolls)

    month_roster_profiles = {target_month: active_profiles}

    output = {
        "students": list(students_by_roll.values()),
        "scores": scores,
        "month_students": month_students,
        "month_extra_columns": hist.month_extra_columns,
        "month_student_extras": hist.month_student_extras,
        "month_roster_profiles": month_roster_profiles,
        "scanned_sheets": {
            "historical": hist.scanned_sheets,
            "active": active.scanned_sheets,
        },
        "generated_at": datetime.now().isoformat(),
        "target_month": target_month,
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Merged output: {out_path}")
    print(f"Target month: {target_month}")
    print(f"Students: {len(output['students'])}")
    print(f"Scores: {len(output['scores'])}")
    print(f"Active roster size: {len(active_rolls)}")


if __name__ == "__main__":
    main()
