# Search Queries for Job Scraper

<!-- Populated by /setup for Artem Sokoliuk. Re-run /setup --section search to update. -->

## Candidate targeting (summary)

- **Role titles:** Senior Backend Engineer, Senior Python Engineer/Developer, Software Engineer (Python-primary), Python Developer, Staff/Lead/Platform Engineer
- **Core skills:** Python, Django, Django REST Framework, aiohttp, asyncio, PostgreSQL, backend/API, high-load/async
- **Based in:** Warsaw, Poland. **Relocation target:** Copenhagen/Denmark (preferred, but only for top-tier salary) or London/UK. Relocation is wanted, not a downside. Fully-remote EU-friendly roles also fine.
- **Work mode:** hybrid preferred; fully remote acceptable; onsite OK. Salary weighted heavily (esp. Copenhagen); prefer roles that mention visa sponsorship / relocation.
- **Deal-breakers (filter out / flag):** heavy on-call/support-dominated roles; non-Python core stacks

## Installed portal CLIs (primary for `/scrape`)

`/scrape` discovers every portal skill under `.agents/skills/*/SKILL.md` and runs its CLI first. Installed here:

- **linkedin-search** - covers both Copenhagen and London (primary for London)
- **jobindex-search** - largest Danish general job board (Copenhagen)
- **jobbank-search** - Danish public job bank (Copenhagen)
- **jobdanmark-search** - Danish board (Copenhagen)
- **jobnet-search** - Danish public employment board (Copenhagen)
- **freehire-search** - country-agnostic board

The `site:` query templates below are the **WebSearch fallback** - for portals without a CLI (notably UK/London boards), company career pages, or when a CLI fails.

## Search Sites

Primary (portal CLIs above). WebSearch fallback boards:

Copenhagen / Denmark:
- **jobindex.dk** - largest Danish general board (also covered by jobindex-search CLI)
- **linkedin.com/jobs** - filter Copenhagen / Denmark (also covered by linkedin-search CLI)
- **thehub.io** - Nordic startup/tech jobs
- **weworkremotely.com / remoteok.com** - remote roles

London / UK:
- **linkedin.com/jobs** - filter London / UK (covered by linkedin-search CLI)
- **indeed.co.uk**
- **otta.com** / **welcometothejungle.com** - tech-focused
- **reed.co.uk**

## Query Categories

Combine each query with the location terms. Run every category for **both** Copenhagen and London.

## THE QUERY RULE (2026-08-14) — read before writing any query

**Never put a stack word in a search query.** Not Python, not Django, not FastAPI, not
PostgreSQL. Proven by experiment: `-q "Python" -l "Netherlands"` paged **six deep (60 results)**
never returned NVIDIA req 4453393675, whose body requires *"Proficiency in Python"* but whose
title is "Senior Software Developer". LinkedIn's guest keyword search indexes the **title**, not
the description. **NVIDIA had 6 open NL reqs and zero were in a 371-entry `seen_jobs.json`.**

A stack-word query therefore finds only employers who happened to put the stack in the title,
and silently discards the rest. The stack must be decided by reading the **body**.

**Correct pipeline:** `./hunt` → generic titles, paginated → `./screen` reads every body and
counts Python vs rival languages → `./scripts/rank_screened.py` ranks by what the body says.

### Generic titles to search (the only kind)

```
Senior Software Engineer          Staff Software Engineer      Backend Developer
Senior Software Developer         Lead Software Engineer       Platform Engineer
Senior Backend Engineer           Principal Software Engineer  Tech Lead
```

### PAGINATION IS MANDATORY

`linkedin-search` has a **fixed page size of 10**. `--limit 20` caps client-side output but does
**not** fetch page 2, so every round before 2026-08-14 saw only the top 10 hits per query. Pass
`--page 1`, `--page 2`, `--page 3` explicitly. `scripts/hunt.py` does this automatically.

---

## Legacy stack-word queries (kept for reference — DO NOT use as the primary sweep)

The categories below are what the old title-matching approach used. They are retained because
they document the target roles, but running them *as queries* reproduces the NVIDIA blind spot.
Use them to understand what a good match looks like, not to search.

### Priority 1: Senior Python Backend

Strongest and most desired direction.

```
site:jobindex.dk "Senior Backend Engineer" Python Copenhagen
site:jobindex.dk "Python" backend Copenhagen
site:linkedin.com/jobs "Senior Python Engineer" Copenhagen
site:linkedin.com/jobs "Senior Backend Engineer" Python London
site:linkedin.com/jobs "Python Developer" London
site:thehub.io "Python" backend Copenhagen
```

### Priority 2: High-load / async / platform backend

Domain expertise (async, high-load, distributed).

```
site:jobindex.dk "Python" (async OR asyncio OR high-load OR distributed) Copenhagen
site:linkedin.com/jobs "Backend Engineer" Django Copenhagen
site:linkedin.com/jobs "Python" (asyncio OR aiohttp OR high-load) London
site:otta.com Python backend London
```

### Priority 3: Staff / Lead / Platform Engineer

Step-up roles to pivot into.

```
site:linkedin.com/jobs "Staff Engineer" Python Copenhagen
site:linkedin.com/jobs "Lead Backend Engineer" Python London
site:jobindex.dk "Platform Engineer" Python Copenhagen
site:linkedin.com/jobs "Tech Lead" Python (Copenhagen OR London)
```

### Priority 4: Broader Python / fintech (wider net)

```
site:linkedin.com/jobs "Software Engineer" Python (Copenhagen OR London)
site:indeed.co.uk "Python developer" London
site:linkedin.com/jobs Python fintech (Copenhagen OR London)
site:jobindex.dk "Software Engineer" Python Copenhagen
```

## Location Filter

Artem is in Warsaw and wants to relocate. Relocation is NOT a downside - do not down-rank a role because it needs a move.

- **Denmark** (Copenhagen preferred; anywhere in DK acceptable) - PASS. Prefer top-tier salary for Copenhagen.
- **London / UK** (all zones + commuter belt) - PASS
- **Fully remote** (EU-friendly, incl. Poland) - PASS
- Elsewhere with relocation support - FLAG for discussion
- Prefer postings that mention visa sponsorship / relocation package.

## Filters — BIAS TOWARDS INCLUSION (set 2026-08-12 by Artem)

Artem wants to apply **broadly**. Coverage beats curation. Only four things are hard exclusions, and each must be **explicitly stated in the posting text** — never inferred from the job title, and never from missing information.

### INCLUDE (all of these are yes)
- **Location:** any city in the target country, plus remote roles where the employer can employ him there.
- **Level:** Senior, Staff, Lead, Principal, "Engineer II/III" at senior banding, or any unlevelled posting asking 5+ years.
- **Python is a core OR co-core backend language.** Include polyglot postings, backend-heavy full-stack, and data-platform/data-engineering roles where Python is primary.
- **Salary unknown → INCLUDE.** Dutch and German postings almost never publish ranges; absence of a figure is not evidence of low pay. (This mistake previously cut good employers - do not repeat it.)
- **Visa status unknown → INCLUDE.** NL/DE postings rarely mention sponsorship, and Germany has no sponsor registry to advertise. Silence is not a rejection.

### EXCLUDE — only when the posting says so explicitly
1. No visa sponsorship / "must already have the right to work in NL/EU" / "NL residents only" / "must be based in the Netherlands".
2. Local language (Dutch/German) required at working level.
3. Security clearance, or EU/national citizenship required.
4. Python entirely absent **and** the core stack is Go / Java / Rust / C# / .NET / Node / Scala / PHP / C++.

### HARD EXCLUSION — he is not an ML/AI engineer (stated 2026-08-13)
Artem is a **Python backend engineer who uses AI tooling**, not someone who builds models or agentic systems. He has never written an LLM, a model, or an agent framework from scratch — Claude Code is a tool in his workflow, nothing more. Applying to ML/AI-engineer roles would be dishonest and he would not pass the interview.

**Do not surface** (regardless of how Python-primary they look): ML Engineer, Machine Learning Engineer, AI Engineer, Applied Scientist, Data Scientist, Analytics Engineer, MLOps Engineer, roles whose core deliverable is models, RAG pipelines, agent frameworks or LLM research.

**Do surface** the adjacent-but-legitimate case: **backend/platform engineering that serves AI systems**, where the deliverable is production services and APIs rather than models. Signal to look for in the posting: "built and deployed Python backend services that run in production", "you're a developer, not a notebook user", API/infrastructure ownership. Label these clearly so he can judge.

**In cover letters:** frame Claude Code as *engineering practice and tooling* ("I work in an AI-augmented way", "I use Claude Code daily for refactoring, tests and documentation"). **Never** imply ML/model-building capability.

Note the consequence honestly: excluding ML/data roles thins an already-thin NL Python market further, because Python in the Netherlands has largely migrated into data/ML. This strengthens the case for Germany, or for relaxing the salary floor.

### Revealed preference (observed 2026-08-12) — surface these, but rank them LOW
Artem asked for broad coverage, then declined three roles on fit grounds. His real target is **product backend + genuine relocation**. So still include, but do not present as top picks:
- **Data engineering / data platform** roles even when Python-primary (he skipped MOIA despite it being the only posting with written visa+relocation support).
- **Hardware/robotics-adjacent** backend (skipped Noyes Robotics - warehouse automation, ops-pull risk).
- **Remote roles that deliver no relocation** (skipped PandaDoc Remote Poland even at EUR 86-128k - relocation is the whole point of the search).

### FLAG, do not drop (he judges these himself)
- On-call / production-support duties mentioned.
- Below-senior level, or a recruiter posting with an undisclosed client.
- Go/Java present alongside Python as co-core.
- Contract/freelance rather than permanent.
- A salary signal **at or below EUR 80k** stated explicitly in the posting (that is genuinely too low). **Superseded 2026-08-18: the EUR 110k floor is DROPPED for the Netherlands.** Artem instructed: *"не будемо лімітувати по ЗП Нідерланди... хіба шо відверто пишеться щось типу до 75 чи 80 тис євро - що дуже мало."* So: never filter or down-rank a NL role for an absent or merely-modest salary; only flag when the posting itself states a ceiling around EUR 75-80k or below. Rationale: a EUR 110k base barely exists for Python in NL, and holding the floor was cutting the entire realistic market.

### IND recognised-sponsor status (grepped from the official register, updated 3 Aug 2026 — ~11,226 entities)
The register is the hard yes/no on Dutch HSM sponsorship. Grep by **legal entity name**, not brand ("NN Group"/"Nationale-Nederlanden" return nothing; **NN Personeel B.V.** is the listed entity).
- **CONFIRMED sponsors:** Picnic, Albert Heijn, bol.com, Ahold Delhaize, Sendcloud, Jumbo, ABN AMRO, ING, NN Personeel B.V., APG, Van Lanschot Kempen, Netflix International, Uber B.V., Alliander, Eneco, TNO, Castor International, Leadinfo, Xebia Nederland, Framer, NXP, Philips, HERE, ASML Netherlands, TomTom International, Nebius B.V., DataSnipper B.V., AgriPlace (Simvia), Screen6 (Samba TV), Siemens Industry Software Netherlands (Mendix), Corsearch, Stream.io *(see note)*, Bitvavo, BlockTech, Telnyx Netherlands, Adyen, Optiver, IMC, Flow Traders.
- **NOT sponsors — deprioritise regardless of fit:** GetStream/Nightwatch, Dott, Swapfiets, Studocu, Miro, Aiven, Confluent, TransIP, Adevinta, Hiber, Withthegrid, NS, ProRail, Channable, Taktile (UK entity only), QRT, Cloudbeds, AeroVect. (Nikhef employs via NWO-I which *is* listed; de Volksbank appears only as ASN Bank N.V.)
- Note: two sweeps disagreed on **Stream.io B.V.** - one found it listed, a later grep did not. Verify before relying on it.

### NL salary reality for senior Python (verified across ~900 companies, 2026-08-12)
**A EUR 110k+ base is close to non-existent for Python roles in the Netherlands.** Only three bands clearing it were found, and two are the wrong stack: Eneco EUR 83-117k (architect/EM level), Airwallex EUR 125-160k (**Java/Kotlin**, no Python), Guerrilla Games EUR 111-195k (**C++**, but offers full visa+relocation support). Realistic Python bands sighted: ABN AMRO EUR 64-93k, APG EUR 64-92k, Van Lanschot Kempen EUR 66-84k, NN EUR 85-113k, ING Chapter Lead EUR 81-129k. **Structural cause:** Amsterdam product-scaleup backends have consolidated on TypeScript/Node and Go; Python now survives mainly in data/analytics/ML engineering. So most Python roles that pass the filter are data-platform, not the product backend Artem wants. Implication: either relax the NL floor to ~EUR 95-105k, or weight Germany higher (where a EUR 130k ask is defensible at Staff/Lead).

### High-value monitoring target
**Just Eat Takeaway — Senior Python Engineer** (req R050154 was filled). JET is a confirmed sponsor that demonstrably hires Senior Python Engineers. Set an alert on their board rather than re-searching.

### Confirmed empty / dead ends for senior Python backend in NL (verified 2026-08-12 — do not re-check)
The "hidden pool at large Dutch employers" hypothesis was tested and **disproved**: the big NL corporates are JVM / .NET / Go shops. Python roles in the Netherlands live at scale-ups and product companies.
- **Fully enumerated, zero senior Python backend:** Nedap (24 eng vacancies: Go, Java/Kotlin, Ruby, .NET, Data Eng, SRE), bol.com (Greenhouse token `bolcom` - a working cheap API for future sweeps; 52 jobs, none senior Python), Ahold Delhaize, Catawiki (Ruby), Databricks Amsterdam (Java/Scala/C++), Flexport (Ruby/Kotlin/TS), Coolblue (TS/C#), Portbase (Java/Angular), Fastned (Java/Kotlin), Luscii (Node), Copernica (PHP), CM.com (Java/Rust/.NET), Sensorfact DevOps (Node), bunq (Kotlin), Picqer (PHP), Fairphone (AOSP).
- **Boards with zero NL engineering roles:** Bird/MessageBird, Sendcloud, Miro, Lokalise, Contentful, Algolia, N26, Form3, GoCardless, Wise, TrueLayer, Raisin, Solaris, Bitpanda, Gemini, Robinhood, Airbnb, Spotify, Sentry, Supabase, Vercel, Grafana Labs.
- **Hard sponsorship/residency knockouts (quoted):** Sytac ("No sponsorship is available, and candidates must already reside in the Netherlands"), Xomnia ("Eligible to work in the Netherlands"), Portbase (Dutch required), Tebi (relocation for EU citizens only), Crisp (B2 Dutch), C Teleport ("we do not relocate candidates currently based outside the country"), kaiko.ai, Schuberg Philis, myTomorrows, Cloudbeds (remote-Europe contract, no HSM), Mollie (no relocation), Booking.com (no relocation - a notable market shift).
- **Unresolved lead worth one check:** Just Eat Takeaway "Python Application Developer with DevOps" (Phenom board returns titles without locations - confirm whether it is NL).
- **Boards that resist scraping:** TomTom, ASML, Signify, Alliander (JS-rendered or unreachable); Workday/Eightfold tenants need POST APIs; techmeabroad.com DNS-fails; Magnet.me `/en/search/jobs` 404s.

### Anti-patterns to avoid when scraping
- **Do not filter on the job title alone.** Titles mentioning another language often still have Python as the primary stack; check the body.
- **Do not blanket-exclude** full-stack, data-platform, platform-engineer or ML-adjacent titles - read them first.
- **Do not cap the recency window at 7 days.** Use 30 days; good roles sit open for months.
- **Do not rely on one board.** Beyond the portal CLIs, sweep Indeed NL, Nationale Vacaturebank, and company ATS boards directly (Greenhouse / Lever / Ashby / Personio / Recruitee / Workable / SmartRecruiters APIs).

### Search gaps found and FIXED 2026-08-26
**1. Employer-hosted Greenhouse boards were unreadable.** Companies run Greenhouse on their own
domain and pass the id as `gh_jid`: `mongodb.com/careers/job/?gh_jid=8066544`,
`schubergphilis.com/careers/7812561003?greenhouse=1&gh_jid=7812561003`. `fetch_body` only matched
the `greenhouse.io` host, so **70 bodies sat UNREACHABLE purely on a URL pattern** - and the
"unreachable" count was being read as "nothing there". Fixed: on any `gh_jid=<id>`, derive the
board token from the hostname (strip `www./jobs./careers./boards.`, take the first label) and hit
`boards-api.greenhouse.io/v1/boards/<token>/jobs/<id>`. Both examples verify 200.
**Lesson: an UNREACHABLE tally is a bug report about the fetcher, not a fact about the market.**

**2. The product-backend title filter was too narrow.** `rank_backend.py` required the words
backend / software / python / founding, so it silently dropped **"Senior Django Developer"** at
Dept - Python core, zero rival languages, exactly the target profile. Fixed by making framework
names first class: `django|fastapi|flask|aiohttp|asyncio`, plus bare `Python Developer`,
`API/Services/Integration Engineer`, and `Sr.` as an abbreviation. Now unit-tested with 13 cases
(7 keep, 6 reject) inside the script's docstring workflow.
**Lesson: filtering on titles is the mistake this whole pipeline exists to avoid - if a title
filter is unavoidable, enumerate the synonyms and TEST it.**

**3. Ireland was never in scope.** `harvest_sponsor_boards.py` had NL and DE only. Telnyx's
Python role is Dublin/Amsterdam, which is what surfaced the omission. Added `IE`; the first run
returned **373 Irish vacancies, 120 engineering, 115 new**. Note what Ireland is: these are
NL-registered sponsor entities with Dublin offices (Grafana Labs, Sony Music, Pinterest, Okta,
Snowflake, Dept), not a survey of Irish employers - there is no Irish equivalent of the IND
register, so Irish-only companies are still uncovered.

### Three ranking views, in increasing strictness (use the right one)
- `rank_loose.py` - everything mentioning Python; former exclusions shown as tags. Artem's verdict
  on this view: *"прям не мій профіль зовсім"* - correct, it sweeps in SRE/DevOps/data/consulting.
- `rank_backend.py` - **product backend only**, title-filtered both ways, below-senior removed.
  **This is the default view.**
- `rank_screened.py` - the original, ranks by Python weight within screened survivors.

### Two screener false-signal bugs, both FIXED 2026-08-19
**Personio pages poisoned every rule.** Personio career pages embed their entire UI translation
table as JSON in the markup (`"employment_type_desc.fixed_term"`, `"Befristet"`, `"Freelancing"`).
`strip_html` kept it, so `contract-not-permanent` fired on **every** Personio posting (Certivity
and thermondo were both wrongly flagged) and the JSON also inflated the Python counts - thermondo
scored py=9 when the real body has py=2, Certivity py=5 when the real body has py=1. Fixed by
stripping `<script>/<style>`, Next.js `self.__next_f` payloads, and runs of 3+ quoted-key JSON
pairs before matching. **Lesson: a suspiciously high py score on a JS-heavy ATS is probably markup.**

**A LinkedIn body is not authoritative for the stack.** Verified 2026-08-19: Staffbase, Circonomit
and emnify all showed Python via LinkedIn and **zero Python** in the employer's own ATS text (real
stacks: Kotlin/Go/Java/TS, and Go+C#). LinkedIn truncates and sometimes rewrites descriptions.
A LinkedIn-sourced PASS/FLAG now carries the flag `linkedin-body-unverified`. **Never apply, and
never recommend, off a LinkedIn body alone - re-screen on the employer ATS first.**

### UNREACHABLE no longer blocks the sweep (fixed 2026-08-18)
`--unassessed` used to leave UNREACHABLE entries `assessed: false` forever, so the same dead URLs
were re-fetched every round and the queue could not drain - a run of 60 spent 45 fetches on them.
Now counted via `unreachable_attempts` and marked assessed after 2 tries, with a note saying the
body was never read so they still cannot be recommended.

### Concurrency: seen_jobs.json has no lock (lost update on 2026-08-18)
Two processes held the file at once and a background screen loop wrote its stale copy back,
**silently destroying 218 entries**. They were only recoverable because the raw scrape output was
still in /tmp. **Never write seen_jobs.json while a background screen/hunt is running.** Serialise,
or add a file lock.

### Known screener limitation: core-detection cues are English-only (found 2026-08-17)
`screen_job.py` decides `python_core` by looking for English requirement cues (`5+ years of experience with`, `strong proficiency in`, ...). A **Dutch-language posting therefore reports `core=False` even when Python is a hard requirement**. Example: a.s.r. "Python Software Engineer" scored `py=7 core=False`, but the body says *"hebt minimaal 5 jaar ervaring met Python"* - Python is unambiguously core. So:
- Treat `core=False` on a Dutch/German-language posting as **unknown**, not as "Python is incidental".
- A fully Dutch-language posting is itself a strong signal the workplace language is Dutch - read it before recommending.

### Second wave of boards tested and retired (2026-08-18)
Tested after Artem asked whether NL has nofluffjobs/djinni equivalents. All reachable, all low or zero yield for senior Python backend:
- **arbeitnow.com/api/job-board-api** - a real public JSON API, but German-market: 651 jobs pulled, **3 in NL**, 1 with Python (a Data Analyst). Dead for NL.
- **devitjobs.nl/api/jobsLight** - working API, 245 NL jobs, 39 Python-ish, 11 senior-titled. Content is Dutch IT-services/consultancy (Ilionx, Info Support, Cegeka, Sopra Steria, EIFFEL, Quad Solutions) plus data/BI/AI and Dutch-titled ops roles (netwerkbeheerder, applicatiebeheerder, systeembeheerder). **Its `hasVisaSponsorship` field is worthless - it is `true` on all 245 records, i.e. a default, not data.** Useful fields that ARE real: `language` (English/Dutch), `workplace`, `companySize`, `activeFrom`, and `redirectJobUrl` which gives the employer's own ATS link. Beware staleness: listings from 2024-08 and 2025-07 sit alongside fresh ones.
- **iamexpat.nl** - `/career/jobs-netherlands/it-technology-positions` works; page 1 = 20 jobs, mostly DevOps/IAM/support/technician. No pagination parameter found. Expat-focused but not senior-Python-focused.
- Not yet swept from this wave: nofluffjobs.com/nl, landing.jobs, eurotechjobs.com.

**Leads these two boards produced, and why each failed** (worth recording so they are not re-surfaced):
- **iwell B.V.** (Utrecht, hybrid, English, IND sponsor) "Hands-on Software Architect" - py=6 core but **C# x10**; stack is *"C# applications running on Azure IoT Edge... an Angular web app with a C# backend... optimization applications in Python"* and it demands moving *"fluently between C#, TypeScript/Angular and Python"*. Python is the smallest slice. Fails the non-Python-core deal-breaker.
- **Swisscom** (Rotterdam, via iamexpat) "Senior Software Engineer" - *"Proficiency in Golang, Python, Vue.js"* (Go first), **hard degree requirement** in Software Engineering/Telecoms (he holds an MA in Marketing), **EUR 60-70k including holiday allowance** which is below the EUR 5,942/month HSM threshold so he could not even qualify for the visa, and a **one-year fixed-term** contract. Offers full family relocation support, which is the only good part.
- **Avy** (Amsterdam) Senior Software Engineer - `activeFrom 2025-07-07`, over a year stale. **Sopra Steria** Python developer - `language: Dutch`, `activeFrom 2024-08`, redirects to a dead ordina.nl page.

### Retired boards - do NOT re-sweep (verified dead 2026-08-17)
The "relocation boards are the last coverage gap for NL" hypothesis was tested and **disproved**. All eight returned zero usable NL Python roles, for structural reasons rather than filtering:
- **relocate.me** - free board decommissioned, renders "0 jobs available" for NL/backend. Product is now a paid newsletter (USD 15/month). Only reachable that way.
- **techmeabroad.com** - domain dead, `getaddrinfo ENOTFOUND` twice (with and without `www.`).
- **Honeypot.io** - HTTP 502 on both `/en/jobs?country=nl` and the root domain.
- **TheHub.io** - **Nordics only** (DK/FI/IS/NO/SE); `countryCode=NL` returns 0. Structurally cannot serve NL.
- **Jobbatical** - not an aggregator; `/jobs` is their own careers page (relocation-services vendor).
- **Welcome to the Jungle / Otta** - login-walled, self-describes coverage as **FR/UK/US**. NL is not a market.
- **Magnet.me** - working URL is `https://magnet.me/en/jobs` (NOT `/en/search/jobs`), with `/en/jobs/<location>`; the function filter does not bind (`/en/jobs/software-development` returns the same generic page). 1,163 pages of Dutch consulting/government/sales. Zero senior Python. Keep only as a near-zero-yield option.
- **Indeed NL** - reachable but poisoned: results dominated by AI Engineer reqs (hard-excluded), data engineering, and junior roles at EUR 3-4.5k/month.
- **builtin.com** - NL paths are **geo-broken**: `builtin.com/jobs/eu/netherlands/amsterdam/...` returns Poland/Krakow listings. Do not trust it for NL.

### Verify liveness on the ATS, always - the Stream near-miss (2026-08-17)
**Stream (getstream.io)** had a Senior/Lead Backend Engineer (Python/Django), Amsterdam, with explicit *"relocation support and visa sponsorship if needed"* - a near-perfect match. It is **closed**. It still read as live across BuiltIn, Techstars and search snippets; only `api.ashbyhq.com/posting-api/job-board/stream` revealed the truth. The mirrors were confidently wrong, not merely stale-looking. Never skip the ATS check because a posting "looks" live.

### Recruitee tenant gotcha (found 2026-08-17)
A brand rename does not move the Recruitee tenant. `simvia.recruitee.com/api/offers/` returns `{"ok":false,"error":"Document not found"}`, but the **old** brand works and redirects to the data: `agriplace.recruitee.com/api/offers/` -> 302 -> the real offer list. If a Recruitee token 404s or returns "Document not found", try the company's **previous** name.
- **Report what was dropped and the quoted reason**, so silent over-filtering is visible.

## Date Filter

Only include jobs posted within the last 14 days, or with an application deadline not yet passed. If a posting date cannot be determined, include it but flag as "date unknown".

## Adapting Queries

If the user specifies a focus (e.g. "/scrape fintech" or "/scrape london"), select the matching category/location and generate 2-3 custom queries for that focus.
