# IMC take-home — the interviewer challenge, run against your actual submission

Two Senior Python Engineers will *"challenge some parts of your solution"*. Below is that
challenge, done properly. Everything here was verified by running your code, not by reading it.

**Baseline facts, confirmed:** 17 tests, all passing. 121 lines of app code, 216 lines of tests.
Stdlib only. Streaming XML parse. `Decimal` throughout. Docker image builds from `app/` alone.

The submission is genuinely good. It will still get picked at, and there is **one claim in it
that is provably false** — find out from me now rather than from them.

---

## 🔴 1. "the fewest bank transfers" is not true, and it is the first line of your README

Your README opens with:

> *"Collapses a day of portfolio-to-portfolio transfers into the **fewest** bank transfers"*

and later:

> *"Then per product: biggest debtor pays the biggest creditor. Every round empties an account,
> so at most `n - 1` transfers."*

The `n - 1` bound is correct. **"Fewest" is not.** Greedy debtor-to-creditor is a heuristic, and
minimising the number of settling transactions is NP-hard (it is a set-partition problem: the
true minimum is `n_nonzero - k`, where `k` is the largest number of disjoint subsets that each
net to zero).

I brute-forced it against your `make_transfers`. Concrete counterexample, balances
`A=-4, B=-3, C=+2, D=+2, E=+3`:

```
your output (4 transfers)          optimal (3 transfers)
  A -> E  3                          B -> E  3        {B,E} nets to zero
  B -> C  2                          A -> C  2
  A -> D  1                          A -> D  2        {A,C,D} nets to zero
  B -> D  1
```

Greedy sends the biggest debtor (A, -4) to the biggest creditor (E, +3) first, which destroys the
exact `{B:-3, E:+3}` pairing. **120 such vectors exist among length-5 balances in ±4 alone.**

Note your own test only asserts an upper bound — `assert len(got) <= max(moving - 1, 0)` — so the
suite never checked minimality. That is a fair test; the README overstated what it proves.

### How to answer

Do not defend the word. Correct it before they do:

> "One thing I would fix in the README: I wrote 'fewest' and that is an overclaim. Greedy
> debtor-to-creditor guarantees at most n−1 transfers per product, and it is optimal when no
> proper subset of the balances nets to zero — but minimising transactions in general is a
> set-partition problem and NP-hard. `A=-4, B=-3, C=2, D=2, E=3` is a counterexample: greedy
> gives 4, the optimum is 3 by settling {B,E} first. On the real input, 2.3 million records
> collapsed to 5,702 transfers, and the n−1 bound is what actually matters at that scale —
> chasing the true optimum would mean subset-sum per product for a saving in the noise. But the
> claim should have said 'at most n−1', not 'fewest'."

That answer is stronger than the original claim. It shows you know the complexity class, you
measured, and you can distinguish "good enough and why" from "optimal".

---

## 🟠 2. mypy is a declared dependency that you never used

`pyproject.toml` lists `mypy = "^1.13"` in dev dependencies. But:

- **zero type hints** in any of `balances.py`, `files.py`, `run.py`, `__main__.py` (I grepped)
- **no `[tool.mypy]` section**
- **no `typecheck` target** in the Makefile
- **no mypy hook** in `.pre-commit-config.yaml` (ruff only)

So the tooling advertises a static-typing standard the code does not meet. A reviewer who opens
`pyproject.toml` before the code will spot this in ten seconds, and for a role that says
*"simple, understandable and extensible code"* it reads as unfinished rather than deliberate.

### How to answer

Own it, do not rationalise:

> "That is a loose end — I pulled mypy in intending to type the module boundaries and did not
> get to it. Given the size I would type the three public functions and the record tuple, which
> is where the real ambiguity is: `get_balances` takes an iterable of 4-string tuples and
> returns a nested defaultdict, and that is not obvious from the signature. I would replace that
> tuple with a small frozen dataclass or NamedTuple and add `--strict` to the Makefile."

**If you have time before the call, actually do it.** Typing four functions and adding a
`typecheck` target is 20 minutes and removes the criticism entirely.

---

## 🟠 3. Input validation is inconsistent — two crash paths with no message

You give clean, quoted `ValueError`s for a bad side and an unmapped portfolio. But quantity is
unguarded. Verified:

| Input | What happens |
|---|---|
| `<Qty>` tag missing → `findtext` returns `None` | `TypeError: conversion from NoneType to Decimal is not supported` |
| `<Qty>abc</Qty>` | `decimal.InvalidOperation: [<class 'decimal.ConversionSyntax'>]` |
| `<Qty>-5</Qty>` with `Side=BUY` | **accepted silently**, balance becomes `-5` |

The first two are raw exceptions with no record context — the operator cannot tell which of 2.3
million records was bad. The third is worse: a negative quantity on a BUY silently inverts the
sign, and nothing downstream catches it because the zero-sum check still passes if the input is
self-consistent.

### How to answer

> "Validation is uneven — I guarded side and portfolio with messages and left quantity bare. A
> missing or non-numeric Qty raises a bare TypeError or InvalidOperation with no record context,
> and a negative quantity on a BUY is accepted silently and flips the sign. I would parse the
> quantity in the same guarded block, require it to be positive, and include the product and
> portfolio in the message the way the other two do."

---

## 🟡 4. `max(owed, key=owed.get)` is O(n) per transfer, so O(n²) per product

They will ask why not a heap. Have the numbers:

> "It is O(n²) in the number of accounts holding a non-zero position *for one product*, not in
> the 2.3 million records. On the real input that is small — 5,702 transfers total across all
> products, 8 seconds end to end, 29 MB. A heap would make it O(n log n), but it needs lazy
> deletion because the amounts mutate as I settle, and at this n the constant factor and the
> extra code are not worth it. If accounts-per-product grew into the thousands I would switch,
> and I would measure first."

That is the right answer: you know the cost, you know the alternative, you chose on evidence.

---

## 🟡 5. `root.clear()` inside the loop — be ready to explain why it is safe

```python
root.clear()   # 213MB -> 15MB
```

It is correct: on an `end` event the element is fully parsed and you have already pulled the four
text values, so discarding it and its siblings loses nothing. Say exactly that, plus the number
you measured. The comment is already good — it is the kind of detail that earns credit, so make
sure you volunteer it rather than waiting to be asked.

One follow-up to expect: *"what if the XML is malformed halfway through?"* Answer honestly —
`iterparse` raises `ParseError`, you do not catch it, and because `save_output` runs only after
the whole parse, **no partial output file is written**. Your tests actually assert that
(`assert not output.exists()`). Frame it as deliberate: all-or-nothing, because a partial
bank-transfer file is worse than none.

---

## 🟡 6. The `Decimal` precision test is a strength — lead with it

`test_decimal_precision_is_caught` documents that Decimal's default 28-digit context makes
`1e30 + 0.000001` round down, so the balances stop summing to zero. Finding that yourself is a
good signal. But the code only *detects* it via the zero-sum guard, it does not handle it.

Expect: *"so what would you do about it?"* The strong answer:

> "Quantities have exactly six decimal places, so the clean fix is to drop Decimal and work in
> integer minor units — parse to `int(Decimal(qty) * 10**6)`. That is exact, has no context
> limit, and is faster. Decimal was the safe first choice; scaled integers are the right one."

---

## 🟢 7. Smaller things, one line each

- **Docker runs as root.** No `USER` directive. For a trading firm, add `useradd` + `USER app`.
  Also there is no `poetry install` in the image — it works only because you are stdlib-only, so
  say that is deliberate, and that adding a dependency would require changing the Dockerfile.
- **`uuid.uuid4()` makes output non-reproducible.** Two runs on the same input produce different
  `TrsfId`s, so you cannot diff them. Defensible (the bank needs unique ids) but have the answer:
  a deterministic id derived from product+accounts+quantity would be diffable, at the cost of
  colliding across days.
- **`__main__.py` calls `main()` at import time**, with no `if __name__ == '__main__'` guard.
  Fine for `python -m app`, but importing the module executes it.
- **`logger.info('Read %d records')` sits after the generator loop**, so it only fires if the
  generator is fully consumed. It is, today. It is fragile if anyone ever breaks early.
- **No ordering guarantee on output.** Deterministic in practice via dict insertion order; worth
  saying you know it is incidental rather than guaranteed.

---

## What to lead with, unprompted

Open the discussion by naming the trade-off yourself. It reframes the whole conversation from
"defend this" to "we are two engineers reviewing code":

> "The core idea is that the bank only cares about the net position per (product, account), so a
> chain like A→B→C collapses to one transfer. That took 2.3 million records to 5,702 transfers in
> 8 seconds and 29 MB. The settlement itself is greedy — biggest debtor pays biggest creditor —
> which bounds it at n−1 per product. I should flag that my README said 'fewest' and that is an
> overclaim; the true minimum is a set-partition problem, and I can give you a counterexample
> where greedy costs one extra transfer. At this scale I would still choose greedy, but the
> wording was wrong."

Nobody expects a perfect submission. They are testing whether you know where your own bodies are
buried. Going in with #1 already conceded, and #2 already fixed, puts you ahead of a candidate
who defends everything.

## If you have an hour before the call

1. Type the four public functions and add `typecheck` to the Makefile (kills #2 outright).
2. Guard the quantity parse with a message and a positivity check (kills #3).
3. Re-read `balances.py` and `files.py` line by line, out loud. Every line must have a reason.
