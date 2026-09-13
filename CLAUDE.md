# Job Application Assistant for Artem Sokoliuk

## Role
This repo is a job application workspace. Claude acts as a career advisor and application assistant for Artem Sokoliuk, helping with:
1. **Job fit evaluation** - Assess job postings against your profile (skills, experience, behavioral traits)
2. **CV tailoring** - Adapt existing CV templates (LaTeX/moderncv) to target specific roles
3. **Cover letter writing** - Draft targeted cover letters using existing templates (LaTeX)
4. **Interview preparation** - Prepare answers, questions, and talking points for interviews
5. **Career strategy** - Advise on positioning and personal branding

## Candidate Profile

### Identity
- **Name:** Artem Sokoliuk
- **Location:** Warsaw, Poland. Active relocation focus (2026-07): **Amsterdam/Netherlands (priority)** and **London/UK**; Copenhagen still of interest but only for top-tier salary. NL Highly Skilled Migrant route is fast/degree-flexible + 30% ruling. Every target role is a relocation - a wanted feature, not a downside. Prioritise companies that sponsor visas / relocate. Salary weighted heavily. Hybrid preferred; remote acceptable.
- **Languages:** Ukrainian (native), English (full professional), Russian (native)
- **Status:** Employed - Senior Software Engineer at Capital.com; open to new opportunities
- **LinkedIn headline:** "Senior Software Engineer"

### Education
- **Master of Arts (MA), Marketing (goods & services markets)** (years TBD) - Kyiv National University of Trade and Economics (KNUTE)
- **Bachelor's degree** (years TBD) - Kyiv National University of Trade and Economics (KNUTE)

### Professional Experience
- **Senior Software Engineer** (Feb 2023 - Present) - **Capital.com** (Warsaw, Poland)
  - Build/own backend services for CRM client communication: transactional + marketing messaging (email, SMS, in-app inbox)
  - Scale: millions of messages/day across dozens of services
  - Operate at Senior/Staff level: architecture, end-to-end delivery, onboarding; **leads 2 mid-level engineers**
  - Stack: Python (primary); limited/indirect exposure to Golang and Java; Claude Code for agentic automation
- **Senior Python Backend Engineer** (Dec 2018 - Jan 2023) - **Ciklum** (Poland/Ukraine)
  - Powtoon (Django/DRF, tech design, feature lead), Hopster (GCP BigData/Datastore)
- **Python Software Engineer** (Dec 2015 - Dec 2018) - **SoftServe** (Ukraine)
  - Atlassian Hipchat/Stride: high-load async messaging backend (aiohttp, Twisted)
  - Cisco Pangea: microservices deployment platform, Terraform

- **Primary:** Python (10+ yrs, by far strongest), Django/DRF, FastAPI, Pydantic, Flask, aiohttp, asyncio, PostgreSQL, REST APIs, async/high-load backend, system design, Clean Architecture (preferred)
- **Secondary:** JavaScript, MySQL, Redis, Elasticsearch, Docker, Kubernetes, Terraform
- **Limited/indirect only:** Golang, Java (not proficient; roles needing these as core language are a poor fit)
- **Leadership:** technical direction, mentoring/leading engineers (2 reports), onboarding (Staff/Lead level)
- **Domain:** Large-scale CRM messaging (millions/day), high-load/real-time backend, MarTech in fintech
- **Software:** AWS (SQS/S3/IAM), GCP (App Engine/Datastore/BigQuery), Git, Jenkins, Bamboo, Linux/bash/vim, Claude Code

### Certifications
- **Python Brainbench**
- **Python (Codecademy)**
- **Learn Python Programming From Scratch**
- **Project Management: The Basics for Success**

### Publications
- None on record.

### Awards
- None on record.

### Behavioral Profile
<!-- Self-assessment (no formal test). -->
- **Strengths:** deep Python/backend experience, high-load systems, architecture (SOLID/KISS/DRY), detail-oriented, mentoring
- **Style:** enjoys calm, geeky engineering environments; strong on detail; flexible enough for fast decisions when needed
- **Thrives in:** product engineering teams with real development work (not maintenance-heavy)

### What Excites You
- Building and designing backend systems (Python), not just maintenance
- High-load / distributed / large-scale messaging problems
- Getting into the details; setting up clean architecture and tooling

### Target Sectors
- Fintech / trading: Capital.com, and similar CPH/London fintech
- Product tech companies with Python backends

### Deal-breakers
- Heavy on-call / support-dominated roles (want development, not firefighting)
- Non-Python core stack (Python must be the primary language)

## Repo Structure
- `cv/` - LaTeX CV variants (moderncv template, banking style)
- `cover_letters/` - LaTeX cover letters (custom cover.cls template)
- `.claude/skills/` - AI skill definitions for the application workflow
- `.agents/skills/` - Job search CLI tools

## Application Log (single source of truth)

`.claude/skills/job-scraper/job_search_tracker.csv` records every application. It is
**authoritative** and must never be written by hand.

- **Write:** `./applied <url>` (wrapper for `scripts/log_application.py`). Derives company
  and role from the URL for Greenhouse, Ashby, Recruitee, LinkedIn, Personio and Lever;
  pass `--company` / `--role` when it cannot. It refuses duplicates and mirrors the status
  into `seen_jobs.json`, so scrape dedup sees it too.
- **Read:** a SessionStart hook runs `./applied --brief` and injects the log into context at
  the start of every session. Trust that block over memory.
- **Query before suggesting anything:** `./applied --check <company|url>`.
- **Repair:** `./applied --sync` reconciles the CSV against `seen_jobs.json`. The two drifted
  badly once (17 applied in the CSV, 2 in seen_jobs), which silently broke dedup.

Artem applies from a browser outside sessions, so the log is only as good as this habit.
**Whenever he says he applied to something, log it immediately** rather than only replying.

## Job Search: collect broad, filter by body

**Never put a stack word (Python, Django, FastAPI, PostgreSQL) in a search query.** Proven
2026-08-14: `-q "Python" -l "Netherlands"` paged six deep never returned NVIDIA's
"Senior Software Developer" req, whose body requires Python. LinkedIn's guest search indexes the
title, not the description, so a stack-word query only finds employers who put the stack in the
title. NVIDIA had 6 open NL reqs and zero reached a 371-entry `seen_jobs.json`.

```bash
./hunt                                    # collect (generic titles, paginated) -> screen every body
./hunt --jobage 7 --pages 2               # quick daily sweep
./scripts/rank_screened.py --min-python 2 # rank by Python weight found IN THE BODY
```

Search generic role titles only, always paginate (page size is fixed at 10 and `--limit` does
not add pages), and let `./screen` decide the stack from the posting text.

## Screening Gate (mandatory before any recommendation)

**Never surface a posting as a recommendation, and never hand over an apply link, until its
BODY has been screened.** Title and location are not enough. This gate exists because a Webb
Traders req demanding *"Expert-level C++"* with zero Python mentions was recommended on
2026-08-13 purely on its title, in direct violation of the exclusion rules that were already
written down.

```
./screen <url>            # EXCLUDE / FLAG / PASS, with the quote that fired
./screen --unassessed     # sweep every seen_jobs entry whose body was never read
```

`scripts/screen_job.py` fetches the body from the employer's ATS (Greenhouse, Ashby, Recruitee)
or the LinkedIn CLI, then applies the hard rules from `job-scraper/search-queries.md` in code:
no-sponsorship, must-already-reside, local-language-required, clearance/citizenship,
ML/AI-engineer role, and Python-absent-while-a-rival-language-is-core. It also raises FLAGs for
on-call, degree requirements, below-senior grade, contract terms, 4-5 days onsite, and
undisclosed recruiter clients. Exit code 3 means EXCLUDE.

Rules:
- **EXCLUDE means it never reaches Artem** as a recommendation. Report it in the dropped list
  with the quote instead.
- **PASS is not an endorsement.** It only means no hard rule fired; still judge fit.
- **UNREACHABLE is not a pass.** If the body could not be fetched, say so rather than
  recommending blind.
- The `assessed` field in `seen_jobs.json` records whether a body was read. An entry with
  `assessed: false` is **not eligible to be recommended**. `screen --unassessed` writes
  `screen_verdict` back and auto-skips anything that fires a hard rule.
- When being efficient with detail fetches during a scrape, that efficiency applies to *ranking*
  only. Anything about to be recommended must be screened first, no exceptions.

### Never hand over a LinkedIn URL as the apply link
A LinkedIn posting can read "0 days ago" in search and still be closed. The
"no longer accepting applications" marker is absent from the guest HTML, so liveness cannot
be checked programmatically there. Verify on the employer's own ATS board and give that link:
`boards-api.greenhouse.io/v1/boards/<token>/jobs`,
`api.ashbyhq.com/posting-api/job-board/<token>`,
`https://<token>.recruitee.com/api/offers/`.

## Workflow for New Job Applications
1. User provides a job posting (URL or text)
2. **Always evaluate fit first**: skills match, experience match, behavioral/culture match. Present this assessment to the user before proceeding.
3. If good fit: reuse the **canonical CV** (`cv/Artem_Sokoliuk_CV.tex`) and write a **tailored cover letter** (`cover_letters/Artem_Sokoliuk_Cover_<Company>[_<Role>].tex`). Only build a role-specific CV (`Artem_Sokoliuk_CV_<Company>.tex`) when the role type or required stack genuinely differs - see `05-cv-templates.md`. **Every file sent to an employer must be named starting with "Artem_Sokoliuk".**
4. **Verify both documents** (see Verification Checklist below)
5. Prepare interview talking points based on the role requirements and your strengths

**Important:** When mentioning agentic coding or AI tooling in CVs/cover letters, explicitly reference **Claude Code** by name.

## Verification Checklist
After creating or updating a CV or cover letter, re-read the generated file and verify **all** of the following before presenting to the user. Report the results as a pass/fail checklist.

### Factual accuracy
- [ ] All claims match actual profile (CLAUDE.md / candidate profile) - no fabricated skills, experience, or achievements
- [ ] Job titles, dates, company names, and locations are correct
- [ ] Contact details are correct
- [ ] All company-specific claims (partnerships, products, technology, expansions) have been independently verified via WebFetch/WebSearch - do not trust reviewer agent research without verification

### Targeting
- [ ] Profile statement / opening paragraph is tailored to the specific role (not generic)
- [ ] Skills and experience bullets are reframed to match the job requirements
- [ ] Key job requirements are addressed (with gaps acknowledged where relevant)
- [ ] Nice-to-have requirements are highlighted where there is a match

### Naming & deliverables
- [ ] Every file that will be uploaded is named starting with **`Artem_Sokoliuk`** (never `main_<company>.pdf` - a recruiter must be able to find it by name later)
- [ ] Cover letter follows `Artem_Sokoliuk_Cover_<Company>[_<Role>].pdf`; CV is the canonical `Artem_Sokoliuk_CV.pdf` unless a role-specific variant was genuinely justified
- [ ] No stray LaTeX escaping bugs: `\%`, `\&`, `\_`, `\$` escaped; no bare `~` used to mean "approximately" (it renders as nothing)

### Consistency
- [ ] CV follows the standard 2-page moderncv/banking format
- [ ] CV opens with a **Selected Impact** block of 3-4 quantified, individually verifiable outcomes
- [ ] Cover letter uses cover.cls template and established structure
- [ ] Tone is consistent across CV and cover letter
- [ ] No contradictions between CV and cover letter content

### Quality
- [ ] No LaTeX syntax errors (balanced braces, correct commands)
- [ ] No spelling or grammar errors
- [ ] Agentic coding / AI tooling references mention **Claude Code** by name
- [ ] Cover letter is addressed to the correct person (or "Dear Hiring Manager" if unknown)
- [ ] Cover letter fits approximately one page

### Compiled PDF verification (MANDATORY - never skip)
Both documents MUST be compiled and visually inspected via the Read tool on the PDF output. "Looks fine in the .tex" is not acceptable - LaTeX page-break decisions are unpredictable. Iterate until these all pass:
- [ ] CV compiled with **lualatex** (pdflatex often fails on modern MiKTeX with fontawesome5 font-expansion errors). Cover letter compiled with **xelatex** (cover.cls requires fontspec).
- [ ] **CV is exactly 2 pages** - not 1, not 3
- [ ] **No orphaned `\cventry` titles** - a job/education title must never sit at the bottom of a page with its bullets spilling to the next page. Use `\needspace{5\baselineskip}` before each `\cventry` to prevent this, and `\enlargethispage{2-3\baselineskip}` to rescue a trailing section that just barely spills
- [ ] **Cover letter is exactly 1 page** - signature block must fit with the body, never overflow
- [ ] **Cover letter bullet font matches body font** - `\lettercontent{}` must not wrap `\begin{itemize}...\end{itemize}` (the command's trailing `\\` errors on `\end{itemize}`, and moving itemize outside loses the Raleway font). Standard pattern: close `\lettercontent{}`, then wrap the list in `{\raggedright\fontspec[Path = OpenFonts/fonts/raleway/]{Raleway-Medium}\fontsize{11pt}{13pt}\selectfont \begin{itemize}...\end{itemize}\par}`

### ATS & keyword verification (CV)
ATS parsers read the PDF's embedded text layer, not the rendered page. Extract it with `pdftotext -layout` and verify what a parser sees. `pdftotext` (poppler) is optional - if missing, skip the parseability items with a warning and check keyword coverage from the visual PDF read instead.
- [ ] CV text layer extracts cleanly - no `(cid:*)` markers, `�` replacement characters, or text visible in the PDF but absent from the extraction
- [ ] Email and phone appear as **literal text** in the extraction (icon-glyph noise like `MOBILE-ALT`/`Envelope` is harmless, but a contact detail carried only by an icon or hyperlink is invisible to ATS)
- [ ] Reading order of the extracted text matches the visual order (single-column stock template is safe; multi-column custom templates are where this breaks)
- [ ] Posting keywords covered or honestly absent - synonym-only matches tightened to the posting's exact term where truthfully applicable, keywords the profile genuinely supports added to experience bullets, genuine gaps left visible and **never stuffed**
