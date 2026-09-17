#!/usr/bin/env python3
"""Turn screened seen_jobs entries into one self-contained HTML page.

Why this exists
---------------
The terminal is the wrong surface for triaging two hundred postings. This writes a single file
with no external assets - no CDN, no fonts, no JS libraries - so it opens offline in Chrome and
survives being emailed to yourself.

Ranking, and why it is NOT by python weight
-------------------------------------------
Sorting by the raw Python mention count is unreliable: Adyen's req *titled* "Python Software
Engineer" scores python=1. So the sort key is, in order:

  1. python_core      - the body states Python as a requirement, not a nice-to-have
  2. fewest CORE rival languages - a Go-core or C++-core role is a poor fit regardless of Python
  3. sponsor licence  - UK only, from the gov.uk register
  4. python weight    - only as a final tie-break

UK sponsorship
--------------
For UK rows each company is checked against gov.uk's Register of licensed sponsors (Workers) via
sponsor_lookup, loaded once and reused rather than shelling out per company. A posting that is
*silent* on sponsorship becomes a ranked likelihood instead of a guess.

Usage
-----
  python3 scripts/report_html.py --first-seen 2026-09-17 --tier UK
  python3 scripts/report_html.py --first-seen 2026-09-17 --tier UK NL DE -o out.html
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SEEN = BASE / ".claude/skills/job-scraper/job_scraper/seen_jobs.json"

# Titles that are not backend engineering, however many times they say "engineer".
NOISE = re.compile(
    r"embedded|firmware|mechanical|structural|photonic|rf engineer|aocs|hardware|\bqa\b|"
    r"test engineer|product assurance|process engineer|sales|account exec|recruit|intern\b|"
    r"graduate|\bmanager\b|analyst|designer|marketing|scientist|npd|business partner|"
    r"consultant|teacher|nurse|driver|technician|administrator|bookkeep|paralegal", re.I)


# Recruiters, staffing agencies and job-board brands that post on behalf of an undisclosed
# client. Added 2026-09-17: the first London report ranked eFinancialCareers, Robert Half and
# Explore Group at the very top, each carrying a confident "licensed sponsor" badge — but the
# register had matched the AGENCY, not the employer doing the hiring, so the badge said nothing
# about whether the actual job is sponsorable. Worse, the role, the team and the stack are all
# second-hand. These rows are pushed below real employers and their sponsor cell is blanked.
AGENCY = re.compile(
    r"recruit|staffing|resourcing|talent|\bhays\b|michael page|robert half|reed specialist|"
    r"efinancialcareers|\bsearch\b|selection|consultancy|consulting group|\bagency\b|"
    r"headhunt|manpower|randstad|adecco|hudson|harvey nash|nigel frank|oscar tech|"
    r"explore group|sr2|trust in soda|doghouse|oliver bernard|levy professionals|venquis|"
    r"jobgether|xpertdirect|european tech recruit|rise technical|client server|iq staffing|"
    r"involved solutions|intec select|corriculo|\bselect ltd\b|\bselect limited\b|"
    r"\bassociates\b|\bpartners\b|\bresource\b|\bpeople\b|\bcareers\b|opus |lorien|"
    r"spectrum it|understanding|\bnext ventures\b|\bzebra\b|\bsoda\b",
    re.I)

# Heuristic, and deliberately imperfect: there is no register of recruitment agencies, and a
# "Ltd" suffix is no signal at all (Octopus Energy and Capital One post directly on reed too).
# So the report tags what it recognises, sorts those rows last, and leaves the
# "named employers only" checkbox ON by default with a way to switch it off — rather than
# deleting rows on a guess.


def is_agency(company: str, flags: list[str]) -> bool:
    return bool(AGENCY.search(company or "")) or "recruiter-undisclosed-client" in flags


def load_sponsor_index():
    """Return lookup(company)->dict, or None if the register is unavailable.

    sponsor_lookup.search() re-reads the 140k-row CSV on every call, which is fine for one
    company on the command line and far too slow for two hundred rows in a report. So the
    register is materialised once here and scored in memory, reusing that module's own
    normalise / match_score so the verdicts stay identical to the CLI's.
    """
    sys.path.insert(0, str(BASE / "scripts"))
    try:
        import sponsor_lookup as sl
        sl.refresh_cache()
        register = [(r.get("Organisation Name", ""), r) for r in sl.load_register()]
    except Exception as exc:                                  # noqa: BLE001
        print(f"  ! sponsor register unavailable ({exc}); UK rows will show as unknown",
              file=sys.stderr)
        return None
    print(f"  register loaded: {len(register):,} rows")

    cache: dict[str, dict] = {}

    def lookup(company: str) -> dict:
        if company in cache:
            return cache[company]
        q_norm, q_words = sl.normalize(company), sl.core_words(company)
        best_score, best_name = 0, ""
        if q_norm:
            for name, _row in register:
                score = sl.match_score(q_norm, q_words, name)
                if score > best_score:
                    best_score, best_name = score, name
        if best_score >= 55:
            cache[company] = {"licensed": True,
                              "confidence": sl.confidence_label(best_score),
                              "name": best_name}
        else:
            cache[company] = {"licensed": False, "confidence": "none", "name": ""}
        return cache[company]

    return lookup


def core_rivals(rivals: str) -> list[str]:
    return [r.strip() for r in (rivals or "").split(",") if "(core)" in r.lower()]


def collect(first_seen: str | None, tiers: list[str]) -> tuple[list[dict], Counter]:
    doc = json.loads(SEEN.read_text())["seen"]
    rows, tally = [], Counter()
    for url, e in doc.items():
        if first_seen and e.get("first_seen") != first_seen:
            continue
        if tiers and e.get("tier") not in tiers:
            continue
        tally[e.get("screen_verdict") or "not-screened"] += 1
        if e.get("screen_verdict") not in ("PASS", "FLAG"):
            continue
        title = e.get("title", "")
        if NOISE.search(title):
            tally["dropped-by-title"] += 1
            continue
        flags = [f if isinstance(f, str) else f.get("rule", "?") for f in (e.get("screen_flags") or [])]
        rows.append({
            "company": e.get("company", "?"), "title": title,
            "location": e.get("location", ""), "portal": e.get("portal", "?"),
            "tier": e.get("tier", "?"), "verdict": e["screen_verdict"],
            "py": e.get("screen_python") or 0, "core": bool(e.get("screen_python_core")),
            "rivals": e.get("screen_rivals", "") or "",
            "flags": [f for f in flags if f != "linkedin-body-unverified"],
            "unverified": "linkedin-body-unverified" in flags,
            "url": url,
        })
        rows[-1]["agency"] = is_agency(rows[-1]["company"], rows[-1]["flags"])
    return rows, tally


def render(rows: list[dict], tally: Counter, title: str) -> str:
    head = """<!doctype html><meta charset="utf-8"><title>{t}</title>
<style>
:root{{--bg:#0f1115;--card:#171a21;--line:#262b36;--txt:#e6e9ef;--dim:#9aa3b2;
--good:#3fb950;--warn:#d29922;--bad:#f85149;--link:#58a6ff}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--txt);
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
header{{padding:20px 24px;border-bottom:1px solid var(--line);position:sticky;top:0;
background:var(--bg);z-index:3}}
h1{{margin:0 0 6px;font-size:18px}} .sub{{color:var(--dim);font-size:13px}}
.controls{{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
input[type=search]{{background:var(--card);border:1px solid var(--line);color:var(--txt);
padding:7px 10px;border-radius:6px;min-width:260px;font-size:13px}}
label{{color:var(--dim);font-size:13px;display:flex;gap:5px;align-items:center;cursor:pointer;
background:var(--card);border:1px solid var(--line);padding:6px 10px;border-radius:6px}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}
th{{color:var(--dim);font-weight:600;font-size:12px;text-transform:uppercase;
letter-spacing:.04em;cursor:pointer;user-select:none;white-space:nowrap}}
th:hover{{color:var(--txt)}}
tr:hover td{{background:#1b1f27}}
a{{color:var(--link);text-decoration:none}} a:hover{{text-decoration:underline}}
.pill{{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;
border:1px solid var(--line);color:var(--dim);white-space:nowrap}}
.core{{color:var(--good);border-color:#23502f;background:#11251a}}
.rival{{color:var(--bad);border-color:#5c2626;background:#2a1414}}
.flag{{color:var(--warn);border-color:#5c4a15;background:#261f0e}}
.spon{{color:var(--good);border-color:#23502f;background:#11251a}}
.nospon{{color:var(--dim)}}
.unv{{color:var(--warn)}}
.co{{font-weight:600}}
.loc{{color:var(--dim);font-size:12px}}
tfoot td{{color:var(--dim);font-size:12px}}
</style>
<header>
<h1>{t}</h1>
<div class="sub">{sub}</div>
<div class="controls">
<input type="search" id="q" placeholder="filter company, title, location…">
<label><input type="checkbox" id="onlycore"> Python is core</label>
<label><input type="checkbox" id="norivals"> no core rivals</label>
<label><input type="checkbox" id="onlyspon"> licensed sponsor</label>
<label><input type="checkbox" id="noflags"> no flags</label>
<label><input type="checkbox" id="noagency" checked> named employers only</label>
<span class="sub" id="count"></span>
</div>
</header>
<table id="t"><thead><tr>
<th data-k="0">Company</th><th data-k="1">Role</th><th data-k="2">Python</th>
<th data-k="3">Core rivals</th><th data-k="4">Sponsor</th><th data-k="5">Flags</th>
<th data-k="6">Source</th><th>Apply</th>
</tr></thead><tbody>
""".format(t=html.escape(title),
           sub=html.escape(", ".join(f"{k}: {v}" for k, v in sorted(tally.items()))))

    body = []
    for r in rows:
        cr = core_rivals(r["rivals"])
        sp = r.get("sponsor") or {}
        if r["agency"]:
            spcell = ('<span class="pill nospon">n/a · agency</span>'
                      '<div class="loc">employer undisclosed</div>')
            spflag = "0"
        elif sp.get("licensed") is True:
            spcell = (f'<span class="pill spon">licensed · {html.escape(sp["confidence"])}</span>'
                      f'<div class="loc">{html.escape(sp.get("name",""))}</div>')
            spflag = "1"
        elif sp.get("licensed") is False:
            spcell = '<span class="pill nospon">not on register</span>'
            spflag = "0"
        else:
            spcell = '<span class="pill nospon">—</span>'
            spflag = "0"
        pyc = (f'<span class="pill core">core · {r["py"]}</span>' if r["core"]
               else f'<span class="pill">side · {r["py"]}</span>')
        rivcell = (" ".join(f'<span class="pill rival">{html.escape(x)}</span>' for x in cr)
                   or '<span class="pill core">none</span>')
        flagcell = " ".join(f'<span class="pill flag">{html.escape(f)}</span>' for f in r["flags"]) or "—"
        unv = ' <span class="pill unv">body unverified</span>' if r["unverified"] else ""
        body.append(
            f'<tr data-core="{int(r["core"])}" data-rivals="{len(cr)}" data-spon="{spflag}" '
            f'data-agency="{int(r["agency"])}" data-flags="{len(r["flags"])}" data-py="{r["py"]}">'
            f'<td class="co">{html.escape(r["company"])}'
            f'{" <span class=\"pill flag\">agency</span>" if r["agency"] else ""}<div class="loc">'
            f'{html.escape(r["location"])} · {html.escape(r["tier"])}</div></td>'
            f'<td>{html.escape(r["title"])}{unv}</td>'
            f'<td>{pyc}</td><td>{rivcell}</td><td>{spcell}</td><td>{flagcell}</td>'
            f'<td><span class="pill">{html.escape(r["portal"])}</span></td>'
            f'<td><a href="{html.escape(r["url"])}" target="_blank" rel="noopener">open ↗</a></td></tr>')

    tail = """</tbody></table>
<script>
const rowsEl=[...document.querySelectorAll('#t tbody tr')];
const q=document.getElementById('q'),cnt=document.getElementById('count');
const cbs=['onlycore','norivals','onlyspon','noflags','noagency'].map(i=>document.getElementById(i));
function apply(){
  const s=q.value.toLowerCase();let n=0;
  for(const tr of rowsEl){
    let ok=tr.textContent.toLowerCase().includes(s);
    if(ok&&cbs[0].checked)ok=tr.dataset.core==='1';
    if(ok&&cbs[1].checked)ok=tr.dataset.rivals==='0';
    if(ok&&cbs[2].checked)ok=tr.dataset.spon==='1';
    if(ok&&cbs[3].checked)ok=tr.dataset.flags==='0';
    if(ok&&cbs[4].checked)ok=tr.dataset.agency==='0';
    tr.style.display=ok?'':'none';if(ok)n++;
  }
  cnt.textContent=n+' / '+rowsEl.length+' shown';
}
q.oninput=apply;cbs.forEach(c=>c.onchange=apply);apply();
document.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{
  const k=+th.dataset.k,tb=document.querySelector('#t tbody');
  const dir=th.dataset.d==='1'?-1:1;th.dataset.d=dir===1?'1':'0';
  [...tb.rows].sort((a,b)=>dir*a.cells[k].textContent.trim()
    .localeCompare(b.cells[k].textContent.trim(),undefined,{numeric:true}))
    .forEach(r=>tb.appendChild(r));
});
</script>"""
    return head + "\n".join(body) + tail


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--first-seen", metavar="YYYY-MM-DD")
    ap.add_argument("--tier", nargs="+", default=[], metavar="T",
                    help="restrict to country tiers, e.g. --tier UK NL")
    ap.add_argument("--no-sponsor", action="store_true",
                    help="skip the gov.uk sponsor-register lookup")
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()

    rows, tally = collect(a.first_seen, a.tier)
    if not rows:
        print("nothing survived the filters — nothing to render")
        return 1
    print(f"{len(rows)} survivors; verdict tally: {dict(tally)}")

    want_uk = any(r["tier"] == "UK" for r in rows)
    if want_uk and not a.no_sponsor:
        print("checking the gov.uk sponsor register (cached once per day)…")
        lookup = load_sponsor_index()
        if lookup:
            for r in rows:
                if r["tier"] == "UK" and not r["agency"]:
                    r["sponsor"] = lookup(r["company"])
            n = sum(1 for r in rows if (r.get("sponsor") or {}).get("licensed"))
            direct = sum(1 for r in rows if r["tier"] == "UK" and not r["agency"])
            ag = sum(1 for r in rows if r["agency"])
            print(f"  {n} of {direct} named employers are on the register "
                  f"({ag} agency/undisclosed-client rows skipped — the register cannot tell you "
                  f"anything about their hidden client)")

    # python_core first, then fewest core rivals, then sponsor, then weight
    # Named employers first — an agency row hides the employer, the team and the real stack.
    rows.sort(key=lambda r: (r["agency"], not r["core"], len(core_rivals(r["rivals"])),
                             not (r.get("sponsor") or {}).get("licensed"), -int(r["py"])))

    scope = "+".join(a.tier) or "all"
    title = f"Job sweep {a.first_seen or 'all dates'} — {scope} — {len(rows)} survivors"
    out = Path(a.out or BASE / f"report_{a.first_seen or 'all'}_{scope}.html")
    out.write_text(render(rows, tally, title), encoding="utf-8")
    print(f"\nwrote {out}")
    print(f"open it with:  open '{out}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
