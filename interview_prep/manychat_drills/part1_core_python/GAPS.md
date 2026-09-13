# Part 1 — my actual gaps, from the cold run on 2026-08-22

Cold run of `QUIZ.md`, no code execution, no AI, no docs. **Score 23.5 / 51.**
Every output in this file was **verified by running it** on CPython 3.14, not recalled.

Read this file, not the chat log. Rehearse the *"say this"* lines out loud in **English** —
that is the actual deliverable, because Manychat scores the mechanism, not the output.

## Status after the fresh-snippet drill, same day (18 new snippets, 19.5/36)

Round scores: 1.5/4 → 2/4 → 4.5/10 → 6/9 → 5.5/9. Trend 38% → 62%.

| Gap | State |
|---|---|
| 1 — `*` repeats the reference | **closed** |
| 2 — late binding closures | **closed** |
| 5 — `is`/`==`, hash+eq contract | **closed** — nailed `{0, False, 0.0, "", None, [], 1, True}` cold |
| 6 — definition ≠ invocation (new, found in the drill) | **closed** |
| 3 — scope, assignment vs mutation | **80%** — mechanism held; still conflated "local" with "error" |
| 4 — argument binding order | **open** — the only one left |

### Gap 3, the remaining 20%: locality is compile-time, the error is runtime

```python
def a():          def b():          def c():
    print(x)          x = 1             for x in [1, 2]:
    x = 1             print(x)              pass
# UnboundLocalError  # 1, fine          print(x)   # 2, fine
```
All three make `x` local — the compiler decides that from the presence of an assignment
(`f.__code__.co_varnames` proves it). Only `a()` raises, because only there does the **read
execute before the assignment**. Locality ≠ error.

### Gap 4, still open — positional args override defaults

```python
def build(prefix, sep="-", *parts, upper=False, **meta): ...
build("a", "b", "c", upper=True, tag=1)
# prefix='a'  sep='b'  parts=('c',)  upper=True  meta={'tag': 1}   -> ('ABC', {'tag': 1})
```
`sep="-"` only applies when no positional lands there. Fill order:
**1.** positionals in order (defaults get overridden) → **2.** `*args` takes the rest →
**3.** anything after `*args` is keyword-only, never positional → **4.** `**kwargs` mops up.

Bonus, verified: `return A if cond else B, meta` parses as `(A if cond else B), meta` —
the comma binds looser than the conditional. Always returns a tuple. Worth criticising aloud.

### `or` for defaults is a bug — use `is None`

```python
def tally(rows, acc=None):
    acc = acc or {}          # BUG: {} is falsy, so a caller's empty dict is discarded
```
Verified: `mine = {}; tally(["x","x"], mine)` leaves `mine == {}` — the caller's container is
never filled, silently, with no exception. With `if acc is None:` it becomes `{'x': 2}`.
Same trap for `0`, `""`, `[]`, `False`. Billing consequence: a legitimate `discount=0`
silently becomes the default.

### `+=` means different things by type

```python
class Counter: total = 0          # self.total += 1  -> assignment (int immutable)
                                  #   -> creates an INSTANCE attr, class attr stays 0
class Bag:     items = []         # self.items += [x] -> list.__iadd__ mutates IN PLACE
                                  #   -> the shared CLASS list is poisoned; other
                                  #      instances see the data. Verified.
```
Identical syntax, opposite blast radius. This is the deepest "mutability and reference
semantics" answer available — say it if class attributes come up.

### Behavioural rule that cost points in three separate rounds

I reach a correct conclusion and fail to propagate it. Said `first is second` → `True`, then
printed them with different contents. Called something "the fix" while pasting the original
code unchanged. Named the mechanism, then proposed `pop()` for a reset.

**After stating a conclusion, re-read my own answer and delete whatever contradicts it** —
out loud: *"wait — if those are the same object then my earlier answer was wrong, it's
actually…"*. Self-correction scores **positive**; a standing contradiction does not.

And: **before calling something a fix, name the exact character I changed.** If I can't
name it, there is no fix.

---

## The two habits that cost more than any missing knowledge

**1. Always give the third sentence.**
Output → mechanism → fix/consequence. I lost points on Q3, Q4, Q6, Q14, Q15 by stopping after
sentence one or two, on questions that *explicitly asked* for the fix, the rule, or the exception
name. The recruiter's own tip list says think out loud; the quiz file says *"the value is the
second sentence, not the first."*

**2. Finish the fix and mentally run it.**
Twice I proposed a fix that crashes: `lambda i: i` (Q7 — `TypeError`, missing argument) and
`self.items = items` with a `None` default (Q19 — `AttributeError: 'NoneType' has no append`).
The idea was right, the code was broken. In CoderPad the code gets **executed**, so a broken fix
is visible instantly. Say the fix, then trace it aloud before claiming it works.

---

## Gap 1 — `*` on a sequence repeats the *reference*

Failed Q3.

```
[[0]*3]*3  -> [[1, 0, 0], [1, 0, 0], [1, 0, 0]]    g[0] is g[1] -> True
[[0]*3 for _ in range(3)] -> [[1, 0, 0], [0, 0, 0], [0, 0, 0]]   g[0] is g[1] -> False
```

`[0] * 3` builds **one** list. The outer `* 3` then stores **three references to that same list**.
A comprehension is the only correct build, because it re-evaluates `[0]*3` on every iteration.

**Say this:** "It prints three identical rows, because `[obj] * 3` copies the reference three
times — `grid[0] is grid[1]` is `True`, it's one list viewed three ways. I'd build it with
`[[0] * 3 for _ in range(3)]` so each row is its own object."

---

## Gap 2 — closures capture the *variable*, not the value

Failed Q7. I also gave a fix that crashes.

```
[lambda: i    for i in range(3)]  -> [2, 2, 2]
[lambda i=i: i for i in range(3)] -> [0, 1, 2]
```

Late binding: the lambda holds the comprehension's `i` cell. By call time the loop is over and
`i == 2`. `lambda i: i` is **not** a fix — it makes `i` a required parameter, so `f()` raises
`TypeError: missing 1 required positional argument`.

The fix works **because of the Q4 mechanism**: a default is evaluated at function-definition
time, so `i=i` freezes the current value. The Q4 footgun is the Q7 tool — say that link out loud,
it scores on both questions.

**Say this:** "`[2, 2, 2]` — late binding. Each lambda closes over the variable `i`, not its
value, and after the comprehension finishes `i` is 2. Fix is `lambda i=i: i`, which captures by
value because defaults are evaluated at definition time."

---

## Gap 3 — scope resolution: `nonlocal` vs `global`

Failed Q8, and my reasoning was **inverted** — I thought `nonlocal` reached the module and
`return x` gave the inner value. It is the exact opposite.

`x = 10` module, `outer` has local `x = 20`, `inner` does `nonlocal x; x = 30`:

```
outer(), x  ->  30 10
```

- **`nonlocal`** → nearest **enclosing function** scope. Never the module.
- **`global`** → module scope only.
- Both are about **writing**. Reading walks LEGB automatically: local → enclosing → global → builtins.

Senior detail, verified: `nonlocal q` with no `q` in any enclosing function is a
**compile-time SyntaxError**, not a runtime error:

```
SyntaxError - no binding for nonlocal 'q' found
```

**Say this:** "`30 10`. `nonlocal` binds to `outer`'s `x`, so `inner` sets that to 30 and
`outer` returns 30. The module-level `x` is untouched at 10 — only `global` would have reached
it. And `nonlocal` requires the name to already exist in an enclosing function, otherwise it's a
SyntaxError at compile time."

---

## Gap 4 — argument binding: bare `*` and `**kw`

Failed Q9. Missed that `c=3` collects into a **dict**, and missed the keyword-only bar entirely.

```python
def f(a, *, b=1, **kw): return a, b, kw

f(1, b=2, c=3)  ->  (1, 2, {'c': 3})
f(1, 2)         ->  TypeError: f() takes 1 positional argument but 2 were given
```

A bare `*` in the signature means **everything after it is keyword-only**. `b` cannot be passed
positionally at all. Unmatched keywords land in `**kw` as a dict.

Why this matters for the role: keyword-only is an **API design tool**. It stops callers depending
on parameter order, so the order can change without breaking anyone. Billing is exactly where
that matters — `charge(account, *, amount, currency)` can never be called with amount and
currency swapped.

**Say this:** "`(1, 2, {'c': 3})` — `c` isn't a named parameter so it collects into `**kw` as a
dict. Then `f(1, 2)` is a TypeError: the bare `*` makes `b` keyword-only, so the positional 2 has
nowhere to go. I use that deliberately on money-handling signatures so callers can't swap
arguments."

---

## Gap 5 — `is` vs `==`, and the hash/eq contract

Failed Q11, Q12, and half of Q13. This is the biggest cluster.

### Identity is not equality

```
[] == []   -> True        [] is []  -> False      # every [] literal is a new object
() is ()   -> True                                # empty tuple IS a CPython singleton
```

Immutable → safe to share, so CPython interns it. Mutable → never shared, or mutating one empty
list would corrupt every empty list in the process.

### nan breaks reflexivity, and containers hide it

```
nan == nan      -> False      # IEEE-754: nan equals nothing, including itself
[nan] == [nan]  -> True       # list eq short-circuits on identity first
nan in [nan]    -> True       # same reason
```

`list.__eq__` compares element-wise but tests `a is b` **before** `a == b`. Both lists hold the
same nan object, so `==` is never called on it. **Consequence: never use nan as a sentinel** —
`value == MISSING` silently fails while `value in [MISSING]` succeeds, two different answers to
the same question.

### Numeric types hash consistently across types

```
1 == True == 1.0     -> True
hash(1), hash(True), hash(1.0) -> 1 1 1
isinstance(True, int) -> True        True + True -> 2
```

Therefore:

```
{1, True, 1.0, "1"}                  -> {1, '1'}, len 2
d[1]="int"; d[1.0]="float"; d[True]="bool"   -> {1: 'bool'}
```

Set and dict care about `__hash__` + `__eq__`, **not** about types. And on assignment to an
existing key, dict **overwrites the value but keeps the first key object** — hence the int `1`
key with the last value.

**Say this (Q12):** "Two. `1`, `True` and `1.0` all hash to 1 and compare equal, so they occupy
one slot — set membership is the hash/eq contract, not the type. `'1'` is separate. The dict
version is nastier: the value gets overwritten three times but the original key object stays, so
you get `{1: 'bool'}`. In production that's a silent dedup bug when keys arrive from mixed
sources."

---

## Two things I got right and should keep doing

- **Q18 was the best answer of the run.** "An iterator holds a reference to the list and an
  index, not a copy" — precise, mechanism-first. Every answer should sound like that.
- **Q17: my first instinct was correct and I talked myself out of it.** Trust the first read,
  then verify it, rather than replacing it with a hedge.

---

## Two bonus mechanisms worth having ready

**Generator `finally` runs on close, not on loop exit.** `break` drops the last reference to the
generator → CPython refcount hits zero immediately → `close()` → `GeneratorExit` is raised at the
paused `yield` → `finally` runs. Verified order: `1`, then `cleanup`. Timing is a CPython
refcounting detail — on PyPy or with a lingering reference it defers to GC, so never rely on it
for correctness. This is exactly why `@contextlib.contextmanager` releases resources in the
`finally` after its `yield`.

**Dict raises loudly, list lies quietly.** Mutating a dict while iterating it →
`RuntimeError: dictionary changed size during iteration`. `.keys()` / `.items()` / `.values()`
are **views** and raise the same way; `list(d)` works only because it is a **snapshot**. A list
raises nothing at all — `remove()` shifts elements under the cursor and elements get skipped:

```
process([1, 2, 3, 4, 5])  ->  [2, 4]     # 2 and 4 were never even tested
```

Best answer is to drop the mutation entirely: `return [x for x in items if x % 2 == 0]`. The
original also mutates the caller's list, which is an unrequested side effect on its own.

---

## Verified answer key (all 20, for re-drilling)

| Q | Output | One-line mechanism |
|---|---|---|
| 1 | `[1, 2, 3, 4]` | `=` binds a second name to the same object |
| 2 | `[1, 2, 3] [1, 2, 3, 4]` | `a[:]` is **shallow** — new outer list, shared elements |
| 3 | `[[1,0,0], [1,0,0], [1,0,0]]` | `*` repeats the reference |
| 4 | `[1]` then `[1, 2]` | default evaluated once at `def` time |
| 5 | `[1, 2, 99] [1, 2]` | shallow shares inner lists; deepcopy recurses (with memo) |
| 6 | `([1, 2, 4], 3)` + `TypeError` | tuple immutability is shallow; such a tuple is unhashable |
| 7 | `[2, 2, 2]` | late binding; fix `lambda i=i:` |
| 8 | `30 10` | `nonlocal` = enclosing function, never module |
| 9 | `(1, 2, {'c': 3})` + `TypeError` | bare `*` ⇒ keyword-only; extras collect into `**kw` |
| 10 | `True True` in a script, `True False` in the REPL | small-int cache −5..256, **plus** `co_consts` dedup per code object |
| 11 | `True False` / `False True` | `[]` never interned; nan not reflexive; list eq short-circuits on identity |
| 12 | `2` → `{1, '1'}` | hash/eq contract, not types |
| 13 | `{1: 'bool'}` | value overwritten, first key object kept |
| 14 | `0` then `1` | `__missing__` **inserts**; `.get()` and `in` do not |
| 15 | `{'a': 1, 'c': 3}`; without `list()` → `RuntimeError` | view vs snapshot |
| 16 | `[0, 2, 4] []` | generator is a one-shot cursor |
| 17 | `1` then `cleanup` | close → `GeneratorExit` at the paused yield → `finally` |
| 18 | `[1, 2, 3, 4]` | iterator holds a reference + index, not a copy |
| 19 | `[1]` | class attribute shared by all instances; `a.items is b.items` → True |
| 20 | `[2, 4]` | list never raises; `remove` shifts under the cursor, elements skipped |

Q10 note: this was verified both ways. `c = 257; d = 257` on one line **in a module** gives
`True`, because the compiler deduplicates constants within one code object. Across separate
`exec` calls (REPL-like) it gives `False`. That context-dependence is the strongest possible
answer to "why must you never rely on it".

---

## Correct fixes, collected

```python
grid = [[0] * 3 for _ in range(3)]                  # gap 1

fns = [lambda i=i: i for i in range(3)]             # gap 2

def add(item: object, target: list | None = None) -> list:   # Q4 — bug is in the signature
    if target is None:
        target = []
    target.append(item)
    return target

class A:                                            # Q19
    def __init__(self, items: list | None = None) -> None:
        self.items = list(items) if items is not None else []
    def add(self, x) -> None:
        self.items.append(x)

def process(items: list[int]) -> list[int]:         # Q20 — remove the mutation, don't fix it
    return [x for x in items if x % 2 == 0]

d = {k: v for k, v in d.items() if k != "b"}        # Q15 — build new, don't mutate
```

`list(items)` in `A.__init__` is deliberate: storing the caller's list directly aliases it.
Verified — with a direct store the caller sees `[1, 2]` after `A.add(2)`; with `list()` the
caller still sees `[1]`.

---

## Re-drill plan

1. Close these 5 gaps on **fresh snippets** (same mechanisms, different code). Re-running
   `QUIZ.md` now would test memory, not the model.
2. Then `python verify.py` in this directory — it prints mechanisms, not just outputs.
3. Then Part 2 async, where the same model (closures over mutable state, shared references
   across coroutines) shows up at higher cost.

Bar for Wednesday: every answer is three sentences, and every fix I propose actually runs.
