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
  ./hunt                                  # every default portal, 30-day window
  ./hunt --jobage 7 --pages 2              # quick daily sweep
  ./hunt --locations London                # UK only: linkedin + reed + totaljobs + wttj
  ./hunt --portals reed wttj -l London     # pick portals explicitly
  ./hunt --portals linkedin xing -l Berlin, Germany   # xing is opt-in, see PORTALS
  ./hunt --no-screen                       # collect and dedup only
  ./hunt --dry-run                         # show the per-portal query plan and exit

Multi-portal since 2026-09-17. A portal is only queried for locations whose country tier it
serves, so reed/totaljobs/wttj run for London, nationalevacaturebank for the Netherlands, and
linkedin for everything. Per-portal caps are respected: totaljobs refuses page 2+ by design.

Note on volume: this issues roughly (titles x matching locations x pages) requests per portal
against public endpoints. Keep --pages modest for routine runs; personal use only.
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
SEEN = BASE / ".claude/skills/job-scraper/job_scraper/seen_jobs.json"
TRACKER = BASE / ".claude/skills/job-scraper/job_search_tracker.csv"


def _cli(skill: str) -> Path:
    return BASE / ".agents/skills" / skill / "cli/src/cli.ts"


# Portal registry. Added 2026-09-17: this script used to hardcode the linkedin CLI and stamp
# "portal": "linkedin" on every record, so the five portal skills installed that day were
# invisible to ./hunt.
#
#   markets   - country tiers (see TIERS) this portal can serve. {"*"} means any.
#               A portal is skipped for a location whose tier it does not serve, because
#               querying reed.co.uk for "Netherlands" is pure waste.
#   location  - does the CLI accept -l? (nationalevacaturebank is NL-only and has no flag)
#   jobage    - does --jobage do anything? (xing accepts and ignores it)
#   max_pages - hard cap. totaljobs refuses anything past page 1 for robots compliance.
#   default   - included in a plain `./hunt`, or opt-in via --portals.
PORTALS: dict[str, dict] = {
    "linkedin": {"skill": "linkedin-search", "markets": {"*"},
                 "location": True, "jobage": True, "max_pages": None, "default": True},
    "reed": {"skill": "reed-search", "markets": {"UK"},
             "location": True, "jobage": True, "max_pages": None, "default": True},
    "totaljobs": {"skill": "totaljobs-search", "markets": {"UK"},
                  "location": True, "jobage": True, "max_pages": 1, "default": True},
    "wttj": {"skill": "wttj-search", "markets": {"UK"},
             "location": True, "jobage": True, "max_pages": None, "default": True},
    "nvb": {"skill": "nationalevacaturebank-search", "markets": {"NL"},
            "location": False, "jobage": True, "max_pages": None, "default": True},
    # OPT-IN ONLY. Xing's index is German-language, so an English query returns nothing, and
    # German queries return German-language postings that the `posting-written-in-local-language`
    # rule then excludes - net yield is about zero. Its robots.txt also disallows /jobs/search
    # for generic crawlers, so keep the volume low. Enable with: --portals linkedin xing
    "xing": {"skill": "xing-search", "markets": {"DE"},
             "location": True, "jobage": False, "max_pages": None, "default": False},
}

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
# London was dropped 2026-08-11, then came back: the profile now targets Amsterdam/NL first and
# London/UK second. Re-added 2026-09-17 together with the UK portal skills. Germany has been the
# primary secondary track since 2026-08-18, when the NL salary floor was relaxed.
LOCATIONS = ["Netherlands", "Germany", "Berlin, Germany", "Munich, Germany", "London"]


# Order matters: the first pattern that matches wins, so US goes before UK to stop
# "New York" being read as "York".
TIERS = {
    "US": r"new york|nyc|san francisco|bay area|seattle|austin|boston|chicago|denver|atlanta|"
          r"los angeles|united states|\busa\b|remote, us",
    "NL": r"netherlands|amsterdam|rotterdam|utrecht|hague|eindhoven|delft|leiden|randstad",
    "IE": r"ireland|dublin|cork|galway|limerick",
    "DE": r"german|deutschland|berlin|munich|münchen|hamburg|frankfurt|cologne|köln|stuttgart",
    "UK": r"united kingdom|england|london|scotland|wales|\bgb\b|\buk\b",
    "DK": r"denmark|copenhagen",
}


def tier_for(loc: str | None, portal: str | None = None) -> str:
    """Derive the country tier from the posting's own location string.

    BUG FIXED 2026-09-08: this used to be hardcoded to "NL" for anything that was not UK, so
    every Irish and German posting collected by --locations was stored as tier NL. That silently
    poisoned every downstream country filter - an "NL apply list" came back full of Dublin and
    Berlin roles.

    EXTENDED 2026-09-17: a positive match still wins, but a location that matches nothing now
    falls back to the portal's market when that portal serves exactly one. reed and totaljobs
    only carry UK jobs, yet their location strings are towns and counties - "Colnbrook,
    Berkshire", "Kingston Upon Thames, Surrey" - which no country pattern will ever match, and
    43 of 147 records from the first multi-portal run landed on tier "??" as a result.
    """
    for tier, pat in TIERS.items():
        if re.search(pat, loc or "", re.I):
            return tier
    if portal:
        markets = PORTALS[portal]["markets"]
        if len(markets) == 1 and "*" not in markets:
            return next(iter(markets))
    return "??"


def repair_location(portal: str, r: dict) -> str:
    """Return a trustworthy location string for one result.

    wttj-search's client-side GB filter substring-matches, so a New York posting comes back as
    `"location": "York, GB"` — it strips "New " and then believes it. Verified 2026-09-17: 24 of
    27 `"York, GB"` results were New York City, identifiable only from the URL slug. So for wttj
    the slug is the source of truth, not the location field.

    Slug shape: `.../jobs/<title>_<city>_<hash>`
    """
    loc = r.get("location", "") or ""
    if portal != "wttj":
        return loc
    slug = (r.get("url") or "").rstrip("/").rsplit("/", 1)[-1]
    parts = slug.split("_")
    if len(parts) >= 3:
        city = parts[-2].replace("-", " ").strip()
        if city:
            return city.title()
    return loc


def norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def job_id(u: str | None) -> str | None:
    m = re.search(r"(\d{9,})", u or "")
    return m.group(1) if m else None


def identity(url: str | None) -> str:
    """Stable dedup key across portals.

    LinkedIn and totaljobs carry a 9+ digit id in the URL, so job_id() is enough for them.
    reed ids are 8 digits, wttj uses a slug and nationalevacaturebank a UUID - job_id()
    returns None for all three, which would have collapsed them into one bucket and let the
    (company, title) fallback do all the work. So: numeric id when there is one, otherwise the
    normalised URL.
    """
    return job_id(url) or norm(url)


def search(portal: str, title: str, location: str, jobage: int, page: int) -> list[dict]:
    spec = PORTALS[portal]
    argv = ["bun", "run", str(_cli(spec["skill"])), "search", "-q", title,
            "--page", str(page), "--format", "json"]
    if spec["location"]:
        argv += ["-l", location]
    if spec["jobage"]:
        argv += ["--jobage", str(jobage)]
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=120, cwd=BASE)
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"    ! {portal} {title} / {location} p{page}: {exc}", file=sys.stderr)
        return []
    if out.returncode != 0:
        return []
    try:
        return json.loads(out.stdout).get("results", [])
    except json.JSONDecodeError:
        return []


def build_plan(portals: list[str], locations: list[str], pages: int) -> list[tuple]:
    """(portal, title, location, page) tuples, skipping combinations that cannot work."""
    plan = []
    for portal in portals:
        spec = PORTALS[portal]
        for loc in locations:
            if "*" not in spec["markets"] and tier_for(loc) not in spec["markets"]:
                continue
            cap = pages if spec["max_pages"] is None else min(pages, spec["max_pages"])
            for title in TITLES:
                plan += [(portal, title, loc, p) for p in range(1, cap + 1)]
    return plan


def load_known() -> tuple[set, set, set]:
    seen = json.loads(SEEN.read_text())["seen"]
    ids = {identity(u) for u in seen} | {identity(e.get("url", "")) for e in seen.values()}
    cts = {(norm(e.get("company")), norm(e.get("title"))) for e in seen.values()}
    with TRACKER.open(newline="") as fh:
        for r in csv.DictReader(fh):
            cts.add((norm(r["company"]), norm(r["role"])))
            ids.add(identity(r.get("url", "")))
    return seen, ids - {None, ""}, cts


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
    ap.add_argument("--portals", metavar="P", nargs="+", choices=sorted(PORTALS),
                    help="override the portal list. Default: every portal marked default=True "
                         "whose market matches a requested location. "
                         f"Available: {', '.join(sorted(PORTALS))}")
    a = ap.parse_args()

    locations = a.locations or LOCATIONS
    portals = a.portals or [n for n, s in PORTALS.items() if s["default"]]
    plan = build_plan(portals, locations, a.pages)

    per_portal: dict[str, int] = {}
    for portal, *_ in plan:
        per_portal[portal] = per_portal.get(portal, 0) + 1
    if not plan:
        print(f"nothing to do: none of {portals} serve any of {locations}")
        return 1
    print(f"query plan: {len(plan)} requests, {a.jobage}-day window, {len(TITLES)} generic titles")
    for portal in portals:
        spec = PORTALS[portal]
        n = per_portal.get(portal, 0)
        served = [loc for loc in locations
                  if "*" in spec["markets"] or tier_for(loc) in spec["markets"]]
        note = "" if n else "   (skipped: no matching location)"
        print(f"  {portal:10s} {n:>4} req  markets={','.join(sorted(spec['markets'])):6s} "
              f"-> {', '.join(served) or '-'}{note}")
    if a.dry_run:
        print("\ntitles:")
        for title in TITLES:
            print(f"  {title}")
        return 0

    print("\n[1/4] collecting")
    pool: dict[str, dict] = {}
    dropped: dict[str, int] = {}
    for i, (portal, t, loc, p) in enumerate(plan, 1):
        res = search(portal, t, loc, a.jobage, p)
        markets = PORTALS[portal]["markets"]
        new = off = 0
        for r in res:
            r["location"] = repair_location(portal, r)
            tier = tier_for(r["location"], portal)
            # A market-locked portal returning a job outside its market means the portal's own
            # geo filter failed. Drop it here rather than let it reach a shortlist.
            if "*" not in markets and tier not in markets:
                off += 1
                dropped[f"{portal}:{tier}"] = dropped.get(f"{portal}:{tier}", 0) + 1
                continue
            key = identity(r.get("url"))
            r.setdefault("_q", t)
            r.setdefault("_loc", loc)
            r.setdefault("_portal", portal)
            r["_tier"] = tier
            if key not in pool:
                new += 1
                pool[key] = r
        offnote = f", {off} off-market" if off else ""
        print(f"  [{i:>3}/{len(plan)}] {portal:10s} {t[:26]:26s} {loc[:14]:14s} p{p} -> "
              f"{len(res):2d} hits, {new:2d} new (pool {len(pool)}){offnote}")
    if dropped:
        print("  off-market results dropped (the portal's own geo filter failed): "
              + ", ".join(f"{k}={v}" for k, v in sorted(dropped.items())))
    if not pool:
        print("no results at all — check that bun runs and the portal CLIs are installed")
        return 1

    print(f"\n[2/4] dedup against seen_jobs + tracker")
    seen, known_ids, known_cts = load_known()
    fresh = []
    for key, r in pool.items():
        if key in known_ids:
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
            "portal": r.get("_portal", "linkedin"), "date": r.get("date"), "first_seen": today,
            "fit": "unknown",
            "tier": r.get("_tier") or tier_for(loc, r.get("_portal")),
            "status": "new", "assessed": False,
            "notes": (f"hunt {today}: {r.get('_portal', 'linkedin')} generic-title sweep, "
                      f"query '{r.get('_q')}' @ {r.get('_loc')}"),
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
