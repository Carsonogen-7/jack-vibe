#!/usr/bin/env python3
"""Decode a JACKVIBE results code from the quiz and print a readable summary.

Usage:
    python3 tools/decode.py "JACKVIBE2.eyJ2Ijoy..."
    python3 tools/decode.py --json "JACKVIBE2...."   # raw JSON only
"""
import base64
import json
import sys

FOOD = ["flavor", "seasoning", "texture", "execution", "ingredients", "portion", "presentation", "crave"]
REST = ["service", "ambiance", "speed", "value"]


def decode(code: str) -> dict:
    code = code.strip()
    prefix, _, body = code.partition(".")
    if not prefix.startswith("JACKVIBE") or not body:
        raise ValueError("Not a JACKVIBE code. It should start with JACKVIBE2.")
    return json.loads(base64.b64decode(body).decode("utf-8"))


def stated_weights(d: dict) -> dict:
    """Slider ratings normalized so food sums to (100 - share) and restaurant to share."""
    share = d.get("share", 20)
    out = {}
    for group, total in ((FOOD, 100 - share), (REST, share)):
        s = sum(d["w"].get(k, 0) for k in group)
        for k in group:
            out[k] = total * d["w"].get(k, 0) / s if s else total / len(group)
    return out


def main(argv):
    raw = "--json" in argv
    args = [a for a in argv if a != "--json"]
    if not args:
        print(__doc__)
        return 1
    d = decode(args[0])
    if raw:
        print(json.dumps(d, indent=2))
        return 0
    w = stated_weights(d)
    print(f"Version {d.get('v')} · restaurant share {d.get('share')}%\n")
    for label, group in (("FOOD", FOOD), ("RESTAURANT", REST)):
        print(label)
        for k in sorted(group, key=lambda k: -w[k]):
            print(f"  {k:<13}{d['w'].get(k, 0):>3}/10  {w[k]:5.1f}%")
        print()
    print("Tradeoffs:  ", d.get("p"))
    print("Dish scores:", d.get("m"))
    print("Dealbreakers:", ", ".join(d.get("deal", [])) or "none")
    print("Price stance:", d.get("price") or "unanswered")
    print("Signature:  ", d.get("sig") or "-")
    print("Best dish:  ", d.get("best") or "-")
    print("Worst dish: ", d.get("worst") or "-")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
