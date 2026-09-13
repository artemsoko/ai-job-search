#!/usr/bin/env python3
"""Collect broad, then filter by BODY. The whole job-hunt pipeline in one command.

Why this replaces the old query-by-keyword approach
---------------------------------------------------
Verified on 2026-08-14: LinkedIn's guest keyword search does NOT reach the job
description. Querying `-q "Python"` for the Netherlands and paging six deep (60
results) never surfaced NVIDIA req 4453396506/4453393675, whose posting body
requires "Proficiency in Python" but whose TITLE is "Senior Software Developer".
NVIDIA had 6 open NL reqs and none were in a 371-entry seen_jobs.json.

So filtering on the query string is structurally broken: it can only ever find
what the employer put in the title. The fix is to invert the pipeline.

  OLD:  query "Senior Python Engineer" -> trust the title -> maybe read the body
  NEW:  query generic role titles       -> read EVERY body -> filter on the body

Stage 4 (screen_job.py) is what actually enforces the stack requirement, by counting
Python and rival languages in the posting text and applying the hard-exclusion rules.

Usage
-----
  ./hunt                       # 30-day window, 3 pages per query
  ./hunt --jobage 7 --pages 2  # quick daily sweep
  ./hunt --no-screen           # collect and dedup only
  ./hunt --dry-run             # show the query plan and exit

Note on volume: this issues roughly (titles x locations x pages) requests against
LinkedIn's public endpoints. Keep --pages modest for routine runs; personal use only.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CLI = BASE / ".agents/skills/linkedin-search/cli/src/cli.ts"
SEEN = BASE / ".claude/skills/job-scraper/job_scraper/seen_jobs.json"
TRACKER = BASE / ".claude/skills/job-scraper/job_search_tracker.csv"

# GENERIC titles only. Deliberately NO "Python", NO "Django", NO stack words: those
# words in a query restrict results to postings that put them in the TITLE, which is
# exactly the blind spot this pipeline exists to remove. The stack is checked in stage 4.
TITLES = [
    "Senior Software Engineer",
    "Senior Software Developer",
    "Senior Backend Engineer",
    "Staff Software Engineer",
    "Lead Software Engineer",
    "Principal Software Engineer",
    "Backend Developer",
    "Platform Engineer",
    "Tech Lead",
]
# London dropped by Artem 2026-08-11 ("в топку той Лондон"); Germany added as the primary
# secondary track 2026-08-18 once the NL salary floor was relaxed.
LOCATIONS = ["Netherlands", "Germany", "Berlin, Germany", "Munich, Germany"]


TIERS = {
    "NL": r"netherlands|amsterdam|rotterdam|utrecht|hague|eindhoven|delft|leiden|randstad",
    "IE": r"ireland|dublin|cork|galway|limerick",
    "DE": r"german|deutschland|berlin|munich|münchen|hamburg|frankfurt|cologne|köln|stuttgart",
    "UK": r"united kingdom|england|london|scotland|wales",
    "DK": r"denmark|copenhagen",
}


def tier_for(loc: str | None) -> str:
    """Derive the country tier from the posting's own location string.

    BUG FIXED 2026-09-08: this used to be hardcoded to "NL" for anything that was not UK, so
    every Irish and German posting collected by --locations was stored as tier NL. That silently
    poisoned every downstream country filter - an "NL apply list" came back full of Dublin and
    Berlin roles.
    """
    for tier, pat in TIERS.items():
        if re.search(pat, loc or "", re.I):
            return tier
    return "??"


def norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def job_id(u: str | None) -> str | None:
    m = re.search(r"(\d{9,})", u or "")
    return m.group(1) if m else None


def search(title: str, location: str, jobage: int, page: int) -> list[dict]:
    try:
        out = subprocess.run(
            ["bun", "run", str(CLI), "search", "-q", title, "-l", location,
             "--jobage", str(jobage), "--page", str(page), "--format", "json"],
            capture_output=True, text=True, timeout=120, cwd=BASE)
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"    ! {title} / {location} p{page}: {exc}", file=sys.stderr)
        return []
    if out.returncode != 0:
        return []
    try:
        return json.loads(out.stdout).get("results", [])
    except json.JSONDecodeError:
        return []


def load_known() -> tuple[set, set, set]:
    seen = json.loads(SEEN.read_text())["seen"]
    ids = {job_id(u) for u in seen} | {job_id(e.get("url", "")) for e in seen.values()}
    cts = {(norm(e.get("company")), norm(e.get("title"))) for e in seen.values()}
    with TRACKER.open(newline="") as fh:
        for r in csv.DictReader(fh):
            cts.add((norm(r["company"]), norm(r["role"])))
            ids.add(job_id(r.get("url", "")))
    return seen, ids - {None}, cts


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect broad, filter by body.")
    ap.add_argument("--jobage", type=int, default=30)
    # RAISED from 3 to 10 on 2026-09-11. Measured that day: "Senior Software Engineer" in the
    # Netherlands with a 7-day window returns 10 NEW jobs per page at page 1, 12, 20, 30 AND 50 —
    # LinkedIn does not loop and does not exhaust. --pages 3 was therefore capturing ~30 of 500+
    # available results per title/location, about 6%. Every sweep before this date sampled that
    # thin slice, which is the real reason "no new roles" kept coming back — the filter was never
    # the bottleneck, the collection was.
    ap.add_argument("--pages", type=int, default=10)
    ap.add_argument("--no-screen", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--locations", metavar="LOC", nargs="+",
                    help="override the default location list, e.g. --locations Netherlands")
    a = ap.parse_args()

    locations = a.locations or LOCATIONS
    plan = [(t, loc, p) for t in TITLES for loc in locations for p in range(1, a.pages + 1)]
    print(f"query plan: {len(TITLES)} generic titles x {len(locations)} locations "
          f"x {a.pages} pages = {len(plan)} requests, {a.jobage}-day window")
    if a.dry_run:
        for t in TITLES:
            print(f"  {t}")
        return 0

    print("\n[1/4] collecting")
    pool: dict[str, dict] = {}
    for i, (t, loc, p) in enumerate(plan, 1):
        res = search(t, loc, a.jobage, p)
        new = sum(1 for r in res if r["id"] not in pool)
        for r in res:
            r.setdefault("_q", t)
            r.setdefault("_loc", loc)
            pool.setdefault(r["id"], r)
        print(f"  [{i:>3}/{len(plan)}] {t[:28]:28s} {loc[:14]:14s} p{p} -> {len(res):2d} hits, {new:2d} new "
              f"(pool {len(pool)})")
    if not pool:
        print("no results at all — check bun and the linkedin CLI")
        return 1

    print(f"\n[2/4] dedup against seen_jobs + tracker")
    seen, known_ids, known_cts = load_known()
    fresh = []
    for jid, r in pool.items():
        if jid in known_ids:
            continue
        if (norm(r["company"]), norm(r["title"])) in known_cts:
            continue
        fresh.append(r)
    print(f"  pool={len(pool)}  already known={len(pool) - len(fresh)}  FRESH={len(fresh)}")

    print(f"\n[3/4] recording as unassessed (body not yet read)")
    doc = json.loads(SEEN.read_text())
    today = date.today().isoformat()
    for r in fresh:
        loc = r.get("location", "")
        doc["seen"][r["url"]] = {
            "title": r["title"], "company": r["company"], "location": loc, "url": r["url"],
            "portal": "linkedin", "date": r.get("date"), "first_seen": today,
            "fit": "unknown",
            "tier": tier_for(loc),
            "status": "new", "assessed": False,
            "notes": f"hunt {today}: generic-title sweep, query '{r.get('_q')}'",
        }
    SEEN.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"  wrote {len(fresh)} entries, seen_jobs now {len(doc['seen'])}")

    if a.no_screen or not fresh:
        print("\nskipping screen (--no-screen or nothing fresh). "
              f"Run: ./screen --unassessed --first-seen {today} --limit {len(fresh)}")
        return 0

    print(f"\n[4/4] screening {len(fresh)} bodies — THIS is the stack filter")
    rc = subprocess.run([sys.executable, str(BASE / "scripts/screen_job.py"),
                         "--unassessed", "--first-seen", today, "--limit", str(len(fresh))],
                        cwd=BASE)
    print(f"\ndone. Rank what survived with:  ./scripts/rank_screened.py --first-seen {today}")
    return rc.returncode


if __name__ == "__main__":
    sys.exit(main())
