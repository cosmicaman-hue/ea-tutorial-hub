import argparse
import glob
import json
import os
import tempfile
from datetime import datetime, timezone


def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _atomic_write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="ea_fee_repair_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


def _norm_date(s):
    s = str(s or "").strip()
    # Keep only YYYY-MM-DD when possible.
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return s


def _fee_fp(item):
    if not isinstance(item, dict):
        return ""
    date = _norm_date(item.get("date") or item.get("paid_on") or item.get("paidAt"))
    amount = str(item.get("amount") or "").strip()
    note = str(item.get("note") or item.get("remarks") or "").strip().lower()
    return f"{date}::{amount}::{note}"


def _merge_history(a, b):
    out = []
    seen = set()
    for src in (a or []), (b or []):
        if not isinstance(src, list):
            continue
        for item in src:
            if not isinstance(item, dict):
                continue
            fp = _fee_fp(item)
            if not fp or fp in seen:
                continue
            seen.add(fp)
            out.append(dict(item))
    out.sort(key=lambda x: _norm_date(x.get("date") or x.get("paid_on") or x.get("paidAt")))
    return out


def _max_date(a, b):
    aa = _norm_date(a)
    bb = _norm_date(b)
    if not aa:
        return bb
    if not bb:
        return aa
    return aa if aa >= bb else bb


def _iter_candidate_paths(instance_dir):
    patterns = [
        os.path.join(instance_dir, "offline_scoreboard_data.STABLE_BACKUP*.json"),
        os.path.join(instance_dir, "offline_scoreboard_data.pre_*.json"),
        os.path.join(instance_dir, "offline_scoreboard_backups", "*.json"),
        os.path.join(instance_dir, "offline_scoreboard_hourly_backups", "*.json"),
        os.path.join(instance_dir, "startup_restore_points", "*.json"),
    ]
    paths = set()
    for pat in patterns:
        for p in glob.glob(pat):
            if p and os.path.isfile(p):
                paths.add(p)
    return sorted(paths, key=os.path.getmtime, reverse=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance-dir", default=os.path.join(os.getcwd(), "instance"))
    ap.add_argument("--min-backups", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    instance_dir = os.path.abspath(args.instance_dir)
    live_path = os.path.join(instance_dir, "offline_scoreboard_data.json")
    live = _load_json(live_path)
    if not live:
        raise SystemExit(f"Cannot load live file: {live_path}")

    candidates = _iter_candidate_paths(instance_dir)
    if len(candidates) < args.min_backups:
        raise SystemExit(f"Not enough backups found under {instance_dir} (found {len(candidates)})")

    # Build best-known payment proof per studentId.
    best = {}
    for path in candidates:
        snap = _load_json(path)
        if not snap:
            continue
        for rec in snap.get("fee_records") or []:
            if not isinstance(rec, dict):
                continue
            try:
                sid = int(rec.get("studentId") or 0)
            except Exception:
                sid = 0
            if sid <= 0:
                continue
            last_paid = _norm_date(rec.get("last_paid_date"))
            hist = rec.get("payment_history") if isinstance(rec.get("payment_history"), list) else []
            if not last_paid and not hist:
                continue
            prev = best.get(sid) or {"last_paid_date": "", "payment_history": []}
            merged = {
                "last_paid_date": _max_date(prev.get("last_paid_date"), last_paid),
                "payment_history": _merge_history(prev.get("payment_history"), hist),
            }
            best[sid] = merged

    live_recs = live.get("fee_records") or []
    if not isinstance(live_recs, list):
        live_recs = []
    changed = 0
    touched = []
    for rec in live_recs:
        if not isinstance(rec, dict):
            continue
        try:
            sid = int(rec.get("studentId") or 0)
        except Exception:
            continue
        if sid <= 0:
            continue
        proof = best.get(sid)
        if not proof:
            continue
        before_paid = _norm_date(rec.get("last_paid_date"))
        before_hist = rec.get("payment_history") if isinstance(rec.get("payment_history"), list) else []
        after_paid = _max_date(before_paid, proof.get("last_paid_date"))
        after_hist = _merge_history(before_hist, proof.get("payment_history"))
        if after_paid != before_paid or len(after_hist) != len(before_hist):
            rec["last_paid_date"] = after_paid
            rec["payment_history"] = after_hist
            # Never backdate updated_at; just bump to now to avoid re-loss.
            rec["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            if not rec.get("created_at"):
                rec["created_at"] = rec["updated_at"]
            changed += 1
            touched.append(sid)

    if not changed:
        print("No fee record repairs needed.")
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(instance_dir, f"offline_scoreboard_data.pre_fee_repair_{stamp}.json")
    if args.dry_run:
        print(f"DRY RUN: would repair fee records: {changed}")
        print("StudentIds to be touched (first 30):", touched[:30])
        return

    # Backup current file, then write repaired.
    _atomic_write_json(backup_path, live)
    _atomic_write_json(live_path, live)

    print(f"Repaired fee records: {changed}")
    print(f"Backup saved: {backup_path}")
    print(f"Updated live: {live_path}")
    print("StudentIds touched (first 30):", touched[:30])


if __name__ == "__main__":
    main()
