# Тримати відкритим під час дзвінка

## Перед кожною відповіддю — 3 секунди

1. **Три речення:** вивід → механізм → фікс/наслідок
2. **Порахуй елементи** структури й назви стільку ж. `()` і `{}` — це елементи
3. **Сказав висновок** → викинь усе, що йому суперечить. Вголос: *"wait — if those are the same object, my earlier answer was wrong…"*
4. **Назвав фікс** → назви символ, який змінив

## НЕ казати

- ❌ "rewrite" → ✅ *"a new Python layer beside the PHP core, with an explicit responsibility split"*
- ❌ infra/platform → ✅ integration, API contracts, product outcomes
- ❌ "because of the GIL it's safe"
- ❌ Go/Java як робочі мови → ✅ *"I read them, I don't write them"*
- ❌ ML/моделі/агенти → ✅ *"I treat a model provider as one more unreliable HTTP dependency"*
- ❌ досвід з payments → ✅ *"I haven't shipped payments, but I've owned a path where a duplicate is a real incident"*

---

## Part 1 — англійські фрази

**Aliasing:** "`b = a` binds a second name to the same object — no copy. Mutation through either is visible through both."

**Shallow:** "`a[:]` copies the outer list only — new list, same element references. For nested mutables I need `deepcopy`."

**`[[0]*3]*3`:** "Three identical rows — `[obj] * 3` copies the reference. `grid[0] is grid[1]` is True. I'd write `[[0]*3 for _ in range(3)]`."

**Mutable default:** "The default is evaluated once, at definition time, and lives in `__defaults__`. Fix is `target=None` plus `if target is None: target = []`."

**Late binding:** "`[2, 2, 2]` — each lambda closes over the variable, not the value. Fix `lambda i=i: i`, which captures at definition time."

**`nonlocal`:** "`nonlocal` binds to the nearest enclosing **function**, never the module — that's `global`. Reading walks LEGB by itself; only assignment needs a declaration. Mutation isn't assignment."

**`UnboundLocalError`:** "An assignment anywhere in the body makes the name local — the compiler decides that. The error only fires if the read executes before the assignment."

**keyword-only:** "The bare `*` makes everything after it keyword-only. Extras collect into `**kw` as a dict. I use it on money signatures so callers can't swap arguments."

**hash/eq:** "`0`, `False` and `0.0` collapse to one entry — same hash, equal values. Set membership is the hash/eq contract, not the type."

**nan:** "`nan != nan`, but `[nan] == [nan]` is True because list equality short-circuits on identity. So never use nan as a sentinel."

**`+=`:** "On an int that's assignment — it creates an instance attribute and shadows the class one. On a list `__iadd__` mutates in place, so the shared class list gets poisoned. Same syntax, opposite blast radius."

**dict vs list під ітерацію:** "A dict raises `RuntimeError`. A list raises nothing — `remove` shifts under the cursor and elements get skipped. I'd filter into a new list instead."

---

## Part 2

**Coroutine:** "Calling an async function gives me a coroutine object — nothing has run. Execution starts on `await` or when wrapped in a task."

**`create_task`:** "`await coro()` runs and waits here. `create_task` schedules it independently — it's already running. Then `await task` only collects the result. Three tasks plus three sequential awaits is the time of the longest, not the sum."

**`gather`:** "I build the coroutines, then hand them to `gather` — input order, first exception re-raised bare. It does **not** cancel the siblings."

**`return_exceptions=True`:** "One flag. Failures come back as values at their own index instead of aborting the batch. Length always matches the input."

**`TaskGroup`:** "Cancels siblings and wraps the failure in an `ExceptionGroup` — a plain `except MyError` won't catch it, I need `except*`. `gather` re-raises bare. That difference changes the error contract."

**Timeout:** "`asyncio.timeout` cancels the work — it doesn't just stop awaiting it, otherwise the request keeps holding a connection after I gave up."

**Semaphore:** "Unbounded fan-out melts the upstream — 429s and tail latency, not a crash. Semaphore caps in-flight; I hold it only around the I/O."

**Cancel:** "`cancel()` is only a request. I await the cancelled tasks with `return_exceptions=True`, otherwise the cancellation hasn't landed and I get unretrieved-exception warnings."

**Retry:** "5xx and timeouts get exponential backoff plus jitter, so clients don't synchronise. 4xx I re-raise immediately — my request is wrong, retrying multiplies load during an incident. Past a threshold I shed rather than retry."

**GIL:** "The GIL is about bytecode execution in CPython threads. It doesn't remove logical races — asyncio tasks interleave at every `await`, and that's where shared mutable state breaks."

```python
await asyncio.gather(*(client.get(u) for u in urls))                      # concurrent, input order
await asyncio.gather(*(...), return_exceptions=True)                      # failures as values
async with asyncio.timeout(t): return await client.get(url)               # cancels
sem = asyncio.Semaphore(n); async with sem: await client.get(url)         # cap in-flight
if exc.status < 500: raise                                                # never retry 4xx
await asyncio.sleep(backoff * 2**n)                                       # + jitter
```

---

## Part 3 — порядок, у якому говорити

1. **Уточнюючі питання спершу.** Обсяг трафіку? SLA на відповідь? Хто викликач? Дедлайн end-to-end? Що можна деградувати?
2. **Контракт.** `POST`, pydantic-модель на вхід і вихід, структурована помилка з кодом.
3. **Межі.** Кожна зовнішня залежність — за портом/Protocol. Адаптер окремо, домен не знає про HTTP.
4. **Бюджет часу.** Загальний дедлайн, розкладений: залежність 2s + LLM 7s + накладні 1s = 10s. Таймаут на кожну. **Жодного необмеженого очікування.**
5. **Ідемпотентність** ← ГОЛОВНА КАРТА, не пропустити.
6. **Помилки.** Ретраї 5xx/429 з backoff+jitter, 4xx одразу наверх. Fallback **не вигадує факти** — `{"error": {"code": "LLM_UNAVAILABLE"}}`, а справжній виняток у лог.
7. **Вивід моделі — недовірений вхід.** Валідувати схемою, діапазони перевіряти, відкидати.
8. **Кеш.** Ключ = хеш нормалізованого входу **+ модель + версія промпту**. Redis, не in-process — реплік кілька. **Single-flight:** 1000 промахів → 1 виклик.
9. **Спостережність.** P50/95/99, коди помилок по бекендах, трейс із бізнес-контекстом, **event loop delay** як сигнал, що хтось блокує лупу.
10. **Concurrency тільки для незалежного.** Якщо LLM залежить від ціни — паралелити нічого.
11. **GDPR:** промпти дослівно не логувати. Manychat обробляє переписки кінцевих користувачів.

### Ідемпотентність — сказати саме так

> "I took a critical send path out of a live pipeline with idempotency enforced at the database level — a unique constraint on the business identity, so a retry is a no-op instead of a double send. For billing that's the same discipline with money as the unit: an idempotency key from the client, a unique index, and the second attempt returns the first result instead of charging again."

### 100 → 5000 req/s — перші 5

1. **Ідемпотентність і дедуплікація** — на 50× трафіку ретраї стають нормою, подвійне списання стає статистикою
2. **Bounded concurrency + backpressure** — Semaphore на кожен апстрім, чергу обмежити, віддавати 429 замість того, щоб падати
3. **Кеш + single-flight** — інакше 5000 промахів стають 5000 викликами апстріму
4. **Бюджети таймаутів і circuit breaker** — деградувати частину, а не тримати весь запит
5. **Спостережність по залежностях** — P95 по кожному апстріму окремо, бо «сервіс повільний» без розбивки не діагностується

Шосте, якщо спитають: **горизонтальне масштабування не рятує** — воно не підіймає ліміт провайдера. Потрібен control layer.

---

## Мої питання до них

1. There's already a Python layer in Product — how do you see the boundary between it and Billing's?
2. What stays in PHP permanently, and what's the first thing you'd want extracted?
3. The two engineers joining after me — what's the timeline, and do I take part in hiring them?
4. What does "zero tolerance for failure" mean concretely — what's the current billing incident rate?
5. What has to be true in 6 months for this to be judged a success?

## Мої числа

10+ років Python · Senior SWE у Capital.com з лют. 2023 · мільйони повідомлень/добу · веду 2 інженерів · ~6 місяців дій. тех-лід · до того Ciklum (Django/DRF), SoftServe (aiohttp/Twisted, високонавантажений async-месенджинг)

**Band: 100–120k. Тиснути у верх діапазону.** Обґрунтування: 10+ років проти вимоги 8+, founding-скоуп, двоє підзвітних, і я вже робив цю форму міграції.
