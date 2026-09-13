"""Per-key quota with a sliding window, plus optimistic-locking accounting.

THIS ONE IS YOUR STORY. You shipped exactly this at Capital.com: real-time frequency caps with
optimistic-locking quota accounting and idempotent decisions. Say that out loud while you code
it, and name the parallel: "frequency cap" -> "plan limit", "consent" -> "entitlement".

Out loud before coding:
  * Fixed window vs sliding window: the fixed-window burst problem at the boundary.
  * Why a deque of timestamps per key, and what it costs in memory at scale.
  * Idempotency: the same request_id must not be charged twice. Why that matters for billing.
  * Concurrency: compare-and-set on a version counter vs SELECT ... FOR UPDATE. You have
    shipped the CAS approach - say why you chose it.
  * Clock is injected, never called directly. Say why: testability, and clock skew in prod.
"""
from __future__ import annotations

from typing import Callable


class QuotaExceeded(Exception):
    pass


class StaleVersion(Exception):
    """Raised when a compare-and-set loses the race."""


class SlidingWindowQuota:
    def __init__(self, limit: int, window_seconds: float, clock: Callable[[], float]) -> None:
        """limit requests per window_seconds, per key. clock() returns seconds as a float."""
        pass

    def allow(self, key: str, request_id: str | None = None) -> bool:
        """True if the request fits in the quota, and charge it.

        If request_id is given and has been seen before for this key, return the SAME answer
        as last time and do NOT charge again.
        """
        raise NotImplementedError

    def remaining(self, key: str) -> int:
        raise NotImplementedError


class VersionedCounter:
    """Compare-and-set accounting, the pattern you used in production."""

    def __init__(self, limit: int) -> None:
        pass

    def read(self) -> tuple[int, int]:
        """Return (used, version)."""
        raise NotImplementedError

    def try_spend(self, amount: int, expected_version: int) -> int:
        """Spend if version matches and the limit allows. Return the new version.

        Raise StaleVersion if expected_version is not current.
        Raise QuotaExceeded if the spend would exceed the limit.
        """
        raise NotImplementedError
