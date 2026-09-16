# Order book — the follow-up discussion (half the grade)

Researched 2026-09-16. The order book / matching engine **is** the reported task at IMC, and the
grading is reported as *"roughly half on correctness and half on the follow-up discussion about
cancels and latency."*

The sentence to internalise:

> *"Candidates who optimize match throughput but leave cancel as a linear scan have optimized the
> wrong end."*

Cancels dominate message volume at a market maker — you quote, the market moves, you pull the
quote. Most orders are cancelled, not filled. So **cancel is the hot path, not match.**

---

## 1. "Now make cancel O(1)" — the question behind the question

Reported as the follow-up that *"is the whole point of the question at most desks."*

**The naive version:** the level is a FIFO queue, so cancel means scanning it for the order id.
O(n) in level size, and busy levels are exactly where cancels concentrate.

**The answer:**

> "Index `order_id -> the node itself`, and make the level an intrusive doubly linked list so the
> unlink is O(1) — a hash lookup plus repointing two neighbours. No scan at any depth."

**What I actually did in the drill, and the honest trade-off:**

> "I used a dict from order id to the resting object plus a `deque` per level, and cancel just
> flips a `live` flag and drops the index entry — O(1), no scan. The cost is a **tombstone**: the
> dead node stays in the deque until the match loop walks past it, so `depth()` has to skip
> non-live orders. That's fine when cancels are followed by matches, but if a level accumulated
> millions of tombstones with no trading I'd be walking corpses. A real intrusive linked list
> unlinks immediately and has no tombstone at all — that's what I'd build if this were production."

**If they push on the heap:** *"you cancelled the best price — your heap still holds it."*

> "Lazy deletion. I don't remove from the heap on cancel, because finding an arbitrary element in a
> binary heap is O(n). Instead the heap can hold stale prices, and `best_bid`/`best_ask` prune from
> the top until they find a price whose level still has live quantity. Amortised it's fine — each
> price is pushed and popped once. The alternative is an indexed heap with a position map so you can
> `sift` after a decrease-key, which makes removal O(log n) but adds bookkeeping on every swap."

---

## 2. Latency — "we're seeing p99 spikes on busy names. What changes?"

The reported expected answer, in their terms (`std::map` / TreeMap):

> "A sorted map means pointer chasing — every price level is a separate heap allocation, so walking
> levels is a chain of cache misses, and p99 is dominated by those misses rather than by the
> algorithm. For equities the price domain is small and known: prices are a fixed tick size within a
> band. So index a **contiguous array by tick offset** instead — `levels[(price - base) // tick]`.
> That turns a tree walk into a stride through cache-resident memory: O(1) access, no allocation
> per level, and predictable latency because there's no rebalancing."

**The trade-off to state, because it's the reason nobody does this universally:**

> "You pay memory for the whole band whether or not it's populated, and you need a fallback for
> instruments where the price range is wide or unbounded — options strikes, or anything where the
> band can move. Typically that's a dense array for the active band plus a map for the tails."

**Python-specific honesty:**

> "In Python the constant factors are different — a `dict` is already C and very fast, and I don't
> control allocation or cache lines, so array-by-tick wins much less than it would in C++. If
> latency at that level were the requirement, the matching engine wouldn't be in Python. Where
> Python belongs in this stack is the tooling, the research and the control plane around the
> engine — which is how I read the role."

That last paragraph is a strong answer: it shows you know the limits of your own language rather
than pretending Python is a low-latency tool.

**General levers, cheapest first:** better algorithm/structure → fewer allocations → avoid
pointer chasing → batch and amortise → preallocate and reuse objects → only then rewrite in a
lower-level language. And always: **measure p99, not the mean.** Tail latency is the product.

---

## 3. Sequencing — "two orders arrive at the same price in the same microsecond. Which fills first?"

Reported as a real follow-up. It tests whether you use a **monotonic sequence number** or a clock.

> "A monotonically increasing sequence number assigned at the point of entry into the book, never a
> wall clock. Three reasons. Clock resolution isn't infinite, so two events genuinely can share a
> timestamp and you'd have no tie-break. `time.time()` can go **backwards** — NTP steps, leap
> second smearing — and an order book whose priority can invert is a correctness bug, not a
> latency one. And if orders arrive from multiple gateways, their clocks disagree.
>
> So: one counter, one writer, incremented per accepted order. It's also what makes the book
> **replayable** — feed the same sequence in and you get the same book, which is how you debug a
> production incident. If I did need wall time for reporting I'd use `time.monotonic_ns` for
> durations and keep it out of the priority decision entirely."

**Consequence worth adding unprompted:** a FIFO deque per level gives you sequence ordering for
free, as long as nothing ever re-sorts the level. That's what my
`test_tie_break_is_arrival_order_not_order_id` guards: if you sort a level by order id anywhere,
priority is silently wrong.

---

## 4. Order types

| Type | Behaviour | The trap |
|---|---|---|
| **Limit** | match what crosses, rest the remainder | — |
| **Market** | no price; sweep until filled or book empty | remainder is **discarded**, never rested |
| **IOC** (immediate-or-cancel) | match what crosses at its limit, discard the rest | never rests; partial fill is fine |
| **FOK** (fill-or-kill) | all of it or none of it | **two passes** |

**FOK is the one they ask about:**

> "FOK has to decide before it mutates. A one-pass implementation starts filling, discovers halfway
> that the book can't complete the quantity, and now the book is already mutated and those makers
> think they traded. So: pass one sums the fillable quantity across every crossing level without
> touching anything; if it's short, return no trades and leave the book byte-identical. Only then
> does pass two execute. My `test_fok_leaves_the_book_UNTOUCHED_when_it_cannot_fill` is exactly
> that check."

Also worth naming if the conversation goes there: **post-only** (reject if it would take
liquidity — a market maker's bread and butter, since you want the maker rebate and the spread),
**stop** orders (triggered, not resting in the book), and **iceberg / hidden** quantity.

---

## 5. Concurrency — asked as "how would you handle concurrent operations?"

> "I wouldn't put a lock around the book. The standard shape is **single-writer per symbol**: one
> thread owns one book and everything arrives through a queue, so matching is sequential by
> construction and there are no races on the data structure at all. You scale **horizontally by
> symbol**, not by threading one book, because a lock on the best price level is the one thing every
> order touches — it would serialise anyway, just with cache-line contention on top.
>
> Readers — market data publishers, risk — get a consistent snapshot rather than sharing the live
> structure: either a sequence-numbered ring buffer they tail, or copy-on-write snapshots. And in
> CPython specifically the GIL means threading buys nothing for the matching itself, which is
> another reason the engine shouldn't be Python."

If they ask about ordering across symbols: *"per-symbol ordering is guaranteed, cross-symbol is
not, and that's usually the right contract — anything needing atomicity across two instruments is
a higher-level concern than the book."*

---

## 6. Pre-trade risk — the bridge to your own work

Almost certainly comes up as *"what else would sit around this?"*, and it is the single best place
to connect to the governance engine:

> "Before an order reaches the book you need a pre-trade gate: position limits, order-size limits,
> price sanity checks against a reference, and self-trade prevention so you don't cross your own
> resting quote. It has to be evaluated on the hot path, be idempotent under retries, and be
> auditable afterwards — you must be able to answer 'why was this order rejected' months later.
>
> That's structurally the system I already own. My governance engine sits in front of a send path
> and evaluates caps, consent and quiet hours before anything leaves, with optimistic-locking
> quota accounting so concurrent decisions can't overspend a limit, and idempotent decisions so a
> retry can't double-count. **Swap 'frequency cap' for 'position limit' and it's the same
> problem** — a real-time gate that has to be right every single time and explainable later."

---

## 7. The structure-choice table, said out loud

| Structure | For | Cost |
|---|---|---|
| `dict[(side, price)] -> deque` | the level itself; FIFO at both ends | O(1) push/pop, no ordering across prices |
| two heaps (bid negated, ask) | current best price only | O(log n) push/pop, O(1) peek, **stale entries need lazy deletion** |
| sorted map / balanced tree | full ordered traversal, range queries | O(log n), but pointer chasing hurts p99 |
| array indexed by tick | fixed, known price band | O(1) and cache-friendly; memory for the whole band |
| `dict[order_id] -> node` | **O(1) cancel** | one extra dict; the thing that actually matters |

The sentence to have automatic:

> "I'd reach for a heap here because I only need the current best price, not a full ordering, so I
> pay O(log n) per update instead of O(n log n) per query. And I keep a separate id-to-node index
> because cancels dominate volume and a scan of the level is the wrong cost to pay."
