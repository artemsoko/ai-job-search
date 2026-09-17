# The IMC postmortem, and the fix that carries forward

**Rejected 2026-09-17** after round 2. This is not an IMC document — the diagnosis applies to
every process still open, starting with Manychat.

## What they praised
GIL, concurrency, context managers, data structures, database knowledge. **The Python preparation
worked.** Nothing in the letter suggests a knowledge problem on fundamentals.

## What they rejected on — four items that are one problem

| Their words | What it means |
|---|---|
| *"answered the technical questions correctly overall, [but] some of the more **practical** questions were **less clearly explained**"* | knows it, can't apply it out loud |
| *"hands-on experience debugging serious Kafka production issues... but your explanation of the **fundamentals** did not reflect the same level"* | learned by firefighting, never read the docs |
| *"your solutions and specific contributions were also **not always clearly articulated**, which was important for us given the stakeholder communication required"* | can't draw the line between what he did and what the team did |
| *"we expected stronger familiarity with basic trading concepts, but you were not able to explain what a stock is"* | the known domain gap |

Three of the four are **articulation, not knowledge.**

## This is the same thing the 2026-09-13 mock found

In that mock the diagnosis was written down verbatim, three answers in a row:

> *"Правильний факт і зупиняєшся. Інтервʼюер отримує «так/ні» там, де просив механізм."*

And the opener: a list of activities with no system, no numbers, the best material deferred
(*"if I can't talk about some improvements, I probably can talk about it later"*).

The rejection letter independently confirms it. **That is the good news inside the bad: knowledge
takes years to build, articulation takes a week.**

The sharpest instance of the cost: they asked about **third-party rate limiting in a FastAPI
integration**. He has *shipped* a distributed rate limiter — the governance engine's
optimistic-locking quota accounting with CAS versioned rows. He had the strongest possible answer
in his own production history and did not connect it.

---

# 1. The protocol — drill this, not more facts

**Every technical answer: fact → mechanism → cost or where it bites.** Three sentences. Then stop.

A correct one-liner scores *worse* than the same fact plus two sentences, because they asked
"explain" and got "yes".

**Every project answer, six beats, ninety seconds:**

1. **Situation**, one sentence, **with a number.** "Million-scale campaigns took five to six hours."
2. **Constraint** — what made it hard. "Without rewriting a pipeline everything else depended on."
3. **My decision** — and explicitly whose it was. "I wrote the design and the idempotency model."
4. **The boundary** — what the team did. "The Go worker was a colleague's; I specified the contract and reviewed it."
5. **Mechanism**, one technical detail. "Duplicate prevention at the database level, so a retry physically can't double-send."
6. **Result with a number**, then **what I'd change.** "5-6x faster. And I found the false-success bug by profiling, not from an alert — success was being inferred rather than confirmed."

Beats 3 and 4 are what IMC said was missing. **Never describe a system without saying which parts
are yours.**

**Drill:** record yourself on phone, ninety seconds, one project. Play it back. If you can't hear
beats 3, 4 and 6 — do it again. Five projects, five recordings. That is the whole exercise.

---

# 2. `logger.error` vs `logger.exception`

> "`logger.exception(msg)` is exactly `logger.error(msg, exc_info=True)` — same ERROR level, but it
> attaches the **current exception's traceback**. So it only makes sense **inside an except block**;
> called anywhere else it logs the traceback as `NoneType: None`, which is a giveaway in logs that
> someone used it wrong.
>
> `logger.error(msg)` records the error condition with **no stack**. I use it for an error that
> isn't an exception, or an exception I've fully handled and deliberately don't want a stack for —
> a 404 from a dependency I retry, where a traceback per occurrence is just noise.
>
> The anti-pattern I actually look for in review is `except X as e: logger.error(f"failed: {e}")`.
> That throws away the traceback and keeps only the message, so you know what broke and have no
> idea where. `logger.exception("failed")` is the fix, and `exc_info=True` works on any level if
> you want a stack at WARNING."

---

# 3. Third-party rate limiting in a FastAPI integration

This is the answer he already owned. Layered, cheapest first.

> "First, **respect the contract rather than guessing**: on a 429 read `Retry-After` and honour it,
> and if they publish `X-RateLimit-Remaining` and `Reset`, throttle off those instead of waiting to
> be told. Guessed backoff against a published budget is how you get rate-limited harder.
>
> Second, **don't hit the limit at all** — a token bucket in front of the client. Single process,
> that's a small limiter plus an `asyncio.Semaphore` to bound concurrency. But the limit is
> **global to the integration, not to the process**, so on more than one pod the counter has to be
> shared — Redis, with the check-and-decrement atomic, a Lua script or `INCR` with an expiry, so two
> pods can't both believe they have the last token.
>
> Third, **retries with exponential backoff and jitter**, capped. Jitter matters because
> synchronised retries reconverge into the next burst. Retry 429 and 5xx, never other 4xx, and only
> where the operation is idempotent — otherwise send an idempotency key so their side dedupes.
>
> Fourth, if the work doesn't have to be synchronous, **decouple it**: accept the request, put it on
> a queue, and have one consumer drain at the permitted rate. That turns a latency problem into a
> throughput problem and makes the rate limit a property of a single consumer rather than of every
> request handler.
>
> Then the FastAPI specifics: one `httpx.AsyncClient` created in the **lifespan** and injected as a
> dependency, not per request, so the connection pool is reused; **explicit connect and read
> timeouts on every call**, because no timeout is how one slow dependency becomes your outage; and a
> circuit breaker so when they're down you fail fast instead of queueing. Metrics on 429 rate, retry
> count and time spent waiting, because that's what tells you the limiter is mis-tuned.
>
> And the reason I'm confident about the shape: **I've built this.** The governance engine in front
> of our send path does exactly this problem — a shared budget, many concurrent consumers, must
> never overspend the cap, must be auditable afterwards. I used optimistic locking on a versioned
> row rather than Redis because I needed the audit trail of which version made which decision.
> Swap 'messages per user per day' for 'requests per second to a vendor' and it's the same system."

`slowapi` limits **inbound** traffic to your own API — mention it only to show you know the
difference, because the question was about **outbound**.

---

# 4. Kafka fundamentals — the gap that embarrassed the prod experience

Learn these nine. Each is one sentence, and together they are the whole "fundamentals" answer.

1. **Partitions are the unit of both parallelism and ordering.** Ordering is guaranteed *within a partition*, never across a topic.
2. **The key decides the partition** — `hash(key) % partitions`. Same key, same partition, therefore ordered. No key, and it's spread round-robin, so you've given up ordering.
3. **Offsets** are per-partition and monotonic. The consumer commits them; the committed offset is just "where to resume".
4. **A consumer group** gets each partition assigned to exactly one member. So **more consumers than partitions leaves consumers idle** — partition count is your parallelism ceiling, and you can't reduce it later.
5. **Rebalancing** reassigns partitions when membership changes. The classic production failure: processing takes longer than `max.poll.interval.ms`, the broker declares the consumer dead, a rebalance starts, the replacement is also too slow — a rebalance loop where throughput goes to zero. Fix by making the handler faster, reducing `max.poll.records`, or moving work off the poll thread.
6. **Delivery semantics.** Commit *after* processing → at-least-once → **duplicates, so consumers must be idempotent**. Commit *before* → at-most-once → loss. Exactly-once needs the idempotent producer plus transactions, and only holds for Kafka-to-Kafka.
7. **Durability** is `acks` plus ISR. `acks=all` with `min.insync.replicas=2` means a write is acknowledged only once it's on two replicas. `acks=1` loses data on leader failure, and `unclean.leader.election.enable=true` loses it by design.
8. **Retention vs compaction.** Retention drops old records by time or size; **log compaction keeps the latest value per key forever**, which is what makes a topic usable as a changelog or state store.
9. **Producer batching** — `linger.ms` and `batch.size` trade latency for throughput. And `max.in.flight.requests.per.connection > 1` with retries **can reorder messages** unless idempotence is enabled.

**Then connect it to the prod story** — that is what was missing:

> "The incident we had was [X]. In fundamentals terms that was a [consumer lag / rebalance loop /
> partition skew from a bad key / poison message with no DLQ] problem, and what it taught me is
> that consumer lag per partition is the metric that matters, because an aggregate lag figure hides
> one hot partition."

**Consumer lag per partition** is the single most useful thing to name unprompted.

---

# 5. Carry it forward — Manychat is the live one

Their decision is due **roughly 2026-09-22 to 2026-09-29**. They already said the Founding
Engineer profile was a slight mismatch but they were considering **Senior or Tech Lead** instead.

**Every one of IMC's four criticisms would hurt there too**, and one of them is worse at Manychat:
*"stakeholder communication"* was IMC's phrase, and a Tech Lead framing raises that bar, not
lowers it. So beats 3, 4 and 6 of the project protocol are the thing to drill this week.

Manychat's domain is **billing**, and he has the directly relevant system. Do not repeat the IMC
mistake of failing to connect the owned system to the question asked.

## What actually changed for the pipeline

Nothing structural. 27 applications, one rejection at the final gate after passing a take-home
that they praised, on a req that openly said financial-data experience was mandatory. The
correctable part is correctable.
