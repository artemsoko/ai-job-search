# Handoff prompt — paste this into a new session

Everything below is one prompt. Paste it as your first message in the Desktop app (or any new
session) with the working directory set to `/Users/artemsokoliuk/ai-job-search`.

---

We're continuing an in-progress job search. Read the context before doing anything else, then
tell me what you understand the current state to be and wait for my instruction.

**Read these first, in this order:**

1. `CLAUDE.md` — my profile, the mandatory workflow, the verification checklists, and the hard
   rules (screening gate, never hand over a LinkedIn URL as an apply link, file-naming).
2. `~/.claude/projects/-Users-artemsokoliuk-ai-job-search/memory/next-actions.md` — the
   authoritative current state. Sections 0/0-A/0a hold the live interview processes and the
   policy changes that override older notes.
3. `./applied --brief` — the application log. Trust it over anything else about where I've applied.
4. `.claude/skills/job-scraper/search-queries.md` — the filter rules, the retired boards, and the
   screener bugs that are fixed vs still open. Read this before running or changing any scrape.

**Where things stand, so you can sanity-check what you read:**

- 26 applications submitted, 8 consciously skipped. `seen_jobs.json` has ~2,223 entries.
- Two live processes, both mine to win:
  - **IMC Trading** (Python SWE, Amsterdam). Recruiter call done. A **Python take-home lands in
    about 2 days with a 72-hour window**. Median comp ~EUR 145k.
  - **Manychat** (Senior Python Engineer, Billing, Amsterdam). **Technical interview Wednesday
    2026-08-26**: 1.5h, CoderPad, 2 interviewers — Core Python (code reading, mutability), Async
    I/O, then an optional LLM-service case study. Recruiter confirmed they are **rewriting billing
    in Python**, the role is framed as **Founding Engineer**, band **EUR 100-120k**.
- The Netherlands is exhausted as a source: four consecutive sweeps, ~1,160 new postings, one
  lead. Germany is the better market and is now the primary track for new applications. Do not
  propose another NL scrape unless I ask.
- Standing honesty rules that must never be broken: I am **not** an ML/AI engineer (I use LLMs,
  I have not built models or agent frameworks); **Go and Java are read-only** for me, never claim
  them as working languages; every claim in a CV or cover letter must be verifiable.

**Prep material already built — do not recreate any of it:**

*IMC:*
- `interview_prep/IMC_Python_SWE_Prep.md` — full process, 12-point take-home checklist,
  Python-internals list, my verified achievement numbers.
- `interview_prep/IMC_Coding_Station_Plan.md` — the confirmed station format plus a 17-question
  clarifying-questions checklist. Recruiter confirmed: no LeetCode, existing APIs to work against,
  **Google allowed, AI not**.
- `interview_prep/imc_takehome_scaffold/` — a **working** Clean-Architecture Python scaffold that
  already passes `make check` (ruff, ruff-format, mypy --strict, 19 tests, 96% coverage) and
  builds a Docker image. `72H_PLAYBOOK.md` inside is the hour-by-hour plan for when the task
  arrives. Copy it, don't rebuild it.
- `interview_prep/imc_drills/` — 68 failing pytest tests in IMC's own format (skeleton +
  pre-written failing tests): order book, top-K, sliding-window max, LRU, quota, merge-K.
  Reference solutions in `solutions/` are verified 68/68 passing. `data_structures_drill.md` is
  the spoken drill and is the highest-value hour of prep.

*Manychat:*
- `interview_prep/manychat_drills/README.md` — read this first; it explains which drills map to
  which part of Wednesday's interview and which are background only.
- `part1_core_python/QUIZ.md` + `verify.py` — 20 predict-the-output questions on mutability and
  reference semantics. `verify.py` prints the mechanism, not just the output.
- `part2_async/` — 18 failing tests: concurrency asserted by timing, gather vs TaskGroup,
  cancellation on timeout, Semaphore-bounded concurrency, retry on 5xx but not 4xx.
- `part3_llm_service/BRIEF.md` + `skeleton.py` — the case study. The skeleton is smoke-tested
  (7 behaviours verified). The brief includes the billing-flavoured variants that became likely
  once the recruiter confirmed the rewrite.
- `interview_prep/Manychat_Senior_Python_Billing.md` — STAR stories, the PHP-core/strangler-fig
  context, and my honest gap answers.

*Tooling you'll need if we go back to searching:*
- `./hunt --locations Netherlands|Germany` collects broad by generic title; `./screen <url>`
  reads the body and applies the hard rules; `./scripts/rank_screened.py` ranks by Python weight
  found in the body; `./applied <url>` logs an application.
- `.claude/skills/job-scraper/job_scraper/sponsor_ats_boards.json` — **848 IND-recognised-sponsor
  companies with live ATS boards.** This is the good source. Re-poll it instead of scraping
  LinkedIn.

**How I want you to work:** be direct, tell me when I'm wrong, and never claim something is
verified unless you ran it. If you find a bug in the tooling, fix it and record it in the skill
file rather than working around it.

My immediate priority is Wednesday's Manychat technical interview, then the IMC take-home.

---

## Notes for me (not part of the prompt)

- The old CLI session transcript, if I ever want it back:
  `claude --resume` from this directory, session `1db02e0a-8ed9-4bed-acc5-c7ebf2346bb1`.
- Nothing important lives only in the transcript. Memory, CLAUDE.md, the skills and every prep
  file are on disk, and the SessionStart hook injects the application log automatically.
