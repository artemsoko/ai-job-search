# Spoken drill: the five structures IMC named

IMC's own document lists these as mandatory: **Dynamic Array, Linked List, Hash Table, Binary
Heap, Binary Search Tree** — *"we do not expect you to be an expert on these data structures
(i.e. implement one from scratch) but they should be a major part of your dialogue with the
interviewers and problem-solving tool box."*

So this is a **speaking** drill, not a coding one. Cover the answer, say it out loud, uncover.

---

## The table, cold

| Structure | Python | Reach for it when | Costs | The catch |
|---|---|---|---|---|
| Dynamic array | `list` | index access, append-heavy, iteration, cache locality | index O(1), append **amortised** O(1), insert/pop at front O(n), search O(n) | resize copies; `pop(0)` in a loop is a hidden O(n²) |
| Linked list | `collections.deque` | O(1) push/pop **both ends**, queues, sliding windows | append/pop either end O(1), index O(n) | no locality, per-node overhead, cannot binary search |
| Hash table | `dict` / `set` | membership, dedup, grouping, counting, index by id | avg O(1) get/set/del, worst O(n) | unordered by hash, memory overhead, keys must be hashable, collisions |
| Binary heap | `heapq` | **top-K, streaming min/max, priority scheduling, best bid/ask** | push/pop O(log n), peek O(1), heapify O(n) | only the extreme is cheap; no search, no ordered iteration; deletion from the middle needs lazy deletion |
| BST / balanced tree | `sortedcontainers.SortedDict` (no stdlib one) | ordered iteration **and** range queries | search/insert/delete O(log n), in-order = sorted | unbalanced degrades to O(n); Python has no builtin, say so |

## Say these sentences until they are automatic

1. *"I'd reach for a heap here because I only need the current best price, not a full ordering,
   so I pay O(log n) per update instead of O(n log n) per query."*
2. *"A dict gives me average O(1) membership, and the trade-off I'm accepting is losing any
   ordering and paying memory overhead."*
3. *"A deque, because the window evicts by position at both ends, and a list would cost O(n)
   on every `pop(0)`."*
4. *"Amortised O(1) — individual appends can be O(n) when the array resizes, but the cost
   averages out across appends."*
5. *"I can't cheaply delete from the middle of a heap, so I'll mark it dead and prune when I
   next read the top. That's lazy deletion."*
6. *"If I need ordered iteration as well as fast lookup, a hash table is the wrong shape and I
   want a balanced tree — in Python that means `sortedcontainers`, not the stdlib."*

## Questions to answer out loud

**Warm-up**
1. Why is `list.append` amortised O(1) and not O(1)? What actually happens on resize?
2. `dict` vs `set` vs `list` for "have I seen this id?" — which, and what do you give up?
3. Why is `deque.popleft()` O(1) but `list.pop(0)` O(n)?
4. `heapq` gives you a min-heap. How do you get a max-heap? (negate; and say the caveat for
   non-numeric keys)
5. Python has no builtin balanced tree. What do you use, and what would you use in C++/Java?

**The ones that separate people**
6. You need the K largest of N streamed numbers, K much smaller than N. Two approaches, costs,
   which and why. (heap of size K → O(N log K), O(K) memory; vs sort → O(N log N), O(N) memory)
7. You must support: insert, delete-by-id, and "give me the current maximum". Which structures,
   and how do they cooperate? (dict for id→node + heap; then the lazy-deletion problem)
8. A hash table degrades to O(n). When, and what would you do about it in a system you own?
9. Why can iteration order of a `dict` be a correctness problem even though CPython 3.7+
   preserves insertion order?
10. Order book: you need best bid, best ask, FIFO within a price level, and O(1) cancel by id.
    Name the structures and justify each. **This is the likely station question — rehearse it.**
11. When is an O(n²) algorithm the right choice in production? (small n, cache locality,
    simplicity; say you'd measure)
12. What does "cache locality" buy you concretely, and which of the five structures has it?

**Trading-flavoured, because IMC is a market maker**
13. Ticks arrive out of order by timestamp. You need the max over the last 5 seconds. Structure?
14. You track price levels and need "all levels between X and Y". Heap or tree? Why?
15. You need to detect a duplicate order id across millions of orders with a memory budget.
    (dict; then, if pressed on memory, mention Bloom filters and their false-positive trade-off)

## Complexity you should never have to think about

```
list      index O(1)   append O(1)*  insert(0) O(n)   in O(n)     sort O(n log n)
deque     index O(n)   append O(1)   appendleft O(1)  popleft O(1)
dict/set  get O(1)~    set O(1)~     del O(1)~        in O(1)~
heapq     push O(log n)  pop O(log n)  peek O(1)      heapify O(n)
tree      search O(log n)  insert O(log n)  in-order traversal O(n) sorted
```
`*` amortised · `~` average, worst O(n)

## After each drill, ask yourself the interviewer's question

*"Why this structure and not the obvious one?"* If you cannot answer in one sentence with a
complexity in it, you have not finished the drill.
