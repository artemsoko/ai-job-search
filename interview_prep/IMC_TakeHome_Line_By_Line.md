# The submitted take-home, line by line

Source: `/Users/artemsokoliuk/Downloads/imc_task`. 121 lines in `app/`, 216 in `tests/`, stdlib
only, 17 tests.

**How to use this.** For each block: what it does, **why this and not the obvious alternative**,
and the question they will ask. The second part is what is actually being tested — they know what
`defaultdict` does. Read it with the code open in PyCharm beside it, out loud, once.

The goal is not to memorise these sentences. It is that by the end you can answer a question this
document does not contain, because you understand the shape of the thing.

---

# `app/balances.py` — all the logic, zero IO

```python
 1  from collections import defaultdict
 2  from decimal import Decimal
```

**Stdlib only, across the whole project.** Not laziness — a dependency here would mean a lock
file to maintain, a `poetry install` layer in the Dockerfile (there isn't one) and a supply-chain
question for a program whose entire job is arithmetic over a file.

> *"Why no dependencies?"* — "Nothing here needed one. The parse is `ElementTree`, the arithmetic
> is `Decimal`, the CLI is `argparse`. Because I stayed stdlib-only the Docker image is just
> `COPY app ./app` with no install step at all. If I'd added one library that changes."

---

```python
 5  def get_balances(records, accounts):
```

**The most important design decision in the submission, and it is invisible unless you point at
it.** This module takes `records` as an *already-open iterable* and `accounts` as a *plain dict*.
It never opens a file, never knows a path exists. All IO lives in `files.py`; `run.py` wires the
two together.

That is what makes the logic testable with no filesystem: 11 of the 17 tests call
`make_transfers` directly with a literal dict. It is also a Clean-Architecture / hexagonal seam —
domain in the middle, IO at the edge — reached by passing arguments rather than by building
classes for it.

> *"Why two modules for 121 lines?"* — "So the logic has no IO in it. `balances.py` is a pure
> function of its arguments, which is why most of the tests are literal dicts with no tmp_path
> and no fixtures. `files.py` is the only place that knows a path or an XML schema exists. If the
> bank switched from XML to CSV tomorrow, `balances.py` doesn't change."

**Weakness to concede if pressed:** the parameters are unannotated, and `records` being "an
iterable of 4-tuples in a specific order" is a contract that exists only in your head and in
`files.py`'s yield order.

---

```python
 6      balances = defaultdict(lambda: defaultdict(Decimal))
```

Two-level accumulator: `balances[product][account] += amount`.

- Outer factory must be a **zero-arg callable returning a dict** — hence the `lambda`. `defaultdict(defaultdict)` would fail on first access because `defaultdict()` with no factory raises on a missing key; you need the *inner* factory bound, which only a lambda (or `partial`) gives you.
- Inner factory is `Decimal` because **`Decimal()` is `Decimal('0')`** — the type doubles as its own zero.

**Alternatives rejected:**
- `dict` + `setdefault` — works, but three lines where one reads better.
- `collections.Counter` — wrong: `Counter` is built for ints, and its arithmetic operators drop non-positive values, which would silently delete exactly the debtor balances this program is about.
- `dict[tuple[product, account]]` flat key — would work, but then settling per product means grouping again afterwards. Nesting matches how the algorithm consumes it.

> *"Why not a plain dict?"* — as above, and then: "the cost of `defaultdict` is that a *read* of a
> missing key inserts it. So I never probe it — I only ever `+=` into it and iterate `.items()`,
> and in the error message I wrap it in `dict()` so I'm not printing a defaultdict repr or
> mutating it while reporting on it."
>
> *"What breaks with defaultdict in production?"* — "Silent key growth from a read, and it won't
> pickle with a lambda factory."

---

```python
 8      for product, portfolio, side, quantity in records:
```

Unpacks the 4-tuple `files.py` yields. **This is the coupling worth naming before they do:** the
order `(product, portfolio, side, quantity)` is duplicated in two files with nothing enforcing
it. Swap two fields in `read_records` and this still runs, just wrongly.

> "A `NamedTuple` for the record would fix that — `record.side` instead of position 2 — and it's
> what I'd change first if this grew. At four fields in a 121-line program I took the tuple."

---

```python
 9          if side not in ('BUY', 'SELL'):
10              raise ValueError(f'unexpected side {side!r} on product {product!r}')
11          if portfolio not in accounts:
12              raise ValueError(f'no bank account mapped for portfolio {portfolio!r}')
```

**Whitelist, not blacklist.** An unknown side is rejected rather than defaulted, because
defaulting means guessing the direction money moves.

`!r` rather than `!s` is deliberate: `repr` quotes the value, so `'BUY '` with a trailing space
or `''` from an empty tag is visible in the message instead of looking identical to `BUY`.

Including `product` / `portfolio` gives the operator something to grep for in a 2.3-million-record
file. (Contrast with the `Qty` path, which has none of this — the known gap.)

**Fail fast rather than skip-and-warn**, and that is a judgement call worth defending:

> *"Why not skip the bad record and keep going?"* — "Because both of these mean the *input* is
> wrong, not the record. An unmapped portfolio means real money wouldn't move and nobody would
> notice; a bad side means I'd have to guess a direction. For a settlement file I'd rather
> produce nothing and have someone fix the mapping. My tests assert no output file is written on
> either path. If the requirement were 'process what you can', I'd want a rejects file as an
> explicit output rather than a log line."

---

```python
14          amount = Decimal(quantity)
15          balances[product][accounts[portfolio]] += amount if side == 'BUY' else -amount
```

`Decimal(quantity)` is constructed **from the string** straight out of the XML — never via
`float`, which would bake in binary error before `Decimal` ever saw it.

Line 15 carries the second real insight of the solution: the accumulator is keyed by
**`accounts[portfolio]`** — the *bank account* — not by portfolio. Several portfolios map to the
same account (in the provided data, `DGH_Neutral_Flux` and `DGH_Flux_Caution` both map to
`ACC-DGH-001`). So a transfer between two portfolios sharing one bank account nets to zero and
correctly produces no bank transfer at all. `test_transfer_inside_one_account` is exactly that.

> *"What was the actual insight in this task?"* — "Two. The bank only cares about the net position
> per product and account, so a chain A→B→C collapses to one transfer — that's what takes 2.3
> million records to 5,702. And the netting key is the bank account, not the portfolio, so
> transfers inside one account disappear for free."

**The known gap, and say it yourself:** `quantity` is unguarded. Missing `<Qty>` → `findtext`
returns `None` → `TypeError: conversion from NoneType to Decimal is not supported`. `<Qty>abc</Qty>`
→ `decimal.InvalidOperation`. Both raw, with no record context, unlike lines 10 and 12.
**Worst of the three:** `<Qty>-5</Qty>` with `Side=BUY` is accepted silently and flips the sign,
and the zero-sum check still passes if the input is self-consistent. Fix: parse in the same
guarded block, require `> 0`, include product and portfolio in the message.

---

```python
20  def make_transfers(product, balances):
21      if sum(balances.values()) != 0:
22          raise ValueError(f'balances for {product!r} do not add up to zero: {dict(balances)}')
```

**The correctness invariant of the whole program.** Every portfolio transfer is a BUY on one side
and a SELL on the other, so per product the signed quantities must sum to exactly zero. If they
don't, the input is not a complete day.

Why raise rather than correct: balancing it would mean inventing a transfer, i.e. moving money
that no source record asked to move.

This guard is also what makes line 30 safe — see below. Point that out; it shows you know why the
check is where it is rather than just that it's good practice.

`dict(balances)` in the message: avoids a `defaultdict(...)` repr and avoids passing the live
object into formatting.

> *"`sum()` on Decimals — any concern?"* — "Yes, and I tested it. `sum` starts from `int` 0, which
> is fine because `Decimal.__radd__` handles it. The real issue is the context: `Decimal` keeps 28
> significant digits, so `1e30 + 0.000001` rounds and the sum stops being zero for reasons that
> have nothing to do with the data. `test_decimal_precision_is_caught` documents that. The proper
> fix for a fixed six-decimal domain is integer minor units — `int(Decimal(qty) * 10**6)` —
> exact, no context limit, and faster."

---

```python
24      owed = {account: -value for account, value in balances.items() if value < 0}
25      due = {account: value for account, value in balances.items() if value > 0}
```

Split into debtors and creditors, with debtors **negated to positive** so the loop below compares
and subtracts magnitudes without sign juggling.

Strict `< 0` / `> 0` **drops zero balances entirely** — an account that nets flat never appears in
either dict, so it never gets a transfer. `test_flat_account_is_skipped` covers it.

> *"Why negate?"* — "So `min(owed[x], due[y])` is a comparison of two magnitudes. With signs kept
> I'd be writing `min(-owed[x], due[y])` and the sign errors live there."

---

```python
27      transfers = []
28      while owed:
29          from_account = max(owed, key=owed.get)
30          to_account = max(due, key=due.get)
31          quantity = min(owed[from_account], due[to_account])
32          transfers.append((product, from_account, to_account, quantity))
```

Greedy: **biggest debtor pays the biggest creditor.**

- `max(owed, key=owed.get)` iterates keys and scores each by value — **O(n) per pick**, so O(n²) per product. Ties resolve to the first maximum in dict insertion order: deterministic in practice, but incidental, not guaranteed.
- **Line 30 cannot `KeyError` on an empty `due`** precisely because of the zero-sum guard on line 21: if anything is owed, something must be due. That is the connection to name.
- Line 31 is the termination argument: settling `min(...)` empties at least one of the two accounts every iteration, so `owed ∪ due` shrinks by at least one each round. Hence **at most n−1 transfers** — and every account settled is one fewer to settle.

> *"Why not a heap?"* — "It'd take the picks to O(log n), but the amounts mutate as I settle, so a
> heap needs lazy deletion — push the updated value, pop and discard stale entries. That's more
> code and more state for a program where n is accounts-holding-a-position *per product*, not 2.3
> million. Measured: 5,702 transfers total, 8 seconds, 29 MB. If accounts-per-product reached the
> thousands I'd switch, and I'd measure first."
>
> *"Is greedy optimal?"* — **NO.** The full concession is in `IMC_TakeHome_Defence.md`. Short
> form: at most n−1, optimal when no proper subset of the balances nets to zero, but the true
> minimum is `n_nonzero − k` where `k` is the largest number of disjoint zero-sum subsets — that's
> set partition, NP-hard. Counterexample, verified against this code: `A=-4, B=-3, C=2, D=2, E=3`
> → greedy 4, optimum 3 (settle `{B,E}` first). The README and `pyproject.toml:4` both say
> "fewest". Both are wrong.

---

```python
34          owed[from_account] -= quantity
35          due[to_account] -= quantity
36          if owed[from_account] == 0:
37              del owed[from_account]
38          if due[to_account] == 0:
39              del due[to_account]
40
41      return transfers
```

Decrement both sides, delete whichever hit zero. Deleting is what makes `while owed` terminate and
what keeps the `max` scans shrinking.

Exactly one of the two deletions fires when the amounts differ; **both** fire when they are equal.

> *"Why `while owed` and not `while owed and due`?"* — "They empty together, by the zero-sum
> invariant. `while owed and due` would look safer and would actually be worse: it'd exit quietly
> on malformed input instead of raising, and I'd ship a settlement file with money missing. I'd
> rather the guard on line 21 be the only place that decides the input is bad."

---

# `app/files.py` — the only module that knows about paths and XML

```python
 9  def read_accounts(accounts_path):
10      with open(accounts_path, encoding='utf-8') as f:
11          return json.load(f)
```

Explicit `encoding='utf-8'` rather than the platform default — the one-line reason: a file written
on Linux CI and read on a Windows box otherwise decodes as cp1252. No schema validation: the
mapping is trusted, and a bad mapping surfaces as the `no bank account mapped` error upstream.

---

```python
14  def read_records(trsfs_path):
15      events = ET.iterparse(trsfs_path, events=('start', 'end'))
16      _, root = next(events)
```

`iterparse` yields `(event, element)` as it parses, instead of `ET.parse` building the entire
2.3-million-record tree first.

`events=('start','end')` requests both — **`start` only so that `next(events)` can hand you the
root element**, which is the handle you need in order to clear it later. With `end` alone the
first event you'd see is the first `</Trsf>`, by which point the root is unreachable.

> *"Why do you need `root` at all?"* — "Because clearing the record isn't enough: `iterparse`
> leaves every finished element attached to the root, so the refcount never drops and the tree
> grows for the whole file. 213 MB versus 15 MB — that's the measurement in the comment."

---

```python
19      for event, record in events:
20          if event != 'end' or record.tag != 'Trsf':
21              continue
22
23          records += 1
24          yield (
25              record.findtext('PrdId'),
26              record.findtext('PrtflNm'),
27              record.findtext('Side'),
28              record.findtext('Qty'),
29          )
```

Filters to `end`-of-`<Trsf>`. `end` matters: on a `start` event the children are not parsed yet,
so `findtext` would return `None`. The `.tag` check skips the root's own events and anything
nested.

`findtext` returns `None` for a missing child — which is the origin of the unguarded-`Qty`
`TypeError`. Good to know it returns `None` rather than raising; that's the API choice that lets
the bug through.

**`yield` makes this a generator**, so `get_balances` consumes records one at a time and memory is
O(1) in record count.

> *"Why a generator and not a list?"* — "It's consumed exactly once, immediately. A list would
> hold 2.3 million tuples alive for no benefit. Two consequences I accept: it's single-pass, so
> anything needing a second look re-parses; and the log line below only fires if the generator is
> exhausted — true today, fragile if someone adds an early break."

---

```python
31          # iterparse leaves read elements on the root. Clearing the record alone
32          # is not enough: that way it is 213MB instead of 15MB.
33          root.clear()
34
35      logger.info('Read %d records', records)
```

**Safe, and be ready to say why:** on an `end` event the element is fully parsed and you have
already pulled the four text values into a tuple, so discarding the element and its siblings loses
nothing you still need.

`logger.info('Read %d records', records)` uses **%-style deferred formatting**, not an f-string —
the string is only interpolated if the record actually gets emitted. `[tool.ruff.lint]` selects
`G`, the logging-format rules, which is what enforces that. Nice detail to point at.

> *"What if the XML is malformed halfway through?"* — "`iterparse` raises `ParseError` and I don't
> catch it. Because `save_output` only runs after the whole parse completes, **no partial output
> file is written** — my tests assert `not output.exists()`. That's deliberate: a partially
> written bank-transfer file is worse than none."

---

```python
38  def save_output(output_path, transfers):
39      out = ET.Element('Trsfs')
40      for product, from_account, to_account, quantity in transfers:
41          node = ET.SubElement(out, 'Trsf')
...
45          # :f, because str(Decimal('1E+3')) would send the bank an exponent
46          ET.SubElement(node, 'Qty').text = f'{quantity:f}'
47          ET.SubElement(node, 'TrsfId').text = str(uuid.uuid4())
48      ET.indent(out)
49      ET.ElementTree(out).write(output_path, encoding='utf-8', xml_declaration=True)
```

- **`f'{quantity:f}'`** — the sharpest small detail in the submission. `str(Decimal('1E+3'))` is
  `'1E+3'`; fixed-point formatting sends `1000.000` instead. Volunteer this one, the comment is
  already there.
- `ET.indent(out)` pretty-prints — makes the output diffable by a human, costs whitespace.
- `uuid.uuid4()` per transfer: unique, but **two runs on the same input produce different ids**, so outputs can't be diffed. Defensible (the bank needs globally unique ids); the alternative is a deterministic id hashed from product+accounts+quantity, which is diffable but collides across days.
- `xml_declaration=True` + explicit encoding: the bank gets `<?xml version='1.0' encoding='utf-8'?>` rather than a guess.

**The asymmetry they will spot: you stream the input and buffer the output.**

> "Deliberate, and the ratio justifies it — 2.3 million records in, 5,702 out. Streaming the write
> would also mean a half-written settlement file if the parse died mid-way, and I chose
> all-or-nothing. If the output ever approached the input's size I'd write incrementally to a temp
> file and rename on success, so the atomicity is in the filesystem instead of in memory."

---

# `app/run.py` — wiring only

```python
10  def main(argv=None):
...
15      args = parser.parse_args(argv)
```

**`argv=None` is a test seam, and it is worth a sentence.** `parse_args(None)` falls back to
`sys.argv[1:]` in production, while tests call `main([accounts, trsfs, output])` directly. That is
why `test_end_to_end` is an in-process function call rather than a `subprocess` — fast, and a
traceback instead of a captured stderr string.

```python
17      accounts = read_accounts(args.accounts)
18      balances = get_balances(read_records(args.trsfs), accounts)
```

`read_records(...)` is passed **as a generator, not materialised** — the one line where the
streaming actually pays off. Accounts are read first, so an unreadable mapping fails before you
spend 8 seconds parsing XML.

```python
20      transfers = []
21      for product in balances:
22          transfers.extend(make_transfers(product, balances[product]))
23
24      save_output(args.output, transfers)
25      logger.info('%d products, %d bank transfers written', len(balances), len(transfers))
```

Settlement is **independent per product** — that's the natural parallelism boundary if this ever
needed it, and a good answer to "how would you scale this".

`save_output` last = all-or-nothing.

> *"Output ordering?"* — "Grouped by product, in dict insertion order, so in practice it's
> deterministic for a given input — but that's incidental, not a guarantee I make. If the bank
> needed a stable order I'd sort explicitly."
>
> *"How would you parallelise it?"* — "Per product, after `get_balances`. The parse is sequential
> and it's only 8 seconds, so the win would be small; the settlement loop is the embarrassingly
> parallel part. I'd measure before adding a process pool for a 121-line program."

---

# `app/__main__.py`

```python
5  basicConfig(level=INFO, format='%(levelname)s %(message)s')
6  main()
```

`basicConfig` **only** in `__main__.py` — library modules call `getLogger(__name__)` and configure
nothing. That is the correct split and worth saying, because getting it backwards is the most
common logging mistake in Python.

**The known flaw:** `main()` runs at import time, with no `if __name__ == '__main__':` guard. Fine
for `python -m app`, but importing `app.__main__` executes the program.

> "Should have a `__name__` guard. It works for `python -m app` because that's exactly what `-m`
> does, but importing the module for any reason — a test, a REPL — runs it."

---

# Tooling — what a reviewer sees before the code

| File | What is right | What is not |
|---|---|---|
| `pyproject.toml` | `requires-python = ">=3.13"`, `dependencies = []`, ruff selects `E,F,I,UP,B,SIM,RET,C4,G`, pytest `pythonpath` + `testpaths` configured | `description` repeats the **"fewest"** overclaim · no `[tool.mypy]` · ruff doesn't select `ANN` |
| `Makefile` | `install / lint / format / test / image / run`, and the `run` target documents its own `ARGS` usage in a comment | **no `typecheck` target** despite mypy being a dev dep |
| `Dockerfile` | `PYTHONUNBUFFERED` + `PYTHONDONTWRITEBYTECODE`, `COPY app ./app` only, `ENTRYPOINT` not `CMD` | **runs as root** — no `USER`; no install step (fine *because* stdlib-only, say so) |
| `.dockerignore` | excludes `.idea`, all three caches, `tests`, `.venv` | — |
| `.pre-commit-config.yaml` | ruff check `--fix` + ruff format, version pinned to match `pyproject` | **ruff only, no mypy hook** |
| **missing** | — | **no root `.gitignore`, and no git history in the zip** — so `.idea/` and `.mypy_cache/` shipped |

`ENTRYPOINT` vs `CMD` is worth one sentence if Docker comes up: `ENTRYPOINT` makes the image
behave like the executable, so `docker run assignment a.json b.xml c.xml` appends the three paths
as arguments instead of replacing the command.

---

# Tests — what to volunteer

17 tests. The two that earn credit:

**`test_random_vectors`** — 2,000 seeded random balance vectors. It does not assert a transfer
list; it asserts **invariants**: replaying the output onto the input cancels to zero
(`positions_kept`), `len(got) <= max(moving - 1, 0)`, every quantity positive, no self-transfers.

> "That's property-based testing done by hand. The thing I care about isn't which transfers come
> out, it's that replaying them preserves every position — so that's what I asserted. Seeded with
> `random.Random(4242)` so a failure is reproducible."

**`test_decimal_precision_is_caught`** — you went looking for the failure mode of the type *you
chose* and wrote the test that documents it.

Also: `workspace` is a fixture that **returns a builder function** rather than a fixed directory,
so each test declares the XML and accounts it needs. `zip(..., strict=True)` catches a length
mismatch instead of truncating. `written()` parses the real output file rather than trusting a
return value.

> *"What did you choose not to test?"* — "Concurrency, because there is none. Performance, because
> I measured it by hand instead of asserting it — an 8-second assertion is a flaky test. And I
> never tested the `Qty` failure paths, which is precisely why they're the unguarded ones. The
> gap in my test suite and the gap in my validation are the same gap."

That last answer is the best one in this document. It shows you can read your own work.

---

# If they ask about AI tooling

They might; it is a normal question in 2026, and IMC's own guidance was *"you can Google or use
open source as you go, but make sure the work you do is your own."* Be straightforward and short,
then get back to the code:

> "I use Claude Code daily, and I used it here the way I use it at work — for scaffolding and for
> arguing with. The decisions are the part I own: stdlib-only, IO out of the logic module, netting
> on the bank account rather than the portfolio, `Decimal` and then finding its context limit, and
> all-or-nothing output. Happy to go through any line of it."

Then **be able to actually do that**, which is the point of this document. What fails is not
having used a tool — it is answering "why is this line here" with "that's what it suggested".

**AI is banned in the final-round coding station.** Drills for that are in `imc_drills/`, agent
off, in PyCharm.
