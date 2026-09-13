"""LRU cache with O(1) get and put.

Out loud before coding:
  * Two valid answers: dict + doubly linked list (what you'd write in C++/Java), or
    collections.OrderedDict.move_to_end (what you'd write in Python). KNOW BOTH, and say
    that OrderedDict *is* a dict + doubly linked list under the hood.
  * Why not a list for recency order? O(n) to move an element.
  * get() counts as a use. That is the classic bug: implement it and say so.
"""
from __future__ import annotations


class LRUCache:
    def __init__(self, capacity: int) -> None:
        pass

    def get(self, key: str) -> int | None:
        """Return the value and mark the key as most-recently-used, or None if absent."""
        raise NotImplementedError

    def put(self, key: str, value: int) -> None:
        """Insert or update, evicting the least-recently-used key when over capacity."""
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def keys_mru_first(self) -> list[str]:
        """Most-recently-used first. Exists so the tests can see your recency order."""
        raise NotImplementedError
