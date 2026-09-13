# Interview Prep: Manychat, Senior Python Engineer (Billing), Amsterdam

Applied 2026-08-11 (self-applied, referral went silent). Live req on their Greenhouse:
https://boards.greenhouse.io/manychat/jobs/8480947002

Format expected: about 2 hours collaborative live coding, practical rather than algorithmic.
FastAPI service designed out loud from a blank editor, plus SQL written by hand with no tooling.

---

## 1. The single most important thing to know

**Manychat's core is PHP, and this Python role exists to carve work out of it.**

Their own engineering blog documents scaling to 25,000 webhooks/second on PHP: ReactPHP
(30+ instances), a custom task manager called **Handyman**, a Redis "Cascade Queue" with a
per-bot **Control Queue** pattern to preserve conversation ordering and kill noisy neighbours,
NGINX + OpenResty routing webhooks in about 50 lines of Lua, and a physical partitioning
scheme they call **Galaxies** (6 production Galaxies, 10 Clusters each, dedicated DB servers).
Scale today: 1B+ conversations a year, 1.5M+ customers, 350+ staff on three continents.

Now re-read the JD with that in mind:

> "This is not a standalone backend. This layer acts as a bridge and execution environment for
> high-load, business-critical workflows that cannot be efficiently handled inside the core system."
> "Identify and extract functionality from the core into scalable services."

That is a strangler-fig migration off a PHP monolith, in the billing domain, and they want
someone who has done exactly this. **This is your strongest card and they do not know it yet.**

Also note: the same req is open in Barcelona, and there is an *Engineering Manager, Billing &
Accounts* req in Barcelona. The domain is being staffed up, which is leverage for levelling.

---

## 2. Your matching story, in three sentences

Use this as the "tell me about yourself" close:

> At Capital.com I own the services that send millions of messages a day for CRM communication.
> Two of the things I built are the same shape as this role: I took the critical send path out
> of an existing pipeline and rewrote it, getting 5 to 6 times faster and 8 to 10 times more
> push throughput, and I designed a governance engine that sits *on top of* the existing
> high-throughput pipeline rather than replacing it, enforcing caps, consent and quiet hours in
> real time before a send.
> The governance engine is quota accounting with idempotency and optimistic locking, which is
> billing logic wearing a different hat.

---

## 3. STAR stories, filled for this role

### STAR A: Extracting a critical path from an existing system (their core JD ask)
- **S:** Capital.com's email/push send path ran inside the existing MarTech pipeline. Million-scale
  campaigns took 5 to 6 hours, and the system reported some deliveries as succeeded when they
  had actually failed.
- **T:** I owned making it fast and making it honest, without a big-bang rewrite of the pipeline
  everything else depended on.
- **A:** Split the path into a Go worker plus a Python executor, and pushed duplicate prevention
  and idempotency down to the database level so a retry could not double-send. Rolled out behind
  DB-backed feature flags so it could be reverted per segment.
- **R:** 5 to 6 times faster on TEST (target is 12 to 15 times), push throughput up 8 to 10 times,
  and the false-succeeded class of bug eliminated. **What I would do differently:** I found the
  false-succeeded bug while profiling, not from an alert. The gap was that success was inferred
  rather than confirmed, and I now treat "how do we know this actually happened" as a design
  question, not an observability afterthought.

### STAR B: A bridge layer, not a replacement (their exact architectural framing)
- **S:** Marketing communications needed real-time governance: frequency caps, consent,
  quiet hours, holdout groups, all evaluated before a message goes out.
- **T:** I authored the spec and design from a PRD and own most of the implementation.
- **A:** Built it as a decision service in front of the existing pipeline rather than inside it.
  Quota enforcement uses optimistic locking on a versioned row (compare-and-set) so concurrent
  sends cannot overspend a cap. Decisions are idempotent, so replays are safe. Messages blocked
  by quiet hours are not dropped, they go DELAYED and get promoted when their window opens.
- **R:** TEST-ready, production planned. Integrates with the existing high-throughput pipeline
  and does not replace it. **Why it matters here:** swap "frequency cap" for "plan limit" and
  "consent" for "entitlement" and this is a metering and billing gate.

### STAR C: Async at high load (their AsyncIO requirement)
- **S:** At SoftServe I worked on the backend for Atlassian's Hipchat/Stride chat products.
- **T:** Handle high-load instant messaging traffic in Python.
- **A:** Async Python throughout, aiohttp and Twisted, non-blocking I/O, careful about
  what blocks an event loop.
- **R:** About 2.5 years on a genuinely high-load messaging product. **Relevance:** Manychat is
  also a messaging product with ordering constraints per conversation. Their per-bot Control
  Queue pattern is solving a problem I recognise.

### STAR D: Engineering quality and rollout (their "drive engineering quality" bullet)
- **S:** Standards drifted across repos in our team.
- **T:** Nobody owned it, so I did.
- **A:** Built a standards reference repo (Poetry, Ruff, CI, Alembic migrations), DB-backed
  feature flags, and a secure release pipeline for the Segmentation DB (TEST, then approval,
  then PROD).
- **R:** Adopted by 4+ repos, coverage to 73% against a 50% goal, review cycle roughly twice as
  fast. Acting tech lead about 6 months, 348 MRs reviewed, 200+ authored, ran senior interviews
  resulting in a hire.

---

## 4. Live coding: what to actually rehearse

They will likely give you a loosely defined problem, in their domain, and watch how you think.
Given the billing domain plus the "bridge layer" framing, rehearse these three from a blank file.
Say every trade-off out loud, because the JD says "thinks in systems, not services".

**Drill 1: usage-metering ingest service (most likely shape)**
FastAPI service that receives usage events from the core, aggregates them per account per
billing period, and enforces a plan limit.
- Idempotency key on every event, unique constraint in the DB, so an at-least-once producer
  cannot double-charge.
- Decide out loud: increment a counter synchronously, or append events and aggregate?
  Say why. Append-only plus rollup is auditable, a counter is cheap but loses the audit trail.
- Concurrency on the limit check: `SELECT ... FOR UPDATE` versus optimistic CAS on a version
  column. You have actually shipped the CAS approach, say so.
- Async boundaries: what awaits, what must not block the loop, where the pool limits are.

**Drill 2: API contract between core and Python layer**
The JD says "own API contracts, ensuring stability, backward compatibility, clear boundaries".
Rehearse: versioning strategy, additive-only changes, what happens when the PHP core sends a
field you do not know yet, timeouts and retries in both directions, and how you avoid a retry
storm. Mention circuit breaking and backoff with jitter.

**Drill 3: design for failure, stated as a checklist**
Retries, idempotency, consistency guarantees, at-least-once versus exactly-once (say plainly
that exactly-once delivery does not exist, you get effectively-once via idempotent consumers),
outbox pattern for "write to DB and publish an event" atomicity, dead-letter handling,
observability with tracing across the PHP/Python boundary.

---

## 5. SQL by hand, no tooling

The JD's nice-to-haves name **replication, partitioning, sharding and PL/pgSQL**. That plus
their Galaxies scheme means database depth is a real signal here. Practise writing these cold:

- Aggregate usage per account per month, including accounts with zero usage (LEFT JOIN against
  a generated period series, not an INNER JOIN).
- Upsert a counter: `INSERT ... ON CONFLICT (account_id, period) DO UPDATE SET used = counter.used + EXCLUDED.used`.
- Optimistic locking by hand: `UPDATE quota SET used = used + $1, version = version + 1 WHERE id = $2 AND version = $3`, then check the affected row count.
- Window functions: running total of spend within a period, and `LAG` to find consumption jumps.
- Explain the difference between partitioning (one database, many tables) and sharding (many
  databases) and when each solves your problem. Their Galaxies model is sharding.
- Be ready for "this query is slow, what do you do": EXPLAIN ANALYZE first, look at whether the
  index is being used, check row estimates versus actuals for a bad plan.

---

## 6. Gaps, and how to answer honestly

**"Our core is PHP. Are you comfortable with that?"**
Do not pretend. Say: I have not written PHP professionally. I would be reading it constantly to
decide what to extract, and reading unfamiliar code to find seams is something I do a lot,
including with Claude Code to map a codebase quickly. What I bring is the extraction pattern,
not PHP fluency, and the role is Python.

**"Have you worked on billing?"**
No, and say so plainly, then pivot in one breath: I have built quota accounting with real-time
caps, idempotent decisions and optimistic-locked counters, which is the same correctness
problem. Money makes the consequences worse but not the mechanics different.

**"Have you done sharding at scale?"**
Honest position: I have worked with partitioned data and large PostgreSQL datasets, but I have
not owned a sharded topology like your Galaxies. Ask them how routing works and whether the
Python layer sees the shard boundary or is shielded from it. Curiosity beats a bluff.

**"Why leave Capital.com?"**
Forward-looking, no criticism: the work is good and I have grown into Staff-level scope there.
The move is about relocating my family to Amsterdam, and about doing this kind of platform
extraction work where it is the mission rather than one project among many.

---

## 7. Questions to ask them

Strongest first, these signal you understood the architecture:

1. Your blog describes the Handyman task manager and the Redis Cascade Queue with per-bot
   queues. Where does the Python layer sit relative to those, and does it consume from the same
   queues or its own?
2. Which workflow is first out of the core? Is there already a candidate, or is scoping that
   part of the job?
3. Do the Python services see the Galaxies shard boundary, or is routing abstracted away from them?
4. Who owns the API contract when the core team and the Python layer disagree on a boundary?
5. How do you trace a request across the PHP and Python boundary today?
6. This req is open in Amsterdam and Barcelona. Is it one headcount or two, and does the team
   sit in one place?
7. What does the first six months look like, and what would make you say this hire went well?
8. Balance between extracting existing functionality and building new product features?

**Ask on levelling early.** The JD says 5+ years and you have 10+ with a team of two reporting
to you and six months as acting tech lead. There is an Engineering Manager req in the same
domain, so ask directly where this role sits in their scale and whether Staff exists on that ladder.

---

## 8. Do before the interview

- [ ] Write Drill 1 end to end, from a blank file, out loud, timed at 45 minutes. No autocomplete.
- [ ] Write all six SQL statements from section 5 by hand, then check them.
- [ ] Read the second Manychat blog post ("How Manychat Scaled to 1 Billion Conversations Using
      PHP") so you can reference their reasoning, not just their numbers.
- [ ] Rehearse STAR A and STAR B out loud until each lands in 90 seconds.
- [ ] Have the false-succeeded bug story ready. It is your best answer to "tell me about a bug
      you are proud of finding" and it maps directly to their "design for failure" bullet.
- [ ] Practise Python cold without Claude Code, since you work with it daily and the muscle
      matters here. Same debt as the Nebius prep.

---

## Sources
- JD: Manychat Senior Python Engineer (Billing), Amsterdam, via LinkedIn 4448843866
- Live req: https://boards.greenhouse.io/manychat/jobs/8480947002
- https://medium.com/manychat-engineering/how-we-tamed-php-to-handle-over-25-000-webhooks-per-second-ce860cb59084
- https://medium.com/manychat-engineering/how-manychat-scaled-to-1-billion-conversations-using-php-a-startups-guide-to-smart-tech-choices-781c74f16f23
- Achievements cross-checked against the verified Capital.com Staff-promotion evidence map
