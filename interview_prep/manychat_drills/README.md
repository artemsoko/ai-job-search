# Manychat technical interview — drills

## ⚠️ Read this first

The **confirmed** format, from Manychat's own email (2026-08-21):

- **1.5 hours**, Zoom + live coding in **CoderPad**, **2 interviewers**, Python.
- **Part 1 — Core Python.** A short exercise on **code reading and problem-solving**. Focus:
  Python fundamentals, data structures, **mutability and reference semantics**, code reasoning.
- **Part 2 — Async I/O.** Focus: async/await, concurrent execution, **non-blocking HTTP calls**,
  error handling in async contexts.
- **Part 3 (optional, depends on background) — Applied backend / AI case study.** Build a small
  backend service integrating **an LLM and external APIs**. Focus: API design, async usage, state
  and error handling, and **production thinking** (reliability, maintainability).

Their own prep advice, worth taking literally:
> "Practice reading code and reasoning about behavior before jumping into implementation."
> "Aim for a clear, working solution first, then improve it if time allows."

**Interview is Wednesday next week.**

## Which drills to do

| Drill | Maps to | Time |
|---|---|---|
| `part1_core_python/` | Part 1. **Predict-the-output** quiz on mutability and references, then executable proof. | 90 min |
| `part2_async/` | Part 2. Failing tests on gather vs TaskGroup, timeouts, cancellation, bounded concurrency, error handling. | 90 min |
| `part3_llm_service/` | Part 3. A FastAPI service calling an LLM + an external API, with the production concerns. | 2 h |

## The billing drills are back in scope — recruiter confirmed the domain

On the recruiter call Manychat confirmed two things that change how to read Part 3:

1. **They really are rewriting billing in Python.** That is the strangler-fig migration off the
   PHP core, and it is the actual work of the role.
2. The role is framed as a **Founding Engineer** on that domain, band roughly **EUR 100-120k**.

So while the *format* information in the email supersedes the earlier guesswork (1.5h in CoderPad
with three named parts — there is **no separate SQL round** and no 2-hour pairing session), the
*domain* guess was right. Part 3 is "build a small backend service integrating an LLM and external
APIs", and a company mid-rewrite of billing may well frame that case study around metering,
entitlements or usage — their real problem.

Therefore:

| Drill | Status |
|---|---|
| `drill1_metering/` | **Relevant again.** Closest thing to a billing Part 3: ingest usage events from the core, aggregate per account per period, enforce a limit, stay idempotent. Do it if you have time after the three core drills. |
| `drill2_plan_state/` | **Plausible.** Upgrade-now / downgrade-at-period-end is billing's signature hard part. Good conversation fuel even if it is not the exercise. |
| `sql/` | **Not a round.** Keep for background only — SQL may come up in discussion, it will not be a station. |

## Rules

1. CoderPad is a **plain shared editor**. No agent, no Copilot, and realistically no autocomplete
   worth relying on. Drill that way: agent off, and for Part 1 do it on paper first.
2. Think out loud — they said so explicitly, twice.
3. Ask clarifying questions and **state your assumptions aloud**. Also explicitly in their tips.
4. Working first, then better. Don't gold-plate before it runs.

```bash
./.venv/bin/python -m pytest part2_async -x -q
```
