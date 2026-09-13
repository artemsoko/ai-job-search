# asyncio + системний рівень — довідник під Manychat

Складено 2026-08-25. Усі числа й виводи в цьому файлі **запущені** на CPython 3.14.
Що не відтворилось — позначено окремо.

---

# 1. Конкурентність проти паралельності

Найчастіше питання, і найчастіше на ньому плутаються.

- **Concurrency** — структура. Багато задач *у процесі виконання* з накладанням у часі. Можна
  на **одному** ядрі. Про **перемикання**.
- **Parallelism** — виконання. Багато задач *фізично одночасно*. Треба **багато** ядер.
  Про **одночасність**.

Конкурентність без паралельності — це asyncio. Паралельність без конкурентності — SIMD.

| Модель | Що дає | Коли брати | Ціна |
|---|---|---|---|
| `asyncio` | конкурентність, 1 потік, 1 ядро | **I/O-bound**: HTTP, БД, диск, черги | усе має бути неблокуючим; одна блокуюча функція вбиває весь луп |
| `threading` | конкурентність, N потоків, **1 ядро для Python-байткоду** (GIL) | блокуючі бібліотеки без async-аналога | GIL, замки, races, ~8 MB стеку на потік |
| `multiprocessing` | **справжня паралельність**, N процесів | **CPU-bound**: криптографія, парсинг, обчислення | пам'ять × N, серіалізація між процесами, дорогий старт |

**Формулювання:**
> "Concurrency is about structure — many tasks in flight, interleaved. Parallelism is about
> execution — many tasks literally at the same instant, which needs multiple cores. asyncio gives
> me concurrency on a single thread, which is exactly right for I/O-bound work: the task isn't
> using the CPU while it waits on a socket. For CPU-bound work asyncio buys nothing — I'd reach
> for processes."

## GIL — точне формулювання

**GIL не робить спільний мутабельний стан безпечним.** Це замок на виконання Python-байткоду в
CPython: в один момент байткод виконує один потік. Наслідки:

- Потоки **не** дають паралельності для Python-коду. Дають — для очікування I/O і для C-розширень,
  що відпускають GIL (numpy, `hashlib`, драйвери БД).
- **Логічні races від GIL не зникають.** `counter += 1` — це read-modify-write, GIL може
  перемкнути потік між кроками.
- В asyncio GIL взагалі ні до чого: один потік. Але races є — таски перемежовуються **на кожному
  `await`**.

Запущено:
```python
counter = 0
async def increment():
    global counter
    current = counter          # усі 10 читають 0
    await asyncio.sleep(0)     # <-- точка перемежування, керування йде в луп
    counter = current + 1      # усі 10 пишуть 1
# результат: counter == 1, детерміновано
```

**Правило:** у asyncio критична секція — це відрізок **між двома `await`**. Немає `await` — код
атомарний. Є `await` — усе між ними може змінитися. Якщо потрібна інваріантність через `await`,
береш `asyncio.Lock` (не `threading.Lock` — той заблокує луп).

> "asyncio is single-threaded, so I don't need locks for CPU-only sections — code between two
> awaits runs atomically. The moment I `await` inside a read-modify-write, another task can
> interleave, and that's a real race. Then I need an `asyncio.Lock`, or better, I move the
> invariant into the database."

---

# 2. Що таке I/O і чому async допомагає

**I/O-bound** — час іде на **очікування зовнішньої системи**, не на обчислення. Сокет, диск, БД,
черга. Процес у цей момент спить у ядрі, CPU вільний.

**CPU-bound** — час іде на обчислення. Процес зайняв ядро.

Async виграє **лише** на I/O: поки таск чекає відповіді сокета, луп віддає ядро іншому таску.
На CPU-bound виграшу нема нуль — навпаки, ти заблокуєш луп.

## Як це працює під капотом

1. Сокет ставиться в **неблокуючий** режим.
2. Луп реєструє його в **мультиплексорі ядра**: `epoll` (Linux), `kqueue` (macOS/BSD),
   IOCP (Windows). Через `selectors`.
3. Луп викликає `epoll_wait` — **один** системний виклик на тисячі сокетів.
4. Ядро повертає готові дескриптори. Луп будить відповідні корутини.

Тому одному потоку під силу 10k+ з'єднань: він не тримає потік на кожне, він тримає **дескриптор**
і чекає нотифікації від ядра.

> "Async I/O isn't magic — the socket is non-blocking and registered with the kernel's
> multiplexer, `epoll` or `kqueue`. One syscall tells the loop which of thousands of descriptors
> are ready. That's why a single thread scales to tens of thousands of connections: it holds file
> descriptors, not threads."

---

# 3. Ресурси: що насправді обмежує сервіс

Питання «які ресурси споживає сервіс» — про це.

| Ресурс | Що його з'їдає | Симптом виснаження |
|---|---|---|
| **CPU** | серіалізація/JSON, крипта, компресія, регулярки, ORM-мапінг, **блокування лупу** | зростає **event loop delay**, P99 злітає при нормальному P50 |
| **RAM** | розмір payload × конкурентність, кеші, буфери сокетів, витоки | OOMKill у k8s, GC-паузи |
| **File descriptors** | **сокет = fd**. З'єднання до апстрімів + вхідні + файли | `OSError: [Errno 24] Too many open files`. Ліміт `ulimit -n` |
| **Ephemeral ports** | вихідні з'єднання, ~28k на IP, плюс `TIME_WAIT` 60s | `Cannot assign requested address` при високій вихідній конкурентності |
| **Network bandwidth / PPS** | великі відповіді, багато дрібних запитів | ретрансмісії, latency без завантаження CPU |
| **Connection pool до БД** | конкурентні запити | таски чекають **у черзі за конекшеном**, а не в БД. Найчастіша «повільна БД», яка не БД |
| **Апстрім-квота** | RPS/TPM провайдера | 429. Горизонтальне масштабування **не допомагає** |

## Хто «відповідає за нетворкінг»

Розділяй шари, це те, що хочуть почути:

1. **Ядро ОС** — TCP/IP, буфери, backlog, `TIME_WAIT`, `epoll`. Ліміти: `ulimit -n`,
   `somaxconn`, розмір ефемерних портів.
2. **Event loop** — мультиплексує fd. Не робить мережу, а **дізнається**, коли ядро готове.
3. **HTTP-клієнт і його пул** (`aiohttp.TCPConnector`, `httpx.Limits`) — keep-alive,
   `limit_per_host`, повторне використання з'єднань. **Це головний тумблер вихідної пропускної
   здатності на рівні застосунку.**
4. **Застосунок** — таймаути, ретраї, `Semaphore`, backpressure.
5. **Інфраструктура** — LB, service mesh, ingress, DNS, sidecar-ліміти.

**Найчастіша помилка:** новий HTTP-клієнт на кожен запит. Убиває keep-alive, робить TLS-хендшейк
щоразу, спалює ефемерні порти. Клієнт створюється **на весь час життя застосунку** — у FastAPI
на `lifespan`.

## Що обмежує пропускну здатність — закон Літтла

```
L = λ × W

L = середня кількість запитів у системі (конкурентність)
λ = пропускна здатність (req/s)
W = середня латентність (s)
```

Отже **λ = L / W**. Пропускна здатність — це конкурентність, поділена на латентність. З цього:

- Латентність апстріму 200 ms, дозволено 10 одночасних → **максимум 50 req/s**. Скільки поди не
  додавай — ліміт у L, не в CPU.
- Хочеш більше λ: або підняти L (конкурентність, пул), або знизити W (кеш, батчинг, ближчий регіон).
- **Черга не підвищує λ.** Вона підвищує W і приховує проблему. Якщо λ_вхід > λ_обробки, черга
  росте безмежно — і ти віддаєш таймаути замість 429.

> "Throughput is concurrency over latency — Little's Law. If the upstream takes 200 ms and I'm
> allowed 10 in flight, my ceiling is 50 req/s no matter how many replicas I run. Adding a queue
> doesn't raise the ceiling, it just converts rejection into latency. So I'd either raise the
> concurrency limit, cut the latency with a cache, or shed load explicitly with a 429."

---

# 4. asyncio: об'єкти й фішки

## Ієрархія

```
coroutine   = async def f() без await -> об'єкт, НІЧОГО не виконано
Future      = обіцянка результату, низький рівень
Task        = Future + запланована корутина. create_task() -> вже біжить
awaitable   = все, що можна await: coroutine, Task, Future, __await__
```

**Ключове:** `await coro()` — запусти і чекай **тут**. `create_task(coro())` — заплануй
**незалежно**, воно вже біжить; `await task` лише забирає результат.

```python
a = asyncio.create_task(f(2))
b = asyncio.create_task(f(1))
c = asyncio.create_task(f(3))
await a; await b; await c      # ~3s = max, НЕ 6s = sum
```

## Примітиви композиції

| Що | Семантика |
|---|---|
| `gather(*aws)` | вхідний порядок · перший виняток **bare** · сусідів **не** скасовує |
| `gather(*aws, return_exceptions=True)` | винятки як **значення** на своїх індексах |
| `TaskGroup()` | скасовує сусідів · виняток в **`ExceptionGroup`** → потрібен `except*` |
| `wait(set, return_when=FIRST_COMPLETED)` | повертає `(done, pending)` · **не** піднімає винятки, вони в `task.result()` |
| `as_completed(aws)` | ітератор у порядку **завершення** |
| `timeout(t)` (3.11+) | **скасовує** тіло. Обгортає блок |
| `wait_for(aw, t)` | те саме для одного awaitable |
| `shield(aw)` | захищає від скасування **зовні** |
| `Semaphore(n)` | не більше n **всередині** блоку |
| `Lock` | взаємне виключення через `await` |
| `Queue(maxsize=n)` | backpressure: `put` чекає, коли повна |
| `to_thread(fn, *a)` | винести блокуючу функцію в потік |

## Скасування — тут ламаються всі

1. `task.cancel()` — **лише запит**. Кидає `CancelledError` у точку `await`.
2. **Треба дочекатись**: `await asyncio.gather(*cancelled, return_exceptions=True)`. Без цього
   скасування не «сіло», і в логах буде `Task exception was never retrieved`.
3. `CancelledError` — це **`BaseException`**, не `Exception`. Тому `except Exception` його
   **не** ловить, і це правильно. Ніколи не глушити.
4. Прибирання — у `finally`. Він виконається і на скасуванні.

Перевірено, `shield`:
```
outer timed out, inner still alive: True
inner result: finished anyway
```
Тобто `wait_for` відвалився по таймауту, а захищений таск добіг. Застосування: не хочеш, щоб
клієнтський таймаут скасував уже початкове списання коштів.

## Блокування лупу — головний грішок

Заміряно:
```
tick() 3×0.02s разом з time.sleep(0.15)      -> 0.197s   (tick не міг виконатись)
tick() 3×0.02s разом з to_thread(time.sleep) -> 0.167s   (наклалось)
```

Що блокує луп: `time.sleep` · `requests` · синхронний драйвер БД · важкі регулярки ·
`json.dumps` на мегабайтах · крипта · `open().read()` великого файлу.

Виходи:
- async-аналог: `asyncio.sleep`, `httpx.AsyncClient`/`aiohttp`, `asyncpg`
- `await asyncio.to_thread(fn, ...)` — для блокуючих бібліотек
- `ProcessPoolExecutor` через `loop.run_in_executor` — для CPU-bound

**Метрика, якою це видно: event loop delay.** Скільки луп не встигав обробити готові колбеки.
Стрибок понад ~1 ms = хтось блокує. Це персональний маркер Sergi з його статті — назви його.

## Дрібні фішки, які показують глибину

- **Тримай посилання на fire-and-forget таск.** Документація попереджає, що луп тримає лише
  слабке посилання і таск може зникнути. *Я намагався відтворити — 50 з 50 добігли і з
  посиланням, і без. Ризик задокументований, але детерміновано не відтворився.* Практика все одно:
  `self._tasks.add(t)` + `t.add_done_callback(self._tasks.discard)`.
- **`asyncio.run` створює і закриває луп.** Двічі в одному процесі — новий луп. Не викликати з
  корутини.
- **Thread-safety:** з іншого потоку в луп — тільки `loop.call_soon_threadsafe` або
  `asyncio.run_coroutine_threadsafe`.
- **`async for` / `async with`** — `__aiter__`/`__anext__`, `__aenter__`/`__aexit__`.
- **`contextvars`** — правильний спосіб протягнути `request_id` через таски. Не глобальні змінні.
- **Дебаг:** `asyncio.run(main(), debug=True)` або `PYTHONASYNCIODEBUG=1` — сварить на повільні
  колбеки і незавейчені корутини.
- **Незавейчена корутина** → `RuntimeWarning: coroutine was never awaited`. Означає забутий
  `await`: функція «працює», логи чисті, не виконалось нічого.

---

# 5. Білінг — задачі, які реально можуть спитати

JD називає: payments, invoicing, **anti-fraud**, **regulatory compliance**, retries,
**idempotency**, consistency guarantees, observability, API contracts, extraction з PHP.

## 5.1 Ідемпотентність — головна карта

**Проблема:** клієнт відправив `POST /charge`, отримав таймаут, повторив. Списати двічі нельзя.

**Рішення:** `Idempotency-Key` від клієнта + **унікальний індекс** у БД.

```sql
CREATE TABLE payment_attempt (
    idempotency_key TEXT PRIMARY KEY,
    account_id      BIGINT NOT NULL,
    amount_minor    BIGINT NOT NULL,
    currency        CHAR(3) NOT NULL,
    status          TEXT NOT NULL,           -- pending | succeeded | failed
    response_body   JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Потік: `INSERT ... ON CONFLICT DO NOTHING`. Вставилось → ти власник, виконуй. Не вставилось →
запис уже є: `succeeded` → віддай **збережену відповідь**; `pending` → віддай `409` або дочекайся.

Тонкість, яку варто назвати: ключ мусить бути привʼязаний до **payload**. Той самий ключ з іншою
сумою — це `422`, не тихе повторення першої відповіді.

> "Idempotency isn't a retry policy, it's a uniqueness constraint. The client sends a key, I
> insert it with `ON CONFLICT DO NOTHING`, and whoever wins the insert does the work. Everyone
> else replays the stored response. It survives concurrent duplicates, process restarts and
> at-least-once delivery, because the guarantee lives in the database, not in the application."

## 5.2 Гроші не бувають float

Перевірено:
```
0.1 + 0.2 == 0.3  ->  False   (0.30000000000000004)
Decimal("0.1") + Decimal("0.2") == Decimal("0.3")  ->  True
```

**Правило:** зберігати **мінорні одиниці цілим** (`amount_minor BIGINT` = центи) або
`NUMERIC(19,4)`. У Python — `Decimal`. `float` для грошей — ніколи. Плюс завжди тримай `currency`
поруч із сумою: сума без валюти безглузда, а JPY не має копійок (`exponent` різний).

## 5.3 Exactly-once не існує. Є at-least-once + ідемпотентність.

Мережа не дає exactly-once. Дає **at-least-once доставку** плюс **ідемпотентну обробку** — а
разом це виглядає як exactly-once для спостерігача. Це чесне формулювання і воно правильне.

## 5.4 Transactional outbox

**Проблема:** треба записати в БД **і** відправити подію в Kafka. Два різні сторе — атомарності
нема. Впав між ними → або списання без події, або подія без списання.

**Рішення:** у **тій самій транзакції** пишеш бізнес-зміну і рядок в `outbox`. Окремий воркер
читає outbox і публікує, помічаючи відправлені. Публікація стає at-least-once → споживач мусить
бути ідемпотентним.

Це саме те, що описує *"the bridge between product features and the existing PHP core"* — дві
системи, одна транзакція неможлива.

## 5.5 Конкурентні списання на один акаунт

Дві паралельні операції читають баланс, обидві бачать достатньо, обидві списують → овердрафт.
Це race через `await`, класика.

Варіанти, від гіршого до кращого:
1. `asyncio.Lock` — працює **лише в одному процесі**. Реплік кілька → не працює.
2. `SELECT ... FOR UPDATE` — песимістичне блокування рядка акаунта. Просто, надійно, серіалізує.
3. **Optimistic locking**: `UPDATE ... WHERE id = ? AND version = ?`, `rowcount == 0` → повтори.
4. **Ledger append-only**: не оновлюй баланс, дописуй проведення. Баланс — сума. Плюс
   `CHECK`-інваріант або обмеження на рівні транзакції.

Для грошей 2 або 4. Назви, що `asyncio.Lock` тут — пастка, бо не переживає масштабування.

## 5.6 Двоїстий запис (double-entry) і реконсиляція

Гроші не «змінюються», гроші **рухаються**. Кожна операція — мінімум два проведення, сума яких
нуль. Дає перевірний інваріант: `SUM(amount) == 0` по транзакції. Реконсиляція — щодобове
зведення власного леджера з виписками провайдера (Stripe), розбіжність = алерт.

## 5.7 Вебхуки від провайдера (Stripe — 7+ років у Manychat)

Чотири речі, які треба сказати:
1. **Перевірка підпису** — обов'язково, інакше будь-хто «оплатить» замовлення.
2. **At-least-once** — Stripe ретраїть. Обробник ідемпотентний по `event.id`.
3. **Порядку немає** — події можуть прийти не в тому порядку або із запізненням. Спирайся на
   версію/таймстемп об'єкта, а не на порядок отримання.
4. **Відповідай 2xx швидко**, роботу — в чергу. Довга обробка в хендлері = ретрай провайдера
   і дублікати.

## 5.8 Нумерація інвойсів

Юридично потрібна **безрозривна** послідовність на юрособу і рік. Postgres `SEQUENCE` **дає
розриви** при відкаті транзакції. Отже: окрема таблиця-лічильник з блокуванням рядка, номер
присвоюється в момент **фіналізації** інвойсу, а не створення драфту.

## 5.9 Anti-fraud — velocity checks

Це не ML. Це вікна й ліміти: N спроб з однієї карти за 10 хв, M різних карт на акаунт за добу,
різкий стрибок середнього чека, невідповідність гео. Реалізація — sliding window у Redis
(`ZADD` + `ZREMRANGEBYSCORE`) або агрегати в Postgres. Рішення: allow / review / block, і
**обов'язково журнал рішення**, бо compliance попросить пояснити кожне.

## 5.10 Compliance / PII

- **PCI DSS:** номерів карт у себе **не тримаємо**. Токен від провайдера — і все. Це різко
  скорочує скоуп аудиту.
- **GDPR:** право на видалення проти обов'язку зберігати фінансові записи — фінансові дані
  зберігаються за законом, персональні псевдонімізуються.
- **Аудит-лог** — незмінний, append-only, з актором і причиною.
- **Не логувати** повні payload'и платежів і промпти LLM дослівно.

## 5.11 Витягування з PHP-ядра — як відповідати

JD: *"Identify functionality worth extracting from the PHP core into Python services."*

Порядок, який показує судження:
1. Спершу **не** переносити. Новий Python-шар бере **новий** функціонал, PHP лишається джерелом істини.
2. Кандидат на витяг = чіткі межі + власні дані + вимірюваний виграш (латентність або
   підтримуваність), і **не** гарячий шлях грошей на першій ітерації.
3. Патерн: **strangler fig** — Python перед PHP, спершу проксює, потім бере на себе окремі
   маршрути.
4. Дані: спочатку читання, запис лишається в PHP. Подвійний запис — лише з ідемпотентністю
   і зіркою для реконсиляції.
5. Обов'язково **зворотна сумісність контракту** і можливість вимкнути фіча-флагом.

> "I wouldn't start by extracting anything. The first win is that new functionality lands in
> Python while PHP stays the source of truth. Then I'd extract something with a clean boundary
> and its own data, prove the pattern, and keep a flag to route back. Money paths go last."

---

# 6. Питання, на які треба мати відповідь

Пройди список і відповідай **вголос, англійською**. Де запинаєшся — повертайся у розділ вище.

**Конкурентність**
1. Concurrency vs parallelism — і що з них дає asyncio?
2. Чому GIL не робить спільний стан безпечним?
3. Де в asyncio критична секція?
4. `asyncio.Lock` vs `threading.Lock` — чому другий у корутині це баг?
5. Коли asyncio не допоможе взагалі?

**asyncio**
6. `await coro()` vs `create_task` — що коли починає виконуватись?
7. `gather` vs `TaskGroup` — семантика помилки і скасування?
8. Чому `except MyError` не ловить помилку з `TaskGroup`?
9. Чому `cancel()` недостатньо?
10. Чому `except Exception` не ловить `CancelledError` і чому це добре?
11. Що робить `shield` і коли він потрібен у білінгу?
12. `Semaphore` — що саме обмежує?
13. Як винести блокуючу бібліотеку з лупу?
14. Як побачити, що луп заблокований?
15. Чому `Queue(maxsize=...)`, а не безрозмірна?

**Системи**
16. Що таке I/O-bound і як async виграє?
17. Що таке `epoll`/`kqueue` і навіщо?
18. Які ресурси виснажуються першими під навантаженням?
19. Чому один HTTP-клієнт на весь застосунок, а не на запит?
20. Що обмежує пропускну здатність — і чому реплік недостатньо? *(закон Літтла)*
21. `Too many open files` — що це і як лікувати?
22. «БД повільна» — як перевірити, що це не пул конекшенів?
23. Черга проти shedding — що обираєш і чому?

**Білінг**
24. Спроєктуй ідемпотентне `POST /charge`.
25. Чому не float для грошей?
26. Exactly-once — існує?
27. Навіщо outbox і яку проблему він розвʼязує?
28. Дві паралельні операції на один баланс — чотири варіанти, який береш?
29. Обробка вебхука Stripe — чотири обов'язкові речі.
30. Чому `SEQUENCE` не годиться для номерів інвойсів?
31. Що витягуєш з PHP першим і чому не гроші?
32. Що робиш, коли LLM/провайдер недоступний — і чому не вигадана відповідь?
