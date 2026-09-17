# The plan — what to do with each evening

Written 2026-09-17, after the IMC rejection. Revisit after every interview outcome.

## The strategic call: this is a CONVERSION problem, not a volume problem

27 applications produced at least three real processes, and IMC reached the **final gate** with a
take-home they **praised**. The top of the funnel works. The loss happened in the room.

So pushing more applications through without fixing conversion just manufactures more rejections
at the same stage. The scarce resource is evenings, not job listings — and the scrape is already
scripted, so it costs almost nothing to keep the pipeline fed.

## LeetCode is the lowest priority, and for this profile it is a trap

- IMC was **explicitly not** LeetCode — existing code, failing tests, a real-world task.
- Manychat's technical was code *reading*, mutability and async — not algorithms.
- **Not one rejection has been about algorithms.**

Grinding LeetCode while the actual failure mode is articulation is the order-book mistake in
career form: *optimising match throughput while cancel is still a linear scan.*

**Rule: LeetCode only when a named employer has confirmed an online assessment** (Nebius has a
HackerRank OA). Never speculatively.

## Allocation

| Activity | Share of evenings | Cost |
|---|---|---|
| **Depth on his own stack + articulation** | **60-70%** | 30-45 min/day |
| Keep the pipeline fed | ~15% | 30-45 min every 2-3 days, scripted |
| Gap harvest after each interview | small | 20 min, same day |
| LeetCode | **0%** until an OA is confirmed | — |

---

# The weekly rhythm

**Every day, 30-45 min — one topic.** The artifact is non-negotiable: **a three-sentence answer
said out loud and recorded, plus one of his own stories connected to it.** Reading without
speaking does not transfer — that is the exact problem, not a lack of knowledge.

**Twice a week — project recordings.** 90 seconds, phone, one project. Five projects, rotating.
Play it back and check the six beats are audible, especially:
- beat 3: **"my decision"**
- beat 4: **the boundary — what the team did**
- beat 6: result with a number, and what he'd change

**Every 2-3 days, 30-45 min — pipeline.** `./hunt --jobage 7` → `./screen --unassessed` → apply to
whatever passes → `./applied <url>`.

**Same day as any interview — gap harvest, 20 min.** Write down every question that landed badly,
verbatim. And **always ask for feedback on a rejection**: IMC's letter was unusually specific and
is the most valuable artifact of the whole search so far.

**Weekends — one longer block.** A mock, or a drill with the agent off.

---

# Topic order

## Week 1 — the red items from the rejection letter

| Day | Topic | The artifact |
|---|---|---|
| 1 | **Kafka I** — topics, partitions as the unit of ordering AND parallelism, keys, offsets, consumer groups, rebalancing and `max.poll.interval.ms` | 3-sentence "how Kafka works" |
| 2 | **Kafka II** — delivery semantics, idempotent consumers, retry topics, DLQ, backoff tiers, transactions, consumer lag per partition | the prod incident retold **with the model first** |
| 3 | **Exceptions, logging, retries** — `logger.exception` vs `error`, exception chaining, `except*`, backoff with jitter, what is safe to retry | the `except X as e: logger.error(f"{e}")` anti-pattern, explained |
| 4 | **asyncio in practice** — timeouts on every call, bounded concurrency, **outbound rate limiting**, `TaskGroup`/`ExceptionGroup`, not blocking the loop | the rate-limiting answer, ending with "I've built this" |
| 5 | **PostgreSQL deeper** — transactions, isolation levels, locking, `SELECT FOR UPDATE` vs optimistic locking, indexes | why he chose CAS optimistic locking over a row lock |

Day 5 is not remediation — IMC **praised** his database knowledge. Turn a pass into a weapon.

## Week 2 — loaded but never fired

Redis · Celery · **Airflow** (he owns `mi-ares-airflow`, so it will be asked) · Docker/K8s ·
system design (low-latency and real-time data processing were named by IMC).

---

# The two rules that make it stick

1. **Model first, story second.** For every technology on the CV: *how it works*, then *what
   happened to me with it*. He has been doing the reverse, and a war story without the model reads
   as "he got lucky putting the fire out". This is the single sentence that explains the Kafka
   criticism.
2. **More detail is not the fix — structure is.** A rambling long answer fails the same way a
   one-liner does. Technical question → three sentences (fact → mechanism → cost). Project → six
   beats, 90 seconds. Talking five times longer without a shape makes it worse.

---

# Live context, 2026-09-17

- **Manychat is the live process.** Decision due roughly **2026-09-22 to 2026-09-29**; they floated **Senior or Tech Lead** instead of Founding Engineer. Every IMC criticism would hurt there, and *"stakeholder communication"* matters **more** at Tech Lead, not less. Their domain is **billing** and he owns the directly relevant system — do not repeat the IMC mistake of leaving an owned system unconnected to the question asked.
- IMC: **rejected**. Nelly: rejected. 27 applications logged, most silent.
- Relocation target is **2026-07**, so there is runway. That argues for fixing conversion now rather than sprinting on volume.
