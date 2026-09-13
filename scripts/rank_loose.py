#!/usr/bin/env python3
"""Loose ranking: Artem's minimal-criteria view (set 2026-08-24).

He asked to strip the filter down to one requirement — **Python must be in the posting** — and to
stop hiding anything else. So this reports EVERY stored posting that mentions Python, and shows
the old exclusion reasons as visible TAGS instead of silently dropping the row.

The only things still treated as genuine knockouts, because they are legal/physical rather than
preferences:
  * no-sponsorship          - the employer says it cannot sponsor; applying is wasted effort
  * below-hsm-threshold     - stated pay under EUR 5,942/month, so IND cannot issue the permit
  * must-already-reside     - residency demanded outright
  * clearance-or-citizenship
  * ml-ai-engineer-role     - HIS rule: applying would be a false claim
  * local-language-required - explicit demand for fluent Dutch/German

Everything else (degree, on-call, below-senior, rival-core language, posting written in the local
language, contract, recruiter-undisclosed, onsite-heavy) is shown, not filtered.

Reads only stored fields — no network, so it is instant and can be re-run freely.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SEEN = BASE / ".claude/skills/job-scraper/job_scraper/seen_jobs.json"

HARD = {
    "no-sponsorship", "below-hsm-threshold", "must-already-reside",
    "clearance-or-citizenship", "ml-ai-engineer-role", "local-language-required",
}
GEO = {
    "NL": r"netherlands|amsterdam|rotterdam|utrecht|hague|eindhoven|delft|leiden|haarlem|"
          r"groningen|nijmegen|arnhem|breda|tilburg|almere|amersfoort|hilversum|\bNL\b",
    "DE": r"german|deutschland|berlin|munich|münchen|hamburg|frankfurt|köln|cologne|stuttgart|"
          r"düsseldorf|leipzig|dresden|nürnberg|nuremberg|hannover|karlsruhe|mannheim|bonn|"
          r"essen|dortmund|bremen|aachen|freiburg|heidelberg|augsburg|\bDE\b",
}


def excl_rule(e: dict) -> str | None:
    m = re.search(r"AUTO-EXCLUDED by screen_job\.py: ([a-z-]+)", e.get("notes") or "")
    return m.group(1) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-08-17", help="first_seen on/after this date")
    ap.add_argument("--country", choices=["NL", "DE", "ALL"], default="ALL")
    ap.add_argument("--min-python", type=int, default=1)
    ap.add_argument("--core-only", action="store_true", help="only where Python reads as required")
    a = ap.parse_args()

    seen = json.loads(SEEN.read_text())["seen"]
    rows = []
    dropped_hard: dict[str, int] = {}
    for u, e in seen.items():
        if (e.get("first_seen") or "") < a.since:
            continue
        if e.get("status") in ("applied", "duplicate"):
            continue
        py = e.get("screen_python") or 0
        if py < a.min_python:
            continue
        if a.core_only and not e.get("screen_python_core"):
            continue
        loc = (e.get("location") or "") + " " + (e.get("tier") or "")
        country = next((c for c, pat in GEO.items() if re.search(pat, loc, re.I)), "??")
        if a.country != "ALL" and country != a.country:
            continue
        r = excl_rule(e)
        if r in HARD:
            dropped_hard[r] = dropped_hard.get(r, 0) + 1
            continue
        tags = []
        if r:
            tags.append(r)                       # a soft exclusion, now just a tag
        tags += [f for f in (e.get("screen_flags") or []) if f != "linkedin-body-unverified"]
        rivalcore = [x.replace("(core)", "") for x in (e.get("screen_rivals") or "").split(",")
                     if "(core)" in x]
        if rivalcore:
            tags.append("core:" + "/".join(rivalcore))
        li = "LI" if "linkedin-body-unverified" in (e.get("screen_flags") or []) else "ATS"
        rows.append((py, bool(e.get("screen_python_core")), country, li,
                     e.get("company") or "", e.get("title") or "", ", ".join(tags), u,
                     e.get("first_seen") or ""))

    rows.sort(key=lambda r: (-r[0], not r[1], r[2]))
    print(f"{len(rows)} postings mention Python (>= {a.min_python}) since {a.since}, "
          f"country={a.country}\n")
    if dropped_hard:
        print("held back only by genuine knockouts:")
        for k, v in sorted(dropped_hard.items(), key=lambda kv: -kv[1]):
            print(f"   {v:>3}  {k}")
        print()
    print(f"{'py':>3} {'':1} {'c':2} {'src':3} {'company':26} {'title':44} tags")
    print("-" * 152)
    for py, core, country, li, co, title, tags, u, seen_at in rows:
        print(f"{py:>3} {'C' if core else ' '} {country:2} {li:3} {co[:26]:26} {title[:44]:44} "
              f"{tags[:52]}")
    print(f"\n(full URLs: rerun with --country and grep, or read seen_jobs.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
