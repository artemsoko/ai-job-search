#!/usr/bin/env python3
"""Mechanical hard-exclusion screen for a job posting.

Why this exists: the filter rules in search-queries.md can only be applied to the
posting BODY, but the scraper skill tells Claude to pre-filter on title/snippet and
fetch detail only for promising hits. So postings reached Artem carrying
`assessed: false` and were recommended anyway. A Webb Traders req demanding
"Expert-level C++" with zero Python mentions got through that gap on 2026-08-13.

This applies the rules in code, cheaply, so every posting can be screened.

Usage
-----
  ./screen <url>                    screen one posting, print verdict + quotes
  ./screen --unassessed [--limit N] screen everything in seen_jobs.json that has
                                    not had its body read, and write the verdict back
  ./screen <url> --json             machine-readable

Verdicts: EXCLUDE (a rule fired, with the quote), FLAG (needs Artem's judgement),
PASS (nothing fired). PASS is not an endorsement, it only means no hard rule hit.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import ssl
import subprocess
import sys
from datetime import date
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SEEN = BASE / ".claude/skills/job-scraper/job_scraper/seen_jobs.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"

# Languages that disqualify when they are core and Python is absent.
RIVALS = {
    "c++": [r"c\+\+"],
    "go": [r"\bgolang\b", r"\bgo\b"],
    "java": [r"\bjava\b(?!script)"],
    "kotlin": [r"\bkotlin\b"],
    "rust": [r"\brust\b"],
    "c#": [r"\bc#", r"\.net\b"],
    "node": [r"\bnode\.?js\b"],
    "scala": [r"\bscala\b"],
    "php": [r"\bphp\b"],
    "ruby": [r"\bruby\b"],
    "elixir": [r"\belixir\b"],
}
# A posting can pin the stack entirely through Python-ecosystem tokens without ever writing
# the word "python" (e.g. "FastAPI, Pydantic, SQLAlchemy, pytest"). Excluding on `\bpython\b`
# alone silently drops those. Found 2026-08-18 while auditing a 281-posting sweep.
PY_ECOSYSTEM = [
    r"\bfastapi\b", r"\bdjango\b", r"\bdjango rest framework\b", r"\bdrf\b", r"\bflask\b",
    r"\bpydantic\b", r"\bpytest\b", r"\bsqlalchemy\b", r"\basyncio\b", r"\baiohttp\b",
    r"\bcelery\b", r"\balembic\b", r"\buvicorn\b", r"\bgunicorn\b", r"\bnumpy\b",
    r"\bpandas\b", r"\bpolars\b", r"\bairflow\b", r"\btwisted\b", r"\bpoetry\b",
]

# Phrasing that marks a language as a hard requirement rather than a passing mention.
CORE_CUES = r"(?:expert[- ]level|expert\b|strong(?:ly)?|deep|advanced|proficien\w+|extensive|mastery|hands[- ]on|solid|\d+\+?\s*years?\s+(?:of\s+)?(?:experience\s+)?(?:in|with)?)"

HARD_RULES = [
    ("no-sponsorship", [
        r"(?:can\s?not|cannot|can't|do(?:es)? not|unable to|no)\s+(?:\w+\s+){0,3}(?:support|offer|provide|sponsor)\w*\s+(?:\w+\s+){0,3}visa",
        r"no visa sponsorship",
        r"visa sponsorship is not (?:available|offered|provided)",
        r"we do not (?:offer|provide) sponsorship",
        r"we do not relocate",
        # Futurewhiz (2026-08-24) slipped through as PASS with: "we aren't able to offer visa
        # sponsorship for this role, so we can only consider candidates who already hold a valid
        # work permit". The old alternation covered "unable to" but not "aren't/isn't able to".
        r"(?:are|is|were|was)n[o']?t able to\s+(?:\w+\s+){0,3}(?:support|offer|provide|sponsor)",
        r"not able to\s+(?:\w+\s+){0,3}(?:support|offer|provide|sponsor)\w*\s+(?:\w+\s+){0,3}visa",
        r"(?:only|can only) consider candidates who already hold",
        r"already hold a valid work permit",
    ]),
    ("must-already-reside", [
        r"must (?:currently )?(?:be )?(?:based|located|residing|reside|live)\s+in",
        r"must already (?:reside|be based|be located|live)",
        r"candidates must (?:currently )?be based",
        r"already (?:reside|residing|based) in the netherlands",
        r"(?:netherlands|nl|uk|dutch) residents only",
        r"eligible to work in the netherlands",
        r"(?:must have|require)\s+(?:the )?(?:existing )?right to work",
        # myTomorrows (2026-08-18) slipped through as PASS with: "we only consider candidates
        # for this position who live within commuting distance to our office in Amsterdam."
        r"within commuting distance",
        r"only consider candidates?(?:[^.]{0,40})?who (?:live|reside|are based)",
    ]),
    ("local-language-required", [
        r"fluent (?:in )?(?:dutch|german|nederlands)",
        r"(?:dutch|german)\s*[-:]?\s*(?:b2|c1|c2)",
        r"(?:b2|c1|c2)\s+(?:level\s+)?(?:dutch|german)",
        r"must speak\s+(?:\w+\s+){0,2}(?:dutch|german)",
        r"(?:dutch|german)\s+(?:language\s+)?(?:is\s+)?(?:required|mandatory|a must)",
        r"beheersing van (?:zowel )?de nederlandse",
        r"nederlands\w*\s+(?:is\s+)?(?:vereist|noodzakelijk)",
        r"verhandlungssicher\w*\s+deutsch",
    ]),
    ("clearance-or-citizenship", [
        r"security clearance",
        r"(?:eu|dutch|german|uk|us)\s+citizenship\s+(?:is\s+)?(?:required|mandatory)",
        r"must be (?:an? )?(?:eu|dutch|german|uk|us)\s+citizen",
        r"relocation for eu citizens only",
    ]),
    ("ml-ai-engineer-role", [
        r"\b(?:machine learning|ml)\s+engineer\b",
        r"\bai engineer\b",
        r"\bapplied scientist\b",
        r"\bdata scientist\b",
        r"\bmlops engineer\b",
        r"\banalytics engineer\b",
        # NVIDIA-style titles that are ML roles without the words "ML"/"AI engineer"
        r"\bdeep learning (?:software )?engineer\b",
        r"\bresearch (?:scientist|engineer), (?:ml|ai|deep learning)\b",
        r"\b(?:ml|model|inference|training)\s+(?:compiler|kernel)\s+engineer\b",
        r"\bcompiler engineer\b",
        r"\bperception engineer\b",
    ]),
]

FLAG_RULES = [
    ("on-call", [r"on[- ]call", r"oncall", r"incident response", r"pager"]),
    ("degree-hard-requirement", [r"(?:bachelor|master|bsc|msc|phd)[^.]{0,120}(?:degree|in computer science)"]),
    ("below-senior", [r"\bmedior\b", r"\bmid[- ]level\b", r"\bjunior\b", r"\bentry level\b",
                      r"\b(?:1|2|3)\+?\s*(?:to\s*\d+\s*)?years? of (?:relevant |professional )?(?:work )?experience"]),
    ("contract-not-permanent", [r"\bfixed[- ]term\b", r"\bfreelance\b", r"\bzzp\b", r"\bcontractor\b",
                                r"\b\d{1,2}[- ]month contract\b", r"initial fixed[- ]term"]),
    ("onsite-heavy", [r"[45]\s*days?\s*(?:per|a)\s*week\s*(?:from|in)\s*(?:the\s*)?office",
                      r"(?:office[- ]first|fully on[- ]?site|on[- ]?site:?\s*5)"]),
    ("recruiter-undisclosed-client", [r"\bmy client\b", r"\bour client\b", r"undisclosed client"]),
]


def _fetch_url(url: str) -> str | None:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # corporate TLS proxy re-signs certs
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
            return r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None


def strip_html(raw: str) -> str:
    """Plain text of a page, with machine payloads removed.

    Personio career pages embed their whole UI translation table as JSON in the markup
    ("employment_type_desc.fixed_term", "Befristet", "Freelancing", ...). Matching rules
    against that made `contract-not-permanent` fire on EVERY Personio posting - Certivity
    and thermondo were both flagged on 2026-08-19 for strings that were never in the ad.
    So drop <script>/<style> bodies and long quoted-key JSON runs first.
    """
    raw = raw or ""
    raw = re.sub(r"<(script|style|noscript)\b[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    # self.__next_f.push([...]) / window.__NUXT__ = {...} style payloads
    raw = re.sub(r"self\.__next_f[^<]{0,200000}", " ", raw)
    # runs of "some.dotted.key":"value" pairs are config, not prose
    raw = re.sub(r'(?:"[\w.\-]+"\s*:\s*"[^"]*"\s*,?\s*){3,}', " ", raw)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return re.sub(r"\s+", " ", txt).strip()


def fetch_body(url: str) -> tuple[str | None, str]:
    """Return (body_text, source_label). Prefers the employer's ATS over LinkedIn."""
    m = re.search(r"greenhouse\.io/(?:embed/job_app\?for=)?([a-z0-9_-]+)/jobs/(\d+)", url, re.I)
    if m:
        raw = _fetch_url(f"https://boards-api.greenhouse.io/v1/boards/{m.group(1)}/jobs/{m.group(2)}")
        if raw:
            try:
                return strip_html(json.loads(raw).get("content", "")), "greenhouse"
            except json.JSONDecodeError:
                pass

    m = re.search(r"ashbyhq\.com/([a-z0-9_.-]+)/([0-9a-f-]{36})", url, re.I)
    if m:
        raw = _fetch_url(f"https://api.ashbyhq.com/posting-api/job-board/{m.group(1)}")
        if raw:
            try:
                for j in json.loads(raw).get("jobs", []):
                    if m.group(2) in (j.get("jobUrl") or "") or m.group(2) == j.get("id"):
                        body = j.get("descriptionPlain") or strip_html(j.get("descriptionHtml", ""))
                        return re.sub(r"\s+", " ", body), "ashby"
            except json.JSONDecodeError:
                pass

    m = re.search(r"(?:([a-z0-9-]+)\.recruitee\.com|jobs\.([a-z0-9-]+)\.com)/o/([a-z0-9-]+)", url, re.I)
    if m:
        token = m.group(1) or m.group(2)
        raw = _fetch_url(f"https://{token}.recruitee.com/api/offers/")
        if raw:
            try:
                for o in json.loads(raw).get("offers", []):
                    if m.group(3) in (o.get("careers_url") or o.get("url") or "") or m.group(3) == o.get("slug"):
                        return strip_html((o.get("description") or "") + " " + (o.get("requirements") or "")), "recruitee"
            except json.JSONDecodeError:
                pass

    # GAP FIXED 2026-08-26: employers host Greenhouse boards on their OWN domain and pass the
    # job id as `gh_jid`, e.g. mongodb.com/careers/job/?gh_jid=8066544 or
    # schubergphilis.com/careers/7812561003?greenhouse=1&gh_jid=7812561003. The greenhouse regex
    # above only matched the greenhouse.io host, so 70 bodies sat UNREACHABLE purely on a URL
    # pattern. The board token is almost always the bare hostname, and both of those verify 200.
    m = re.search(r"[?&]gh_jid=(\d+)", url, re.I)
    if m:
        job_id = m.group(1)
        host = re.sub(r"^https?://", "", url).split("/")[0]
        host = re.sub(r"^(www|jobs|careers|boards)\.", "", host)
        stem = host.split(".")[0]
        for token in dict.fromkeys([re.sub(r"[^a-z0-9]", "", stem.lower()), stem.lower()]):
            for api in (f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{job_id}",
                        f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{job_id}?questions=false"):
                raw = _fetch_url(api)
                if raw:
                    try:
                        content = json.loads(raw).get("content", "")
                    except json.JSONDecodeError:
                        continue
                    if content:
                        return strip_html(content), "greenhouse"

    m = re.search(r"linkedin\.com/jobs/view/[^/]*?(\d{9,})", url, re.I)
    if m:
        cli = BASE / ".agents/skills/linkedin-search/cli/src/cli.ts"
        if cli.exists():
            try:
                out = subprocess.run(["bun", "run", str(cli), "detail", m.group(1), "--format", "plain"],
                                     capture_output=True, text=True, timeout=90, cwd=BASE)
                if out.returncode == 0 and out.stdout.strip():
                    return re.sub(r"\s+", " ", out.stdout), "linkedin"
            except (subprocess.SubprocessError, OSError):
                pass

    raw = _fetch_url(url)
    return (strip_html(raw), "raw-html") if raw else (None, "unreachable")


# Artem 2026-08-19: skip a posting whose BODY is written in the local language, not just ones
# that explicitly demand it. Rationale: an employer that advertises in German/Dutch runs its
# engineering in German/Dutch, and he speaks neither. This is stricter than the old
# "local-language-required" rule, which only fired on an explicit demand.
LOCAL_LANG_MARKERS = {
    "german": [r"\bund\b", r"\bf(?:ü|ue)r\b", r"\bmit\b", r"\bwir\b", r"\bdein\b", r"\bdu\b",
               r"\bnicht\b", r"\beine\b", r"\bwerden\b", r"\bErfahrung\b", r"\bKenntnisse\b",
               r"\bAufgaben\b", r"\bm/w/d\b", r"\bbringst\b", r"\bunserer?\b"],
    "dutch":  [r"\bhet\b", r"\been\b", r"\bvoor\b", r"\bwij\b", r"\bjij\b", r"\bjouw\b",
               r"\bniet\b", r"\bervaring\b", r"\bwerkzaamheden\b", r"\bfunctie\b",
               r"\bwaarbij\b", r"\bzoeken\b", r"\bmet\b", r"\bals\b", r"\bwordt\b"],
}


def posting_language(low: str) -> tuple[str | None, int]:
    """Return (language, marker_hits) when the body reads as German/Dutch rather than English.

    Counts distinctive stopwords. A stray German word in an English posting scores 1-2; a
    posting actually written in German scores far higher, so the threshold separates them.
    """
    best, best_n = None, 0
    for lang, pats in LOCAL_LANG_MARKERS.items():
        n = sum(len(re.findall(pat, low)) for pat in pats)
        if n > best_n:
            best, best_n = lang, n
    # Normalise against length so a long English posting with a German benefits list is safe.
    words = max(1, len(low.split()))
    if best and best_n >= 12 and (best_n / words) >= 0.02:
        return best, best_n
    return None, best_n


def lang_score(low: str, patterns: list[str]) -> tuple[int, bool, str]:
    """(mentions, is_core, quote). is_core when a requirement cue sits next to it."""
    total, core, quote = 0, False, ""
    for p in patterns:
        hits = list(re.finditer(p, low))
        total += len(hits)
        for h in hits:
            window = low[max(0, h.start() - 90):h.end() + 40]
            if re.search(CORE_CUES + r"[^.]{0,40}$", window[: len(window) - (h.end() - h.start()) + 5]) \
                    or re.search(CORE_CUES, window[:90]):
                core = True
                if not quote:
                    quote = low[max(0, h.start() - 110):h.end() + 110].strip()
    return total, core, quote


# An ML/AI job title only disqualifies when it names THIS role. Two things must not fire it:
# a colleague ("you'll work alongside a Data Scientist"), and job-board nav chrome
# (arbeitnow renders a "Categories: AI ... Data Scientist ..." menu on every page).
# The cue and the title are usually separated by an article or adjectives
# ("looking for a Senior ML Engineer", "alongside a Data Scientist"), so allow real words
# between them, not just punctuation.
COLLEAGUE_CUES = r"(?:alongside|together with|work(?:ing)? with|collaborat\w*|partner\w*|pair\w*|support|embedded with|report(?:s|ing)? to|hand(?:ing|s)? off to|team of|our)\b.{0,30}$"
ROLE_CUES = r"(?:looking for|seeking|hiring|recruiting|we need|as an?|the role|this role|role:|position|vacancy|job title|title\"?:)\b.{0,45}$"


# "(no Dutch required)" and "we do not require German" must NOT fire the language rule.
# This inversion excluded two Picnic reqs on 2026-08-14 — precisely the postings that go out
# of their way to say the local language is unnecessary.
NEGATION_CUES = r"(?:\bno\b|\bnot\b|\bnon\b|without|isn'?t|aren'?t|do(?:es)?n'?t|need not|no need (?:for|of)|nor\b|neither\b)[^.;!?]{0,40}$"


def _is_negated(low: str, m: re.Match) -> bool:
    before = low[max(0, m.start() - 60):m.start()]
    if re.search(NEGATION_CUES, before):
        return True
    # "Dutch is a plus / nice to have / not mandatory" appearing just after the match.
    after = low[m.end():m.end() + 70]
    return bool(re.search(r"^\W{0,10}(?:is\s+)?(?:a\s+)?(?:plus|bonus|nice[- ]to[- ]have|advantage|preferred|optional|not required|not mandatory)", after))


def _is_the_role(low: str, m: re.Match) -> bool:
    before = low[max(0, m.start() - 90):m.start()]
    if re.search(COLLEAGUE_CUES, before):
        return False
    # Nav chrome: several unrelated category words crammed together with no sentence structure.
    window = low[max(0, m.start() - 160):m.end() + 160]
    nav_terms = sum(t in window for t in ("categories", "android", "ausbildung", "minijob",
                                          "nebenjob", "praktikum", "part time", "homeoffice",
                                          "customer service", "freelance", "frontend"))
    if nav_terms >= 3:
        return False
    if re.search(ROLE_CUES, before):
        return True
    # Otherwise only trust it near the top of the posting, where the title lives.
    return m.start() < 400


def screen(url: str) -> dict:
    body, source = fetch_body(url)
    if not body:
        return {"url": url, "verdict": "UNREACHABLE", "source": source,
                "reasons": [{"rule": "fetch-failed",
                             "quote": "Could not retrieve the posting body. Do NOT hand this over as an apply link."}],
                "flags": []}

    low = body.lower()
    reasons, flags = [], []

    for name, pats in HARD_RULES:
        for p in pats:
            for m in re.finditer(p, low):
                if name == "ml-ai-engineer-role" and not _is_the_role(low, m):
                    continue  # a colleague, or site nav chrome, not the job itself
                if name in ("local-language-required", "no-sponsorship", "must-already-reside",
                            "clearance-or-citizenship") and _is_negated(low, m):
                    continue  # "(no Dutch required)", "sponsorship is not a problem", etc.
                reasons.append({"rule": name, "quote": body[max(0, m.start() - 130):m.end() + 190].strip()})
                break
            else:
                continue
            break

    # "Zero Python mentions" is only meaningful if we actually got a posting. A JS shell or a
    # truncated page yields py=0 and would otherwise be excluded as if the stack were wrong.
    if len(body) < 600:
        return {"url": url, "verdict": "UNREACHABLE", "source": source, "body_len": len(body),
                "reasons": [{"rule": "body-too-short",
                             "quote": f"Only {len(body)} chars retrieved — not enough to judge the "
                                      f"stack. Do NOT treat as a stack mismatch, and do NOT hand "
                                      f"over as an apply link. Body: {body[:200]}"}],
                "flags": []}

    # A stated salary below the Dutch Highly Skilled Migrant threshold is a HARD gate, not a
    # preference: below EUR 5,942/month IND will not grant the permit, so the role is
    # unreachable regardless of how good it is. Added 2026-08-24 after Futurewhiz passed with
    # "EUR 4900 - EUR 5600 per month" - visa-ineligible AND explicitly non-sponsoring.
    HSM_MONTHLY = 5942
    for m in re.finditer(r"(?:eur|EUR|\u20ac)\s?([0-9][0-9.,]{2,6})\s*(?:-|–|to)\s*"
                         r"(?:eur|EUR|\u20ac)?\s?([0-9][0-9.,]{2,6})\s*(?:per|/|a)?\s*month",
                         body, re.I):
        try:
            top = float(m.group(2).replace(".", "").replace(",", "."))
        except ValueError:
            continue
        if 1000 < top < HSM_MONTHLY:
            reasons.append({
                "rule": "below-hsm-threshold",
                "quote": f"Stated top of band is about EUR {top:,.0f}/month, under the Dutch "
                         f"Highly Skilled Migrant threshold of EUR {HSM_MONTHLY}/month, so the "
                         f"permit cannot be granted: "
                         f"\"{body[max(0, m.start() - 60):m.end() + 60].strip()}\""})
            break

    plang, pn = posting_language(low)
    if plang:
        reasons.append({"rule": "posting-written-in-local-language",
                        "quote": f"The posting body is written in {plang} ({pn} marker words). "
                                 f"Artem does not speak German or Dutch, and an employer that "
                                 f"advertises in the local language runs its engineering in it."})

    py, py_core, _ = lang_score(low, [r"\bpython\b"])
    rival_report = {}
    for lang, pats in RIVALS.items():
        n, core, q = lang_score(low, pats)
        if n:
            rival_report[lang] = {"mentions": n, "core": core, "quote": q}

    core_rivals = [l for l, r in rival_report.items() if r["core"]]
    eco_hits = [re.search(pat, low) for pat in PY_ECOSYSTEM]
    eco_hits = [m for m in eco_hits if m]
    if py == 0 and eco_hits:
        # The word "python" is absent but the stack is unmistakably Python. Surface it for a
        # human read instead of dropping it.
        names = ", ".join(sorted({m.group(0) for m in eco_hits}))
        flags.append({"rule": "python-implied-by-ecosystem",
                      "quote": f"The word \"Python\" never appears, but these Python-ecosystem "
                               f"tokens do: {names}. Read the stack yourself before judging."})
    elif py == 0:
        if core_rivals:
            worst = core_rivals[0]
            reasons.append({"rule": "python-absent-rival-core",
                            "quote": f"Zero Python mentions; {worst} is stated as a hard requirement: "
                                     f"\"{rival_report[worst]['quote'][:220]}\""})
        else:
            reasons.append({"rule": "python-absent",
                            "quote": "Zero Python mentions anywhere in the posting body."})
    elif not py_core and core_rivals:
        flags.append({"rule": "python-not-core",
                      "quote": f"Python appears {py}x but never as a stated requirement, while "
                               f"{', '.join(core_rivals)} is/are required."})

    for name, pats in FLAG_RULES:
        for p in pats:
            m = re.search(p, low)
            if m:
                # "mentoring junior developers" describes who he'd coach, not his own grade.
                if name == "below-senior":
                    ctx = low[max(0, m.start() - 60):m.end() + 60]
                    if re.search(r"mentor|coach|guide|teach|onboard|grow(?:ing)?\s+(?:the\s+)?team", ctx):
                        continue
                q = body[max(0, m.start() - 120):m.end() + 170].strip()
                if name == "degree-hard-requirement" and re.search(
                        r"or equivalent|equivalent (?:practical )?experience", low):
                    q += "  [softened: posting allows equivalent experience]"
                    name = "degree-requirement-softened"
                flags.append({"rule": name, "quote": q})
                break

    # A LinkedIn body is not authoritative. Verified 2026-08-19: Staffbase, Circonomit and
    # emnify all showed Python via LinkedIn and ZERO Python in the employer's own ATS text
    # (their real stacks are Kotlin/Go/Java, and Go+C#). So never treat a LinkedIn-sourced
    # PASS/FLAG as a confirmed stack match - say so on the record.
    if source == "linkedin" and not reasons:
        flags.append({"rule": "linkedin-body-unverified",
                      "quote": "Stack was read from LinkedIn, which can truncate or rewrite the "
                               "posting. Re-screen against the employer's own ATS before applying."})

    verdict = "EXCLUDE" if reasons else ("FLAG" if flags else "PASS")
    return {"url": url, "verdict": verdict, "source": source, "python_mentions": py,
            "python_is_core": py_core, "rivals": rival_report, "reasons": reasons, "flags": flags}


def render(r: dict) -> None:
    mark = {"EXCLUDE": "EXCLUDE", "FLAG": "FLAG", "PASS": "PASS", "UNREACHABLE": "UNREACHABLE"}[r["verdict"]]
    print(f"[{mark}] {r['url']}")
    print(f"  source={r.get('source')} python={r.get('python_mentions')} python_core={r.get('python_is_core')}")
    if r.get("rivals"):
        print("  rivals: " + ", ".join(
            f"{k}x{v['mentions']}{'(CORE)' if v['core'] else ''}" for k, v in r["rivals"].items()))
    for x in r["reasons"]:
        print(f"  EXCLUDE {x['rule']}: {x['quote'][:300]}")
    for x in r["flags"]:
        print(f"  flag {x['rule']}: {x['quote'][:240]}")
    print()


def persist(entry: dict, r: dict) -> None:
    """Write a screen result onto a seen_jobs entry.

    Extracted 2026-08-24. It used to live inline in the --unassessed branch only, so
    `./screen <url>` printed a correct verdict and saved nothing - which silently wasted a
    448-URL sweep and left a known-dead posting sitting at PASS.
    """
    entry["screen_verdict"] = r["verdict"]
    entry["screen_python"] = r.get("python_mentions", 0)
    entry["screen_python_core"] = r.get("python_is_core", False)
    entry["screen_rivals"] = ",".join(
        f"{k}{'(core)' if v['core'] else ''}" for k, v in (r.get("rivals") or {}).items())
    entry["screen_flags"] = [x["rule"] for x in r.get("flags", [])]
    entry["screen_date"] = date.today().isoformat()
    if r["verdict"] != "UNREACHABLE":
        entry["assessed"] = True
    else:
        entry["unreachable_attempts"] = (entry.get("unreachable_attempts") or 0) + 1
        if entry["unreachable_attempts"] >= 2:
            entry["assessed"] = True
            entry["notes"] = (entry.get("notes", "") +
                              " | body UNREACHABLE after 2 attempts - never read, NOT a stack "
                              "verdict, do not recommend from this entry").strip(" |")
    if r["verdict"] == "EXCLUDE":
        entry["status"], entry["fit"], entry["assessed"] = "skipped", "low", True
        entry["notes"] = "AUTO-EXCLUDED by screen_job.py: " + "; ".join(
            f"{x['rule']} - {x['quote'][:180]}" for x in r["reasons"])
    elif r["verdict"] == "FLAG":
        entry["notes"] = (entry.get("notes", "") + " | screened FLAG: " + ", ".join(
            x["rule"] for x in r["flags"])).strip(" |")


def main() -> int:
    p = argparse.ArgumentParser(description="Apply hard-exclusion rules to a posting body.")
    p.add_argument("url", nargs="?")
    p.add_argument("--unassessed", action="store_true",
                   help="screen every seen_jobs entry whose body was never read, and write results back")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--first-seen", dest="first_seen", metavar="YYYY-MM-DD",
                   help="restrict --unassessed to entries first seen on this date (one scrape round)")
    p.add_argument("--include-ranked", action="store_true",
                   help="also screen entries /rank scored without reading their body")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    if a.unassessed:
        doc = json.loads(SEEN.read_text())
        seen = doc["seen"]
        # "ranked" entries were scored by /rank without their body ever being read, which is
        # the same blind spot as "new". They are eligible too.
        eligible = ("new", None, "ranked") if a.include_ranked else ("new", None)
        todo = [u for u, e in seen.items()
                if not e.get("assessed") and e.get("status") in eligible and u.startswith("http")
                and (not a.first_seen or e.get("first_seen") == a.first_seen)]
        todo = todo[: a.limit]
        print(f"screening {len(todo)} unassessed posting(s)\n")
        tally = {"EXCLUDE": 0, "FLAG": 0, "PASS": 0, "UNREACHABLE": 0}
        for u in todo:
            r = screen(u)
            render(r)
            tally[r["verdict"]] += 1
            persist(seen[u], r)
        SEEN.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
        print("tally:", tally)
        return 0

    if not a.url:
        p.print_help()
        return 1
    r = screen(a.url)
    print(json.dumps(r, indent=2, ensure_ascii=False)) if a.json else render(r)

    # Persist when we already know this posting, so a single re-screen is not thrown away.
    doc = json.loads(SEEN.read_text())
    entry = doc["seen"].get(a.url)
    if entry is None:
        jid = re.search(r"(\d{7,})", a.url)
        if jid:
            for u, e in doc["seen"].items():
                if jid.group(1) in u:
                    entry = e
                    break
    if entry is not None:
        persist(entry, r)
        SEEN.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
        print(f"  [saved to seen_jobs: {r['verdict']}]")

    return 0 if r["verdict"] in ("PASS", "FLAG") else 3


if __name__ == "__main__":
    sys.exit(main())
