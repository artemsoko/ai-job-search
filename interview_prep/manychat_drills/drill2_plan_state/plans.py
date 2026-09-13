"""Subscription plan state machine: upgrade, downgrade, cancel, reactivate — idempotently.

Say out loud before coding:
  * Model the ALLOWED TRANSITIONS as data (a dict of state -> allowed next states), not as
    if/elif. Same open/closed argument as a rules table.
  * Upgrades take effect immediately (the customer paid for more now). Downgrades take effect at
    period end (they already paid for this period). This asymmetry is the whole point of the
    exercise - state it before you code it.
  * Proration: charge the difference for the remaining fraction of the period, rounded how?
    Ask, then say your assumption.
  * Idempotency: the same change_id applied twice must not double-charge or double-transition.
  * What is the state of a cancelled subscription that is still inside its paid period?
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class Status(Enum):
    ACTIVE = "active"
    PENDING_DOWNGRADE = "pending_downgrade"
    CANCELLED = "cancelled"          # cancelled and the paid period has ended


class InvalidTransition(Exception):
    pass


@dataclass(frozen=True)
class Plan:
    code: str
    monthly_cents: int


@dataclass(frozen=True)
class Charge:
    account_id: str
    cents: int
    reason: str


class Subscriptions:
    def __init__(self, clock: Callable[[], float], period_seconds: float) -> None:
        # Model the allowed transitions as DATA, not if/elif. Suggested state per account:
        #   plan, scheduled_plan, status, period_start, cancel_at_period_end
        # plus a dict of change_id -> result for idempotency.
        self._clock = clock
        self._period = period_seconds

    def subscribe(self, account_id: str, plan: Plan, change_id: str) -> Charge:
        """Start a subscription. Charges the full plan price."""
        raise NotImplementedError

    def status(self, account_id: str) -> Status:
        raise NotImplementedError

    def current_plan(self, account_id: str) -> Plan | None:
        """The plan in effect right now."""
        raise NotImplementedError

    def scheduled_plan(self, account_id: str) -> Plan | None:
        """The plan that takes effect at period end, if a downgrade is pending."""
        raise NotImplementedError

    def change_plan(self, account_id: str, plan: Plan, change_id: str) -> Charge | None:
        """Upgrade takes effect NOW with a prorated charge.

        Downgrade is scheduled for period end and charges nothing (returns None).
        """
        raise NotImplementedError

    def cancel(self, account_id: str, change_id: str) -> None:
        """Cancel at period end. Access continues until then."""
        raise NotImplementedError

    def tick(self) -> None:
        """Apply anything that was scheduled for period end. Called when the clock has moved."""
        raise NotImplementedError
