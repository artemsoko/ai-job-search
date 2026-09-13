"""Reference solutions for part2_async — verified against all 18 tests.

Import shim: reuse the skeleton's HttpClient/HttpError so the fake client is identical.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fetching import HttpClient, HttpError  # noqa: E402


async def fetch_all(client: HttpClient, urls: list[str]) -> list[Any]:
    """gather: schedules everything, preserves INPUT order, re-raises the first failure."""
    return list(await asyncio.gather(*(client.get(u) for u in urls)))


async def fetch_all_tolerant(client: HttpClient, urls: list[str]) -> list[Any | Exception]:
    """Same call, one flag. Failures become VALUES at their own index."""
    return list(
        await asyncio.gather(*(client.get(u) for u in urls), return_exceptions=True)
    )


async def fetch_first_success(client: HttpClient, urls: list[str]) -> Any:
    """Race them. First success wins, losers get cancelled, last error survives."""
    if not urls:
        raise ValueError("no urls")

    pending = {asyncio.create_task(client.get(u), name=u) for u in urls}
    last_error: BaseException | None = None
    try:
        while pending:
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                try:
                    return task.result()
                except Exception as exc:
                    last_error = exc
        raise last_error  # type: ignore[misc]
    finally:
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)


async def fetch_with_timeout(client: HttpClient, url: str, timeout: float) -> Any:
    """asyncio.timeout CANCELS the body on expiry — it does not merely stop waiting."""
    async with asyncio.timeout(timeout):
        return await client.get(url)


async def fetch_bounded(client: HttpClient, urls: list[str], limit: int) -> list[Any]:
    """Concurrency cap. Semaphore is held only around the I/O, gather keeps order."""
    sem = asyncio.Semaphore(limit)

    async def one(url: str) -> Any:
        async with sem:
            return await client.get(url)

    return list(await asyncio.gather(*(one(u) for u in urls)))


async def fetch_with_retry(
    client: HttpClient, url: str, attempts: int, backoff: float = 0.0
) -> Any:
    """Retry transient (5xx) only. 4xx is a bug in my request — retrying can't fix it."""
    last_error: HttpError | None = None
    for n in range(attempts):
        try:
            return await client.get(url)
        except HttpError as exc:
            if exc.status < 500:
                raise
            last_error = exc
            if n < attempts - 1:
                await asyncio.sleep(backoff * 2**n)
    raise last_error  # type: ignore[misc]
