import pytest

from plans import Charge, InvalidTransition, Plan, Status, Subscriptions

BASIC = Plan("basic", 1000)
PRO = Plan("pro", 3000)


class FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def subs(clock):
    return Subscriptions(clock=clock, period_seconds=100.0)


def test_subscribe_charges_full_price(subs):
    c = subs.subscribe("a", BASIC, "c1")
    assert c.cents == 1000
    assert subs.status("a") == Status.ACTIVE
    assert subs.current_plan("a") == BASIC


def test_subscribe_is_idempotent(subs):
    first = subs.subscribe("a", BASIC, "c1")
    second = subs.subscribe("a", BASIC, "c1")
    assert first == second
    assert subs.current_plan("a") == BASIC


def test_upgrade_applies_immediately(subs, clock):
    subs.subscribe("a", BASIC, "c1")
    clock.advance(50)                      # half the period gone
    subs.change_plan("a", PRO, "c2")
    assert subs.current_plan("a") == PRO
    assert subs.scheduled_plan("a") is None


def test_upgrade_is_prorated_for_the_remaining_period(subs, clock):
    subs.subscribe("a", BASIC, "c1")
    clock.advance(50)                      # 50% remaining
    charge = subs.change_plan("a", PRO, "c2")
    # difference is 2000 cents for half a period
    assert charge is not None
    assert charge.cents == 1000


def test_upgrade_at_period_start_charges_the_full_difference(subs):
    subs.subscribe("a", BASIC, "c1")
    charge = subs.change_plan("a", PRO, "c2")
    assert charge.cents == 2000


def test_downgrade_is_scheduled_and_charges_nothing(subs, clock):
    subs.subscribe("a", PRO, "c1")
    clock.advance(50)
    charge = subs.change_plan("a", BASIC, "c2")
    assert charge is None
    assert subs.current_plan("a") == PRO           # still on PRO, they paid for it
    assert subs.scheduled_plan("a") == BASIC
    assert subs.status("a") == Status.PENDING_DOWNGRADE


def test_scheduled_downgrade_applies_at_period_end(subs, clock):
    subs.subscribe("a", PRO, "c1")
    subs.change_plan("a", BASIC, "c2")
    clock.advance(101)
    subs.tick()
    assert subs.current_plan("a") == BASIC
    assert subs.scheduled_plan("a") is None
    assert subs.status("a") == Status.ACTIVE


def test_upgrade_cancels_a_pending_downgrade(subs, clock):
    subs.subscribe("a", PRO, "c1")
    subs.change_plan("a", BASIC, "c2")             # downgrade pending
    subs.change_plan("a", PRO, "c3")               # changed their mind
    assert subs.scheduled_plan("a") is None
    assert subs.status("a") == Status.ACTIVE


def test_change_plan_is_idempotent(subs, clock):
    subs.subscribe("a", BASIC, "c1")
    a = subs.change_plan("a", PRO, "c2")
    b = subs.change_plan("a", PRO, "c2")
    assert a == b
    assert subs.current_plan("a") == PRO


def test_same_plan_change_is_a_no_op(subs):
    subs.subscribe("a", BASIC, "c1")
    assert subs.change_plan("a", BASIC, "c2") is None
    assert subs.current_plan("a") == BASIC


def test_cancel_keeps_access_until_period_end(subs, clock):
    subs.subscribe("a", PRO, "c1")
    subs.cancel("a", "c2")
    assert subs.current_plan("a") == PRO
    assert subs.status("a") != Status.CANCELLED
    clock.advance(101)
    subs.tick()
    assert subs.status("a") == Status.CANCELLED
    assert subs.current_plan("a") is None


def test_cancel_is_idempotent(subs):
    subs.subscribe("a", BASIC, "c1")
    subs.cancel("a", "c2")
    subs.cancel("a", "c2")
    assert subs.status("a") != Status.CANCELLED


def test_cannot_change_plan_on_an_unknown_account(subs):
    with pytest.raises(InvalidTransition):
        subs.change_plan("ghost", PRO, "c1")


def test_cannot_change_plan_after_cancellation_completed(subs, clock):
    subs.subscribe("a", BASIC, "c1")
    subs.cancel("a", "c2")
    clock.advance(101)
    subs.tick()
    with pytest.raises(InvalidTransition):
        subs.change_plan("a", PRO, "c3")


def test_tick_is_safe_to_call_repeatedly(subs, clock):
    subs.subscribe("a", PRO, "c1")
    subs.change_plan("a", BASIC, "c2")
    clock.advance(101)
    subs.tick()
    subs.tick()
    assert subs.current_plan("a") == BASIC
