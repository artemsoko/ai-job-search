"""Usage metering and plan-limit enforcement.

The most likely shape of their live exercise: the PHP core emits usage events, this Python layer
aggregates them per account per billing period and decides whether an account may do more.

Say out loud before coding:
  * At-least-once delivery from the core means EVERY event needs an idempotency key, or you
    double-charge. This is the single most important design point.
  * Append-only events + rollup, versus a single incremented counter. Append is auditable and you
    can recompute; a counter is cheap but loses the trail. Billing usually wants the audit trail.
    Say which you'd choose and why.
  * Concurrency on the limit check: SELECT ... FOR UPDATE versus optimistic compare-and-set on a
    version column. YOU HAVE SHIPPED THE CAS APPROACH at Capital.com - say so.
  * Period boundaries: what happens to an event that arrives after the period closed?
  * Why the clock is injected and never called directly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class LimitExceeded(Exception):
    pass


@dataclass(frozen=True)
class UsageEvent:
    account_id: str
    event_id: str          # idempotency key from the core
    units: int
    at: float              # epoch seconds


@dataclass(frozen=True)
class Decision:
    allowed: bool
    used: int
    limit: int
    reason: str = ""


class MeteringService:
    def __init__(self, clock: Callable[[], float], period_seconds: float) -> None:
        """period_seconds defines the billing period, e.g. 30 days.

        Set up your state here. Suggested, but argue for your own:
          self._clock, self._period
          self._limits: dict[str, int]
          self._events: dict[str, list[UsageEvent]]     append-only, auditable
          self._seen: dict[tuple[str, str], Decision]   (account_id, event_id) -> decision
        """
        self._clock = clock
        self._period = period_seconds
        self._limits: dict[str, int] = {}

    def set_limit(self, account_id: str, limit: int) -> None:
        # Given to you - the plumbing is not the exercise.
        self._limits[account_id] = limit

    def record(self, event: UsageEvent) -> Decision:
        """Charge the event against the account's period usage.

        A replay of the same event_id must return the SAME decision and must NOT charge twice.
        An event that would push usage over the limit is rejected and NOT charged.
        """
        raise NotImplementedError

    def usage(self, account_id: str) -> int:
        """Units consumed in the current period."""
        raise NotImplementedError

    def remaining(self, account_id: str) -> int:
        raise NotImplementedError
