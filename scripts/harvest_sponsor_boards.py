#!/usr/bin/env python3
"""Harvest live vacancies from the ATS boards of IND-recognised sponsor companies.

Why this exists: LinkedIn's guest search indexes titles only, and four consecutive NL sweeps
through it produced ~1,160 postings and one lead. Polling employers' own ATS boards instead
returns FULL bodies, proves liveness, and every company here is a confirmed IND sponsor by
construction — so the visa question is closed before the posting is even read.

The board list is `job_scraper/sponsor_ats_boards.json`, built once by probing all 12,915
entities in the IND register against 4 ATS providers. Re-poll it; do not rebuild it.

Usage
-----
  ./scripts/harvest_sponsor_boards.py                    # Netherlands (default)
  ./scripts/harvest_sponsor_boards.py --country DE
  ./scripts/harvest_sponsor_boards.py --country NL --store   # write new entries to seen_jobs

Known gap: the original probe accepted HTTP 200 only, so Recruitee tenants that 302 from an old
brand name (agriplace -> simvia) are missing from the board list.
"""
from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
BOARDS = BASE / ".claude/skills/job-scraper/job_scraper/sponsor_ats_boards.json"
SEEN = BASE / ".claude/skills/job-scraper/job_scraper/seen_jobs.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")

COUNTRIES = {
    "NL": (r"netherlands|amsterdam|rotterdam|utrecht|den haag|the hague|eindhoven|delft|leiden|"
           r"haarlem|groningen|nijmegen|arnhem|breda|tilburg|almere|amersfoort|hilversum|zwolle|"
           r"maastricht|enschede|apeldoorn|zoetermeer|amstelveen|hoofddorp|schiphol|\bnl\b"),
    "IE": r"ireland|dublin|cork|galway|limerick|\\bIE\\b",
    "DE": (r"germany|deutschland|berlin|munich|m(?:ü|ue)nchen|hamburg|frankfurt|cologne|"
           r"k(?:ö|oe)ln|stuttgart|d(?:ü|ue)sseldorf|dusseldorf|leipzig|dresden|nuremberg|"
           r"n(?:ü|ue)rnberg|hannover|karlsruhe|mannheim|bonn|essen|dortmund|bremen|aachen|"
           r"freiburg|heidelberg|potsdam|\bde\b"),
}
ENG = re.compile(r"engineer|developer|programmer|architect|\bswe\b|\bsde\b", re.I)


def _ctx() -> ssl.SSLContext:
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c


def _get(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        return urllib.request.urlopen(req, timeout=20, context=_ctx()).read().decode("utf-8", "replace")
    except Exception:
        return None


def _parse(provider: str, raw: str) -> list[tuple[str, str | None, str]]:
    """-> [(title, location, url)]"""
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return []
    out: list[tuple[str, str | None, str]] = []
    if provider == "greenhouse":
        for j in d.get("jobs", []):
            out.append((j.get("title"), (j.get("location") or {}).get("name"), j.get("absolute_url")))
    elif provider == "ashby":
        for j in d.get("jobs", []):
            if j.get("isListed") is False:
                continue
            out.append((j.get("title"), j.get("location"), j.get("jobUrl")))
    elif provider == "lever":
        for j in d if isinstance(d, list) else []:
            out.append((j.get("text"), (j.get("categories") or {}).get("location"), j.get("hostedUrl")))
    elif provider == "recruitee":
        for j in d.get("offers", []):
            if j.get("status") and j["status"] != "published":
                continue
            loc = ", ".join(x for x in (j.get("city"), j.get("country_code")) if x)
            out.append((j.get("title"), loc, j.get("careers_url")))
    return [(t, l, u) for t, l, u in out if t and u]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", choices=sorted(COUNTRIES), default="NL")
    ap.add_argument("--store", action="store_true", help="write new entries into seen_jobs.json")
    ap.add_argument("--workers", type=int, default=28)
    a = ap.parse_args()

    doc = json.loads(BOARDS.read_text())
    companies = doc["companies"]
    tasks = [(tok, meta["legal_name"], prov, url)
             for tok, meta in companies.items()
             for prov, url in meta["boards"].items()]
    print(f"polling {len(tasks)} boards across {len(companies)} sponsor companies")

    def work(t: tuple[str, str, str, str]) -> list[tuple]:
        tok, legal, prov, url = t
        raw = _get(url)
        if not raw:
            return []
        return [(prov, tok, legal, title, loc, u) for title, loc, u in _parse(prov, raw)]

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        all_jobs = [j for sub in ex.map(work, tasks) for j in sub]

    geo = re.compile(COUNTRIES[a.country], re.I)
    in_country = [j for j in all_jobs if j[4] and geo.search(j[4])]
    eng = [j for j in in_country if ENG.search(j[3])]
    print(f"  live vacancies total : {len(all_jobs)}")
    print(f"  in {a.country:<18}: {len(in_country)}")
    print(f"  engineering titles   : {len(eng)}")

    seen = json.loads(SEEN.read_text())["seen"]

    def jid(u: str) -> str | None:
        m = re.search(r"(\d{7,})", u or "")
        return m.group(1) if m else None

    known_ids = {jid(u) for u in seen if jid(u)}
    fresh = [j for j in eng
             if j[5] not in seen and (jid(j[5]) not in known_ids if jid(j[5]) else True)]
    print(f"  NOT already in base  : {len(fresh)}")

    out = BASE / f"job_harvest_{a.country}_{date.today().isoformat()}.json"
    out.write_text(json.dumps(fresh, indent=2, ensure_ascii=False))
    print(f"  written -> {out.name}")

    if a.store and fresh:
        doc2 = json.loads(SEEN.read_text())
        s = doc2["seen"]
        added = 0
        for prov, tok, legal, title, loc, url in fresh:
            if url in s:
                continue
            s[url] = {"title": title, "company": legal, "location": loc, "url": url,
                      "portal": f"ats:{prov}", "first_seen": date.today().isoformat(),
                      "tier": a.country, "status": "new", "assessed": False,
                      "ind_sponsor": "CONFIRMED - IND recognised-sponsor register",
                      "source": f"sponsor-board harvest {date.today().isoformat()}"}
            added += 1
        SEEN.write_text(json.dumps(doc2, indent=2, ensure_ascii=False))
        print(f"  stored {added}; seen_jobs now {len(s)}")
        print("  next: ./screen --unassessed --limit 60   (repeat until it plateaus)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
