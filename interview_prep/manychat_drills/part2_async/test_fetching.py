import asyncio
import time

import pytest
from fetching import (
    HttpClient,
    HttpError,
    fetch_all,
    fetch_all_tolerant,
    fetch_bounded,
    fetch_first_success,
    fetch_with_retry,
    fetch_with_timeout,
)

pytestmark = pytest.mark.asyncio


async def test_fetch_all_returns_in_input_order():
    c = HttpClient(responses={"a": 1, "b": 2, "c": 3})
    assert await fetch_all(c, ["c", "a", "b"]) == [3, 1, 2]


async def test_fetch_all_is_actually_concurrent():
    """Three 100ms requests must take ~100ms, not ~300ms."""
    c = HttpClient(responses={u: u for u in "abc"}, delays={u: 0.1 for u in "abc"})
    start = time.perf_counter()
    await fetch_all(c, ["a", "b", "c"])
    assert time.perf_counter() - start < 0.25


async def test_fetch_all_propagates_failure():
    c = HttpClient(responses={"a": 1}, failures={"b": 500})
    with pytest.raises(HttpError):
        await fetch_all(c, ["a", "b"])


async def test_fetch_all_empty_list():
    assert await fetch_all(HttpClient(), []) == []


async def test_tolerant_returns_exceptions_in_place():
    c = HttpClient(responses={"a": 1, "c": 3}, failures={"b": 500})
    got = await fetch_all_tolerant(c, ["a", "b", "c"])
    assert got[0] == 1
    assert isinstance(got[1], HttpError)
    assert got[2] == 3


async def test_tolerant_does_not_abort_the_batch():
    c = HttpClient(responses={"b": 2}, failures={"a": 500})
    got = await fetch_all_tolerant(c, ["a", "b"])
    assert isinstance(got[0], Exception) and got[1] == 2


async def test_first_success_returns_the_winner():
    c = HttpClient(responses={"slow": "s", "fast": "f"},
                   delays={"slow": 0.2, "fast": 0.01})
    assert await fetch_first_success(c, ["slow", "fast"]) == "f"


async def test_first_success_is_fast_because_it_cancels():
    c = HttpClient(responses={"slow": "s", "fast": "f"},
                   delays={"slow": 1.0, "fast": 0.01})
    start = time.perf_counter()
    await fetch_first_success(c, ["slow", "fast"])
    assert time.perf_counter() - start < 0.3


async def test_first_success_skips_failures():
    c = HttpClient(responses={"good": "g"}, failures={"bad": 500})
    assert await fetch_first_success(c, ["bad", "good"]) == "g"


async def test_first_success_raises_when_all_fail():
    c = HttpClient(failures={"a": 500, "b": 503})
    with pytest.raises(HttpError):
        await fetch_first_success(c, ["a", "b"])


async def test_timeout_raises():
    c = HttpClient(responses={"slow": 1}, delays={"slow": 1.0})
    with pytest.raises(asyncio.TimeoutError):
        await fetch_with_timeout(c, "slow", timeout=0.05)


async def test_timeout_returns_fast_result():
    c = HttpClient(responses={"quick": 42}, delays={"quick": 0.01})
    assert await fetch_with_timeout(c, "quick", timeout=1.0) == 42


async def test_timeout_actually_cancels_not_just_stops_waiting():
    c = HttpClient(responses={"slow": 1}, delays={"slow": 0.5})
    start = time.perf_counter()
    with pytest.raises(asyncio.TimeoutError):
        await fetch_with_timeout(c, "slow", timeout=0.05)
    assert time.perf_counter() - start < 0.2


async def test_bounded_respects_the_limit():
    urls = [str(i) for i in range(10)]
    c = HttpClient(responses={u: int(u) for u in urls}, delays={u: 0.05 for u in urls})
    got = await fetch_bounded(c, urls, limit=3)
    assert got == list(range(10))
    assert c.max_concurrent_seen <= 3


async def test_bounded_still_concurrent_within_the_limit():
    urls = [str(i) for i in range(6)]
    c = HttpClient(responses={u: int(u) for u in urls}, delays={u: 0.05 for u in urls})
    start = time.perf_counter()
    await fetch_bounded(c, urls, limit=3)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.2          # 2 waves of 0.05, not 6 serial
    assert c.max_concurrent_seen == 3


async def test_retry_succeeds_first_time():
    c = HttpClient(responses={"a": 1})
    assert await fetch_with_retry(c, "a", attempts=3) == 1
    assert len(c.calls) == 1


async def test_retry_gives_up_and_raises():
    c = HttpClient(failures={"a": 503})
    with pytest.raises(HttpError):
        await fetch_with_retry(c, "a", attempts=3)
    assert len(c.calls) == 3


async def test_retry_does_not_retry_4xx():
    c = HttpClient(failures={"a": 404})
    with pytest.raises(HttpError):
        await fetch_with_retry(c, "a", attempts=5)
    assert len(c.calls) == 1
