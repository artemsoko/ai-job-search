"""A starting shape for Part 3. Type this from memory until it takes under ten minutes.

Not meant to be run against a real provider - the point is the SHAPE: ports, concurrency,
timeouts, retries, schema validation of model output, and a fake for tests.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from typing import Protocol

# --- ports -------------------------------------------------------------------


class LLMProvider(Protocol):
    async def complete(self, prompt: str, *, timeout: float) -> str: ...


class ContextAPI(Protocol):
    async def account_context(self, account_id: str, *, timeout: float) -> dict: ...


# --- domain models (Pydantic in the real thing; dataclasses here to stay dependency-free) ---


@dataclass(frozen=True)
class ClassifyRequest:
    conversation_id: str
    account_id: str
    text: str


@dataclass(frozen=True)
class Classification:
    intent: str
    confidence: float
    suggested_reply: str | None = None


class UpstreamUnavailable(Exception):
    """Raised when a dependency failed in a way the caller must be told about."""


# --- service -----------------------------------------------------------------


class ClassifierService:
    def __init__(
        self,
        llm: LLMProvider,
        context_api: ContextAPI,
        *,
        llm_timeout: float = 5.0,
        api_timeout: float = 2.0,
        attempts: int = 3,
        max_concurrent_llm: int = 10,
    ) -> None:
        self._llm = llm
        self._api = context_api
        self._llm_timeout = llm_timeout
        self._api_timeout = api_timeout
        self._attempts = attempts
        self._sem = asyncio.Semaphore(max_concurrent_llm)
        self._cache: dict[str, Classification] = {}

    @staticmethod
    def _cache_key(req: ClassifyRequest) -> str:
        # Normalise before hashing, or the cache never hits.
        norm = " ".join(req.text.lower().split())
        return hashlib.sha256(f"{req.account_id}:{norm}".encode()).hexdigest()

    async def classify(self, req: ClassifyRequest) -> Classification:
        key = self._cache_key(req)
        if cached := self._cache.get(key):
            return cached

        # The two calls are independent -> run them concurrently.
        # GOTCHA worth saying out loud: TaskGroup wraps a child failure in an ExceptionGroup, so
        # `except UpstreamUnavailable` at the FastAPI layer will NOT catch it - you need `except*`,
        # or catch the group and unwrap. Verified: a failing child surfaces as
        # ExceptionGroup([UpstreamUnavailable]). This is the concrete difference from
        # asyncio.gather, which re-raises the first exception bare. Mention it if you use
        # TaskGroup, because it changes your error contract.
        async with asyncio.TaskGroup() as tg:
            ctx_task = tg.create_task(self._fetch_context(req.account_id))
            raw_task = tg.create_task(self._ask_llm(req))
        _ctx, raw = ctx_task.result(), raw_task.result()

        result = self._parse(raw)
        self._cache[key] = result
        return result

    async def _fetch_context(self, account_id: str) -> dict:
        try:
            return await self._api.account_context(account_id, timeout=self._api_timeout)
        except (TimeoutError, asyncio.TimeoutError):
            # Enrichment is best-effort; degrade rather than fail the request.
            return {}

    async def _ask_llm(self, req: ClassifyRequest) -> str:
        last: Exception | None = None
        for n in range(self._attempts):
            try:
                async with self._sem:
                    return await self._llm.complete(self._prompt(req), timeout=self._llm_timeout)
            except (TimeoutError, asyncio.TimeoutError) as exc:
                last = exc
                await asyncio.sleep(0.1 * 2**n)      # add jitter in the real thing
        raise UpstreamUnavailable("model provider unavailable") from last

    @staticmethod
    def _prompt(req: ClassifyRequest) -> str:
        return (
            "Classify the customer message. Reply with JSON only, keys: "
            'intent (string), confidence (0-1 float), suggested_reply (string or null).\n\n'
            f"Message: {req.text}"
        )

    @staticmethod
    def _parse(raw: str) -> Classification:
        """Model output is UNTRUSTED INPUT. Validate it, never pass it through."""
        try:
            data = json.loads(raw)
            intent = data["intent"]
            confidence = float(data["confidence"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise UpstreamUnavailable("model returned malformed output") from exc
        if not isinstance(intent, str) or not 0.0 <= confidence <= 1.0:
            raise UpstreamUnavailable("model returned out-of-range values")
        reply = data.get("suggested_reply")
        return Classification(intent=intent, confidence=confidence,
                              suggested_reply=reply if isinstance(reply, str) else None)


# --- the FastAPI layer, for reference -----------------------------------------
#
# app = FastAPI()
#
# @app.post("/v1/messages/classify", response_model=ClassificationOut, status_code=200)
# async def classify(body: ClassifyIn, svc: ClassifierService = Depends(get_service)):
#     try:
#         return await svc.classify(ClassifyRequest(**body.model_dump()))
#     except UpstreamUnavailable as exc:
#         raise HTTPException(status_code=503, detail="classification unavailable") from exc
#
# The client is built once at startup and shared:
# @asynccontextmanager
# async def lifespan(app): async with httpx.AsyncClient(timeout=...) as c: ...
