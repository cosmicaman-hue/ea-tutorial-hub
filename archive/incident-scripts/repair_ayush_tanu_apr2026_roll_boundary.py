import json
import shutil
from datetime import datetime
from pathlib import Path


DB_PATH = Path(r"C:\var\data\ea_tutorial_hub\offline_scoreboard_data.json")
BACKUP_STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_PATH = DB_PATH.with_name(f"{DB_PATH.stem}.bak-ayush-tanu-roll-boundary-{BACKUP_STAMP}.json")

TARGETS = [
    {
        "student_id": 1,
        "name": "Ayush Gupta",
        "old_roll": "EA24A01",
        "new_roll": "EA24B15",
        "effective_month": "2026-04",
        "repair_months": ["2026-02", "2026-03"],
    },
    {
        "student_id": 12,
        "name": "Tanu Sinha",
        "old_roll": "EA24A04",
        "new_roll": "EA24B16",
        "effective_month": "2026-04",
        "repair_months": ["2026-02", "2026-03"],
    },
]


def replace_roll_in_month_students(data, month_key, old_roll, new_roll):
    rolls = data.get("month_students", {}).get(month_key)
    if not isinstance(rolls, list):
        return False
    changed = False
    next_rolls = []
    seen = set()
    for roll in rolls:
        normalized = str(roll or "").strip().upper()
        if normalized == new_roll:
            normalized = old_roll
            changed = True
        if normalized and normalized not in seen:
            seen.add(normalized)
            next_rolls.append(normalized)
    if changed:
        data["month_students"][month_key] = next_rolls
    return changed


def replace_roll_in_month_profiles(data, month_key, student_id, old_roll, new_roll):
    profiles = data.get("month_roster_profiles", {}).get(month_key)
    if not isinstance(profiles, list):
        return False
    changed = False
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        profile_roll = str(profile.get("roll") or "").strip().upper()
        profile_sid = int(profile.get("studentId") or 0)
        if profile_sid == student_id or profile_roll == new_roll:
            if profile_roll == new_roll:
                profile["roll"] = old_roll
                changed = True
            if profile_sid == student_id and profile.get("roll") != old_roll:
                profile["roll"] = old_roll
                changed = True
            if profile_sid == 0:
                profile["studentId"] = student_id
                changed = True
    return changed


def ensure_april_profile_ids(data, student_id, new_roll):
    profiles = data.get("month_roster_profiles", {}).get("2026-04")
    if not isinstance(profiles, list):
        return False
    changed = False
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        if str(profile.get("roll") or "").strip().upper() == new_roll and int(profile.get("studentId") or 0) != student_id:
            profile["studentId"] = student_id
            changed = True
    return changed


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Live DB not found: {DB_PATH}")

    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backup created: {BACKUP_PATH}")

    data = json.loads(DB_PATH.read_text(encoding="utf-8"))
    changed = False

    roll_history = data.get("roll_history", [])
    if not isinstance(roll_history, list):
        raise ValueError("roll_history is not a list")

    for target in TARGETS:
        student_id = target["student_id"]
        old_roll = target["old_roll"]
        new_roll = target["new_roll"]
        effective_month = target["effective_month"]

        matching_entries = [
            entry for entry in roll_history
            if isinstance(entry, dict)
            and int(entry.get("student_id") or 0) == student_id
            and str(entry.get("old_roll") or "").strip().upper() == old_roll
            and str(entry.get("new_roll") or "").strip().upper() == new_roll
        ]
        if not matching_entries:
            raise ValueError(f"No roll_history entry found for {target['name']} {old_roll}->{new_roll}")

        for entry in matching_entries:
            if entry.get("effective_month") != effective_month:
                entry["effective_month"] = effective_month
                changed = True

        for month_key in target["repair_months"]:
            changed = replace_roll_in_month_students(data, month_key, old_roll, new_roll) or changed
            changed = replace_roll_in_month_profiles(data, month_key, student_id, old_roll, new_roll) or changed

        changed = ensure_april_profile_ids(data, student_id, new_roll) or changed

    if not changed:
        print("No changes were needed.")
        return

    data["server_updated_at"] = datetime.now().astimezone().isoformat()
    DB_PATH.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"Repair complete: {DB_PATH}")


if __name__ == "__main__":
    main()
