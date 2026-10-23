#!/usr/bin/env python3
"""Decode a JACKLOG review-log code from log.html and print the reviews.

Usage:
    python3 tools/decode_log.py "JACKLOG1.eyJ2Ijox..."
    python3 tools/decode_log.py --json "JACKLOG1...."            # raw JSON only
    python3 tools/decode_log.py --csv reviews.csv "JACKLOG1...." # merge into a CSV

--csv adds the reviews to the file, creating it if needed. Each review has an id,
so sending the same review twice (or an edited version) replaces the old row
instead of duplicating it.
"""
import base64
import csv
import json
import os
import sys

FOOD = ["flavor", "seasoning", "texture", "execution", "ingredients", "portion", "presentation", "crave"]
REST = ["service", "ambiance", "speed", "value"]
COLUMNS = ["id", "date", "restaurant", "dish", "price", *FOOD, *REST, "dealbreakers", "overall", "note"]


def decode(code: str) -> dict:
    code = code.strip()
    prefix, _, body = code.partition(".")
    if not prefix.startswith("JACKLOG") or not body:
        raise ValueError("Not a review-log code. It should start with JACKLOG1.")
    return json.loads(base64.b64decode(body).decode("utf-8"))


def to_row(r: dict) -> dict:
    row = {"id": r["id"], "date": r.get("date", ""), "restaurant": r.get("rest", ""), "dish": r.get("dish", ""),
           "price": r.get("price", ""), "dealbreakers": ";".join(r.get("deal", [])),
           "overall": r.get("o", ""), "note": r.get("note", "")}
    for k in FOOD:
        row[k] = r.get("f", {}).get(k, "")
    for k in REST:
        row[k] = r.get("r", {}).get(k, "")
    return row


def merge_csv(path: str, rows: list) -> tuple:
    existing = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            existing = {row["id"]: row for row in csv.DictReader(f)}
    added = sum(1 for r in rows if r["id"] not in existing)
    existing.update({r["id"]: r for r in rows})
    ordered = sorted(existing.values(), key=lambda r: (r["date"], r["id"]))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(ordered)
    return added, len(rows) - added, len(ordered)


def fmt(v):
    return "  -" if v == "" else f"{float(v):4.1f}"


def main(argv):
    raw = "--json" in argv
    csv_path = None
    args = []
    it = iter(argv)
    for a in it:
        if a == "--json":
            continue
        if a == "--csv":
            csv_path = next(it, None)
            continue
        args.append(a)
    if not args:
        print(__doc__)
        return 1
    d = decode(args[0])
    if raw:
        print(json.dumps(d, indent=2, ensure_ascii=False))
        return 0
    rows = [to_row(r) for r in d.get("r", [])]
    print(f"Log version {d.get('v')} · {len(rows)} review(s)\n")
    for row in rows:
        title = " @ ".join(x for x in (row["dish"], row["restaurant"]) if x)
        price = f" · ${row['price']}" if row["price"] != "" else ""
        print(f"{row['date']}  {title}{price}  OVERALL {fmt(row['overall'])}")
        print("   food: " + "  ".join(f"{k[:5]} {fmt(row[k])}" for k in FOOD))
        print("   rest: " + "  ".join(f"{k[:5]} {fmt(row[k])}" for k in REST))
        if row["dealbreakers"]:
            print("   dealbreakers: " + row["dealbreakers"].replace(";", ", "))
        if row["note"]:
            print("   note: " + row["note"])
        print()
    if csv_path:
        added, updated, total = merge_csv(csv_path, rows)
        print(f"{csv_path}: {added} added, {updated} updated, {total} total")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
