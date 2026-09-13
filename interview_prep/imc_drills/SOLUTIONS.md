# Reference solutions — do not open until the timer is done

They live in `solutions/`, one file per drill, and all 68 tests pass against them (verified).
To check your own work against a reference, diff the approach, not the characters — several of
these have more than one right answer and the interview cares about which you can justify.

| Drill | Reference | The one thing the solution demonstrates |
|---|---|---|
| 1 order book | `solutions/order_book.py` | **Lazy deletion.** Cancels flip a `live` flag; the heap is only pruned when a best price is read. Nothing is ever removed from the middle of a heap. |
| 2 top-K | `solutions/top_k.py` | `heapq.nsmallest(k, ...)` is a size-k heap internally, so O(m log k) not O(m log m). |
| 3 window max | `solutions/window_max.py` | Monotonic deque of **indices**, so eviction by position is O(1). A heap cannot do that cheaply. |
| 4 LRU | `solutions/lru.py` | `OrderedDict.move_to_end` — and the line to say aloud: OrderedDict *is* a dict plus a doubly linked list. |
| 5 quota | `solutions/quota.py` | Idempotency memo checked **before** charging, and CAS that bumps a version so a stale writer loses. |
| 6 merge K | `solutions/merge_k.py` | A generator holding K heads, `(value, idx, iterator)` so ties never compare iterators. |

## Where each drill will bite you

- **Order book:** the trade price is the **maker's** price, not the taker's. And after cancelling
  the top of the book, `best_bid()` must recover — that is the lazy-deletion test.
- **Top-K:** ties. Decide the rule and state it; in a real interview, ask.
- **Window max:** `while values[dq[-1]] <= v` uses `<=` not `<`, otherwise equal values pile up.
- **LRU:** `get()` counts as a use. Forgetting that is the classic bug.
- **Quota:** a denied request must also be memoised, or a replay of a denial re-checks and can
  flip to allowed once the window slides.
- **Merge K:** if you call `list(stream)` anywhere, the infinite-stream test hangs.
