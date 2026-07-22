#!/usr/bin/env python3
"""Manage per-student login credentials for the Cloudflare public site.

The public site (public_site/index.html) gates the Scoreboard and Information
tabs behind a client-side login. Credentials live in
public_site/credentials.json as per-student salted SHA-256 hashes:

    { "credentials": [ { "roll": "EA24B15", "salt": "<hex>", "hash": "<hex>" } ] }

PRIMARY PATH (recommended): manage credentials from the LAN app's Admin Control
Panel (Admin login -> Admin Control Panel -> "Public Site Login Credentials").
The server stores them in the PublicSiteCredential table and writes
credentials.json from the active rows on every Force Publish.

This script is a STANDALONE FALLLOWBACK for offline/CLI-only provisioning. Any
file it writes is OVERWRITTEN by the server on the next Force Publish, so use it
only when the LAN admin app is unavailable.

IMPORTANT SECURITY NOTE
-----------------------
This is a SOFT GATE only. credentials.json is served as a static public file,
so anyone can download it and brute-force the hashes offline. Use strong,
unique passwords. Do NOT reuse passwords that protect anything sensitive.

Usage
-----
Add or update a single student (will prompt for the password hidden):

    python scripts/generate_credentials.py EA24B15

Add or update several students from a CSV file (columns: roll,password):

    python scripts/generate_credentials.py --csv students_passwords.csv

List the rolls currently in credentials.json:

    python scripts/generate_credentials.py --list

Remove a student:

    python scripts/generate_credentials.py --remove EA24B15

The browser computes SHA-256(salt + password) over UTF-8 bytes using Web
Crypto, so this script uses the exact same encoding (hashlib + UTF-8) to
produce matching hashes.
"""
from __future__ import annotations

import argparse
import csv
import getpass
import hashlib
import json
import os
import secrets
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
CREDS_PATH = os.path.join(ROOT, "public_site", "credentials.json")


def _load() -> dict:
    if not os.path.isfile(CREDS_PATH):
        return {"credentials": []}
    with open(CREDS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("credentials"), list):
        return {"credentials": []}
    return data


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(CREDS_PATH), exist_ok=True)
    with open(CREDS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _hash_password(salt: str, password: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _upsert(data: dict, roll: str, password: str) -> None:
    roll = roll.strip().upper()
    salt = secrets.token_hex(8)
    entry = {"roll": roll, "salt": salt, "hash": _hash_password(salt, password)}
    creds = data["credentials"]
    for i, c in enumerate(creds):
        if str(c.get("roll", "")).upper() == roll:
            creds[i] = entry
            print(f"Updated credential for {roll}")
            return
    creds.append(entry)
    print(f"Added credential for {roll}")


def cmd_add(roll: str) -> int:
    password = getpass.getpass(f"Password for {roll}: ")
    if not password:
        print("Empty password aborted.", file=sys.stderr)
        return 1
    data = _load()
    _upsert(data, roll, password)
    _save(data)
    print(f"Wrote {CREDS_PATH}")
    return 0


def cmd_csv(path: str) -> int:
    added = 0
    data = _load()
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].strip().lower() in {"roll", "username"}:
                continue
            if len(row) < 2:
                print(f"Skipping malformed row: {row}", file=sys.stderr)
                continue
            _upsert(data, row[0].strip(), row[1])
            added += 1
    _save(data)
    print(f"Processed {added} entr(ies); wrote {CREDS_PATH}")
    return 0


def cmd_list() -> int:
    data = _load()
    creds = data.get("credentials", [])
    if not creds:
        print("(no credentials)")
        return 0
    print(f"{len(creds)} credential(s) in {CREDS_PATH}:")
    for c in creds:
        print(f"  {c.get('roll')}")
    return 0


def cmd_remove(roll: str) -> int:
    roll = roll.strip().upper()
    data = _load()
    before = len(data["credentials"])
    data["credentials"] = [
        c for c in data["credentials"] if str(c.get("roll", "")).upper() != roll
    ]
    if len(data["credentials"]) == before:
        print(f"{roll} not found.", file=sys.stderr)
        return 1
    _save(data)
    print(f"Removed {roll}; wrote {CREDS_PATH}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Manage public_site/credentials.json")
    p.add_argument("roll", nargs="?", help="Student roll no. to add/update")
    p.add_argument("--csv", dest="csv_path", help="CSV file (roll,password) to bulk import")
    p.add_argument("--list", action="store_true", help="List configured rolls")
    p.add_argument("--remove", metavar="ROLL", help="Remove a student's credential")
    args = p.parse_args()

    if args.list:
        return cmd_list()
    if args.remove:
        return cmd_remove(args.remove)
    if args.csv_path:
        return cmd_csv(args.csv_path)
    if args.roll:
        return cmd_add(args.roll)
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
