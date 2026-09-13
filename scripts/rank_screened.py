#!/usr/bin/env python3
"""Rank screened postings by what their BODY actually says about the stack.

Python weight comes from the posting text (counted by screen_job.py), not from the
title, which is the whole point of the collect-broad-filter-by-body pipeline.

Usage:
  ./scripts/rank_screened.py                      # everything screened, best first
  ./scripts/rank_screened.py --first-seen 2026-08-14
  ./scripts/rank_screened.py --tier NL --min-python 2
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SEEN = BASE / ".claude/skills/job-scraper/job_scraper/seen_jobs.json"

# Employers already established as recognised IND sponsors (see search-queries.md).
SPONSORS = {
    "picnic", "albertheijn", "bolcom", "aholddelhaize", "sendcloud", "jumbo", "abnamro", "ing",
    "nnpersoneel", "apg", "vanlanschotkempen", "netflix", "uber", "alliander", "eneco", "tno",
    "castor", "leadinfo", "xebia", "framer", "nxp", "philips", "here", "asml", "tomtom",
    "nebius", "datasnipper", "agriplace", "simvia", "screen6", "sambatv", "mendix", "corsearch",
    "bitvavo", "blocktech", "telnyx", "adyen", "optiver", "imc", "flowtraders",
}
NOT_SPONSORS = {
    "getstream", "nightwatch", "dott", "swapfiets", "studocu", "miro", "aiven", "confluent",
    "transip", "adevinta", "hiber", "withthegrid", "ns", "prorail", "channable", "taktile",
    "qrt", "cloudbeds", "aerovect",
}


def _matches(key: str, name: str) -> bool:
    """Short names must match exactly. A bare substring test tagged Harrington Starr and
    Us3 Consulting as sponsors because both contain "ing"."""
    if len(name) <= 4:
        return key == name
    return key == name or key.startswith(name) or name in key


def sponsor_tag(company: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "", company.lower())
    if any(_matches(key, s) for s in SPONSORS):
        return "SPONSOR"
    if any(_matches(key, s) for s in NOT_SPONSORS):
        return "not-sponsor"
    return ""


def tier_of(entry: dict) -> str:
    """Older rounds wrote city names into `tier`; normalise to NL / UK / other."""
    t = (entry.get("tier") or "").strip()
    if t in ("NL", "UK"):
        return t
    loc = (entry.get("location") or "") + " " + t
    if re.search(r"united kingdom|england|london|scotland|wales", loc, re.I):
        return "UK"
    if re.search(r"netherlands|amsterdam|rotterdam|utrecht|hague|eindhoven|randstad", loc, re.I):
        return "NL"
    if re.search(r"german|berlin|munich|münchen|hamburg", loc, re.I):
        return "DE"
    return "??"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first-seen")
    ap.add_argument("--tier", choices=["NL", "UK", "DE"])
    ap.add_argument("--min-python", type=int, default=0)
    ap.add_argument("--include-flagged", action="store_true", default=True)
    a = ap.parse_args()

    seen = json.loads(SEEN.read_text())["seen"]
    rows = []
    for u, e in seen.items():
        if e.get("screen_verdict") not in ("PASS", "FLAG"):
            continue
        if a.first_seen and e.get("first_seen") != a.first_seen:
            continue
        tier = tier_of(e)
        if a.tier and tier != a.tier:
            continue
        py = e.get("screen_python")
        if py is None:  # older entries kept their metrics inside notes
            m = re.search(r"py=(\d+) core=(\w+)", e.get("notes") or "")
            py = int(m.group(1)) if m else 0
            core = (m.group(2) == "True") if m else False
        else:
            core = bool(e.get("screen_python_core"))
        flags = ", ".join(e.get("screen_flags") or [])
        if py < a.min_python:
            continue
        rows.append((py, core, tier, e["company"], e["title"],
                     e.get("location", ""), e["screen_verdict"], sponsor_tag(e["company"]), flags, u))

    rows.sort(key=lambda r: (-r[0], not r[1], r[3]))
    print(f"{len(rows)} screened survivors, ranked by Python weight IN THE BODY\n")
    print(f"{'py':>3} {'':1} {'v':4} {'t':2} {'company':22} {'title':44} {'sponsor':11} flags")
    print("-" * 132)
    for py, core, tier, co, t, loc, v, sp, fl, u in rows:
        print(f"{py:>3} {'C' if core else ' '} {v:4} {tier:2} {co[:22]:22} {t[:44]:44} {sp:11} {fl[:30]}")
    if not rows:
        print("(nothing — has ./screen run on this batch yet?)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
