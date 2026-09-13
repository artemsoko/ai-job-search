"""Maximum in every sliding window of size w.

Out loud before coding:
  * Naive: max() per window -> O(n*w).
  * Heap: O(n log n) and you need lazy deletion of out-of-window entries.
  * Monotonic deque: O(n) total, each index pushed and popped at most once.
  * SAY WHY NOT A HEAP HERE: the window evicts by POSITION, not by value, so a heap ordered by
    value cannot cheaply drop the element that just fell out of the window.
"""
from __future__ import annotations


def sliding_window_max(values: list[int], w: int) -> list[int]:
    """One maximum per window position. len(result) == len(values) - w + 1."""
    raise NotImplementedError
