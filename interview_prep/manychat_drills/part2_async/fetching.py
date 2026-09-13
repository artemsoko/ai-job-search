"""Async I/O drill — exactly the ground Manychat named for Part 2.

Their focus list: async/await, concurrent execution, non-blocking HTTP calls, error handling in
async contexts.

`HttpClient` is a fake so the drill needs no network. Treat it as aiohttp/httpx: every call is a
coroutine that may raise, may be slow, and must not be awaited serially when it could run
concurrently.

Say out loud before coding each one:
  * Serial awaits in a loop is the classic mistake. N * latency instead of max(latency).
  * gather vs TaskGroup: gather(return_exceptions=True) collects failures as values; TaskGroup
    cancels siblings on the first error. Which one you want depends on whether partial results
    are useful. SAY WHICH AND WHY.
  * A timeout must cancel the work, not just stop waiting for it.
  * Unbounded concurrency will melt the upstream. A Semaphore is the fix.
  * Never block the event loop: no time.sleep, no requests.get, no CPU-bound work inline.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any


class HttpError(Exception):
    def __init__(self, status: int, url: str) -> None:
        super().__init__(f"{status} for {url}")
        self.status = status
        self.url = url


@dataclass
class HttpClient:
    """Fake async HTTP client. Configure responses, delays and failures per URL."""

    responses: dict[str, Any] = field(default_factory=dict)
    delays: dict[str, float] = field(default_factory=dict)
    failures: dict[str, int] = field(default_factory=dict)   # url -> status code
    calls: list[str] = field(default_factory=list)
    max_concurrent_seen: int = 0
    _in_flight: int = 0

    async def get(self, url: str) -> Any:
        self.calls.append(url)
        self._in_flight += 1
        self.max_concurrent_seen = max(self.max_concurrent_seen, self._in_flight)
        try:
            await asyncio.sleep(self.delays.get(url, 0))
            if url in self.failures:
                raise HttpError(self.failures[url], url)
            return self.responses.get(url)
        finally:
            self._in_flight -= 1


async def fetch_all(client: HttpClient, urls: list[str]) -> list[Any]:
    """Fetch every URL CONCURRENTLY, results in the same order as urls.

    If any request fails, let the exception propagate.
    """

    return list(await asyncio.gather(*(client.get(url) for url in urls)))


async def fetch_all_tolerant(client: HttpClient, urls: list[str]) -> list[Any | Exception]:
    """Same, but a failed URL yields its exception in place instead of aborting the batch."""
    return list(await asyncio.gather(*(client.get(url) for url in urls), return_exceptions=True))


async def fetch_first_success(client: HttpClient, urls: list[str]) -> Any:
    """Return the first successful response and CANCEL the rest.

    Raise the last error if every URL fails.
    """
    raise NotImplementedError


async def fetch_with_timeout(client: HttpClient, url: str, timeout: float) -> Any:
    """Return the response, or raise asyncio.TimeoutError. Must actually cancel the request."""
    async with await client.get(url, timeout=timeout) as response:



async def fetch_bounded(client: HttpClient, urls: list[str], limit: int) -> list[Any]:
    """Fetch concurrently but never more than `limit` requests in flight at once."""
    raise NotImplementedError


async def fetch_with_retry(
    client: HttpClient, url: str, attempts: int, backoff: float = 0.0
) -> Any:
    """Retry on HttpError with 5xx. Do NOT retry 4xx - that is a client bug, not a blip.

    Sleep `backoff * 2**n` between attempts. Raise the last error when attempts run out.
    """
    raise NotImplementedError
