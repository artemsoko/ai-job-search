#!/usr/bin/env python3
"""Application log: the single source of truth for where Artem has applied.

Why this exists: the tracker CSV used to be written only when Claude was in the
loop. Applications submitted from a browser, outside a session, left holes, and
the scrape dedup then failed to catch them. This script is runnable from a plain
terminal so the log stays true regardless of whether a session is open.

Usage
-----
  ./applied <url> [--role "..."] [--company "..."] [--status applied] [--notes "..."]
  ./applied --list                 show everything logged, newest first
  ./applied --sync                 reconcile tracker CSV <-> seen_jobs.json
  ./applied --check <url|company>  did I already apply here?

Company/role are derived from the URL where the ATS makes that possible, so the
common case is just `./applied <url>`.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TRACKER = BASE / ".claude/skills/job-scraper/job_search_tracker.csv"
SEEN = BASE / ".claude/skills/job-scraper/job_scraper/seen_jobs.json"
FIELDS = ["company", "role", "location", "date_applied", "status", "url", "notes"]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def _get(url: str, timeout: int = 20) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE  # corporate TLS proxy re-signs certs
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None


def derive(url: str) -> tuple[str | None, str | None, str | None]:
    """Return (company, role, location) inferred from the URL. None where unknown."""
    # Greenhouse: job-boards[.eu].greenhouse.io/<token>/jobs/<id> or boards.greenhouse.io/...
    m = re.search(r"greenhouse\.io/(?:embed/job_app\?for=)?([a-z0-9_-]+)/jobs/(\d+)", url, re.I)
    if m:
        token, jid = m.group(1), m.group(2)
        body = _get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{jid}")
        if body:
            try:
                d = json.loads(body)
                return token, d.get("title"), (d.get("location") or {}).get("name")
            except json.JSONDecodeError:
                pass
        return token, None, None

    # Ashby: jobs.ashbyhq.com/<token>/<uuid>
    m = re.search(r"ashbyhq\.com/([a-z0-9_.-]+)/([0-9a-f-]{36})", url, re.I)
    if m:
        token, jid = m.group(1), m.group(2)
        body = _get(f"https://api.ashbyhq.com/posting-api/job-board/{token}")
        if body:
            try:
                for j in json.loads(body).get("jobs", []):
                    if jid in (j.get("jobUrl") or "") or jid == j.get("id"):
                        return token, j.get("title"), j.get("location")
            except json.JSONDecodeError:
                pass
        return token, None, None

    # Recruitee: <token>.recruitee.com/o/<slug> or jobs.<company>.com/o/<slug>
    m = re.search(r"(?:([a-z0-9-]+)\.recruitee\.com|jobs\.([a-z0-9-]+)\.com)/o/([a-z0-9-]+)", url, re.I)
    if m:
        token = m.group(1) or m.group(2)
        slug = m.group(3)
        return token, slug.replace("-", " ").title(), None

    # LinkedIn: /jobs/view/<slug>-at-<company>-<id> or /jobs/view/<id>
    m = re.search(r"linkedin\.com/jobs/view/([a-z0-9%\-]*?)-at-([a-z0-9%\-]+?)-(\d{9,})", url, re.I)
    if m:
        role = urllib.parse.unquote(m.group(1)).replace("-", " ").title()
        company = urllib.parse.unquote(m.group(2)).replace("-", " ").title()
        return company, role, None

    # Personio: <token>.jobs.personio.de/job/<id>
    m = re.search(r"([a-z0-9-]+)\.jobs\.personio\.[a-z]+/job/(\d+)", url, re.I)
    if m:
        return m.group(1), None, None

    # Lever: jobs.lever.co/<token>/<uuid>
    m = re.search(r"jobs\.lever\.co/([a-z0-9-]+)/", url, re.I)
    if m:
        return m.group(1), None, None

    return None, None, None


def read_rows() -> list[dict]:
    if not TRACKER.exists():
        return []
    with TRACKER.open(newline="") as fh:
        return list(csv.DictReader(fh))


def write_rows(rows: list[dict]) -> None:
    with TRACKER.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def job_id(url: str) -> str | None:
    m = re.search(r"(\d{9,})", url or "")
    return m.group(1) if m else None


def touch_seen(url: str, company: str, role: str, status: str) -> str:
    """Mirror the status into seen_jobs.json so scrape dedup sees it too."""
    if not SEEN.exists():
        return "seen_jobs.json missing"
    doc = json.loads(SEEN.read_text())
    seen = doc["seen"]
    jid = job_id(url)
    hits = []
    for u, e in seen.items():
        same_url = u == url or e.get("url") == url
        same_id = jid and (jid == job_id(u) or jid == job_id(e.get("url", "")))
        same_ct = norm(e.get("company")) == norm(company) and norm(e.get("title")) == norm(role)
        if same_url or same_id or same_ct:
            hits.append(u)
    for u in hits:
        seen[u]["status"] = status
    if not hits:
        seen[url] = {
            "title": role or "",
            "company": company or "",
            "location": "",
            "url": url,
            "portal": "manual",
            "date": "",
            "first_seen": date.today().isoformat(),
            "fit": "high",
            "status": status,
            "assessed": True,
            "notes": "added by log_application.py",
        }
        hits.append(url)
    SEEN.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    return f"seen_jobs.json: {len(hits)} entry(ies) set to {status}"


def cmd_add(args) -> int:
    url = args.url
    company, role, location = derive(url)
    company = args.company or company
    role = args.role or role
    location = args.location or location or ""
    if not company:
        print("Could not derive the company from that URL. Pass --company.", file=sys.stderr)
        return 1
    if not role:
        print("Could not derive the role from that URL. Pass --role.", file=sys.stderr)
        return 1

    rows = read_rows()
    for r in rows:
        if r.get("url") == url or (norm(r["company"]) == norm(company) and norm(r["role"]) == norm(role)):
            print(f"ALREADY LOGGED: {r['company']} / {r['role']} ({r['status']}, {r['date_applied']})")
            print("Nothing written. Use a different --role if this is a second req.")
            return 2

    rows.append({
        "company": company,
        "role": role,
        "location": location,
        "date_applied": args.date or date.today().isoformat(),
        "status": args.status,
        "url": url,
        "notes": args.notes or "",
    })
    write_rows(rows)
    print(f"LOGGED: {company} / {role} [{args.status}]")
    print(" ", touch_seen(url, company, role, args.status))
    return 0


def cmd_list(_args) -> int:
    rows = read_rows()
    rows.sort(key=lambda r: r.get("date_applied", ""), reverse=True)
    print(f"{len(rows)} logged applications\n")
    for r in rows:
        print(f"{r['date_applied']:11s} {r['status']:12s} {r['company'][:24]:24s} {r['role'][:44]}")
    return 0


def cmd_brief(_args) -> int:
    """Compact one-block summary, used by the SessionStart hook."""
    rows = read_rows()
    live = [r for r in rows if r["status"] in ("applied", "interviewing", "offer")]
    if not live:
        print("APPLICATION LOG: empty.")
        return 0
    by_status: dict[str, list[str]] = {}
    for r in sorted(live, key=lambda x: x.get("date_applied", ""), reverse=True):
        by_status.setdefault(r["status"], []).append(f"{r['company']} ({r['role'][:34]})")
    print(f"APPLICATION LOG ({len(live)} live, {len(rows)} total) - do NOT re-suggest these:")
    for status, items in by_status.items():
        print(f"  {status}: " + "; ".join(items))
    skipped = [r["company"] for r in rows if r["status"] == "skipped"]
    if skipped:
        print("  consciously skipped: " + ", ".join(sorted(set(skipped))))
    print("  Log a new one with: ./applied <url>")
    return 0


def cmd_check(args) -> int:
    needle = norm(args.needle)
    rows = read_rows()
    hits = [r for r in rows if needle in norm(r["company"]) or needle in norm(r["url"]) or needle in norm(r["role"])]
    if not hits:
        print(f"NOT FOUND: nothing logged matching '{args.needle}'")
        return 1
    for r in hits:
        print(f"MATCH: {r['company']} / {r['role']} [{r['status']}] {r['date_applied']}\n  {r['url']}")
        if r.get("notes"):
            print(f"  notes: {r['notes']}")
    return 0


def cmd_sync(_args) -> int:
    """Push every tracker status into seen_jobs.json and report drift."""
    rows = read_rows()
    doc = json.loads(SEEN.read_text())
    seen = doc["seen"]
    fixed = missing = 0
    for r in rows:
        url, company, role, status = r["url"], r["company"], r["role"], r["status"]
        jid = job_id(url)
        hits = []
        for u, e in seen.items():
            if (u == url or e.get("url") == url
                    or (jid and (jid == job_id(u) or jid == job_id(e.get("url", ""))))
                    or (norm(e.get("company")) == norm(company) and norm(e.get("title")) == norm(role))):
                hits.append(u)
        if not hits:
            missing += 1
            seen[url or f"manual:{norm(company)}:{norm(role)}"] = {
                "title": role, "company": company, "location": r.get("location", ""),
                "url": url, "portal": "tracker", "date": "", "first_seen": r.get("date_applied", ""),
                "fit": "high", "status": status, "assessed": True,
                "notes": "backfilled from tracker CSV by --sync",
            }
            continue
        for u in hits:
            if seen[u].get("status") != status:
                seen[u]["status"] = status
                fixed += 1
    SEEN.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"sync done: {fixed} status(es) corrected, {missing} tracker row(s) backfilled into seen_jobs.json")
    from collections import Counter
    print("seen_jobs statuses:", Counter(e.get("status") for e in seen.values()))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Log and query job applications.")
    p.add_argument("url", nargs="?", help="application URL")
    p.add_argument("--company")
    p.add_argument("--role")
    p.add_argument("--location")
    p.add_argument("--status", default="applied",
                   choices=["applied", "not_applied", "skipped", "interviewing", "rejected", "offer", "withdrawn"])
    p.add_argument("--notes")
    p.add_argument("--date", help="YYYY-MM-DD, defaults to today")
    p.add_argument("--list", action="store_true")
    p.add_argument("--brief", action="store_true", help="compact summary for the SessionStart hook")
    p.add_argument("--sync", action="store_true")
    p.add_argument("--check", dest="needle", metavar="URL|COMPANY")
    a = p.parse_args()

    if a.brief:
        return cmd_brief(a)
    if a.list:
        return cmd_list(a)
    if a.sync:
        return cmd_sync(a)
    if a.needle:
        return cmd_check(a)
    if not a.url:
        p.print_help()
        return 1
    if a.date:
        datetime.strptime(a.date, "%Y-%m-%d")
    return cmd_add(a)


if __name__ == "__main__":
    sys.exit(main())
