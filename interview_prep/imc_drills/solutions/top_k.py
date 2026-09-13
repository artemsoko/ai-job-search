from __future__ import annotations

import heapq
from collections import Counter
from typing import Iterable


def top_k_frequent(items: Iterable[str], k: int) -> list[str]:
    if k < 0:
        raise ValueError("k must be non-negative")
    if k == 0:
        return []
    counts = Counter(items)
    # nlargest is a size-k heap internally: O(m log k), not a full sort.
    return [item for item, _ in heapq.nsmallest(k, counts.items(), key=lambda kv: (-kv[1], kv[0]))]


class StreamingTopK:
    def __init__(self, k: int) -> None:
        if k < 0:
            raise ValueError("k must be non-negative")
        self._k = k
        self._counts: Counter[str] = Counter()

    def add(self, item: str) -> None:
        self._counts[item] += 1

    def top(self) -> list[str]:
        if self._k == 0:
            return []
        return [i for i, _ in heapq.nsmallest(self._k, self._counts.items(),
                                              key=lambda kv: (-kv[1], kv[0]))]
