import pytest

from quota import QuotaExceeded, SlidingWindowQuota, StaleVersion, VersionedCounter


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


def test_allows_up_to_the_limit(clock):
    q = SlidingWindowQuota(limit=3, window_seconds=60, clock=clock)
    assert [q.allow("u1") for _ in range(3)] == [True, True, True]


def test_blocks_over_the_limit(clock):
    q = SlidingWindowQuota(limit=2, window_seconds=60, clock=clock)
    q.allow("u1")
    q.allow("u1")
    assert q.allow("u1") is False


def test_keys_are_independent(clock):
    q = SlidingWindowQuota(limit=1, window_seconds=60, clock=clock)
    assert q.allow("u1") is True
    assert q.allow("u2") is True
    assert q.allow("u1") is False


def test_window_slides(clock):
    q = SlidingWindowQuota(limit=1, window_seconds=10, clock=clock)
    assert q.allow("u1") is True
    clock.advance(9)
    assert q.allow("u1") is False
    clock.advance(2)          # first request is now outside the window
    assert q.allow("u1") is True


def test_remaining_reflects_usage(clock):
    q = SlidingWindowQuota(limit=3, window_seconds=60, clock=clock)
    assert q.remaining("u1") == 3
    q.allow("u1")
    assert q.remaining("u1") == 2


def test_remaining_recovers_as_window_slides(clock):
    q = SlidingWindowQuota(limit=2, window_seconds=10, clock=clock)
    q.allow("u1")
    q.allow("u1")
    assert q.remaining("u1") == 0
    clock.advance(11)
    assert q.remaining("u1") == 2


def test_idempotent_request_is_not_charged_twice(clock):
    q = SlidingWindowQuota(limit=1, window_seconds=60, clock=clock)
    assert q.allow("u1", request_id="r1") is True
    assert q.allow("u1", request_id="r1") is True     # replay, same answer
    assert q.remaining("u1") == 0                      # charged once only


def test_idempotent_denial_is_also_replayed(clock):
    q = SlidingWindowQuota(limit=1, window_seconds=60, clock=clock)
    q.allow("u1", request_id="r1")
    assert q.allow("u1", request_id="r2") is False
    assert q.allow("u1", request_id="r2") is False


def test_cas_spend_and_version_bump():
    c = VersionedCounter(limit=10)
    used, version = c.read()
    assert (used, version) == (0, 0)
    new_version = c.try_spend(4, expected_version=version)
    assert new_version != version
    assert c.read()[0] == 4


def test_cas_rejects_stale_version():
    c = VersionedCounter(limit=10)
    _, v0 = c.read()
    c.try_spend(1, expected_version=v0)
    with pytest.raises(StaleVersion):
        c.try_spend(1, expected_version=v0)


def test_cas_refuses_to_overspend():
    c = VersionedCounter(limit=5)
    _, v = c.read()
    with pytest.raises(QuotaExceeded):
        c.try_spend(6, expected_version=v)
    assert c.read()[0] == 0


def test_concurrent_spenders_cannot_exceed_limit():
    """Two readers see the same version; only one spend may land."""
    c = VersionedCounter(limit=1)
    _, va = c.read()
    _, vb = c.read()
    c.try_spend(1, expected_version=va)
    with pytest.raises(StaleVersion):
        c.try_spend(1, expected_version=vb)
    assert c.read()[0] == 1
