import pytest

from metering import Decision, MeteringService, UsageEvent


class FakeClock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def svc(clock):
    s = MeteringService(clock=clock, period_seconds=100.0)
    s.set_limit("acct", 10)
    return s


def ev(eid, units, at, account="acct"):
    return UsageEvent(account_id=account, event_id=eid, units=units, at=at)


def test_unknown_account_has_no_usage(svc):
    assert svc.usage("nobody") == 0


def test_records_usage(svc, clock):
    d = svc.record(ev("e1", 3, clock()))
    assert d.allowed is True
    assert svc.usage("acct") == 3
    assert svc.remaining("acct") == 7


def test_accumulates_across_events(svc, clock):
    svc.record(ev("e1", 3, clock()))
    svc.record(ev("e2", 4, clock()))
    assert svc.usage("acct") == 7


def test_rejects_event_that_would_exceed_limit(svc, clock):
    svc.record(ev("e1", 8, clock()))
    d = svc.record(ev("e2", 5, clock()))
    assert d.allowed is False
    assert svc.usage("acct") == 8          # the rejected event was NOT charged


def test_allows_event_that_exactly_hits_the_limit(svc, clock):
    d = svc.record(ev("e1", 10, clock()))
    assert d.allowed is True
    assert svc.remaining("acct") == 0


def test_replay_of_same_event_id_is_not_charged_twice(svc, clock):
    first = svc.record(ev("e1", 4, clock()))
    second = svc.record(ev("e1", 4, clock()))
    assert first.allowed == second.allowed is True
    assert svc.usage("acct") == 4


def test_replay_of_a_rejection_returns_the_same_decision(svc, clock):
    svc.record(ev("e1", 9, clock()))
    a = svc.record(ev("e2", 5, clock()))
    b = svc.record(ev("e2", 5, clock()))
    assert a.allowed is False and b.allowed is False
    assert svc.usage("acct") == 9


def test_replay_is_scoped_per_account(clock):
    s = MeteringService(clock=clock, period_seconds=100.0)
    s.set_limit("a", 5)
    s.set_limit("b", 5)
    s.record(UsageEvent("a", "shared-id", 2, clock()))
    s.record(UsageEvent("b", "shared-id", 2, clock()))
    assert s.usage("a") == 2
    assert s.usage("b") == 2


def test_accounts_are_independent(clock):
    s = MeteringService(clock=clock, period_seconds=100.0)
    s.set_limit("a", 1)
    s.set_limit("b", 1)
    assert s.record(UsageEvent("a", "e1", 1, clock())).allowed is True
    assert s.record(UsageEvent("b", "e2", 1, clock())).allowed is True
    assert s.record(UsageEvent("a", "e3", 1, clock())).allowed is False


def test_usage_resets_when_the_period_rolls(svc, clock):
    svc.record(ev("e1", 10, clock()))
    assert svc.remaining("acct") == 0
    clock.advance(101)
    assert svc.usage("acct") == 0
    assert svc.record(ev("e2", 5, clock())).allowed is True


def test_raising_the_limit_frees_capacity(svc, clock):
    svc.record(ev("e1", 10, clock()))
    assert svc.record(ev("e2", 1, clock())).allowed is False
    svc.set_limit("acct", 20)
    assert svc.record(ev("e3", 1, clock())).allowed is True


def test_decision_reports_used_and_limit(svc, clock):
    d = svc.record(ev("e1", 2, clock()))
    assert (d.used, d.limit) == (2, 10)


def test_rejects_non_positive_units(svc, clock):
    with pytest.raises(ValueError):
        svc.record(ev("e1", 0, clock()))


def test_account_with_no_limit_set_is_rejected_not_unlimited(clock):
    """Fail closed, not open. Say this out loud: in billing, unknown means deny."""
    s = MeteringService(clock=clock, period_seconds=100.0)
    d = s.record(UsageEvent("unconfigured", "e1", 1, clock()))
    assert d.allowed is False
