from __future__ import annotations

from collections import defaultdict, deque
from typing import Callable


class QuotaExceeded(Exception):
    pass


class StaleVersion(Exception):
    pass


class SlidingWindowQuota:
    def __init__(self, limit: int, window_seconds: float, clock: Callable[[], float]) -> None:
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._decisions: dict[tuple[str, str], bool] = {}

    def _evict(self, key: str) -> None:
        cutoff = self._clock() - self._window
        dq = self._hits[key]
        while dq and dq[0] <= cutoff:
            dq.popleft()

    def allow(self, key: str, request_id: str | None = None) -> bool:
        if request_id is not None:
            prior = self._decisions.get((key, request_id))
            if prior is not None:
                return prior              # idempotent replay, not charged again
        self._evict(key)
        ok = len(self._hits[key]) < self._limit
        if ok:
            self._hits[key].append(self._clock())
        if request_id is not None:
            self._decisions[(key, request_id)] = ok
        return ok

    def remaining(self, key: str) -> int:
        self._evict(key)
        return max(0, self._limit - len(self._hits[key]))


class VersionedCounter:
    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._used = 0
        self._version = 0

    def read(self) -> tuple[int, int]:
        return self._used, self._version

    def try_spend(self, amount: int, expected_version: int) -> int:
        if expected_version != self._version:
            raise StaleVersion(f"expected {expected_version}, have {self._version}")
        if self._used + amount > self._limit:
            raise QuotaExceeded(f"{self._used}+{amount} > {self._limit}")
        self._used += amount
        self._version += 1
        return self._version
