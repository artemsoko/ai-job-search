# Validated roles — 11 Sep 2026

All 24 product-backend hits from today's deep sweep were checked: liveness confirmed on every
one, employer ATS probed where a company has one, and his own rules applied. Grouped by how much
you can trust the posting.

---

## TIER 1 — verified on the employer's own ATS

**Taktile — Backend Engineer, Team Atlas — BERLIN (not Dublin)**
https://jobs.ashbyhq.com/taktile/97cd39e0-de71-4361-a035-2250a689fb70
LinkedIn listed this as Dublin. Their own Ashby board says **Berlin Office**. Fintech
decision-platform, Series B. Note: Taktile appears in the IND register notes as *not* a Dutch
sponsor (UK entity only) — irrelevant here because this is a German role, but it means the visa
route is Blue Card § 18g and must be asked.

---

## TIER 2 — real named employers, no public ATS found, so LinkedIn is the only source

Python confirmed as a requirement in the body. Apply, but expect the posting to be the only
record and ask the recruiter to confirm the stack.

### Germany

**nnamu — Senior Backend Software Engineer (m/f/x) — Berlin** · py=2 core, **no rival language**
https://de.linkedin.com/jobs/view/senior-backend-software-engineer-m-f-x-at-nnamu-4463478776

**Berliner Verlag — Senior Backend Engineer (m/f/d) — Berlin** · py=2 core, Node non-core
https://de.linkedin.com/jobs/view/senior-backend-engineer-m-f-d-at-berliner-verlag-4461883757

**atmo — Full Stack Founding Engineer — Berlin, hybrid** · py=2 core
https://de.linkedin.com/jobs/view/full-stack-founding-engineer-atmo-berlin-based-hybrid-at-atmo-4463468067

**VAARHAFT — Backend Developer (f/m/d) — Hamburg** · py=2 core · ⚠ hard degree requirement
https://de.linkedin.com/jobs/view/full-time-backend-developer-f-m-d-at-vaarhaft-4462547266

### Ireland

**SMBC Group — Senior Python Engineer — Tralee, Co. Kerry** · they have a Workable board, so the
req may be verifiable there: `apply.workable.com/api/v1/widget/accounts/smbc`
https://ie.linkedin.com/jobs/view/senior-python-engineer-at-smbc-group-4418978082

**JPMorganChase — Software Engineer III, Python — Dublin**
https://ie.linkedin.com/jobs/view/software-engineer-iii-python-at-jpmorganchase-4445314635

**CrowdStrike — Sr. Software Engineer, Cloud Platform (Hybrid, Dublin)**
https://ie.linkedin.com/jobs/view/sr-software-engineer-cloud-platform-hybrid-dublin-at-crowdstrike-4441051876

**Datavant Ireland — Senior Software Engineer — Galway**
https://ie.linkedin.com/jobs/view/senior-software-engineer-at-datavant-ireland-4427001930

**Mars Capital — Python Developer / Engineer — Dublin** · py=7, highest of the day · ⚠ hard degree
https://ie.linkedin.com/jobs/view/python-developer-engineer-at-mars-capital-4463855965
https://ie.linkedin.com/jobs/view/python-developer-at-mars-capital-4438087150

### Netherlands

**Hadrian — Senior Backend Engineer (Offensive Security Platforms) — Amsterdam**
py=4 · ⚠ Go and C# are core, so Python is not the primary language
https://nl.linkedin.com/jobs/view/senior-backend-engineer-offensive-security-platforms-at-hadrian-4463550571

**Cboe Global Markets — Lead Software Engineer — Amsterdam**
py=3 · ⚠ Java core. You have an unsent Cboe cover letter from August for a different req.
https://nl.linkedin.com/jobs/view/lead-software-engineer-at-cboe-global-markets-4446135073

---

## TIER 3 — recruiters, client undisclosed

Highest Python weight of the day sits here, which is the trade-off: strong stack signal, unknown
employer, no way to check visa support or team before you talk to them. Worth a message to the
recruiter asking who the client is and whether they sponsor, before sending anything.

| py | Agency | Role | Link |
|---|---|---|---|
| 7 | Archer Recruitment | Senior Python Developer, Dublin | https://ie.linkedin.com/jobs/view/senior-python-developer-%E2%80%93-career-progression%21-at-archer-recruitment-4465631263 |
| 6 | IQ Staffing | Python Developer, Utrecht | https://nl.linkedin.com/jobs/view/python-developer-at-iq-staffing-4464181999 |
| 5 | Client Server | Software Engineer Python — **Energy Optimisation**, Amsterdam | https://nl.linkedin.com/jobs/view/software-engineer-python-energy-optimisation-at-client-server-4465014708 |
| — | Morgan McKinley | Senior Python Developer, Dublin | https://ie.linkedin.com/jobs/view/senior-python-developer-at-morgan-mckinley-4464865176 |
| — | Methodius IT Recruitment | Senior Python Developer / Technical Lead, Dublin | https://ie.linkedin.com/jobs/view/senior-python-developer-technical-lead-at-methodius-it-recruitment-4462484404 |
| — | Berkley Group | Senior Backend Engineer, Dublin | https://ie.linkedin.com/jobs/view/senior-backend-engineer-at-berkley-group-4465679936 |

**Client Server — Energy Optimisation** is worth noting on its own: same domain as Gradyent, so
energy-tech now has two independent openings for you.

---

## EXCLUDED, and why

- **TechHeads — Principal Python Engineer, Greenfield GenAI** (Dublin, py=6). GenAI build from
  scratch. Your stated rule: you are an LLM user, not an agent-framework builder.
- **Lawrence Harvey — Senior Python SWE (FastAPI / LangGraph / Agent Orchestration)** ×2,
  Baden-Württemberg and Hesse, py=5. Agent orchestration, same rule. Also the title states
  **"up to €90,000"**, below where you should be aiming in Germany.
- **Jobgether — Senior Software Engineer** (Germany). Java core, on-call.
- **Jobster — Lead Backend Engineer, Jobbird.com** (Munich). C++ and Node core.

---

## The honest caveat on all of Tier 2 and 3

Every one of those links is LinkedIn. Today's sweep produced **zero PASS verdicts** — all 219
survivors are FLAG — because the `linkedin-body-unverified` rule now fires on any body read from
LinkedIn. That is working as intended: LinkedIn has misreported the stack three separate times
this project (Staffbase and Circonomit and emnify all showed Python and had none on their own
boards), hid a Dutch-language requirement at Schuberg Philis, listed a role at TeleClinic that
had already been pulled, and today put a Taktile Berlin role in Dublin.

So: **check the company's own careers page before you invest a cover letter.** The Tier 1 link is
the only one I can vouch for.
