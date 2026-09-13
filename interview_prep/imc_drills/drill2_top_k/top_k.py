"""Top-K most frequent items from a stream.

Out loud before coding:
  * Naive: count everything, sort by count -> O(n + m log m) where m = distinct items.
  * Better: count, then keep a size-K min-heap -> O(n + m log K). Say why that wins when K << m.
  * When is sorting actually fine? (small m, or you need the full ordering anyway)
  * Ties: this spec breaks them by the item itself, ascending. Ask about tie rules in a real one.
"""
from __future__ import annotations

from typing import Iterable


def top_k_frequent(items: Iterable[str], k: int) -> list[str]:
    """Return the k most frequent items, most frequent first, ties broken by item ascending."""
    raise NotImplementedError


class StreamingTopK:
    """Same thing but fed one item at a time, so it must hold state."""

    def __init__(self, k: int) -> None:
        pass

    def add(self, item: str) -> None:
        raise NotImplementedError

    def top(self) -> list[str]:
        raise NotImplementedError
