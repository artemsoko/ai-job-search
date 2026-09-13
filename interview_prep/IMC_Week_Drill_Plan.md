# IMC — one-week hard drill plan

## Read this first: IMC's station is NOT LeetCode

Riccardo confirmed on the recruiter call: **no LeetCode.** The 2–2.5h station gives you a task to
*implement* against **APIs and code that already exist**, you are expected to **dig the
requirements out yourself** (that part is scored), **Google is allowed and AI is not**, and their
own document says *"you are not expected to... necessarily solve the problem during the time
provided."* A first-hand account puts the difficulty at *"still about medium LeetCode
complexity"* and describes a shared PyCharm with **pre-written failing tests**.

So grinding a generic Blind-75 is the wrong training. What IS worth drilling is narrow:

1. **Writing correct Python cold, in an IDE, with no agent.** This is your real weakness — you
   live in Claude Code.
2. **Fluency in the five structures IMC named in their PDF** — Dynamic Array, Linked List,
   Hash Table, Binary Heap, Binary Search Tree. Their words: *"they should be a major part of
   your dialogue."* You must justify a choice out loud with a complexity in the sentence.
3. **Design-shaped problems**, because "implement against existing APIs" is closer to
   `Design X` than to `reverse a string`.

Everything below is chosen for those three. Every link was checked against the NeetCode
solutions repository, so the slugs are real.

> ⚠️ Note on the links: `neetcode.io` is a single-page app that returns HTTP 200 for **any**
> slug, including nonsense, so a link opening is not proof. I verified each slug instead against
> `github.com/neetcode-gh/leetcode` (394 solution files), which is why the LeetCode number is
> given alongside — if a link ever misbehaves, search the number.

## How to drill (this matters more than the problem list)

- **PyCharm. Claude Code and Copilot OFF.** Docs and search are fine, that mirrors the station.
- **Say the plan out loud before typing**: restate the problem, name the naive solution and its
  cost, name your choice and its cost, then code.
- **45 minutes per problem, hard stop.** If you are stuck at 30, look it up, understand it, and
  re-implement from scratch the next day.
- **Re-solve, do not re-read.** A problem you have only read is not learned.
- Keep a one-line note per problem: *"heap because I only need the current best, log n per
  update instead of n log n per query."* That sentence is the actual deliverable.

---

## Day 1 — Hash tables and arrays — the warm-up that is not optional

*Gets you typing Python cold again. Do all six; they should take under 3 hours total.*

- [two-sum](https://neetcode.io/problems/two-sum) · LC 1
- [group-anagrams](https://neetcode.io/problems/group-anagrams) · LC 49
- [top-k-frequent-elements](https://neetcode.io/problems/top-k-frequent-elements) · LC 347
- [product-of-array-except-self](https://neetcode.io/problems/product-of-array-except-self) · LC 238
- [longest-consecutive-sequence](https://neetcode.io/problems/longest-consecutive-sequence) · LC 128
- [valid-parentheses](https://neetcode.io/problems/valid-parentheses) · LC 20

**Say out loud on each:** why a dict and not a list, what the average vs worst case is, and what you give up (ordering, memory overhead).

## Day 2 — Heaps — the single most likely structure at a market maker

*A limit order book is a heap problem. If you drill one day hardest, make it this one.*

- [kth-largest-element-in-a-stream](https://neetcode.io/problems/kth-largest-element-in-a-stream) · LC 703
- [last-stone-weight](https://neetcode.io/problems/last-stone-weight) · LC 1046
- [k-closest-points-to-origin](https://neetcode.io/problems/k-closest-points-to-origin) · LC 973
- [kth-largest-element-in-an-array](https://neetcode.io/problems/kth-largest-element-in-an-array) · LC 215
- [task-scheduler](https://neetcode.io/problems/task-scheduler) · LC 621
- [find-median-from-data-stream](https://neetcode.io/problems/find-median-from-data-stream) · LC 295

**find-median-from-data-stream is the key one** — two heaps kept balanced. That two-heap pattern is exactly how you hold best-bid and best-ask. **Say:** why a heap and not a sorted list; why you cannot cheaply delete from the middle; what lazy deletion is and when you need it.

## Day 3 — Design problems — closest shape to the real station

*'Implement against existing APIs' is a design problem wearing a different hat.*

- [lru-cache](https://neetcode.io/problems/lru-cache) · LC 146
- [design-hashmap](https://neetcode.io/problems/design-hashmap) · LC 706
- [insert-delete-getrandom-o1](https://neetcode.io/problems/insert-delete-getrandom-o1) · LC 380
- [time-based-key-value-store](https://neetcode.io/problems/time-based-key-value-store) · LC 981
- [design-twitter](https://neetcode.io/problems/design-twitter) · LC 355
- [min-stack](https://neetcode.io/problems/min-stack) · LC 155

**design-twitter is the best single proxy for the station**: it forces dict + heap + linked-list thinking together, and there is no single right answer, so you have to justify. **insert-delete-getrandom-o1** teaches the dict+array swap trick, which is the same move as O(1) order cancellation by id.

## Day 4 — Sliding window and monotonic deque — streaming data

*Tick streams, rolling windows, and 'max over the last N' are daily work at a trading firm.*

- [best-time-to-buy-and-sell-stock](https://neetcode.io/problems/best-time-to-buy-and-sell-stock) · LC 121
- [longest-substring-without-repeating-characters](https://neetcode.io/problems/longest-substring-without-repeating-characters) · LC 3
- [permutation-in-string](https://neetcode.io/problems/permutation-in-string) · LC 567
- [sliding-window-maximum](https://neetcode.io/problems/sliding-window-maximum) · LC 239
- [daily-temperatures](https://neetcode.io/problems/daily-temperatures) · LC 739
- [car-fleet](https://neetcode.io/problems/car-fleet) · LC 853

**sliding-window-maximum is the one to nail.** Monotonic deque, O(n). **Say why NOT a heap:** the window evicts by *position*, and a heap ordered by *value* cannot cheaply drop the element that just fell out. That sentence is worth more than the code.

## Day 5 — Intervals, stacks, linked lists — the remaining fundamentals

*Rounds out the five structures. Intervals show up constantly in scheduling and rate decks.*

- [merge-intervals](https://neetcode.io/problems/merge-intervals) · LC 56
- [insert-interval](https://neetcode.io/problems/insert-interval) · LC 57
- [non-overlapping-intervals](https://neetcode.io/problems/non-overlapping-intervals) · LC 435
- [reverse-linked-list](https://neetcode.io/problems/reverse-linked-list) · LC 206
- [reorder-list](https://neetcode.io/problems/reorder-list) · LC 143
- [copy-list-with-random-pointer](https://neetcode.io/problems/copy-list-with-random-pointer) · LC 138
- [largest-rectangle-in-histogram](https://neetcode.io/problems/largest-rectangle-in-histogram) · LC 84

**largest-rectangle-in-histogram** is the hardest thing on this plan. If you are short on time, skip it and do the two linked-list ones twice instead — linked-list manipulation is what LRU is built on.

## Day 6 — Trees, tries, and merging streams

*BST is the fifth structure IMC named. You will not implement one, but you must talk about one.*

- [validate-binary-search-tree](https://neetcode.io/problems/validate-binary-search-tree) · LC 98
- [kth-smallest-element-in-a-bst](https://neetcode.io/problems/kth-smallest-element-in-a-bst) · LC 230
- [binary-tree-level-order-traversal](https://neetcode.io/problems/binary-tree-level-order-traversal) · LC 102
- [implement-trie-prefix-tree](https://neetcode.io/problems/implement-trie-prefix-tree) · LC 208
- [merge-k-sorted-lists](https://neetcode.io/problems/merge-k-sorted-lists) · LC 23

**merge-k-sorted-lists is the finale** — heap of iterators, O(N log K), and it must be lazy. **Say:** when a BST beats a hash table (ordered iteration and range queries) and that Python has no builtin balanced tree, so you would reach for `sortedcontainers`.

## Day 7 — no new problems. Consolidate.

1. **Re-solve, from a blank file, without notes:** `find-median-from-data-stream`,
   `lru-cache`, `sliding-window-maximum`, `merge-k-sorted-lists`. If any takes more than
   25 minutes, that is your weak spot — drill it again tomorrow.
2. **Say the five-structure table out loud** from `imc_drills/data_structures_drill.md` until
   it is automatic. This is the graded skill, not the coding.
3. **Do the order-book drill** in `imc_drills/drill1_order_book/` (19 failing tests, agent off).
   It is the closest thing in this repo to the real station: add/cancel/match limit orders with
   price-time priority, and it forces heap + dict + deque together with lazy deletion.
4. **Run the 17-question clarifying checklist** in `IMC_Coding_Station_Plan.md` against the
   order-book task as if a person were answering. Requirement-digging is scored.

---

## If you only have three days

Day 2 (heaps) → Day 3 (design) → Day 7 (order book + the spoken structure drill). That covers
the likely problem shape, the graded skill, and the format rehearsal.

## What NOT to spend time on

Dynamic programming, backtracking, graph algorithms beyond BFS/DFS, bit manipulation, and
anything labelled Hard on LeetCode. None of it matches a station described as *"a real-world
task an employee at IMC may need to solve"* against existing code, and none of it is in the five
structures they named. If you find yourself on a DP problem, you have drifted.

## Reminder about the other half of this round

The 60-minute interview with two Senior Python Engineers comes **before** the station, and they
**will challenge parts of your take-home**. Re-reading your own submission and preparing a
one-sentence "why this and not the obvious alternative" for every non-obvious decision is worth
more than any problem on this list. Send me the assignment and your code and I will run that
challenge against you first.

