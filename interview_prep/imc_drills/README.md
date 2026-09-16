# IMC drills — run these the way the real station runs

IMC's coding station gives you **Python in PyCharm with failing unit tests already written**.
A candidate's own words: *"Pre-defined unittests here help a lot, you can go and 'fix' them one
by one, implementing missing pieces of logic."* So these drills are built the same way: a
skeleton that raises `NotImplementedError`, and a test file that fails until you implement it.

## Rules while drilling (this is the point)

1. **Open in PyCharm. Turn Claude Code and Copilot OFF.** CONFIRMED by the recruiter on
   2026-08-19: **Google is allowed in the station, AI is not.** So reading docs and Stack
   Overflow while you drill is realistic and fine. An agent writing the code is practising
   the wrong thing.
2. **Set a timer.** Drill 1 (order book): 60 min. Drills 2-6: 25 min each.
3. **Talk out loud the whole time**, to an empty room if needed. The station scores your
   reasoning, not your typing. IMC: *"We are interested in seeing how you clarify the problem
   and your thought process and the reasoning behind any decisions that you make."*
4. **Before writing code**, say aloud: restate the problem, ask the clarifying questions,
   name the naive solution and its cost, name your choice and its cost.
5. **Run the tests first and read them.** They are the spec. Fix one at a time.
6. Do NOT open `SOLUTIONS.md` until you have a passing implementation or the timer is done.

## Run

```bash
cd interview_prep/imc_drills
python3 -m pytest drill1_order_book -x -q      # one drill, stop at first failure
python3 -m pytest -q                            # everything
```

## Also confirmed on the recruiter call

The station gives you **existing APIs / code already written**, and **you are expected to dig the
requirements out yourself** — that part is scored. So before each drill, read the test file first
and say the spec back out loud. Run through the clarifying-questions checklist in
`../IMC_Coding_Station_Plan.md` as if a person were there to answer it.

## Order to do them in

| # | Drill | Why | Time |
|---|-------|-----|------|
| 1 | **Order book** | Most likely shape at a market maker. Heap + dict + deque in one. | 60 min |
| 2 | Top-K frequent | Heap vs sort trade-off, the classic "why not sorted()" | 25 min |
| 3 | Sliding-window max | Monotonic deque. Say why NOT a heap. | 25 min |
| 4 | LRU cache | dict + doubly linked list. Two valid answers, know both. | 25 min |
| 5 | Rate limiter / quota | **You have shipped this.** Connect it to your governance engine out loud. | 25 min |
| 6 | Merge K sorted streams | Heap of iterators, streaming not materialising. | 25 min |

## What tasks can actually come up — researched 2026-09-16, tiered by confidence

Aggregator sites mix roles and regions freely, so this is split by how much it can be trusted.

**HIGH — matches his role, region and station format:**
- **Order book / matching engine.** Multiple independent sources, and the format lines up (existing code plus pre-written failing tests, in PyCharm). `drill1_order_book` covers it.
- Confirmed station shape: 5-10 min reading the task, interviewer walkthrough, 10 min thinking with **Google allowed**, approach discussion, then code. First-hand: *"a complex system to build"*, *"still about medium LeetCode complexity"*.

**MEDIUM — reported for IMC, role/region unclear:**
- **Market-maker simulation** — *"write code to simulate a market maker and determine how you would set your bid-ask spread"*. **No drill exists. Highest-value gap**, because it is uniquely IMC-shaped AND it forces the domain knowledge he fumbled in round 2 (spread, inventory risk, skewing).
- **Time-series anomaly detection** over stock prices. No drill.
- **LRU cache** — explicitly reported, and `drill4_lru` already covers it.
- Sharpe ratio as a function; BST insertion; longest substring without repeating characters; grid BFS; "simulation, data-structure design".
- **System design**: *"design a high-frequency trading system to minimize latency"*, *"challenges in real-time data processing"*, multithreading. **IMC mentioned system design to him directly. No prep exists.**

**LOW — other tracks, not his:**
2-D DP and Combination Sum (QR/quant track), Asteroid Collision and similar (the online-assessment pool), Neurolympics and the trading games (trader track), the 120-minute HackerRank with two problems (other roles — already flagged in `IMC_Python_SWE_Prep.md`).

## Drill 1 now has TWO stages — added 2026-09-16 after researching how the question is really run

`drill1_order_book` holds **38 failing tests**, not 19.

- `test_order_book.py` (19) — correctness: matching, price-time priority, maker price, partial fills, cancel, the lazy-deletion trap.
- `test_order_book_stage2.py` (19) — **the follow-ups, which reports say carry half the grade**: arrival-order tie-breaking (fails if you sort a level by order id), market / IOC / **FOK with its two-pass requirement**, `modify` (reducing quantity keeps time priority, increasing loses it), and a timing test that a linear-scan `cancel` fails by a wide margin.

Do stage 1 to green first, then stage 2. Both are verified 38/38 against `solutions/order_book.py`.

**Read `ORDER_BOOK_FOLLOWUPS.md` after you have code that passes.** That is the spoken half:
why cancel must be O(1) and what a tombstone costs, the p99 / array-indexed-by-tick answer,
monotonic sequence numbers instead of wall clocks, FOK's two passes, single-writer-per-symbol
concurrency, and the pre-trade risk bridge to your governance engine.

The finding that should change how you spend the hour: **cancels dominate message volume at a
market maker** — you quote, the market moves, you pull the quote. So cancel is the hot path, not
match. *"Candidates who optimize match throughput but leave cancel as a linear scan have optimized
the wrong end."*

## The sentence you must be able to say without thinking

> "I'd reach for a heap here because I only need the current best price, not a full ordering,
> so I pay O(log n) per update instead of O(n log n) per query."

Swap the nouns. Say it for every structure in `data_structures_drill.md`.
