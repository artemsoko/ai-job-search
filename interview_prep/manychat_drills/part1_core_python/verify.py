"""Run the quiz snippets and print real output. Check your paper answers against this."""
import copy
from collections import defaultdict

def q(n, explanation):
    print(f"\n--- Q{n} ---")
    print(f"    WHY: {explanation}")

q(1, "b = a binds a second name to the SAME list. No copy. Mutation is visible through both.")
a = [1, 2, 3]; b = a; b.append(4); print("   ", a)

q(2, "a[:] is a shallow copy, so append touches only b.")
a = [1, 2, 3]; b = a[:]; b.append(4); print("   ", a, b)

q(3, "[[0]*3]*3 repeats the SAME inner list 3 times. Fix: [[0]*3 for _ in range(3)].")
grid = [[0] * 3] * 3; grid[0][0] = 1; print("   ", grid)
print("    correct:", [[0] * 3 for _ in range(3)])

q(4, "Default args are evaluated ONCE at def time. Fix: target=None, then target = target or [].")
def add(item, target=[]):
    target.append(item); return target
print("   ", add(1)); print("   ", add(2))

q(5, "copy.copy shares the inner lists; deepcopy clones them.")
original = {"a": [1, 2], "b": [3]}
shallow = copy.copy(original); deep = copy.deepcopy(original)
original["a"].append(99); print("   ", shallow["a"], deep["a"])

q(6, "A tuple's BINDINGS are immutable; the objects it points at may be mutable.")
t = ([1, 2], 3); t[0].append(4); print("   ", t)
try: t[1] = 5
except TypeError: print("    TypeError on rebinding, as expected")

q(7, "Closures capture the VARIABLE, not the value. All lambdas see the final i. "
     "Fix: lambda i=i: i, or functools.partial.")
fns = [lambda: i for i in range(3)]; print("   ", [f() for f in fns])
print("    fixed:", [f() for f in [lambda i=i: i for i in range(3)]])

q(8, "nonlocal rebinds outer's x. The module-level x is untouched.")
x = 10
def outer():
    x = 20
    def inner():
        nonlocal x; x = 30
    inner(); return x
print("   ", outer(), x)

q(9, "b is keyword-only because of the bare *. Extra kwargs land in kw.")
def f(a, *, b=1, **kw): return a, b, kw
print("   ", f(1, b=2, c=3))
try: f(1, 2)
except TypeError: print("    TypeError: positional b rejected")

q(10, "Small ints -5..256 are pre-interned, so `256 is 256` is True everywhere. For larger ints "
      "identity depends on constant folding and on the CPython version - on this interpreter even "
      "257 compares identical, on others it does not. That unpredictability IS the lesson: `is` "
      "means 'same object', and for numbers you must use ==. Comparing ints with `is` is a bug "
      "even when it happens to work.")
a1 = 256; b1 = 256; c1 = 257; d1 = 257; print("   ", a1 is b1, c1 is d1)
big = 10**9
print("    built at runtime:", big is 10**9, "(and == is", big == 10**9, ")")

q(11, "== compares values, is compares identity. list __eq__ short-circuits on identity FIRST, "
      "so [nan] == [nan] is True even though nan != nan.")
print("   ", [] == [], [] is [])
xn = float("nan"); print("   ", xn == xn, [xn] == [xn])

q(12, "1, True and 1.0 all hash equal, so the set keeps one of them plus the string.")
print("   ", len({1, True, 1.0, "1"}))

q(13, "Same reason: the KEY stays as first inserted, the VALUE is overwritten.")
d = {}; d[1] = "int"; d[1.0] = "float"; d[True] = "bool"; print("   ", d)

q(14, "defaultdict INSERTS on read via __missing__. In prod this silently grows memory and "
      "makes 'read-only' code mutate state. Use .get() when you only want to look.")
dd = defaultdict(list); print("   ", len(dd)); _ = dd["missing"]; print("   ", len(dd))

q(15, "list(d) snapshots the keys, so deleting is safe. Without it: "
      "RuntimeError: dictionary changed size during iteration.")
d = {"a": 1, "b": 2, "c": 3}
for k in list(d):
    if k == "b": del d[k]
print("   ", d)

q(16, "A generator is exhausted after one pass. The second list() sees nothing.")
g = (v * 2 for v in range(3)); print("   ", list(g), list(g))

q(17, "finally runs when the generator is closed - at break, GC finalises it and throws "
      "GeneratorExit. Order proves it runs after the break.")
def gen():
    try:
        yield 1; yield 2
    finally:
        print("    cleanup")
for v in gen():
    print("   ", v); break

q(18, "iter() holds a reference to the live list, so the append IS seen.")
data = [1, 2, 3]; it = iter(data); data.append(4); print("   ", list(it))

q(19, "items is a CLASS attribute, shared by every instance. Fix: assign it in __init__.")
class A:
    items = []
    def add(self, v): self.items.append(v)
aa, bb = A(), A(); aa.add(1); print("   ", bb.items)

q(20, "Mutating a list while iterating it skips elements: the index advances while the list "
      "shrinks. Build a new list instead: [i for i in items if not i % 2].")
def process(items):
    for item in items:
        if item % 2: items.remove(item)
    return items
print("   ", process([1, 2, 3, 4, 5]))
print("    correct:", [i for i in [1, 2, 3, 4, 5] if not i % 2])
