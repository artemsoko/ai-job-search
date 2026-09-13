---
framework_version: 1.0.0
---

# Job Evaluation Framework

<!-- SETUP: Skill match areas and career goals are personalized by running /setup -->

## Scoring Dimensions

Evaluate each job posting against these five dimensions:

### 1. Technical Skills Match (0-100)
How well do the required/preferred skills align with the candidate's capabilities?

| Score | Meaning |
|-------|---------|
| 80-100 | Core requirements are primary skills |
| 60-79 | Most requirements match, 1-2 gaps that are learnable |
| 40-59 | Partial match, significant upskilling needed |
| 0-39 | Fundamental mismatch |

**Strong match areas:** Python (Django, DRF, FastAPI, Pydantic, Flask, aiohttp, asyncio), async/high-load backend, REST APIs, PostgreSQL/MySQL/Redis, Clean Architecture + SOLID, Docker/Kubernetes, AWS + GCP
**Moderate match areas:** Terraform, Elasticsearch, JavaScript, CI (Jenkins/Bamboo), MarTech/data systems, fintech domain
**Weak match areas:** non-Python core languages (Go, Java, C#, Rust) - Go/Java are only limited/indirect exposure, NOT working languages, so any role that needs them as a core/primary language is a poor fit; heavy frontend frameworks (React/Vue); formal CS degree signals (background is MA + self-taught engineering); ML/data-science modeling

### 2. Experience Match (0-100)
Does work history align with what they're looking for?

| Score | Meaning |
|-------|---------|
| 80-100 | Direct experience in the same domain and role type |
| 60-79 | Related experience, transferable skills clear |
| 40-59 | Adjacent experience, would need to make the case |
| 0-39 | Unrelated experience |

**Strong:** Senior/Staff Python backend engineering, high-load/real-time systems (large-scale CRM messaging, millions/day), web & API backends, system design/architecture, mentoring & leading engineers (2 reports), product engineering teams
**Moderate:** platform/DevOps-adjacent work (Terraform, k8s, deployment tooling), MarTech/CRM communication systems
**Entry-level:** formal people-management at scale (large teams), pure data science/ML

### 3. Behavioral/Culture Fit (0-100)
Does the role and company culture match the behavioral profile?

| Score | Meaning |
|-------|---------|
| 80-100 | Culture strongly matches behavioral preferences |
| 60-79 | Mixed signals but mostly compatible |
| 40-59 | Some friction areas |
| 0-39 | Significant culture mismatch |

**Red flags to research:** Department disorganization, work dominated by maintenance over development, poor chemistry with leadership, culture mismatches. Check reviews, media coverage, LinkedIn connections, and network contacts for insider perspective.

### 4. Location & Logistics (Pass/Fail + Notes)
Artem is based in **Warsaw, Poland** and wants to relocate. Relocation is a WANTED feature, not a downside. Preference: **Copenhagen/Denmark (but only for top-tier salary)** or **London/UK**.
- Copenhagen / Denmark, hybrid or onsite (relocation): PASS - preferred, but flag whether salary looks top-tier (see Salary Benchmark)
- London / UK, hybrid or onsite (relocation): PASS
- Fully remote (EU-friendly, incl. Poland): PASS
- Elsewhere with relocation support: FLAG (discuss with user)
- For every role: check for **visa sponsorship / relocation package** and note it (candidate is a non-EU... Ukrainian national in Poland - relocation logistics matter).
- Heavy on-call / support-dominated: FLAG (deal-breaker leaning FAIL)
- Non-Python core stack: FLAG (deal-breaker leaning FAIL)
- Frequent international travel: FLAG (discuss with user)

**Salary weighting note:** Artem weights salary heavily, especially for Copenhagen (a CPH offer must pay top-tier to beat London). Treat a clearly low salary for the market as a strong negative in Career Alignment, and always surface the Salary Benchmark / posted range when available.

### 5. Career Alignment & Motivation (0-100)
Does this role advance career goals and contain tasks that energize?

| Score | Meaning |
|-------|---------|
| 80-100 | Strongly aligned with career direction, clear growth path |
| 60-79 | Good role but only partially aligned with long-term goals |
| 40-59 | Decent job but doesn't build toward career goals |
| 0-39 | Dead end or backwards step |

**Career goals:**
- Get a role where the title and mandate match the scope he already operates at (Staff / Lead / Platform) - he frequently works above his current Senior title
- Work on high-load / distributed / large-scale messaging systems with real design ownership
- Stay in a product engineering environment (build over maintain); keep technical leadership + mentoring

**Motivation filter:** Evaluate not just whether you *can* do the tasks, but whether the tasks will *energize* you. Consider:
- Tasks that energize: designing and building backend systems, async/high-load problems, architecture decisions, tooling and automation
- Tasks that drain: on-call/support-dominated work, firefighting, maintenance-only roles, non-Python stacks
- Non-task factors: leadership style, department culture, company values, degree of autonomy

**Life situation alignment:** Consider personal constraints:
- **Location**: based in Copenhagen; targeting Copenhagen + London. Hybrid preferred; fully remote acceptable (incl. remote if relocating). London on-site implies relocation - flag it.
- **Flexibility**: hybrid strongly preferred over full onsite
- **Professional development**: wants growth toward staff/lead and harder technical problems

### 6. Salary Benchmark (Optional)

If the salary lookup tool is configured (`salary_data.json` exists), look up the company:
```
python salary_lookup.py "<Company Name>" --json
```

If a city is known from the posting, add `--city "<City>"` to narrow results.

Present findings as:
```
### Salary Benchmark
| Metric | Value |
|--------|-------|
| [Category] index | XX.X (+/-X.X% vs baseline) |
| Overall index | XX.X (+/-X.X% vs baseline) |
```

Interpret results relative to the baseline defined in the data file's metadata. For index-based data, higher typically means above-market compensation.

If the salary tool is not configured, skip this section.

## Output Format

Present the evaluation as:

```
## Job Fit Evaluation: [Role] at [Company]

| Dimension | Score | Notes |
|-----------|-------|-------|
| Technical Skills | XX/100 | [brief note] |
| Experience Match | XX/100 | [brief note] |
| Behavioral Fit | XX/100 | [brief note] |
| Location | PASS/FAIL | [brief note] |
| Career Alignment | XX/100 | [brief note] |

**Overall Score: XX/100** (weighted average of scored dimensions)

### Verdict: [Strong Fit / Good Fit / Moderate Fit / Weak Fit / Poor Fit]

### Key Strengths for This Role
- [bullet points]

### Gaps to Address
- [bullet points]

### Recommendation
[1-2 sentences: apply/skip/apply with caveats]

### Company Research Checklist
- [ ] Checked company website (mission, values, recent news)
- [ ] Checked review sites (Glassdoor, Jobindex, etc.)
- [ ] Checked LinkedIn for team size, recent hires, connections
- [ ] Checked media for restructuring, growth, or workplace issues
- [ ] Identified network contacts who may know the team/manager
```

## Weighting
- Technical Skills: 30%
- Experience Match: 25%
- Behavioral Fit: 15%
- Career Alignment: 30%

(Location is pass/fail, not weighted)

## Thresholds
- **Strong Fit** (75+): Definitely apply, tailor everything
- **Good Fit** (60-74): Apply, address gaps in cover letter
- **Moderate Fit** (45-59): Consider carefully, discuss with user
- **Weak Fit** (30-44): Probably skip unless strategic reasons
- **Poor Fit** (<30): Skip

## Pre-Application: Call the Employer (Best Practice)

Before writing the application, consider whether the candidate should call the contact person listed in the posting. **Only call if there are substantive questions** - never call just to "be remembered."

### When to Suggest Calling
- The posting has unclear or ambiguous requirements
- It's unclear which competencies are essential vs. nice-to-have
- The role description is vague about day-to-day tasks
- There's a named contact person who invites questions

### Good Questions to Ask
- "What are the primary challenges in this role?"
- "How is time typically divided across the listed responsibilities?"
- "Which competencies are most critical for success in this position?"
- "What does success look like in the first 6-12 months?"

### Rules for the Call
- Prepare a 30-second "elevator pitch" about your background in case they ask
- The call's purpose is **gathering information**, not delivering a pitch
- Take notes - use what you learn to tailor the application
- Reference the conversation naturally in the cover letter ("After speaking with [name], I was especially drawn to...")
