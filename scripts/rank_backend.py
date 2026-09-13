#!/usr/bin/env python3
"""Strict pass: PRODUCT BACKEND roles only, across NL / IE / DE.

Artem's feedback 2026-08-26 after reading the loose list: "прям не мій профіль зовсім" — the
loose view was correct per its own rule (Python is a stated requirement) but it swept in SRE,
DevOps, data engineering, platform-ops, consulting and solutions roles. He builds product
backends. So this filter works on the TITLE as well as the body:

  * TITLE must look like a product backend / software engineering role
  * TITLE must not be SRE / DevOps / Data / Platform-ops / Cloud / Consultant / Solutions /
    Forward-Deployed / QA / Firmware / Embedded / Quantitative / Automation / ML / AI
  * Python must be a stated requirement in the body
  * seniority must not read below-senior
  * the five legal knockouts still apply, plus his own no-ML rule
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SEEN = BASE / ".claude/skills/job-scraper/job_scraper/seen_jobs.json"

HARD = {"no-sponsorship", "below-hsm-threshold", "must-already-reside",
        "clearance-or-citizenship", "local-language-required", "ml-ai-engineer-role",
        "posting-written-in-local-language"}

# Verified dead or already declined this session.
DEAD = ["schuberg", "teleclinic", "marvelx", "sytac", "futurewhiz", "freeday", "akqa",
        "holidu", "quantware", "jetbrains", "awin", "ips intelligent", "samotics",
        "certivity", "thermondo", "idealo"]

GEO = {
    "NL": r"netherlands|amsterdam|rotterdam|utrecht|hague|eindhoven|delft|leiden|haarlem|"
          r"groningen|nijmegen|arnhem|breda|tilburg|almere|amersfoort|hilversum|amstelveen",
    "IE": r"ireland|dublin|cork|galway|limerick",
    "DE": r"german|deutschland|berlin|munich|münchen|hamburg|frankfurt|köln|cologne|stuttgart|"
          r"düsseldorf|leipzig|dresden|nürnberg|hannover|karlsruhe|mannheim|augsburg|ansbach",
}

# A product-backend title looks like one of these...
# GAP FIXED 2026-08-26: the first version required the words backend/software/python/founding,
# so it silently dropped "Senior Django Developer" at Dept — a perfect match. Framework names
# and bare "Python Developer"/"API Engineer" forms are now first-class.
GOOD = re.compile(
    r"\b(back[- ]?end|backend|server[- ]?side)\b"
    r"|\b(django|fastapi|flask|aiohttp|asyncio)\b"
    r"|\bpython\b.{0,24}\b(engineer|developer|dev)\b"
    r"|\b(engineer|developer)\b.{0,24}\bpython\b"
    r"|\b(api|services?|integration)\b.{0,16}\b(engineer|developer)\b"
    r"|\bfounding\s+engineer\b"
    r"|\b(senior|staff|lead|principal|sr\.?)\s+(software\s+)?(engineer|developer)\b",
    re.I)

# ...and must not look like any of these.
BAD = re.compile(
    r"\b(sre|site\s+reliability|devops|dev[- ]ops|infrastructure|infra|cloud\s+(ops|engineer|"
    r"architect)|kubernetes|observability|data\s+(engineer|platform|scientist|analyst|ops)|"
    r"dataops|mlops|machine\s+learning|\bml\b|\bai\b|agentic|llm|consultant|consulting|"
    r"solutions?\s+(architect|engineer|consultant)|forward\s+deployed|presales|pre[- ]sales|"
    r"\bqa\b|test\s+automation|sdet|firmware|embedded|\bdsp\b|quantitative|quant\b|"
    r"automation\s+engineer|support|security\s+engineer|network|frontend|front[- ]end|"
    r"mobile|android|\bios\b|unity|graduate|intern|trainee|working\s+student|"
    r"manager|architect\b|kernel|c\+\+|golang|\bgo\b|java\b|kotlin|\.net|\bc#|rust|node\.?js|"
    r"typescript|ruby|php|scala)", re.I)


def excl(e: dict) -> str | None:
    m = re.search(r"AUTO-EXCLUDED by screen_job\.py: ([a-z-]+)", e.get("notes") or "")
    return m.group(1) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-08-17")
    ap.add_argument("--country", choices=["NL", "IE", "DE", "ALL"], default="ALL")
    ap.add_argument("--min-python", type=int, default=2)
    ap.add_argument("--show-rejected", action="store_true")
    a = ap.parse_args()

    seen = json.loads(SEEN.read_text())["seen"]
    keep, rejected = [], []
    for u, e in seen.items():
        if (e.get("first_seen") or "") < a.since:
            continue
        if e.get("status") in ("applied", "duplicate"):
            continue
        py = e.get("screen_python") or 0
        if py < a.min_python or not e.get("screen_python_core"):
            continue
        if excl(e) in HARD:
            continue
        co = e.get("company") or ""
        if any(x in co.lower() for x in DEAD):
            continue
        title = e.get("title") or ""
        loc = (e.get("location") or "") + " " + (e.get("tier") or "")
        country = next((k for k, p in GEO.items() if re.search(p, loc, re.I)), None)
        if country is None or (a.country != "ALL" and country != a.country):
            continue
        flags = e.get("screen_flags") or []
        if "below-senior" in flags:
            rejected.append((title, co, "below-senior")); continue
        if not GOOD.search(title):
            rejected.append((title, co, "title not product-backend")); continue
        if BAD.search(title):
            rejected.append((title, co, "title is " + (BAD.search(title).group(0)))); continue
        rivalcore = [x.replace("(core)", "") for x in (e.get("screen_rivals") or "").split(",")
                     if "(core)" in x]
        tags = [f for f in flags if f != "linkedin-body-unverified"]
        if rivalcore:
            tags.append("core:" + "/".join(rivalcore))
        src = "LI" if "linkedin-body-unverified" in flags else "ATS"
        keep.append((py, country, src, co, title, e.get("location") or "", tags, u))

    keep.sort(key=lambda r: (r[1], -r[0]))
    print(f"PRODUCT BACKEND ONLY — {len(keep)} roles (rejected {len(rejected)} on title/level)\n")
    cur = None
    for py, c, src, co, t, loc, tags, u in keep:
        if c != cur:
            cur = c
            print(f"\n{'='*96}\n{c}\n")
        print(f"py={py} [{src}] {co}")
        print(f"   {t}")
        print(f"   {loc}" + (f"   TAGS: {', '.join(tags)}" if tags else ""))
        print(f"   {u}\n")
    if a.show_rejected:
        print(f"\n{'='*96}\nREJECTED ON TITLE/LEVEL\n")
        for t, co, why in sorted(rejected, key=lambda r: r[2]):
            print(f"   [{why[:34]:34}] {co[:26]:26} {t[:52]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
