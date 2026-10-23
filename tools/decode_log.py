#!/usr/bin/env python3
"""Decode a JACKLOG review-log code from log.html and print the reviews.

Usage:
    python3 tools/decode_log.py "JACKLOG2.eyJ2Ijoy..."
    python3 tools/decode_log.py --json "JACKLOG2...."            # raw JSON only
    python3 tools/decode_log.py --csv reviews.csv "JACKLOG2...." # merge into a CSV

Reads both formats:
  JACKLOG1  flat reviews, each with its own restaurant scores
  JACKLOG2  restaurants ("places") with one set of restaurant scores each, plus dishes that point at a place

--csv adds the dishes to the file, creating it if needed. Each dish has an id, so sending the same dish
twice (or an edited version) replaces the old row instead of duplicating it. Restaurants are kept in
<csv name>_places.json; when a restaurant's scores change, every dish row from that restaurant is updated.
"""
import base64
import csv
import json
import os
import sys

FOOD = ["flavor", "seasoning", "texture", "execution", "ingredients", "portion", "presentation", "crave"]
REST = ["service", "ambiance", "speed", "value"]
COLUMNS = ["id", "date", "place_id", "restaurant", "dish", "price", *FOOD, *REST, "dealbreakers", "overall", "note"]


def decode(code: str) -> dict:
    code = code.strip()
    prefix, _, body = code.partition(".")
    if not prefix.startswith("JACKLOG") or not body:
        raise ValueError("Not a review-log code. It should start with JACKLOG2.")
    return json.loads(base64.b64decode(body).decode("utf-8"))


def places_of(d: dict) -> dict:
    return {p["id"]: p for p in d.get("p", [])} if d.get("v", 1) >= 2 else {}


def to_row(r: dict, places: dict) -> dict:
    p = places.get(r.get("place"))
    rest_scores = p.get("r", {}) if p else r.get("r", {})
    row = {"id": r["id"], "date": r.get("date", ""), "place_id": r.get("place", ""),
           "restaurant": p["name"] if p else r.get("rest", ""), "dish": r.get("dish", ""),
           "price": r.get("price", ""), "dealbreakers": ";".join(r.get("deal", [])),
           "overall": r.get("o", ""), "note": r.get("note", "")}
    for k in FOOD:
        row[k] = r.get("f", {}).get(k, "")
    for k in REST:
        row[k] = rest_scores.get(k, "")
    return row


def merge_csv(path: str, rows: list, places: dict) -> tuple:
    existing = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            existing = {row["id"]: row for row in csv.DictReader(f)}
    added = sum(1 for r in rows if r["id"] not in existing)
    existing.update({r["id"]: r for r in rows})

    places_path = os.path.splitext(path)[0] + "_places.json"
    known = {}
    if os.path.exists(places_path):
        with open(places_path, encoding="utf-8") as f:
            known = json.load(f)
    known.update(places)
    with open(places_path, "w", encoding="utf-8") as f:
        json.dump(known, f, indent=2, ensure_ascii=False)

    # Rows from JACKLOG1 have no place id: link them by restaurant name, then copy each place's
    # current name and scores onto all of its rows so a restaurant reads the same everywhere
    by_name = {p["name"].strip().lower(): p for p in known.values()}
    for row in existing.values():
        if not row.get("place_id"):
            p = by_name.get(row.get("restaurant", "").strip().lower())
            if p:
                row["place_id"] = p["id"]
        p = known.get(row.get("place_id"))
        if p:
            row["restaurant"] = p["name"]
            for k in REST:
                row[k] = p.get("r", {}).get(k, "")

    ordered = sorted(existing.values(), key=lambda r: (r["date"], r["id"]))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
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
    places = places_of(d)
    rows = [to_row(r, places) for r in d.get("r", [])]
    print(f"Log version {d.get('v')} · {len(rows)} dish(es) · {len(places)} restaurant(s)\n")
    for p in places.values():
        print(f"{p['name']}  restaurant: " + "  ".join(f"{k[:5]} {fmt(p.get('r', {}).get(k, ''))}" for k in REST))
    if places:
        print()
    for row in rows:
        title = " @ ".join(x for x in (row["dish"], row["restaurant"]) if x)
        price = f" · ${row['price']}" if row["price"] != "" else ""
        print(f"{row['date']}  {title}{price}  OVERALL {fmt(row['overall'])}")
        print("   food: " + "  ".join(f"{k[:5]} {fmt(row[k])}" for k in FOOD))
        if not places:
            print("   rest: " + "  ".join(f"{k[:5]} {fmt(row[k])}" for k in REST))
        if row["dealbreakers"]:
            print("   dealbreakers: " + row["dealbreakers"].replace(";", ", "))
        if row["note"]:
            print("   note: " + row["note"])
        print()
    if csv_path:
        added, updated, total = merge_csv(csv_path, rows, places)
        print(f"{csv_path}: {added} added, {updated} updated, {total} total")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
