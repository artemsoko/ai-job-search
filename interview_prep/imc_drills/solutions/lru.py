from __future__ import annotations

from collections import OrderedDict


class LRUCache:
    """OrderedDict IS a dict + doubly linked list. Say that in the interview."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._cap = capacity
        self._data: OrderedDict[str, int] = OrderedDict()

    def get(self, key: str) -> int | None:
        if key not in self._data:
            return None
        self._data.move_to_end(key, last=False)   # front = most recent
        return self._data[key]

    def put(self, key: str, value: int) -> None:
        if key in self._data:
            self._data.move_to_end(key, last=False)
            self._data[key] = value
            return
        self._data[key] = value
        self._data.move_to_end(key, last=False)
        if len(self._data) > self._cap:
            self._data.popitem(last=True)         # back = least recent

    def __len__(self) -> int:
        return len(self._data)

    def keys_mru_first(self) -> list[str]:
        return list(self._data.keys())
