# Part 1 — Core Python: predict the output

**Do this on paper first.** Write your answer, THEN run `python3 verify.py` to check.

This is not a coding exercise, it's a *reading* exercise — which is exactly what Manychat said
Part 1 is. The skill is tracing what an object graph does, out loud, before touching a keyboard.

For each snippet: what does it print, and **why** — say the reason in terms of references,
mutation and binding.

---

## Mutability and aliasing

**Q1**
```python
a = [1, 2, 3]
b = a
b.append(4)
print(a)
```

**Q2**
```python
a = [1, 2, 3]
b = a[:]
b.append(4)
print(a, b)
```

**Q3**
```python
grid = [[0] * 3] * 3
grid[0][0] = 1
print(grid)
```
*The classic. Why, and how do you build it correctly?*

**Q4**
```python
def add(item, target=[]):
    target.append(item)
    return target

print(add(1))
print(add(2))
```
*Name the rule that causes this and the correct signature.*

**Q5**
```python
import copy
original = {"a": [1, 2], "b": [3]}
shallow = copy.copy(original)
deep = copy.deepcopy(original)
original["a"].append(99)
print(shallow["a"], deep["a"])
```

**Q6**
```python
t = ([1, 2], 3)
t[0].append(4)
print(t)
try:
    t[1] = 5
except TypeError as e:
    print("TypeError")
```
*Is a tuple immutable? Say it precisely.*

---

## Binding and scope

**Q7**
```python
fns = [lambda: i for i in range(3)]
print([f() for f in fns])
```
*Name the mechanism and the one-line fix.*

**Q8**
```python
x = 10
def outer():
    x = 20
    def inner():
        nonlocal x
        x = 30
    inner()
    return x
print(outer(), x)
```

**Q9**
```python
def f(a, *, b=1, **kw):
    return a, b, kw
print(f(1, b=2, c=3))
try:
    f(1, 2)
except TypeError:
    print("TypeError")
```

---

## Identity, equality, interning

**Q10**
```python
a = 256; b = 256
c = 257; d = 257
print(a is b, c is d)
```
*Why, and why you must never rely on it.*

**Q11**
```python
print([] == [], [] is [])
x = float("nan")
print(x == x, [x] == [x])
```
*The last one surprises people. Explain it.*

---

## Data structures and their semantics

**Q12**
```python
s = {1, True, 1.0, "1"}
print(len(s))
```

**Q13**
```python
d = {}
d[1] = "int"
d[1.0] = "float"
d[True] = "bool"
print(d)
```

**Q14**
```python
from collections import defaultdict
d = defaultdict(list)
print(len(d))
_ = d["missing"]
print(len(d))
```
*Why does merely reading change the size, and when does that bite you in production?*

**Q15**
```python
d = {"a": 1, "b": 2, "c": 3}
for k in list(d):
    if k == "b":
        del d[k]
print(d)
```
*What happens if you drop the `list()`? Name the exception.*

---

## Generators and laziness

**Q16**
```python
g = (x * 2 for x in range(3))
print(list(g), list(g))
```

**Q17**
```python
def gen():
    try:
        yield 1
        yield 2
    finally:
        print("cleanup")

for v in gen():
    print(v)
    break
```
*When does cleanup run, and what forces it?*

**Q18**
```python
data = [1, 2, 3]
it = iter(data)
data.append(4)
print(list(it))
```

---

## The ones that reveal seniority

**Q19**
```python
class A:
    items = []
    def add(self, x):
        self.items.append(x)

a, b = A(), A()
a.add(1)
print(b.items)
```
*What's the bug and what's the fix?*

**Q20**
```python
def process(items):
    for item in items:
        if item % 2:
            items.remove(item)
    return items
print(process([1, 2, 3, 4, 5]))
```
*Don't just predict it — say the rule about mutating while iterating.*

---

## How to answer these in the interview

Do not just say the output. Say the **mechanism**:

> "It prints `[1, 2, 3, 4]` because `b = a` binds another name to the same list object — there's
> no copy. Any mutation through either name is visible through both. If I wanted independence I'd
> use `a[:]` or `list(a)` for a shallow copy, and `copy.deepcopy` if the elements are mutable too."

That is the answer they're scoring. The value is the second sentence, not the first.
