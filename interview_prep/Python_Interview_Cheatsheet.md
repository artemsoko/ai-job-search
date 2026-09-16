# Python interview cheat sheet

Every output in this file was **executed on CPython 3.13.13**, not recalled. Where a behaviour is
version-dependent it says so.

Built for spoken interviews: each answer is written the way you would **say** it, not the way a
textbook writes it.

## How to answer — the pattern that scores

**Fact → mechanism → cost or where it bites.** Three sentences. A correct one-liner scores worse
than the same fact plus two sentences of mechanism, because the interviewer asked *"explain"* and
you handed back *"yes"*.

> ❌ "Generators are lazy."
> ✅ "A generator produces values on demand instead of materialising them, so memory is O(1) in the
> number of items rather than O(n). The cost is it's single-pass — anything that needs a second
> look has to re-run it. That's why my XML parse is a generator: 2.3 million records, one alive at
> a time."

And when you don't know: *"I don't know that one. My guess is X, but I'd check it in the REPL
rather than commit to it."* That beats a confident wrong answer with senior interviewers.

---

## Contents

1. [Types and the data model](#1-types-and-the-data-model)
2. [Collections and complexity](#2-collections-and-complexity)
3. [Copying](#3-copying)
4. [Functions](#4-functions)
5. [Iterators and generators](#5-iterators-and-generators)
6. [OOP](#6-oop)
7. [Exceptions and context managers](#7-exceptions-and-context-managers)
8. [Concurrency](#8-concurrency)
9. [Memory and garbage collection](#9-memory-and-garbage-collection)
10. [Modules and imports](#10-modules-and-imports)
11. [Typing](#11-typing)
12. [Numbers](#12-numbers)
13. [Strings, bytes, encoding](#13-strings-bytes-encoding)
14. [Testing](#14-testing)
15. [Performance](#15-performance)
16. [TRICKY — predict the output](#16-tricky--predict-the-output)
17. [Rapid-fire](#17-rapid-fire)

---

# 1. Types and the data model

## Mutable vs immutable

| Immutable | Mutable |
|---|---|
| `int`, `float`, `complex`, `bool`, `Decimal`, `Fraction` | `list`, `dict`, `set`, `bytearray` |
| `str`, `bytes`, `tuple`, `frozenset`, `range` | most user classes, `array`, `deque` |
| `None`, `Ellipsis`, enum members | `dataclass` (unless `frozen=True`) |

**Say it like this:** "Immutable means the object's value can't change after construction — rebinding
the name makes a new object. It matters for three reasons: immutables can be hashed and used as
dict keys, they can be shared safely between threads without a lock, and they're safe as default
arguments."

**The trap:** a tuple is immutable, but **what it contains need not be.** `t = (1, [2])` — you
can't replace `t[1]`, but you can mutate the list inside it. So a tuple containing a list is
**unhashable**, which is how the distinction actually shows up in practice.

## Hashability

An object is hashable if it has `__hash__` and that hash never changes while the object lives.
Immutable built-ins are hashable; `list`, `dict`, `set` are not.

**The invariant that matters:** if `a == b` then `hash(a) == hash(b)`. Define one without the other
and dict lookups silently break. Define `__eq__` on a class and Python sets `__hash__ = None` for
you — making it unhashable — precisely to stop you shipping that bug.

## `is` vs `==`

- `==` calls `__eq__` — value equality.
- `is` compares identity — the same object in memory.

**Use `is` only for:** `None`, sentinels you created, and enum members.

Small ints (−5..256) and short strings are cached or interned by CPython, and literals in the same
compiled unit get folded into one constant — so `is` *appears* to work on numbers and then stops:

```python
256 is 256          # True  (and Python 3.8+ emits a SyntaxWarning for this)
int('257') is int('257')   # False  -- built at runtime, two objects
```

**Say:** "Interning is an implementation detail I never rely on. `is` is for identity, and the only
values I use it with are `None` and sentinels."

## Truthiness

Falsy: `False`, `None`, `0`, `0.0`, `Decimal(0)`, `''`, `()`, `[]`, `{}`, `set()`, and any object
whose `__bool__` returns `False` or whose `__len__` returns `0`.

**Everything else is truthy — including `'False'`, `'0'`, and `[0]`.**

The bug this causes: `if value:` when `0` is a legitimate value. Use `if value is not None:`.

---

# 2. Collections and complexity

| Operation | `list` | `deque` | `dict` / `set` |
|---|---|---|---|
| index `x[i]` | **O(1)** | O(n) | — |
| append / push right | O(1) amortised | **O(1)** | — |
| insert / pop at front | O(n) | **O(1)** | — |
| insert / delete middle | O(n) | O(n) | — |
| membership `x in c` | O(n) | O(n) | **O(1)** avg |
| key lookup | — | — | **O(1)** avg, O(n) worst |
| `min` / `max` | O(n) | O(n) | O(n) |
| sort | O(n log n) | — | — |

Plus `heapq` on a list: push/pop **O(log n)**, peek `h[0]` **O(1)**, `heapify` **O(n)**.
And `sortedcontainers.SortedDict` (third party) for ordered iteration with O(log n) insert.

## Which one, and the sentence that justifies it

| Reach for | When | The line to say |
|---|---|---|
| `list` | index access, append-heavy, cache locality | "Contiguous, so index is O(1) and it's cache-friendly. Growth is amortised O(1) because it over-allocates." |
| `deque` | queue, sliding window, both ends | "O(1) at both ends. Trade-off is no O(1) indexing and no locality — it's a doubly linked list of blocks." |
| `dict` / `set` | membership, dedup, grouping, counting | "Average O(1), at the cost of memory overhead and no ordering by value." |
| `heapq` | top-K, streaming min/max, priority | "I only need the current best, not a full sort — log n per update instead of n log n per query." |
| BST / `SortedDict` | ordered iteration + range queries | "When I need sorted order maintained, not just the extreme." |

## `dict` internals

Open addressing with probing (**not** chaining). Since 3.6 the layout is **split**: a compact,
insertion-ordered entries array plus a sparse index array.

- That split is *why* dicts are ordered — and since 3.7 insertion order is a **language guarantee**, not an implementation detail.
- Deletion leaves a tombstone in the index array.
- Resize at roughly 2/3 load factor, which is what makes growth amortised.
- Average O(1), **worst O(n)** when every key collides — the basis of hash-flooding attacks, which is why `str` hashing is randomised per process by default (`PYTHONHASHSEED`).

`set` is the same machinery without values.

## Useful members of `collections`

`defaultdict` (factory on missing key — **note a read inserts**), `Counter` (`most_common`; built
for ints, and its `+`/`-` operators **drop non-positive counts**), `deque(maxlen=N)` (a ring
buffer for free), `namedtuple`, `ChainMap`, `OrderedDict` (now only needed for `move_to_end` and
order-sensitive equality).

---

# 3. Copying

```python
b = a              # same object, two names. Not a copy at all.
b = a.copy()       # or list(a), a[:], dict(a), copy.copy(a) -- SHALLOW
b = copy.deepcopy(a)   # recursive, handles cycles, slow
```

**Shallow** copies the outer container and shares the inner objects:

```python
orig = [[1, 2], [3, 4]]
sh = copy.copy(orig)
sh[0].append(99)
orig            # [[1, 2, 99], [3, 4]]   <- the inner list was shared
```

**Say:** "Shallow duplicates the container and shares the contents, so mutating a nested object
shows through both. Deep copy recurses and tracks a memo dict so cycles terminate — correct but
expensive. In practice I usually want neither: I prefer immutable data or an explicit
reconstruction, because a deep copy in a hot path is a smell."

Control it on your own classes with `__copy__` and `__deepcopy__`.

---

# 4. Functions

## How arguments are passed

Neither by value nor by reference — **the parameter name is bound to the same object**
("call by object reference"). So rebinding inside the function is invisible outside; mutating is
visible.

```python
def f(lst, x):
    lst.append(1)   # visible to the caller -- mutation
    x = 99          # invisible -- rebinding a local name
```

## Mutable default arguments 🔴

The default is evaluated **once, at function definition**, and stored on `func.__defaults__`:

```python
def bad(x=[]):
    x.append(1); return x
bad()   # [1]
bad()   # [1, 1]   <- same list every call
```

Fix: `def good(x=None): x = [] if x is None else x`.

Same mechanism, less obvious instance: a `@dataclass` field with a mutable default raises
`ValueError` at class-creation time — the language forcing `field(default_factory=list)` on you.

## Signature syntax

```python
def f(a, b, /, c, d, *args, e, f=1, **kwargs): ...
#          ^ positional-only      ^ keyword-only from here
```

`/` (3.8+) means callers can't use the name — useful when you may rename it later. Everything after
`*` or `*args` is keyword-only, which is how you stop `send(user, True, False)` happening.

## Closures and late binding 🔴

A closure captures the **variable**, not the value:

```python
fs = [lambda: i for i in range(3)]
[f() for f in fs]      # [2, 2, 2]  -- not [0, 1, 2]
```

By the time they're called the loop is done and `i` is 2. Fix with a default argument
(`lambda i=i: i`) or `functools.partial`. Same root cause as the classic loop-variable-in-a-callback
bug.

`nonlocal` rebinds a name in the enclosing function scope; `global` at module scope. Reading works
without either — only **assignment** needs the declaration.

## Decorators

A callable that takes a function and returns a replacement; `@` is sugar for
`f = decorator(f)`.

```python
import functools

def timed(fn):
    @functools.wraps(fn)                 # copies __name__, __doc__, __wrapped__
    def inner(*args, **kwargs):
        ...
        return fn(*args, **kwargs)
    return inner
```

**Why `wraps` matters:** without it the wrapped function reports the wrapper's name, and
introspection, docs tooling and pytest's test discovery all degrade.

Decorators with arguments are three levels deep (`deco(arg)` returns the real decorator). Class
decorators and `__call__`-based decorators do the same job with state.

## `functools` worth naming

- `lru_cache` / `cache` — memoise. **Three pitfalls:** arguments must be hashable; it holds **strong** references, so `@lru_cache` on a method keeps `self` alive forever (verified); and the cache is shared across instances, not per-instance.
- `partial` — pre-bind arguments; also the clean fix for late binding.
- `cached_property` — computed once per instance, stored in `__dict__` (so it needs no `__slots__` conflict).
- `singledispatch` — type-based dispatch, the Pythonic answer to the visitor pattern.
- `reduce`, `total_ordering`, `wraps`.

---

# 5. Iterators and generators

**Iterable** has `__iter__`. **Iterator** has `__iter__` *and* `__next__`, and raises
`StopIteration` when exhausted. A `for` loop calls `iter()` then `next()` until `StopIteration`.

A generator is an iterator the compiler writes for you: any function containing `yield`.

```python
def gen():
    try:
        x = yield 1        # yield is an EXPRESSION -- it receives what .send() passes
        yield 2
    finally:
        print("cleanup")   # runs on .close() and on GC

g = gen()
next(g)          # 1
g.send('hello')  # x == 'hello', returns 2
g.close()        # "cleanup"
```

**Generator vs list — the answer:**

> "A generator computes on demand, so memory is O(1) in the number of items and the first result
> arrives immediately. A list materialises everything up front. Generators are single-pass and
> exhausted once consumed — `list(g)` a second time gives `[]` — and you can't `len()` them or
> index them. So: generator for a stream you consume once, list when you need random access, a
> length, or more than one pass."

`yield from` delegates to a sub-iterable and forwards `send`/`throw` — the plumbing that made
coroutines possible before `async def`.

**Generator expressions** `(x for x in it)` vs list comprehensions `[x for x in it]`: same syntax,
lazy vs eager. `sum(x*x for x in big)` never builds the list.

`itertools` worth knowing by name: `chain`, `islice`, `groupby` (**requires pre-sorted input** —
the classic bug), `tee`, `product`, `combinations`, `count`, `cycle`, `accumulate`, `batched`
(3.12+).

---

# 6. OOP

## Class vs instance attributes 🔴

```python
class A:
    shared = []             # ONE list, on the class
    def __init__(self):
        self.own = []       # a new list per instance

a1, a2 = A(), A()
a1.shared.append('x')
a2.shared               # ['x']   <- shared
a2.own                  # []      <- not
```

Attribute lookup goes instance `__dict__` → type → MRO. Assigning `self.shared = ...` creates an
instance attribute that **shadows** the class one rather than modifying it.

## MRO and `super()`

C3 linearisation: left to right, depth first, and a class never precedes its parents.

```python
class A: pass
class B(A): pass
class C(A): pass
class D(B, C): pass
D.__mro__   # D, B, C, A, object
```

`super()` walks the MRO of the **instance's** type, not the lexical parent. So in cooperative
multiple inheritance every class in the chain must call `super()`, or part of the chain silently
never runs.

## `@property`, `@classmethod`, `@staticmethod`

- `property` — computed attribute with an optional setter; the Pythonic reason you don't write Java getters up front.
- `classmethod` — receives the class; the idiom for alternative constructors (`from_json`).
- `staticmethod` — receives nothing; a namespaced plain function.

All three are **descriptors** — objects implementing `__get__`/`__set__`, which is the mechanism
behind properties, methods and `__slots__` alike.

## Which record type

| | Mutable | Validation | Cost | Use for |
|---|---|---|---|---|
| `NamedTuple` | no | no | cheapest, tuple-compatible | small fixed records, tuple unpacking |
| `@dataclass` | yes (`frozen=True` available) | no | cheap | domain objects, `slots=True` for memory |
| `TypedDict` | yes | no (static only) | zero, it *is* a dict | describing JSON shapes |
| `pydantic.BaseModel` | yes | **yes, at runtime** | real per-object cost | system boundaries: HTTP, config, queues |

**Say:** "Pydantic at the boundary, dataclasses inside. Runtime validation is exactly what I want
where untrusted data enters and exactly what I don't want in a hot inner loop."

## `__slots__`

Replaces the per-instance `__dict__` with a fixed array of descriptors.

Measured on 3.13: the instance is 48 bytes either way, but without slots it also carries a
**280-byte `__dict__`**. Faster attribute access too.

Costs: no new attributes at runtime, no `__weakref__` unless you add it, and care with multiple
inheritance.

## ABC vs Protocol

- `abc.ABC` + `@abstractmethod` — **nominal**: you must inherit. Enforced at instantiation.
- `typing.Protocol` — **structural**, i.e. static duck typing. No inheritance, checked by the type checker; add `@runtime_checkable` for a (shallow) `isinstance`.

**Say:** "I reach for Protocol for ports in a hexagonal design — the adapter doesn't have to import
my abstraction, which keeps the dependency arrow pointing inward."

## Dunder methods worth listing

`__init__` / `__new__` (allocation, the hook for immutables and singletons) · `__repr__`
(unambiguous, for developers) vs `__str__` (readable) · `__eq__` + `__hash__` together ·
`__lt__` (+ `functools.total_ordering`) · `__len__`, `__getitem__`, `__contains__`, `__iter__` ·
`__enter__`/`__exit__` · `__call__` · `__getattr__` (only on failure) vs `__getattribute__` (always).

---

# 7. Exceptions and context managers

```
BaseException
├── SystemExit, KeyboardInterrupt, GeneratorExit   <- NOT caught by `except Exception`
└── Exception
    ├── ArithmeticError → ZeroDivisionError
    ├── LookupError → IndexError, KeyError
    ├── OSError → FileNotFoundError, TimeoutError, ConnectionError
    └── ValueError, TypeError, AttributeError, RuntimeError, StopIteration
```

**Never `except:` bare** — it swallows `KeyboardInterrupt` and `SystemExit`. `except Exception` is
the broad-but-sane form.

`try/except/else/finally`: `else` runs only if no exception was raised — it keeps the protected
block minimal. `finally` always runs, and a `return` in `finally` **discards** a pending exception.

Chaining: `raise X from e` sets `__cause__` (explicit); a bare `raise X` inside an except block
sets `__context__` implicitly. `raise X from None` suppresses the noise.

## Context managers

```python
class Resource:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        return False    # truthy SWALLOWS the exception -- the classic mistake
```

```python
from contextlib import contextmanager, suppress, ExitStack

@contextmanager
def resource():
    r = acquire()
    try:
        yield r
    finally:
        r.release()     # needs the try/finally to survive an exception in the body
```

`suppress(FileNotFoundError)` for the ignore-this case, `ExitStack` for a dynamic number of
resources.

**Say:** "A context manager is the only construct that guarantees release on the exception path.
That's not style — it's how connections leak."

## `ExceptionGroup` and `except*` (3.11+)

```python
try:
    async with asyncio.TaskGroup() as tg: ...
except* ValueError as eg:
    eg.exceptions       # a tuple of the matching sub-exceptions
```

Verified: a `TaskGroup` child failure arrives as an **`ExceptionGroup`**, so a plain
`except ValueError` **does not catch it**. `asyncio.gather` re-raises the first exception **bare**,
so there `except ValueError` does work. You also cannot mix `except` and `except*` on the same
`try` — that's a `SyntaxError`.

**This difference changes your error contract, and it is the single best asyncio signal you can
give in an interview.**

---

# 8. Concurrency

## The GIL

One lock per interpreter allowing only one thread to execute Python bytecode at a time.

**What it protects:** the interpreter's internal state — above all reference counts — so the
runtime doesn't corrupt itself.

**What it does NOT protect: your data.** The switch is **time-based** — 5 ms by default
(`sys.getswitchinterval()`, verified `0.005`) — so a thread is preempted mid-operation. `x += 1` is
load, add, store; two threads can both load 5 and both store 6. **You still need locks.**

Nuance worth adding: some operations are atomic *by accident* because they're a single C-level call
— `list.append`, a dict assignment. That's a CPython implementation detail, not a language
guarantee, so don't build on it.

**Crucially: the GIL is released around blocking I/O** (and by C extensions that choose to), which
is exactly why threads are still useful.

Python 3.13 ships an opt-in **free-threaded** build (PEP 703) with no GIL. Know it exists; don't
claim production experience. Removing the GIL makes data races your problem.

## Choosing

| Bottleneck | Use | Why |
|---|---|---|
| CPU-bound | `multiprocessing` / `ProcessPoolExecutor` | separate interpreters, real parallelism, GIL irrelevant |
| Blocking I/O in a library you can't change | `ThreadPoolExecutor` | GIL is released during the wait |
| High-concurrency I/O you control | `asyncio` | a task, not a thread stack, per in-flight operation |
| Numeric arrays | NumPy / C extension | releases the GIL and vectorises |

Processes: own memory, so arguments and results are **pickled** across an IPC boundary and startup
is expensive. Sharing needs `multiprocessing.shared_memory`, `Value`, `Array`. You do **not** need
a core per process — the OS schedules them; cores only cap real parallelism.

Primitives: `Lock`, `RLock`, `Semaphore`, `Event`, `Condition`, `Barrier`, `queue.Queue`
(thread-safe), `threading.local`.

## asyncio

One event loop per thread running ready callbacks. `async def` defines a coroutine; `await` yields
control back to the loop.

**Anything blocking stalls every task on that loop** — a sync DB driver, `requests`, `time.sleep`,
a CPU-heavy loop. Push those to `loop.run_in_executor` / `asyncio.to_thread`.

```python
await asyncio.gather(*tasks)             # first exception re-raised BARE;
                                          # siblings are NOT cancelled, they keep running
async with asyncio.TaskGroup() as tg:    # 3.11+: cancels siblings,
    tg.create_task(...)                   # raises ExceptionGroup
```

- **Cancellation** is a `CancelledError` raised at the next `await`. It inherits from
  `BaseException` (3.8+), so `except Exception` won't swallow it. Cleanup belongs in `finally`;
  `asyncio.shield` protects a critical section.
- **Bound concurrency** with a `Semaphore`. *"Unbounded `gather` over a million rows is how you DDoS
  your own downstream."*
- `asyncio.timeout()` (3.11+) is the modern form of `wait_for`.
- A coroutine does nothing until awaited or wrapped in a task. A bare `create_task` whose reference
  you drop can be garbage collected mid-flight — **keep a reference**.

---

# 9. Memory and garbage collection

**Two mechanisms:**

1. **Reference counting** — the primary one. When a refcount hits zero the object is freed
   *immediately* and deterministically.
2. **A generational cycle collector** (`gc` module, three generations) — because refcounting alone
   can never free `a.b = b; b.a = a`.

Consequences to say out loud:
- `__del__` on an object inside a cycle runs at an unpredictable time, or effectively never. Use a context manager instead.
- `weakref` is the tool for caches and parent pointers — a weak reference does not keep the target alive (verified: the ref returns `None` right after `del`).
- `sys.getsizeof` is shallow. It does not follow references.
- CPython frees to its own allocator (pymalloc) arenas, so RSS often does not fall after a peak.

**The story to tell** — it's yours and it is exactly this topic:

> "`iterparse` keeps every finished element attached to the root, so there's a live reference and
> the refcount never drops. `record.clear()` isn't enough — it drops the children but leaves the
> empty element in root's child list, so I'd still accumulate 2.3 million of them. Clearing the
> root is safe because on the `end` event I've already pulled the four values I need. Measured: 213
> megabytes down to 15."

---

# 10. Modules and imports

`import x` executes the module **once** and caches it in `sys.modules`; later imports are a dict
lookup. Module-level code is therefore effectively a singleton initialiser — which is why
expensive work or side effects at import time is a design smell.

```python
if __name__ == '__main__':
    main()
```

`__name__` is `'__main__'` only for the entry point. Without the guard, **importing** the module
runs it — and `multiprocessing` on spawn platforms re-imports your module in the child, so a
missing guard causes infinite process spawning.

**Circular imports:** usually a layering error. Fixes, in order of preference — move the shared
piece to a third module, depend on an abstraction instead, or (last resort) import inside the
function. `from x import y` at module scope fails on a cycle where plain `import x` survives,
because the name isn't bound yet.

Absolute imports over relative. Packages are directories; `__init__.py` is optional since 3.3
(namespace packages) but still how you define a package's public surface.

---

# 11. Typing

Hints are **not enforced at runtime** — they're for the type checker, the IDE and the reader.
`typing.get_type_hints` reads them; Pydantic and FastAPI *choose* to act on them.

```python
def f(x: int | None = None) -> list[str]: ...        # 3.10+ unions, 3.9+ builtin generics
type Alias = dict[str, list[int]]                     # 3.12+ type statement
def g[T](items: list[T]) -> T: ...                    # 3.12+ generic syntax
```

- `Optional[X]` **is** `X | None`. It means "may be None", not "may be omitted".
- `Any` disables checking; `object` accepts anything but lets you do nothing with it. Prefer `object`.
- `Protocol` for structural typing, `TypeVar`/`ParamSpec` for generics, `Literal`, `Final`, `TypedDict`, `NewType`, `cast` (a checker-only assertion, no runtime effect), `assert_never` for exhaustiveness.
- `from __future__ import annotations` makes annotations lazy strings — avoids quoting forward references and cuts import-time cost.

**The honest senior line:** "Hints on public boundaries and anything non-obvious. `mypy --strict`
in CI, because type hints without a checker in the pipeline are documentation that rots — that was
the loose end in my own take-home: mypy was a declared dependency with zero annotations, so it
proved nothing."

---

# 12. Numbers

`int` is arbitrary precision. `float` is IEEE-754 double — **binary**, so decimal fractions like
0.1 are inexact:

```python
0.1 + 0.2 == 0.3        # False
0.1 + 0.2               # 0.30000000000000004
sum([0.1] * 10) == 1.0  # True  <- rounding happens to land exactly; do NOT rely on it
```

- `round` uses **banker's rounding** (half to even): `round(2.5)` is `2`, `round(3.5)` is `4`.
- Floor division and modulo follow the **divisor's** sign: `-7 // 2 == -4`, `-7 % 2 == 1`.
- Compare floats with `math.isclose`, never `==`.

**`Decimal`** — base-10 exact, for money and anything where a decimal fraction must be exact.

```python
Decimal('0.1') + Decimal('0.2') == Decimal('0.3')   # True
Decimal(0.1)   # Decimal('0.1000000000000000055511151231257827021181583404541015625')
```

**Always construct from a string, never from a float** — a float argument bakes in the error before
Decimal sees it. The default context keeps **28 significant digits** (`getcontext().prec`), so very
large magnitudes still round; that is a context limit, not an exactness guarantee.

Formatting: `str(Decimal('1E+3'))` is `'1E+3'` — scientific. `f"{Decimal('1E+3'):f}"` is `'1000'`;
`:f` refuses scientific notation but does not pad decimals.

**Best answer for a fixed-scale domain:** integer minor units. `int(Decimal(qty) * 10**6)` is
exact, has no context limit, and is faster because `int` arithmetic is C while `Decimal` is a Python
object.

`Fraction` for exact rationals. `bool` **is a subclass of `int`**: `isinstance(True, int)` is True
(but `type(True) is int` is False), and `True == 1`, which is why `{1, True, 1.0}` is a single-element set.

---

# 13. Strings, bytes, encoding

`str` is a sequence of Unicode code points; `bytes` is a sequence of 0-255. **Encode to go out,
decode to come in** — there is no such thing as an unencoded string on the wire.

- Always pass `encoding=` explicitly to `open()`. Without it Python uses the platform default, so a file written on Linux CI decodes as cp1252 on Windows. (3.15 will default to UTF-8; `PYTHONUTF8=1` today.)
- Strings are immutable, so `s += x` in a loop is O(n²). Use `''.join(parts)`.
- f-strings are fastest and the default. Keep `%`-style for **logging** — `logger.info('n=%d', n)` defers formatting until the record is actually emitted, which ruff's `G` ruleset enforces.
- `str.translate` for bulk character mapping; `re.compile` once outside the loop.
- Interning is an implementation detail: compare with `==`.

---

# 14. Testing

```python
@pytest.mark.parametrize('side,expected', [('BUY', 1), ('SELL', -1)])
def test_sign(side, expected): ...
```

- **Fixtures** for setup, with `scope='function'|'class'|'module'|'session'`. A fixture that returns a *builder function* lets each test declare what it needs — stronger than a fixed one.
- `parametrize` for truth tables; `monkeypatch` for env vars and attributes; `tmp_path` for filesystem work; `caplog` for log assertions; `pytest.raises(X, match='...')` — always with `match`, or you can't tell which `ValueError` you caught.
- **Fakes over mocks.** *"A mock asserts how I called a collaborator; a fake asserts what happened. Mocks give you tests that pass while production breaks."*
- Property-based testing (`hypothesis`, or by hand with a seeded RNG): assert **invariants**, not outputs. *"For the settlement code the invariant isn't which transfers come out, it's that replaying them preserves every position. That's what I asserted, over 2,000 seeded random vectors."*
- Coverage is a floor, not a goal. 100% line coverage with no assertion on the error path means nothing.

---

# 15. Performance

**Measure first.** `time.perf_counter` for a one-off, `timeit` for microbenchmarks, `cProfile` +
`snakeviz` for a call profile, `py-spy` to attach to a live process, `tracemalloc` for memory.

What is actually slow in Python: attribute lookup and function calls in tight loops, per-object
overhead, and anything that should have been vectorised. What is not slow: the parts that are
already C — `sort`, `join`, `dict`, comprehensions, most of `itertools`.

Order of levers, cheapest first:
1. **A better algorithm or data structure.** O(n²) → O(n) beats every micro-optimisation.
2. Do less work: cache (`lru_cache`), short-circuit, batch I/O, avoid re-parsing.
3. Move the loop into C: comprehensions, `map`, `str.join`, NumPy.
4. Hoist out of the loop: precompile regexes, bind methods to locals, avoid repeated attribute chains.
5. `__slots__` / generators if memory is the constraint.
6. Only then: `asyncio` for I/O concurrency, processes for CPU, Cython/Rust/C for the last 10%.

**Say:** "Almost every Python performance problem I've actually hit was I/O or an accidental O(n²),
not interpreter speed."

---

# 16. TRICKY — predict the output

Every result below was executed on 3.13. Cover the right column and work down.

| Expression | Result | Mechanism |
|---|---|---|
| `m = [[0]*3]*3; m[0][0] = 1; m` | `[[1,0,0],[1,0,0],[1,0,0]]` | `*` copies the **reference** — three names for one inner list. Use `[[0]*3 for _ in range(3)]`. |
| `def f(x=[]): x.append(1); return x` twice | `[1]` then `[1,1]` | default evaluated once at definition |
| `[f() for f in [lambda: i for i in range(3)]]` | `[2,2,2]` | closures capture the variable; loop finished |
| `{1, True, 1.0}` | `{1}` | equal and same hash → one element |
| `{1:'a', True:'b', 1.0:'c'}` | `{1: 'c'}` | key keeps the **first** insertion, value the **last** |
| `nan == nan` / `nan is nan` | `False` / `True` | IEEE-754 says NaN equals nothing; identity is unaffected |
| `nan in [nan]` | `True` | `in` checks identity **before** equality |
| `t = (1,[2]); t[1] += [3]` | `TypeError` **and `t == (1,[2,3])`** | `+=` mutates in place, then the assignment back into the tuple fails. The mutation already happened. |
| `256 is 256` | `True` (+ SyntaxWarning) | literal folding / small-int cache |
| `int('257') is int('257')` | `False` | built at runtime, two objects |
| `0.1 + 0.2 == 0.3` | `False` | binary floats |
| `sum([0.1]*10) == 1.0` | **`True`** | rounding happens to cancel — luck, not a rule |
| `round(2.5), round(3.5)` | `(2, 4)` | banker's rounding, half to even |
| `-7 // 2, -7 % 2` | `(-4, 1)` | floor division; modulo takes the divisor's sign |
| `bool('False'), bool([0])` | `(True, True)` | non-empty is truthy |
| `[] == False` | `False` | falsy ≠ equal to `False` |
| `hash(-1), hash(-2)` | `(-2, -2)` | `-1` is CPython's error sentinel, so it's remapped |
| class attr `shared = []` mutated via one instance | visible on all | one object on the class |
| `d = defaultdict(list); d['missing']` | `d == {'missing': []}` | a **read** inserts |
| `copy.copy([[1,2],[3,4]])` then mutate inner | original changes | shallow |
| `'ab' in 'abc'` / `'ab' in ['abc']` | `True` / `False` | substring vs element |
| `g = (i for i in range(3)); list(g); list(g)` | `[0,1,2]` then `[]` | exhausted |
| `all([]), any([])` | `(True, False)` | vacuous truth |
| `sorted(['10','9','2'])` | `['10','2','9']` | lexicographic |
| `isinstance(True, int)` / `type(True) is int` | `True` / `False` | `bool` subclasses `int` |
| `[1,2,3] == (1,2,3)` | `False` | different types never compare equal here |
| `TaskGroup` child raises `ValueError`, caught by `except ValueError` | **misses it** | arrives as `ExceptionGroup`; needs `except*` |
| `gather` child raises `ValueError`, caught by `except ValueError` | **catches it** | `gather` re-raises bare |

---

# 17. Rapid-fire

One or two sentences each. Use these when the question is clearly a warm-up.

**`list` vs `tuple`?** Mutable vs immutable; tuple is hashable, slightly cheaper, and signals a
fixed-shape record.

**Why can't a list be a dict key?** Unhashable, because its hash would change as it mutates and the
entry would become unfindable.

**`append` vs `extend`?** `append` adds one element; `extend` consumes an iterable.
`[1].append([2])` → `[1, [2]]`.

**`remove` vs `pop` vs `del`?** By value / by index-and-return / by index or slice.

**Shallow vs deep copy?** Container duplicated with shared contents vs recursive duplication.

**`*args` / `**kwargs`?** Collect extra positional / keyword arguments; at a call site they unpack.

**Comprehension vs `map`/`filter`?** Comprehensions read better and are usually faster;
`map` is fine with an existing function. Both beat an append loop.

**Does Python have private attributes?** No, only conventions: `_x` means internal, `__x` triggers
name mangling to `_Class__x` (to avoid subclass collisions, not for security).

**`@staticmethod` vs `@classmethod`?** No implicit first argument vs receives the class; the latter
is how you write alternative constructors.

**What is `self`?** Just the conventional name for the first parameter — the instance, passed
explicitly by the descriptor protocol.

**Is Python interpreted or compiled?** Compiled to bytecode, then that bytecode is interpreted by
the CPython VM.

**`__new__` vs `__init__`?** Allocation vs initialisation. You need `__new__` for immutable types
and singletons.

**`str` vs `repr`?** Readable for users vs unambiguous for developers. `repr` is what the REPL and
containers show — so `'BUY '` with a trailing space is visible in `repr`, not in `str`. That's why
error messages use `!r`.

**Why `if __name__ == '__main__'`?** So importing the module doesn't execute it.

**`==` vs `is` in one line?** Same value vs same object.

**How do you reverse a list?** `list.reverse()` in place, `reversed(lst)` as a lazy iterator, or
`lst[::-1]` for a new list.

**What's a lambda's limit?** A single expression, no statements — so no assignment, no `try`.

**GIL in one sentence?** One lock serialising bytecode execution, released around I/O, which is why
CPU-bound work needs processes and I/O-bound work does not.

---

## If you only have twenty minutes

1. §8 concurrency — GIL, the three-way choice, `gather` vs `TaskGroup`. **The only question reported twice for IMC is threading vs multiprocessing.**
2. §9 memory — and say your own `root.clear()` story.
3. §16 tricky table — read the right column once.
4. One rehearsal of "explain a technical thing to a non-technical person" (IMC asked this twice, in two forms: a stack, and binary search).
