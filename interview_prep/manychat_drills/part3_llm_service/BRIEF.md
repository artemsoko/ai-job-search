# Part 3 — Applied backend / AI case study

Manychat's wording: *"you'll build a small backend service integrating an LLM and external APIs.
Focus: API design, async usage, state and error handling, and production thinking (reliability,
maintainability)."*

## First, the thing to get straight in your head

**This is not ML engineering.** You are not training a model, not building an agent framework, not
writing a RAG pipeline from scratch. You are building a **backend service that calls an LLM API
as one more unreliable external dependency** — alongside another external API — and making the
whole thing behave in production.

That is squarely your job description. Your honest position stays intact: you are a user of LLMs,
not a model builder. Nothing in Part 3 asks you to be one. Do not hedge or apologise here — treat
the LLM as a slow, expensive, occasionally-wrong HTTP call and design accordingly. **That framing
is itself the senior answer.**

## The likely shape

Something like: an endpoint that takes user text, enriches it from an external API, asks an LLM to
do something with it, and returns a structured result.

**And now with the recruiter's confirmation that they are rewriting billing in Python, a
billing-flavoured variant is a live possibility.** A company mid-migration tends to reach for its
own problem when inventing an exercise. Plausible framings:

- An endpoint that takes a usage event from the core, records it idempotently, and asks an LLM to
  categorise or explain a charge. **Metering plus an LLM.**
- A service that answers "why is my invoice this amount" by fetching line items from an external
  API and having the model explain them in plain language.
- Entitlement checking: given an account and a requested action, fetch the plan from an API and
  have the model resolve an ambiguous policy question.

If it goes that way, everything in `../drill1_metering/` applies directly: idempotency keys on
every event because the core delivers at-least-once, append-only events versus a counter, fail
closed when a limit is unknown, and period-boundary handling. **Say those unprompted** — you built
that exact machinery at Capital.com, and in a billing rewrite it is the most relevant thing about
you.

Two more sentences worth having ready, because this is a *rewrite*:

> "Since you're carving billing out of the PHP core, I'd assume the core keeps emitting events
> during the migration and both systems are live for a while. Is that right? Because then the
> Python side needs to be idempotent and replay-safe by construction, not as a later hardening
> step."

> "I've done this shape before: I took the critical send path out of an existing pipeline rather
> than rewriting the pipeline, and pushed idempotency down to the database so a retry physically
> couldn't double-send. In billing that's the difference between a bug and a double charge."

## Say these out loud — this is what "production thinking" means to them

Work through this list in the design conversation. Each one is a point.

### API design
- `POST` returning a structured response; Pydantic models for request and response so validation
  is declarative and the schema is self-documenting.
- Explicit error contract: which status codes, and what the body looks like on failure. Never leak
  a provider error verbatim to the caller.
- Versioned path or header, because the response shape will change.
- If generation is slow: return `202` with a job id and let the client poll, or stream. **Say that
  you'd ask which the client needs** rather than assuming.

### Async usage
- Every outbound call is `await`ed; the LLM call and the external API call run **concurrently**
  when they don't depend on each other, `asyncio.gather` or a `TaskGroup`.
- One shared client with a connection pool, created at app startup, not per request.
- Nothing blocking in a handler: no `requests`, no `time.sleep`, no JSON-parsing a 50MB payload
  inline. CPU-bound work goes to a thread or process pool.

### Reliability — the heart of it
- **Timeouts on every external call.** An LLM with no timeout will hang a worker indefinitely.
  Separate connect and read timeouts.
- **Retries with exponential backoff and jitter**, on 5xx and timeouts only. Never retry a 400.
- **Idempotency key** on the write path, so a client retry doesn't produce a second charge or a
  second generation. *You have shipped exactly this* — say so.
- **Circuit breaker or bulkhead** so a dead provider degrades one feature instead of the service.
- **A fallback**: cached answer, a cheaper model, or an honest "unavailable" — decide and say
  which. Silent failure is the worst option.
- **Bounded concurrency** to the provider, because they rate-limit you and you will hit it.

### State and correctness
- Where does state live, and is the handler stateless? (It should be.)
- LLM output is untrusted input: **validate it against a schema** before returning it. If you
  asked for JSON, parse it and reject malformed output rather than passing it through.
- What happens on a partial failure — enrichment succeeded, generation failed? Do you return
  partial data, and is that in the contract?

### Cost and observability
- LLM calls cost money per token. **Cache** on a hash of the normalised input. Say what the cache
  key is and what invalidates it.
- Log latency, token counts and error rates per provider. Trace ids across both external calls.
- **Never log the prompt or the response verbatim if it contains user data** — that's a GDPR
  problem, and Manychat handles end-user conversations, so say this unprompted. It will land.

### Maintainability
- The provider sits behind a **port** (a Protocol), so it can be faked in tests and swapped for
  another vendor. This is the same seam you used for the RNG in the IMC scaffold.
- Tests use a fake provider, not the network. No test should need an API key.

## Rehearse this, from a blank CoderPad, in 40 minutes

```
POST /v1/messages/classify
  body: {"conversation_id": str, "text": str}
  returns: {"intent": str, "confidence": float, "suggested_reply": str | None}
```

Behaviour: fetch the account's context from an external API, call the LLM to classify the text and
draft a reply, validate the LLM's JSON against a schema, return the result. Concurrent where
possible, timeouts everywhere, retries on 5xx, idempotent per `conversation_id` + text hash,
cached, and with a fake provider in tests.

**Order of work in the interview:** get a working endpoint with a hardcoded happy path FIRST, say
out loud which production concerns you are deferring and why, then add them in priority order.
Their own tip: *"Aim for a clear, working solution first, then improve it if time allows."*

## The one-liner if they ask about your AI experience

> "I use LLMs daily as an engineering tool — I work in Claude Code — and I'd treat a model
> provider in production the way I treat any unreliable third party: behind a port, with timeouts,
> retries, bounded concurrency, a schema check on the way out and a fallback. What I haven't done
> is build models or agent frameworks from scratch, and I'd rather be clear about that."
