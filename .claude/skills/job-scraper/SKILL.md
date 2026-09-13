---
name: scrape
description: >
  Finds new job postings matching your profile via installed portal-search CLIs
  (LinkedIn, local job boards, and any skills added with /add-portal). Deduplicates
  across runs. Triggers on: job scrape, find jobs, search jobs, new jobs, job search,
  scrape jobs, /scrape
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(bun --version), Bash(bun run .agents/skills/*/cli/src/cli.ts *), WebFetch, WebSearch, Agent, AskUserQuestion
---

# Job Scraper

---

## How It Works

This skill searches job portals using the **installed portal-search CLIs** in
`.agents/skills/` (plus WebSearch as a fallback), using queries from your profile.
It deduplicates against previously seen jobs and the application tracker, and
presents new matches with a quick fit assessment.

## Invocation

The user triggers this skill by saying things like:
- "Find new jobs"
- "Scrape for jobs"
- "Any new positions?"
- "/scrape"

Optional arguments:
- A focus area, e.g. "/scrape data science" or "/scrape geophysics"
- "broad" to run all search categories, e.g. "/scrape broad"

---

## Execution Steps

### Step 0: Load State

1. Read `job_scraper/seen_jobs.json` (create if missing - start with `{"seen": {}}`)
2. Read `job_search_tracker.csv` to extract already-applied companies+roles
3. Read `search-queries.md` (this directory) for the search strategy

### Step 1: Search — collect BROAD, never filter on the stack in the query

**The single most important rule in this skill.** Verified empirically on 2026-08-14:

> LinkedIn's guest keyword search does **not** reach the job description. Querying
> `-q "Python"` for the Netherlands and paging **six deep (60 results)** never returned
> NVIDIA req 4453393675, whose body says *"Proficiency in Python"* but whose title is
> "Senior Software Developer". NVIDIA had 6 open NL reqs; **zero** were in a 371-entry
> `seen_jobs.json`.

Therefore **a query containing a stack word can only ever find postings that put that word
in the title.** Every stack-word query silently discards the employers who describe the stack
in the body, which is most of them. This is how NVIDIA, and an unknown number of others,
stayed invisible for a month.

**The pipeline is inverted: search generic, filter by body.**

```bash
./hunt                        # 30-day window, 3 pages per query, then screens every body
./hunt --jobage 7 --pages 2   # quick daily sweep
./hunt --dry-run              # print the query plan without running it
./scripts/rank_screened.py --first-seen <today> --min-python 2
```

`scripts/hunt.py` runs the whole thing: collect → dedup → record → screen every body →
hand off to ranking. Prefer it over ad-hoc CLI calls.

Rules for any query you write by hand:

1. **Generic role titles only.** "Senior Software Engineer", "Senior Software Developer",
   "Senior Backend Engineer", "Staff/Lead/Principal Software Engineer", "Backend Developer",
   "Platform Engineer", "Tech Lead".
2. **Never put Python, Django, FastAPI, asyncio, PostgreSQL or any other stack word in the
   query.** The stack is decided in Step 3 by reading the body.
3. **Always paginate.** Page size is fixed at 10 and `--limit` does not add pages. Pass
   `--page 1`, `--page 2`, `--page 3` explicitly.
4. **Recency: 30 days, not 14.** Good roles sit open for months.

Fall back to `WebSearch` only for portals with no CLI skill, or if `bun` is unavailable.

#### 1a. Check bun availability

```bash
bun --version
```

If this fails (bun not installed), skip to **1c (WebSearch fallback)** for all portals and note the fallback in the Step 5 output.

#### 1b. Run CLI tools (primary — run these in parallel where possible)

Discover all installed portal CLI skills by reading every `SKILL.md` found under `.agents/skills/*/SKILL.md`. Each file documents that portal's exact CLI flags and usage examples. **Use each portal's own documented interface — do not guess flags.** This approach automatically includes any new portals added via `/add-portal` without requiring changes to this file.

For each installed portal skill:

1. Read its `SKILL.md` to find the correct `bun run …` invocation and supported flags.
2. Translate the query terms from `search-queries.md` into that portal's flag format (e.g. `--key`, `--search-string`, `--query`, filter codes — whatever the portal's SKILL.md specifies).
3. Scope to the last 14 days using the portal's supported recency flag (`--jobage`, `--since <YYYY-MM-DD>`, `--order PublicationDate`, etc. — as documented per portal).
4. Cap results to ~20 per call using the portal's limit flag.
5. Use `--format json` for machine-readable output.

Run all portal CLI calls in parallel where possible using the Agent tool. Collect all `results` arrays into a single pool for Step 2, keeping each result tagged with its source portal skill (for Step 2 `detail` lookups).

If a CLI tool exits with a non-zero code, log the error message and continue — do not abort the whole search.

#### 1c. WebSearch fallback

Use `WebSearch` for:
- Portals listed in `search-queries.md` that do **not** have a corresponding directory under `.agents/skills/`
- Any portal whose CLI fails at runtime
- When bun is unavailable (Step 1a failed)

Use the site-specific query strings from `search-queries.md` directly as WebSearch queries for these portals.

### Step 2: Fetch & Parse

For each promising result from Step 1:

**From CLI results:** Search output already includes title, company, location, date,
and URL. For jobs worth a deeper look, fetch full detail with that portal's `detail`
command (see its SKILL.md — do not guess flags) to extract **key requirements**,
**application deadline**, and a brief description snippet.

**From WebSearch results:** Use `WebFetch` on the posting URL and extract the same
fields manually.

For every candidate:
- Skip if the URL or company+title combo already exists in `seen_jobs.json`
- Skip if the company+role already appears in `job_search_tracker.csv`

### Step 3: Screen, then Quick Fit Assessment

**3a. Screening gate (mandatory, runs on the posting body).** Before any job is presented:

```bash
./screen <url>          # one posting: EXCLUDE / FLAG / PASS with the quote that fired
./screen --unassessed   # sweep everything in seen_jobs.json whose body was never read
```

`scripts/screen_job.py` applies the hard rules from `search-queries.md` in code: no-sponsorship,
must-already-reside, local-language-required, clearance/citizenship, ML/AI-engineer role, and
Python-absent-while-a-rival-language-is-core. It writes `screen_verdict` into `seen_jobs.json`
and auto-sets `status: skipped` on anything that fires a hard rule.

- **EXCLUDE** → never present it. List it in the dropped table with the quoted reason.
- **FLAG** → present it, but surface the flag (on-call, degree bar, below-senior, contract,
  4-5 days onsite, undisclosed client) so the candidate judges it.
- **PASS** → no hard rule fired. This is *not* an endorsement; still assess fit.
- **UNREACHABLE** → say the body could not be read. Do not recommend blind.

An entry with `assessed: false` has never had its body read and is **not eligible** to be
presented as a recommendation.

**3b. Quick fit check** on what survives (NOT the full evaluation from `04-job-evaluation.md`):

- **High match**: Role directly involves your core skills
- **Medium match**: Role is adjacent to your experience
- **Low match**: Role requires significant skills you lack

### Step 4: Deduplicate & Store

1. Add ALL fetched jobs (new and skipped) to `seen_jobs.json` with structure:
```json
{
  "seen": {
    "<url_or_company_title_key>": {
      "title": "...",
      "company": "...",
      "url": "...",
      "first_seen": "YYYY-MM-DD",
      "fit": "high/medium/low",
      "status": "new/skipped/evaluated/ranked/expired"
    }
  }
}
```

`/rank` extends this schema additively: ranked entries also carry `rank_score` (0–100 overall score), `rank_verdict` (fit band, e.g. "strong fit"), and `rank_date` (ISO date of ranking). The `status` field is set to `"ranked"`. Do not drop these fields when re-writing entries.

2. Only present jobs NOT already in the seen list or tracker.

### Step 5: Present Results

Present new jobs in a table sorted by fit (high first):

```
## New Job Matches - YYYY-MM-DD

Found X new positions (Y high, Z medium, W low match).

| # | Fit | Title | Company | Location | Deadline | URL |
|---|-----|-------|---------|----------|----------|-----|
| 1 | High | ... | ... | ... | ... | [Link](...) |

### High-Match Highlights
For each high-match job, add 2-3 bullet points:
- Why it matches your profile
- Key requirements to check
- Any red flags
```

After presenting, ask:
> "Want me to evaluate any of these in detail? Just give me the number(s)."

If the user picks a number, invoke the **job-application-assistant** skill workflow (fit evaluation first, then CV + cover letter if approved).

If the run found many new jobs (roughly 8+), also suggest `/rank` - it batch-scores all new postings against the full fit framework and returns a ranked shortlist, which beats eyeballing a long table. (`/rank` sets the `ranked` and `expired` status values in `seen_jobs.json`; treat both as already-seen for dedup purposes.)

### Step 6: Update Tracker (Optional)

If the user decides to apply to any job, add a row to `job_search_tracker.csv`.

---

## Important Rules

1. **Never fabricate job postings.** Only present jobs from actual CLI search/detail output or WebSearch/WebFetch results.
2. **Respect deduplication.** Always check seen_jobs.json AND job_search_tracker.csv before presenting.
3. **Focus on configured geographic area.** Skip jobs that require relocation or are clearly outside commute range.
4. **Only open positions.** Skip postings with expired deadlines or those marked as closed.
5. **Be efficient with detail fetches, but never at the cost of the screening gate.** Don't run `detail` or WebFetch on every search hit while *ranking* — pre-filter by title/snippet, then fetch only promising matches. **But nothing may be presented as a recommendation, and no apply link may be handed over, until `./screen <url>` has read its body.** Title-only judgement is how a "Expert-level C++" req with zero Python got recommended on 2026-08-13. Screening is cheap: `./screen --unassessed` sweeps the backlog in one command.
6. **Parallel searches.** Run portal CLI searches in parallel; use WebSearch only for gaps the CLIs don't cover.
