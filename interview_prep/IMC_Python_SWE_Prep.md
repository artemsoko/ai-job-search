# IMC Trading — Python Software Engineer (Amsterdam). Express prep

Applied 2026-08-12. Req: https://job-boards.eu.greenhouse.io/imc/jobs/4630983101
Median comp signal: ~EUR 145k. No external clients ("no non-sense requests"), so no on-call circus.

## Good news first: this format suits you far better than LeetCode

The 2-hour station is NOT a blank-editor algorithm grind. From a first-hand senior-SDE
account of IMC Amsterdam (aikikode.me, 2022):

- You get **5-10 min to read the task document** yourself.
- The interviewer then **walks you through the requirements**.
- You get a **10-minute independent thinking break, and you may Google / search during it**.
- You **discuss and refine the approach with the interviewers** before writing code.
- You code in a **shared PyCharm instance that already contains failing unit tests**.
  Direct quote: *"Pre-defined unittests here help a lot, you can go and 'fix' them one by one,
  implementing missing pieces of logic."*
- IMC's own doc: *"You are not expected to know the answer right away nor necessarily solve
  the problem during the time provided."*

So it is a TDD-shaped, conversation-heavy exercise with search allowed. That is much closer to
how you actually work than Nebius' closed-book notepad round.

Difficulty is reported as **"still about medium LeetCode complexity"** — not hard.

## The four things they actually score

1. **Production-readiness** (home assignment). The algorithm is trivial on purpose.
2. **Reasoning out loud** (coding station). Clarifying the problem and justifying decisions.
3. **Data-structure vocabulary** (coding station). Fluency, not implementation.
4. **Depth on your own past work** (technical interview with two tech leads).

---

## Stage 1: home assignment — "another simple game", 3 days, ~5h typical

Reported task: a **Rock-Paper-Scissors** style game, one account says they were asked to use the
**visitor pattern**. Expect a variant, not that exact task ("another simple game").

The trap: *"The logic there is very simple, but the target is to make it production-ready."*
One candidate spent **10-15 minutes on the algorithm and ~5 hours on everything around it**:
CLI, Docker, unit tests, Makefile, documentation.

IMC's own words: *"as if it were for a production system... simple, understandable and
extensible code. **Testing is important to us.**"*

**This is your strongest round. Treat it as the differentiator, not a chore.** Ship:

- [ ] `pyproject.toml` (Poetry or uv), pinned deps, Python version declared
- [ ] Clean Architecture layering: domain (game rules) / application (orchestration) /
      adapters (CLI, IO). Rules must be testable with zero IO.
- [ ] **Extensibility demonstrated**: adding a new move (e.g. Rock-Paper-Scissors-Lizard-Spock)
      or a new player type must require NO change to existing rule code. Say this in the README.
      This is precisely what the visitor-pattern hint is probing: open/closed principle.
- [ ] PyTest: unit tests per rule, a parametrised truth table for all move pairs, one
      end-to-end CLI test. Add coverage output.
- [ ] Type hints everywhere + `mypy` clean. Ruff clean. Pre-commit config.
- [ ] `Makefile`: `make install / test / lint / run / docker-build`
- [ ] `Dockerfile` (multi-stage, non-root user)
- [ ] `README.md`: how to run, how to test, **design-decisions section with the trade-offs you
      rejected and why**. They challenge your choices later, so pre-arm the answers.
- [ ] Deterministic RNG seam (inject a random source) so the game is testable. Small detail,
      strong signal.
- [ ] Sensible error handling on bad input; no bare `except`.
- [ ] Git history with meaningful commits, not one "initial commit".

Honesty note: you use Claude Code daily. Use it, but **read and own every line** — they will
challenge specific choices and "the tool wrote it" is a fail. IMC's guidance: *"you can Google
or use open source as you go, but make sure the work you do is your own."*

## Stage 2: 60-min interview, two Senior Python Engineers

Covers: your experience and the technical choices you made, a challenge on parts of your
assignment solution, **Python-specific technical questions**, then functional (how you worked,
your specific contribution, where you were pro-active) and motivation.

Python internals to have ready — these are the classic IMC-style probes:
- GIL: what it does and does not protect; threading vs multiprocessing vs asyncio, and when
  each is right. (You have real asyncio/aiohttp production experience — lead with it.)
- `dict`/`set` internals: hashing, collision resolution, why average O(1), amortised resize.
- Mutable default arguments; `is` vs `==`; identity of small ints and interned strings.
- Generators vs lists, memory profile, `yield from`.
- Context managers and `contextlib`; `__enter__`/`__exit__` and exception suppression.
- Dataclasses vs `NamedTuple` vs Pydantic; `__slots__` and why it saves memory.
- Decorators, `functools.wraps`, closures and late binding.
- MRO / cooperative `super()`.
- `asyncio`: event loop, what blocks it, `gather` vs `TaskGroup`, cancellation.
- Testing: fixtures, parametrise, monkeypatch, fakes vs mocks, why you prefer fakes.

## Stage 3: final round, four stations (one day, or two by preference)

Most candidates split it over two days. Take the two-day option — it is offered.

### 3a. Intro to IMC with the Technology Lead (30 min)
Low-stakes. Have two sharp questions ready about the tech landscape.

### 3b. Problem-solving and coding station (2 - 2.5 hours) — the one you fear
Setup: **Python in PyCharm**, shared instance, failing unit tests pre-written.
IMC: *"a problem which simulates a real-world task that an employee at IMC may need to solve...
We are interested in seeing how you clarify the problem and your thought process and the
reasoning behind any decisions."* And: *"We are not evaluating how well you know this language
at this stage, but rather how well you can apply the concepts."*

**Mandatory from IMC's own document** — usage and performance of:
`Dynamic Array`, `Linked List`, `Hash Table`, `Binary Heap`, `Binary Search Tree`.
*"We do not expect you to be an expert on these data structures (i.e. implement one from
scratch) but they should be a major part of your dialogue."*

So you must be able to SAY, unprompted and fluently:

| Structure | Reach for it when | Costs |
|---|---|---|
| Dynamic array (`list`) | index access, append-heavy, cache locality | index O(1), append amortised O(1), insert/delete mid O(n) |
| Linked list (`deque`) | O(1) push/pop at both ends, queue/sliding window | index O(n), no locality |
| Hash table (`dict`/`set`) | membership, dedup, grouping, counting | avg O(1), worst O(n), unordered-by-hash, memory overhead |
| Binary heap (`heapq`) | top-K, streaming min/max, priority scheduling, order book price levels | push/pop O(log n), peek O(1), build O(n) |
| BST / balanced tree | ordered iteration + range queries; `sortedcontainers.SortedDict` in Python | O(log n) search/insert, in-order traversal sorted |

Rehearse the sentence pattern: *"I'd reach for a heap here because I only need the current best
price, not a full sort, so I pay log n per update instead of n log n per query."*

**Drills (do these in PyCharm, not in an editor with an agent):**
1. Order book: add/cancel/match limit orders. `dict` of price to `deque`, plus two heaps for
   best bid/ask. Explain why heap over sorted list. **Most likely shape given the domain.**
2. Top-K by frequency from a stream. `Counter` + size-K heap. Say why not full sort.
3. Sliding-window max over a tick stream. Monotonic `deque`. Say why not a heap.
4. LRU cache. `dict` + doubly linked list, or `OrderedDict`. Explain both.
5. Rate limiter / quota counter. You have SHIPPED this (optimistic-locking quota accounting) —
   connect it out loud.
6. Merge K sorted streams. Heap of iterators.

**Process, not speed.** Do all of this every time, out loud:
- Restate the problem and confirm it back before touching the keyboard.
- Ask about scale, ordering guarantees, duplicates, concurrency, error cases.
- State the naive solution and its cost, then the improvement and its cost.
- Run the failing tests first, read them — they encode the spec.
- Fix one test at a time. Narrate why the current one is next.
- Say your trade-offs aloud, including the ones you reject.
- If stuck, say what you would look up and why. Searching is allowed.

### 3c. Technical interview, two technical leads
Deep dive on your real experience + abstract questions about tech you have used + **results you
achieved**. Bring numbers, they are already verified:
- send path re-architecture: **5-6x faster**, million-scale campaigns from 5-6 hours to about
  one hour, push throughput **8-10x**, eliminated a false-delivery bug
- **10x audience scale to 20M users** via an Airflow profiling pipeline, six runs a day
- governance engine: real-time caps, consent, quiet hours, holdout groups, optimistic-locking
  quota accounting, idempotent decisions
- acting tech lead ~6 months: **348 MRs reviewed, 200+ authored**, coverage on a core service
  to **73%**

### 3d. Possible extra: behavioural + basic trading knowledge
One account describes a mixed STAR + trading round. Their doc does not list it, but be ready.
Minimum market literacy: how a stock trade works, what an option is, **bid-ask spread**, what a
market maker does and why liquidity provision earns the spread. IMC is a market maker providing
liquidity — know that much about the business.

---

## Your two real gaps, and the honest framing

1. **Cold Python in an IDE.** You live in Claude Code. Mitigation: do the 6 drills above in
   PyCharm with the agent OFF. Install PyCharm now — IMC explicitly says *"Basic familiarity
   with PyCharm will give you more time to focus on solving the problem."*
2. **Financial data.** The req says *"Experience working with financial data is a must, ideally
   in the financial services industry."* You are in fintech at Capital.com but on CRM
   messaging, not market data. **Do not claim backtesting or market-data experience.** Bridge
   honestly: regulated environment, auditability, correctness under load, idempotency,
   millions of events a day, consequences of a wrong decision being financial. Then say plainly
   that order books and market data would be new to you and that you want that.

## Levelling — raise it on the first call
The req asks "4+ years"; you have 10+ and lead two engineers. Ask early where this lands on
their ladder, or you risk a mid-level offer on a role whose median is ~EUR 145k.

## Note on conflicting reports
Some sources describe a **120-minute HackerRank with 2 medium/hard problems** for IMC. That does
NOT match the document IMC sent you for this role, which starts with the take-home game. The
HackerRank reports are likely other roles or regions. Prepare for YOUR document; if a recruiter
mentions an online assessment, ask which format.

## Express plan if time is short
1. **Ship the take-home properly.** Highest leverage, and it plays to your strengths.
2. **Say the data-structure table out loud until it is automatic.** Cheapest big win.
3. **Order book drill in PyCharm, agent off.** Most likely problem shape.
4. **Rehearse the four verified achievement numbers as 60-second stories.**
5. Skim options / bid-ask / market making — one hour is enough.
