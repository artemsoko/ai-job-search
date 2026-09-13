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

## The sentence you must be able to say without thinking

> "I'd reach for a heap here because I only need the current best price, not a full ordering,
> so I pay O(log n) per update instead of O(n log n) per query."

Swap the nouns. Say it for every structure in `data_structures_drill.md`.
