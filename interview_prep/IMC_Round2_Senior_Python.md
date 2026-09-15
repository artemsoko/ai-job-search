# IMC Round 2 — 60 min, two Senior Python Engineers

**Company:** IMC Trading · **Role:** Python Software Engineer, Amsterdam
**Req:** https://job-boards.eu.greenhouse.io/imc/jobs/4630983101 (applied 2026-08-12)
**Stage:** take-home passed 2026-09-09 → this round. Date: _fill in_.

IMC's own description of this round, verbatim:

> • To a large extent it will be technical. We would like to hear about your experience, the
> technical challenges you have faced and the choices you made. You might be challenged on some
> parts of your solution to the home assignment. You can also expect some Python related
> technical questions.
> • We would also like to hear about your experience on a more functional level: how did you
> work, what was your specific contribution, with whom and how did you interact, in which areas
> were you perhaps pro-active? etc.
> • Your motivation may be discussed: what drives you, what do you enjoy, what do you dislike,
> what is important to you in your work.

**Who you are talking to matters.** Not a recruiter and not a lead — two peers. They are deciding
"would I want this person reviewing my MRs". That changes the register: less narrative, more
specifics, and it is fine to say "I don't know, here is how I'd find out". With peers, the
failure mode is overselling, not underselling.

**Rough budget for 60 min:** ~10 experience overview, ~15 assignment challenge, ~15 Python
questions, ~10 functional, ~10 motivation + your questions. Keep the opener to 90 seconds or you
will eat the Python block.

---

# BLOCK A — the assignment challenge

**Primary source: `IMC_TakeHome_Defence.md`. Read it fully, it is the deep version.** This block
is only the delta found on a second pass over the actual submitted folder
(`~/Downloads/imc_task`, byte-identical to the copy already reviewed).

## Open with the concession, unprompted

Re-verified against your real code today — greedy gives 4, the optimum is 3:

```
balances A=-4 B=-3 C=+2 D=+2 E=+3
your code (4):  A->E 3 | B->C 2 | A->D 1 | B->D 1
optimum   (3):  B->E 3 (={B,E} nets to zero) | A->C 2 | A->D 2
```

> "Before you pick at it, let me flag the one thing I'd change. The README says 'fewest bank
> transfers' and that is an overclaim. Greedy biggest-debtor-pays-biggest-creditor guarantees at
> most n−1 per product and is optimal when no proper subset of the balances nets to zero — but
> the true minimum is n_nonzero minus the number of disjoint zero-sum subsets, which is
> set-partition, so NP-hard. `A=-4, B=-3, C=2, D=2, E=3` gives 4 with my code where 3 is
> possible. At 2.3 million records collapsing to 5,702 transfers I'd still choose greedy, but
> the wording should have said 'at most n−1'."

### NEW — the overclaim is in two places, not one
`pyproject.toml:4` also says `description = "Nets portfolio transfers down to the fewest bank
account transfers"`. If you concede the README, concede both in the same breath — otherwise it
looks like you only fixed what they found.

### NEW — what you actually shipped in the zip
The archive contains `.idea/` (including `workspace.xml`), `.mypy_cache/`, `.pytest_cache/`,
`.ruff_cache/`, and there is **no root `.gitignore` and no git history**. Your `.dockerignore`
excludes all of it, so you clearly thought about it for the image and not for the deliverable.

If it comes up — and unzipping is the first thing a reviewer does:

> "Fair. `.dockerignore` covers the image but I never added a root `.gitignore`, so IDE and tool
> caches went out with the zip. I also sent it as a plain archive rather than a repo, so you
> can't see the commit history — and history is part of how you'd judge whether the work is
> mine. Both are hygiene misses, not design ones, but they're the first thing you saw."

Do not volunteer this one first. Lead with the algorithm concession (that shows depth); this one
only shows tidiness, and raising it first makes you look small-bore.

### mypy — the precise, honest status
`mypy = "^1.13"` is in dev-deps. `.mypy_cache/3.13/` exists, so it was run. But: **6 functions in
`app/`, zero parameter or return annotations**, no `[tool.mypy]` section, no `typecheck` target in
the Makefile, and `.pre-commit-config.yaml` runs ruff only. `[tool.ruff.lint]` selects
`E,F,I,UP,B,SIM,RET,C4,G` — no `ANN`. So mypy passing proves nothing.

> "mypy ran clean, but with no annotations that's vacuous — it's a declared standard the code
> doesn't meet. The place annotations would actually earn something is `get_balances`: it takes
> an iterable of 4-tuples of `str | None` and returns a nested defaultdict, and none of that is
> visible in the signature. I'd make the record a NamedTuple and turn on `ANN` in ruff."

### The asymmetry they are most likely to notice
You **stream the input and buffer the output**. `read_records` is a generator with `root.clear()`;
`save_output` builds the whole `Trsfs` tree in memory and calls `ET.indent(out)` before writing.

> "Deliberate, and the numbers justify it: 2.3 million records in, 5,702 transfers out — three
> orders of magnitude. Streaming the write would also mean a partially written bank-transfer file
> if the parse dies halfway, and I decided all-or-nothing is the right failure mode there. My
> tests assert it — `assert not output.exists()` on both error paths. If the output ever
> approached the input's size I'd switch to incremental write plus write-to-temp-then-rename."

Second-order version of the same question: *"so streaming didn't actually bound your memory?"*

> "Correct — `iterparse` plus `root.clear()` bounds the parse tree, not the result. The balances
> dict is O(products × accounts with a non-zero position), which is small and independent of
> record count. That's why 2.3 million records fit in 29 MB. The 213 MB comment in `files.py` is
> what happens with the tree alone."

### Remaining items — see the defence doc for full answers
Unguarded `Qty` parse (missing tag → bare `TypeError`; `abc` → `InvalidOperation`; **negative Qty
on BUY accepted silently and flips the sign**) · `max(owed, key=owed.get)` is O(n²) per product,
heap needs lazy deletion, not worth it at this n · `Decimal` 28-digit context detected but not
handled → scaled integers (`int(Decimal(qty) * 10**6)`) are the right fix · Docker runs as root,
no `USER` · `uuid4` makes output non-diffable · `__main__.py` calls `main()` at import time with
no `if __name__ == '__main__'` guard · `logger.info('Read %d records')` only fires if the
generator is fully consumed.

### Two things to make sure you get credit for
They may not ask. Volunteer them.

1. **`test_random_vectors`** — 2,000 seeded random balance vectors, asserting positions are
   preserved by replay (`positions_kept`), the n−1 bound holds, every quantity is positive and
   no self-transfers. That is property-based testing by hand. Say so: *"the invariant I care
   about isn't the exact transfer list, it's that replaying the output onto the input cancels to
   zero. That's what I asserted."*
2. **`test_decimal_precision_is_caught`** — you went looking for the failure mode of your own
   chosen type and wrote the test that documents it. Then have the fix ready (scaled ints).

Also worth one sentence each if the code is on screen: `zip(..., strict=True)` (3.10+, catches
length mismatch instead of silently truncating), and `f'{quantity:f}'` in `save_output` — because
`str(Decimal('1E+3'))` would have sent the bank an exponent. That comment is already in the code;
point at it.

---

# BLOCK B — Python technical questions

This was the real gap in your prep: the other files list topics, not answers. Two senior Python
engineers will go two questions deep on whatever you open. The pattern that works with peers:
**mechanism → cost → when it bites me in production.** Third clause is what separates you from a
candidate who read a blog post.

## Where they will start, because your own code invites it

**"Why `defaultdict(lambda: defaultdict(Decimal))`?"**
> "Two-level grouping keyed by product then account, and I want `+=` on a key I've never seen. The
> inner factory is `Decimal` because `Decimal()` is zero. The lambda is needed because
> `defaultdict` takes a zero-arg callable and `defaultdict(Decimal)` as the outer factory would
> give me a Decimal, not a dict. The cost is that a read of a missing key **inserts** it — which
> is why I convert with `dict(balances)` in the error message rather than probing it, and why I
> iterate `.items()` instead of testing membership."

Follow-up they like: *"so what's the bug defaultdict causes most often?"*
> "Silent key creation during a read — a `if d[k]` check grows the dict. And it doesn't pickle
> with a lambda factory."

**"`Decimal` vs `float` vs `int` here."**
> "Quantities have six decimal places and I compare the sum against exactly zero, so binary float
> is out — `0.1 + 0.2 != 0.3` and the residue accumulates over 2.3 million additions. `Decimal`
> is base-10 exact within its context. The catch I found and tested: the default context is 28
> significant digits, so `1e30 + 0.000001` rounds and the zero-sum check starts failing for
> reasons that have nothing to do with the data. The better choice for a fixed 6-decimal domain
> is integer minor units — exact, no context, and faster, because `Decimal` is a Python object
> with arithmetic in Python-level code while `int` arithmetic is C with small-int caching."

**"Generator vs list in `read_records`."**
> "It's consumed exactly once, immediately, by `get_balances`, so a list would buy nothing and
> cost one live object per record. The generator makes memory O(1) in records. Two consequences I
> accept: it's single-pass, so anything that needs a second look has to re-parse; and my
> `logger.info('Read %d records')` after the loop only fires if the generator is exhausted — true
> today, fragile if someone adds an early break. The `records` counter is closure state, which is
> exactly why that log line is fragile."

## The classics, in the order they usually come

**GIL.** Protects the interpreter's internal state (refcounts, object headers) so one bytecode
op is atomic; it does **not** make your logic atomic — `x += 1` is load/add/store and can be
preempted between them. CPU-bound Python does not scale on threads; I/O-bound does, because the
GIL is released around blocking syscalls. So: threads for blocking I/O and C extensions that
release it, multiprocessing for CPU-bound, asyncio for high-concurrency I/O where thread stacks
and context-switch cost dominate. Add the production clause: *"the reason I reach for asyncio
first isn't speed, it's that tens of thousands of in-flight HTTP sends cost me tasks, not
threads."* If they push on 3.13 free-threading: know it exists, is opt-in, and that removing the
GIL makes data races your problem — do not claim you've run it in production.

**`dict` / `set` internals.** Open addressing with probing (not chaining). Since 3.6 the layout
is split: a compact insertion-ordered entries array plus a sparse index array — which is why
dicts are ordered and why deletion leaves a tombstone. Average O(1), worst O(n) when hashes
collide. Resize at ~2/3 load, so `append`-style growth is amortised. Costs worth naming: memory
overhead per entry, and hashability means `__hash__` and `__eq__` must agree — a mutable key
whose hash changes is unfindable. `{1, True, 1.0}` is one element because they hash and compare
equal.

**`is` vs `==`.** `is` is identity, `==` is `__eq__`. Small ints (-5..256) and interned strings
are shared, so `is` sometimes appears to work and then stops. `is` is correct for `None`, for
sentinels, and for enum members. The trap you can name from real code: `nan is nan` is True but
`nan == nan` is False, so `nan in [nan]` is True (list containment checks identity first) — and
`Decimal('NaN')` behaves the same way, which matters in a zero-sum check.

**Mutable default arguments.** The default is evaluated once, at function definition, and bound
to `__defaults__` — so a `[]` default accumulates across calls. Use `None` + assign inside. Same
mechanism, less-known instance: a `@dataclass` field with a mutable default is a `ValueError`,
which is the language forcing `field(default_factory=list)` on you.

**Closures and late binding.** A closure captures the variable, not the value, so
`[lambda: i for i in range(3)]` gives three functions all returning 2. Fix with a default arg or
`functools.partial`. Same cause as the classic loop-variable-in-a-callback bug.

**Context managers.** `__enter__`/`__exit__`; `__exit__` returning truthy **swallows** the
exception, which is the one thing people get wrong. `contextlib.contextmanager` turns a generator
into one, with the teardown after `yield` and a `try/finally` if you want it to survive an
exception. `contextlib.suppress` and `ExitStack` for a dynamic number of resources. Production
clause: *"the reason I care is that a context manager is the only construct that guarantees
release on an exception path, which is how connections leak."*

**Dataclass vs NamedTuple vs Pydantic vs `__slots__`.** NamedTuple: immutable, tuple-indexable,
cheap, good for a record like the 4-tuple in my parse. Dataclass: mutable by default, `frozen=True`
and `slots=True` available, no runtime validation. Pydantic: runtime validation and coercion at a
real per-object cost — right at a system boundary, wrong in a hot inner loop. `__slots__` drops
the per-instance `__dict__` and stores attributes in a fixed array: less memory, faster access,
at the price of no dynamic attributes and care with multiple inheritance.

**Decorators.** A callable returning a callable; `@` is sugar for rebinding the name.
`functools.wraps` copies `__name__`/`__doc__`/`__wrapped__` so introspection and tooling survive.
`lru_cache` pitfalls you can speak to: it keys on the arguments so they must be hashable, it
holds strong references so caching a method keeps `self` alive forever, and it is not
per-instance.

**MRO / `super()`.** C3 linearisation, left-to-right, depth-first, with a parent never preceding
its child. `super()` walks the MRO of the *instance's* type, not the lexical parent — which is
why cooperative multiple inheritance needs every class in the chain to call `super()`.

**asyncio.** One event loop per thread running ready callbacks; any blocking call (a sync DB
driver, `time.sleep`, a CPU-heavy loop, `requests`) stalls every task — that's `run_in_executor`
or a thread. `gather` re-raises the first exception bare and by default leaves siblings running;
`TaskGroup` (3.11+) cancels siblings and raises an **`ExceptionGroup`**, so `except MyError` will
not catch it — you need `except*`. Name that difference explicitly, it is the single best asyncio
signal you can give. Cancellation is a `CancelledError` raised at the next await point, so
cleanup belongs in `finally`, and `asyncio.shield` protects a critical section. Bound concurrency
with a `Semaphore` — *"unbounded `gather` over a million rows is how you DDoS your own
downstream, which is a lesson I have actually paid for on a send path."*

**Memory / GC.** Reference counting frees immediately at zero; a generational cycle collector
handles reference cycles. So `__del__` on an object in a cycle is unpredictable, and `weakref` is
the tool for caches and parent pointers. Tie it to your code: *"`root.clear()` in my parse is
exactly this — `iterparse` keeps every parsed element attached to the root, so the refcount never
drops. 213 MB versus 15 MB."*

**Testing.** Fixtures for setup with scope control, `parametrize` for a truth table,
`monkeypatch` for environment and attributes, `tmp_path` for filesystem work (you used it). Fakes
over mocks — *"a mock asserts how I called a collaborator, a fake asserts what happened. Mocks
make tests that pass while production breaks."* Your `workspace` fixture returning a builder
function rather than a fixed directory is the right pattern and worth one sentence.

## The answer to give when you don't know

> "I don't know that one. My guess is X, but I'd check it in the docs / with a quick REPL test
> rather than commit to it."

With two senior engineers this scores better than a confident wrong answer, and it is the
behaviour they are hiring for. **Never** guess and assert.

---

# BLOCK C — experience and the choices you made

They will pick one system and go deep. Offer the **send path** first — it is the strongest and
it is genuinely a high-load correctness story. Keep the OCL governance engine in reserve as the
design story, and the Airflow/profiler work for scale.

Full narratives are in `IMC_Recruiter_QA_Cheatsheet.md`. **Do not reuse that version verbatim** —
it is pitched at a recruiter. With engineers, compress the setup to two sentences and spend the
time on the mechanism.

## Send path — the engineer-grade version
Setup: the email and push send path lived inside the existing MarTech pipeline. Million-scale
campaigns took 5-6 hours; the system reported some deliveries as succeeded when they had failed.
Constraint: no big-bang rewrite of a pipeline everything else depended on.

What you did, in mechanism terms: split the path into a Go worker plus a Python executor, pushed
duplicate prevention and idempotency **down to the database level** so a retry physically could
not double-send, and rolled out behind **DB-backed feature flags** so it could be reverted per
segment rather than all at once.
Result: **5-6x faster (measured on TEST)**, million-scale campaigns ~5-6h → ~1h, **push
throughput 8-10x**, and the false-succeeded class of bug eliminated.

Drill-downs to have loaded:

- *"Why idempotency at the DB level and not in the app?"* → "Application-level dedup needs a
  distributed lock or a cache that is itself a consistency problem, and it fails exactly when you
  need it — a process dying between 'marked sent' and 'sent'. A unique constraint on the logical
  send key makes the double-send impossible rather than unlikely, and the database is already the
  thing I trust. The cost is that the insert can fail and the code has to treat a constraint
  violation as success, not as an error."
- *"What was actually slow?"* → be honest about what you measured versus what you assumed. The
  reflection that lands: **"success was being inferred rather than confirmed."** Since then you
  treat "how do we know this actually happened" as a design question, not an observability
  afterthought.
- *"You said Go."* → the honest line, every time: "Python is my language, ten years. The worker
  was Go and I wrote the technical design, specified the contract and reviewed it, but I would not
  call myself a Go engineer, and I'd rather tell you now than have it surface later. Java I can
  read, I don't write it." Never let this drift into a claim.

## OCL governance engine — the design story
Real-time caps, consent, quiet hours and holdout evaluated **before** send. The pieces that are
interesting to engineers: **optimistic locking with a CAS versioned row** for quota accounting,
idempotent decisions, and a window-aware DELAYED-then-promote path for quiet hours. You authored
the spec and design from the PRD and own most of the code. TEST-ready; production was scheduled
for Q3.

- *"Why optimistic locking and not a lock or a counter?"* → "Contention is real but not extreme,
  and a pessimistic lock on a hot row serialises the whole send path. CAS on a versioned row
  gives me a bounded retry and, crucially, an **auditable** record of which version made which
  decision. A bare atomic increment is faster and tells you nothing about why a message was
  blocked — and 'why was this blocked' is the actual requirement."
- *"Why a service in front of the pipeline rather than inside it?"* → "Inside was faster to ship
  and would have coupled a compliance concern to a throughput concern permanently. In front meant
  more moving parts, but caps, consent and quiet hours became independently testable and
  independently deployable."
- The bridge sentence, and say it here: **"swap 'frequency cap' for 'position limit' and it is
  structurally the same problem."**

## Scale story
User-profiler migration to Airflow automation, ~6 runs a day with Slack alerting, unlocking
**~10x audience scale to ~20M users**; you became owner of `mi-ares-airflow`.

## The financial-data gap — raise it yourself
The req says *"Experience working with financial data is a must."* Do not wait to be caught.

> "I should be straight about the one requirement I don't meet on paper. Ten years of high-load
> Python in regulated fintech, but on the CRM and communications side — I have never worked with
> order books or tick data. What transfers is the shape: decisions that must be auditable,
> idempotent and provably correct under concurrency, millions of events a day, and being wrong
> costs money rather than looking bad. The market data itself would be new, and that is honestly
> part of why I want this."

With engineers, add the concrete: the take-home *was* financial data — a 2.3-million-record
settlement file where the zero-sum invariant is the whole correctness argument, and where you
went and found Decimal's context limit yourself.

---

# BLOCK D — functional level

Their exact words: *"how did you work, what was your specific contribution, with whom and how did
you interact, in which areas were you perhaps pro-active?"* That is four questions. Answer all
four — most candidates answer one.

## "What was your specific contribution, versus the team's?"
Be precise about the boundary. Overclaiming is the fastest way to fail a reference check, and
peers can smell it.

> "On the send path: the design and the critical path were mine — the technical design document,
> the DB-level idempotency model and the rollout strategy. The Go worker was built with the
> colleague who owns that service; I specified the contract and reviewed the implementation. The
> two engineers I lead picked up migrating the older campaign types once the pattern was proven.
> On the governance engine I'm the spec author and the code owner of most of it."

Also have the honest boundary ready: **you did not build the transactional-email backend from
scratch.** You built separate services, the governance engine, and major performance and
reliability rewrites on top of the existing pipeline. Say that if asked what you inherited.

## "How did you work / with whom?"
- Wrote the spec and design from a PRD → so: product and stakeholders, not just tickets.
- **Acting tech lead for ~6 months**, including a stretch as the solo backend engineer.
- **348 MRs reviewed, 200+ authored.** PR cycle time roughly halved.
- Ran Senior interviews, one hire.
- Currently leads and mentors two engineers; owns onboarding.
- Cross-team: holdout and campaign-goal tracking spans three services and exists so Data and
  Analytics can measure campaign impact — that work was for another team's benefit, not yours.

If they ask about code review specifically (likely — they are the people whose MRs you'd review):
> "At 348 reviews you learn to separate 'this is wrong' from 'this isn't how I'd write it', and
> only block on the first. I leave the second as a comment and let the author decide. What I do
> block on is an untested error path and a missing idempotency guarantee."

## "Where were you pro-active?" — four concrete, unprompted items
1. **The `Hermes` engineering-standards reference repo** — Poetry, Ruff, CI, Alembic. Nobody asked
   for it; it was adopted by 4+ repos. Test coverage on the core service to **73% against a 50%
   goal**.
2. **DB-backed feature flags** — built because the rewrite needed per-segment revert, then reused.
3. **The Segmentation DB secure release pipeline** (TEST → approval → PROD) — a process gap, not a
   ticket.
4. **Found the false-succeeded delivery bug while profiling**, not from an alert — and the fix was
   a design change, not more monitoring.

Pick two, not four. Then stop. The fourth one is the best if you only get one.

## "Tell me about a mistake" / disagreement
> "The false-success bug. I owned that path and I found it by accident rather than by design. The
> lesson wasn't 'add monitoring', it was that I'd let the system infer an outcome it should have
> confirmed."

> "On idempotency I wanted it at the database level and a colleague wanted application-level
> dedup. I wrote both up with the failure modes and we went with the database. If it had gone the
> other way I'd have built it properly and moved on."

---

# BLOCK E — motivation

## "What drives you / what do you enjoy?"
> "Building and designing backend systems, and getting into the details. The part of the job I
> actually enjoy is the part most people call overhead — choosing the data model, setting up the
> tooling so the whole team moves faster, making the failure modes explicit. That's why the
> take-home was fun: the algorithm was twenty minutes and everything around it was the real work.
> And I like a short loop to the person who needs the thing, which is the specific reason your
> posting caught me — everything internal, no external clients, the users sit a few metres away."

## "What do you dislike?" — the trap in this set
Your honest answer is "heavy on-call and support-dominated work". Said carelessly that reads as
*won't support his own code*, which is disqualifying at a trading firm.

Say it as ownership, not avoidance:
> "Work that is structurally reactive. I've been in stretches where the week was other people's
> escalations and nothing I built moved forward — and I don't mean being on call for what I ship,
> which I think you should be. I mean a role where firefighting is the job rather than a signal
> that something needs fixing properly. My instinct with a recurring page is to go remove the
> cause, and I want to be somewhere where that's the expected response rather than a luxury."

Never criticise Capital.com, your manager or your team. Not once.

## "What is important to you in your work?"
> "Technically strong colleagues — I want to be the person learning in the room at least some of
> the time. Real development work rather than maintenance. And a calm, geeky environment; I do my
> best work where the default is to get the detail right rather than to ship and see."

## "Why IMC / why leave?"
> "The work in the posting is close to what I already do — high-load async Python, deterministic
> logic, auditability — pointed at a harder domain. And relocating to the Netherlands with my
> family is a deliberate decision: my daughter would go to school in English, my wife works in QA
> and that market works for her. Nothing is wrong at Capital.com. I want the next step to be a
> harder technical domain rather than more of the same, and those two things point at the same
> move."

Market-maker literacy, one paragraph, in case it comes up: IMC earns the spread by being
consistently present on both sides of a market and providing liquidity, rather than by predicting
direction — which is why latency and correctness are business problems there rather than
engineering preferences. If they go deeper into options or greeks: *"that's beyond what I know
today and I'd rather say so than guess."*

---

# Questions to ask them

They are engineers. Ask engineering questions, and ask ones that only they can answer.

1. "What did you actually look at in my submission, and what would have made you more
   comfortable?" — best question in the set. Direct feedback from the two people who reviewed it.
2. "What does a Python service in your stack look like at the boundaries — where does Python stop
   and C++ start, and how do the two talk?"
3. "How much of your week is new development versus extending something that exists? And who
   decides what gets built?"
4. "What is the testing culture concretely — are there services you'd deploy on a green pipeline
   alone, or is there always a human gate?"
5. "The posting says no external clients and the users are internal. What does that change day to
   day — what do you get to do that you couldn't at a product company?"
6. "What's the thing about working here that took you longest to get used to?"

Cut anything the recruiter already answered — asking twice signals you weren't listening.

**Do not** negotiate salary in this round, and do not ask about levelling here. These are peers,
not the decision-makers on either. Levelling goes to Riccardo or to the Technology Lead in the
final round. (Anchor for later: Amsterdam median total ~EUR 145k; target total EUR 160-175k with
base the majority; red line on base EUR 110k.)

---

# The hour before

1. **Re-read `balances.py`, `files.py`, `run.py` line by line, out loud.** Every line needs a
   reason. "The tool suggested it" is an automatic fail — and you use Claude Code daily, so this
   is the real risk in this round.
2. **Re-read `tests/test_transfers.py`.** They will ask what you chose not to test.
3. Say the counterexample out loud twice: `A=-4, B=-3, C=2, D=2, E=3` → greedy 4, optimum 3.
4. Have the numbers on a card: **2,325,046 records → 5,702 transfers, 8s, 29 MB. 17 tests, 121
   lines of app code, stdlib only.** And: 5-6x / 8-10x / 20M / 348 MRs / 73%.
5. If you have twenty spare minutes, actually annotate the six functions and add a `typecheck`
   target to the Makefile. It kills the mypy criticism outright and it is a legitimate thing to
   mention: *"I fixed that after I sent it."*

## Three things not to do
1. Don't defend "fewest". Concede it first, in both files.
2. Don't inflate Go or Java. Read-only, every time.
3. Don't manufacture enthusiasm for markets. Honest curiosity beats rehearsed passion, especially
   with engineers.

---

After the interview: `/outcome IMC` to log the stage and anything they said — it sharpens the
final-round prep (`IMC_Coding_Station_Plan.md`, `imc_drills/`).

---

# STORY SELECTION — decided in the 2026-09-13 mock, read this before anything else

**The opener must be Python you wrote with your own hands.** Two Senior Python Engineers will ask
*"which part did you write?"* within about thirty seconds of anything you describe, and the answer
has to be "that code is mine, in Python" without qualification.

## Do NOT open with the Debezium / CDC pipeline
It is the most interesting-sounding thing on your plate and it is **implemented in Java by another
team — you did not write it.** Leading with it means the first drill-down of the interview lands on
work you cannot claim in the language they are hiring for. Burned time plus the impression that you
reached for the shiniest story rather than your own.

**Where it belongs instead: Block D, "with whom did you interact / where were you pro-active".**
There it is genuinely strong — you own the design of a cross-team pipeline that another team
implements in a language that isn't yours. Say it exactly that way:

> "I'm the design owner on a change-data-capture pipeline — Debezium off the user tables into
> Kafka, consumer runs the calculation, then we aggregate and fan out to three services. The
> implementation is Java and it's another team's code; my part is the design, the event contracts
> and the review. I mention it because most of my week is that kind of work now — the interesting
> problems are in the seams between services rather than inside one of them."

That is an honest, senior answer and it costs you nothing.

## The Python spine to lead with instead
Ordered. Everything here is Python you wrote or own.

1. **The messaging platform — millions of messages a day.** You know it cold and you wrote parts of
   it in Python. This is the opener: it gives scale in one sentence and it is unambiguously yours.
2. **The send-path rewrite.** Be precise about the boundary, because it is not pure Python: the
   **Python executor and the DB-level idempotency / duplicate-prevention model are yours**; the Go
   worker was built by the colleague who owns that service, and you wrote the design, specified the
   contract and reviewed it. State that split *before* they ask — 5-6x faster, million-scale
   campaigns ~5-6h → ~1h, push throughput 8-10x, false-succeeded bug eliminated.
3. **The OCL governance engine.** Spec/design author from the PRD, code owner of most of it.
   Optimistic-locking CAS quota, idempotent decisions, window-aware DELAYED-then-promote.
4. **User-profiler migration to Airflow** — ~6 runs/day, ~10x audience to ~20M users, you own
   `mi-ares-airflow`.
5. **The Hermes engineering-standards repo** — Poetry/Ruff/CI/Alembic, coverage to 73% against a
   50% goal, adopted by 4+ repos. Unambiguously Python and unambiguously proactive.

## The sentence that protects you all round
Say it once, early, unprompted, and never let it drift:

> "Python is my language — ten years, and by far my strongest. I work alongside Go and Java and
> I design and review services in both, but I don't write them, and I'd rather tell you that now
> than have it surface later."

---

# VERIFIED 2026-09-15 — yes, they really do discuss the assignment in this round

Artem asked whether the "you might be challenged on your home assignment" line is real or boilerplate. Searched it. Both are true: the sentence is boilerplate, and it happens anyway.

**First-hand, senior SDE, IMC Amsterdam** ([aikikode.me](https://aikikode.me/blog/interview-preparation-2022/)) — describing exactly this stage:

> "Discussed the home assignment, talked about Python experience in general and some dive-into knowledge."

Three-for-three against the email Artem received: assignment, Python experience, deep-dive. Same author on the assignment itself: *"I spent about 10-15 min coding the main algorithm and then about 5 hours wrapping it into proper command line tools, Docker, writing unittests, Makefile and documentation."*

**The wording is from IMC's standard deck**, which is public on [Scribd](https://www.scribd.com/document/800068203/IMC-Python-Process-Overview-and-Introduction-Deck) — search snippets quote it verbatim, identical to the email. So it is a template, not a comment on his submission. Still: the account above confirms the discussion is real, and the deck is the same document that correctly predicted every other stage.

**A Python question actually asked in an IMC Amsterdam technical round** ([Taro, June 2024](https://www.jointaro.com/interviews/companies/imc-trading/experiences/software-engineer-amsterdam-june-1-2024-no-offer-negative-a0e1b0be/)): *"What is the difference between threading and multiprocessing?"* → straight into the GIL answer already in Block B. Lead with the production clause: asyncio first for high-concurrency I/O because tens of thousands of in-flight sends cost tasks, not thread stacks.

**Register: discussion, not interrogation.** Consistently reported as friendly — aikikode calls the whole set *"more of a discussion with colleagues rather than an exam"*, and Glassdoor reports interviewers giving hints when candidates stall. What they weight ([Glassdoor](https://www.glassdoor.com/Interview/IMC-Trading-Software-Engineer-Interview-Questions-EI_IE278100.0,11_KO12,29.htm)): *"justifying choices made and not just coding out solutions, where reason matters more than just doing"*, and *"expect to defend technical decisions from past projects"*. No account anywhere describes a line-by-line code audit.

**Two calibration notes.** Most public IMC data is other roles or other regions — HackerRank OA, C++, Java, and the older visitor-pattern Rock-Paper-Scissors assignment. Artem's was the portfolio-to-bank-transfer problem, so the assignment set has rotated; old "the game" accounts describe the previous variant. (One [1Point3Acres thread](https://www.1point3acres.com/interview/thread/1109367) is indexed as a Python "stock transfer problem" — same shape as his — but the page 403s, so that is unverified.) Average process length is reported at ~22 days.

## What Python questions do they actually ask? — searched 2026-09-15

**Honest answer: there is no public list, and that is itself the finding.** Across Taro, Glassdoor, aikikode and the aggregator guides, only a handful of concrete IMC questions are reported, and they are fundamentals rather than trivia. Do not spend the remaining prep time on a quiz deck.

**Actually reported, IMC-specific:**

| Question | Source |
|---|---|
| *"What is the difference between threading and multiprocessing?"* | [Taro — SWE, Amsterdam, Jun 2024](https://www.jointaro.com/interviews/companies/imc-trading/experiences/software-engineer-amsterdam-june-1-2024-no-offer-negative-a0e1b0be/) |
| *"Questions about threading, memory allocation, and explaining a stack to a non-technical person"* | [Taro — SWE Graduate, Chicago](https://www.jointaro.com/interviews/companies/imc-trading/experiences/software-engineer-graduate-chicago-illinois-february-1-2021-no-offer-positive-18b60ecd/) |
| *"Define binary search to a non-CS person"* | [Glassdoor — Amsterdam](https://www.glassdoor.com/Interview/IMC-Trading-Amsterdam-Interview-Questions-EI_IE278100.0,11_IL.12,21_IM1112.htm) |
| OOP design, where *"developers keep asking questions about your implementation as you write the code"* | Glassdoor — Amsterdam |
| *"language-specific questions (C++ memory model, **Python performance**, etc.)"* | [techinterview.org](https://www.techinterview.org/companies/imc-trading-interview-guide/) |

**So the evidence points at exactly three areas, and two of them repeat:**
1. **Threading vs multiprocessing vs asyncio, and the GIL** — the only question reported twice. Must be automatic. Block B has the answer; the production clause matters more than the definition.
2. **Memory** — reference counting, the cycle collector, what actually holds objects alive. His own `root.clear()` / 213 MB → 15 MB story is the perfect vehicle and he should steer here.
3. **Explaining something technical to a non-technical person** — asked in two different forms (stack, binary search). Worth rehearsing once: no jargon, one analogy, thirty seconds.

**What replaces trivia: depth on his own code and his own systems.** IMC's own document says *"We are not evaluating how well you know this language at this stage, but rather how well you can apply the concepts."* aikikode's account of this exact round is *"discussed the home assignment, talked about Python experience in general and some dive-into knowledge"* — a conversation, not a quiz.

**The most useful single sentence found in the whole search** — a Python Engineer describing IMC's coding round as *"non-adversarial"*, where the point is *"seeing if you can take feedback"* ([Taro — Python Engineer, Sydney, Apr 2025](https://www.jointaro.com/interviews/companies/imc-trading/experiences/python-engineer-sydney-australia-april-23-2025-no-offer-positive-0e5f97cb/)). That reframes the whole assignment block: **when they push on his code, the graded behaviour is how he responds, not whether he was right first time.** Conceding "fewest" is therefore not damage control — it is the thing being measured.

Same source on the later coding station: 30 min pre-reading, ~1h coding after a design discussion, ~1h post-discussion and optimisation with *"curve-ball handling"*. One other report names the station task as building **a matching engine for a trading system** — which is the order-book drill in `imc_drills/`, so that drill stays priority one for the final round.
