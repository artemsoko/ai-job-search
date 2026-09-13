from __future__ import annotations

import heapq
from typing import Iterable, Iterator


def merge_sorted(streams: list[Iterable[int]]) -> Iterator[int]:
    heap: list[tuple[int, int, Iterator[int]]] = []
    for idx, stream in enumerate(streams):
        it = iter(stream)
        first = next(it, None)
        if first is not None:
            heap.append((first, idx, it))
    heapq.heapify(heap)
    while heap:
        value, idx, it = heapq.heappop(heap)
        yield value
        nxt = next(it, None)
        if nxt is not None:
            heapq.heappush(heap, (nxt, idx, it))
