from __future__ import annotations

from collections import deque


def sliding_window_max(values: list[int], w: int) -> list[int]:
    if w <= 0:
        raise ValueError("window must be positive")
    if not values:
        return []
    if w > len(values):
        raise ValueError("window larger than input")
    out: list[int] = []
    dq: deque[int] = deque()          # indices, values decreasing front->back
    for i, v in enumerate(values):
        while dq and values[dq[-1]] <= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - w:
            dq.popleft()
        if i >= w - 1:
            out.append(values[dq[0]])
    return out
