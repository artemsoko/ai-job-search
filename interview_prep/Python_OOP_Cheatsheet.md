# Python OOP — descriptors, slots, MRO, decorators

Все запущено на CPython 3.14. Виводи справжні.

---

## `__slots__`

Прибирає `__dict__` у інстансів. Атрибути живуть у фіксованих слотах.

```python
class WithSlots:
    __slots__ = ("a", "b")
    def __init__(self, a, b): self.a, self.b = a, b
```

```
dict-based:  344 bytes (obj + __dict__)      has __dict__: True
slots     :   48 bytes                       has __dict__: False
s.c = 3 -> AttributeError: 'WithSlots' object has no attribute 'c'
                           and no __dict__ for setting new attributes
```

**Що дає:** ~7× менше пам'яті на цьому прикладі, швидший доступ до атрибутів, і **захист від опечаток** — `self.amout = 5` падає, а не створює тихо новий атрибут.

**Пастки:**
- Не можна додати атрибут, якого немає в `__slots__`.
- **Спадкоємець без свого `__slots__` повертає `__dict__`** — перевірено, весь виграш зникає. Треба `__slots__ = ()` у дитині.
- Не поєднується з `__weakref__` без явного додавання його в слоти.
- Множинне спадкування двох класів з непорожніми `__slots__` — `TypeError`.

**Коли брати:** мільйони дрібних об'єктів — рядки з БД, тіки, події. Не для звичайних сервісних класів, там це передчасна оптимізація.

Сучасний варіант: `@dataclass(slots=True)`.

> "`__slots__` removes the per-instance `__dict__`, so attributes live in fixed slots — about seven times less memory in my test, plus you get a typo guard because assigning an undeclared attribute raises instead of silently creating one. The catch is that a subclass without its own `__slots__` reintroduces `__dict__` and you lose the whole benefit. I'd use it for millions of small objects, not for service classes."

---

## Descriptors

Об'єкт, який визначає `__get__` / `__set__` / `__delete__` і живе **як атрибут класу**. Перехоплює доступ до атрибута інстанса.

```python
class Positive:
    def __set_name__(self, owner, name):        # викликається при створенні класу
        self._name = "_" + name
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self                          # доступ через клас
        return getattr(obj, self._name)
    def __set__(self, obj, value):
        if value <= 0:
            raise ValueError(f"{self._name[1:]} must be positive, got {value}")
        setattr(obj, self._name, value)

class Charge:
    amount = Positive()
```

```
__set_name__ called: owner=Charge name=amount
c.amount = 100
c.amount = -5  ->  ValueError - amount must be positive, got -5
type(Charge.amount) -> Positive
```

### Data vs non-data — це і є «cool» питання

| Тип | Що визначає | Хто виграє при конфлікті з `instance.__dict__` |
|---|---|---|
| **non-data** | тільки `__get__` | **`__dict__` інстанса** |
| **data** | `__get__` + `__set__` (або `__delete__`) | **дескриптор** |

Перевірено:
```
non-data (only __get__):  from instance __dict__    <- instance dict WINS
data (__get__+__set__) :  from DATA descriptor      <- descriptor WINS
```

Порядок пошуку атрибута: **data descriptor на класі → `instance.__dict__` → non-data descriptor / звичайний атрибут класу → `__getattr__`**.

**Навіщо це в реальності:** саме тому `functools.cached_property` працює — вона non-data, тому після першого обчислення значення сідає в `__dict__` інстанса і **перекриває** дескриптор. Другий доступ дескриптора вже не торкається.

**Що ще є дескриптором:** `property`, `classmethod`, `staticmethod`, і **звичайні функції** — саме `function.__get__` перетворює функцію в bound method, коли ти пишеш `obj.method`.

> "A descriptor is a class attribute that intercepts attribute access through `__get__` and `__set__`. The distinction that matters is data versus non-data: if it only defines `__get__`, the instance dict wins; add `__set__` and the descriptor wins. That's exactly why `cached_property` works — it's non-data, so the computed value lands in the instance dict and shadows it. And plain functions are descriptors too — `__get__` is what turns a function into a bound method."

---

## `property` — це дескриптор з цукром

```python
class Account:
    def __init__(self, minor): self._minor = minor

    @property
    def amount(self):                    # getter
        return self._minor / 100

    @amount.setter
    def amount(self, v):                 # setter
        if v < 0: raise ValueError("negative")
        self._minor = round(v * 100)
```

```
a.amount -> 19.99      type(Account.amount) -> property
a.amount = 25.5  ->  _minor == 2550
```

`property` — **data descriptor**, тому завжди виграє в інстанса.

**Коли property, коли descriptor:**
- **property** — одна конкретна властивість одного класу.
- **descriptor** — та сама логіка на **багатьох** атрибутах або класах. `Positive()` вище можна повісити на десять полів; десять `@property` з однаковим тілом — копіпаста.

**Правило, яке варто сказати:** не роби `get_x()` / `set_x()` як у Java. Починай зі звичайного публічного атрибута; `property` додаєш **пізніше**, коли з'явилась валідація або обчислення — і **інтерфейс не змінюється**, викликач так само пише `obj.amount`. Це і є перевага property над геттерами.

> "In Python you don't write getters up front — you expose a plain attribute and promote it to a `property` later if you need validation or computation, and callers never change. `property` is just a data descriptor with syntax sugar. When the same rule applies to many fields or many classes, I write the descriptor directly instead of repeating the property."

---

## MRO і `super()`

```python
class A:
    def who(self): return "A"
class B(A):
    def who(self): return "B->" + super().who()
class C(A):
    def who(self): return "C->" + super().who()
class D(B, C):
    def who(self): return "D->" + super().who()
```

```
D().who()  ->  D->B->C->A
MRO        ->  D -> B -> C -> A -> object
```

**Головне:** `super()` — це **не «батько»**. Це **наступний у MRO** поточного об'єкта. У `B.who` `super()` вказує на `C`, хоча `B` успадковує від `A`. Тому і `C` виконався.

MRO будується алгоритмом **C3 linearization**: дитина перед батьками, порядок базових класів зберігається, кожен клас один раз. Якщо консистентного порядку не існує — `TypeError` при **створенні класу**, не при виклику.

**Diamond problem** Python вирішує саме цим: `A` виконується **один раз**, не двічі.

**Практика:** для кооперативного спадкування всі в ланцюжку мусять викликати `super()`, інакше ланцюг рветься. Тому міксини завжди роблять `super().__init__(**kwargs)`.

> "`super()` doesn't mean parent — it means the next class in this object's MRO, which depends on the actual instance, not on where the code is written. In a diamond, `B.who` calling `super()` reaches `C`, not `A`, which is how Python runs the shared base exactly once. The order comes from C3 linearization, and an impossible order is a TypeError at class-creation time."

---

## Decorators

Декоратор — виклик під час `def`. `@deco` над `def f` — це `f = deco(f)`, і воно виконується **на імпорті модуля**, не на виклику.

### Три рівні, коли декоратор приймає аргументи

```python
import functools

def retry(attempts):                      # 1. приймає аргументи -> віддає декоратор
    def decorator(fn):                    # 2. приймає функцію   -> віддає обгортку
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):     # 3. виконується на КОЖЕН виклик
            for n in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except ValueError:
                    if n == attempts - 1:
                        raise
        return wrapper
    return decorator

@retry(attempts=3)
def flaky(x):
    """docstring survives"""
```

`@retry(attempts=3)` — зверни увагу на **дужки**: спершу викликається `retry(3)`, її результат і є декоратором. Без аргументів дужок немає і рівнів два.

```
flaky(1) -> ok  (3 спроби)
__name__ preserved by wraps: flaky   __doc__: docstring survives
unwrap to the original: flaky.__wrapped__
```

### `functools.wraps` — не косметика

Без неї `flaky.__name__` стане `"wrapper"`, `__doc__` зникне, і зламаються: логи, `help()`, генерація OpenAPI у FastAPI, pytest-репорти, будь-яка інтроспекція. `wraps` ще й ставить `__wrapped__`, тому до оригіналу можна дістатись.

### Порядок стекування — знизу вгору

```python
@tag("outer")
@tag("inner")
def hello(): return "hi"
```
```
<outer><inner>hi</inner></outer>
```

Найближчий до `def` застосовується **першим**, решта обгортають його. Читай знизу.

### Два моменти в часі — це те, на чому плутаються

| Де код | Коли виконується | Скільки разів |
|---|---|---|
| тіло `decorator` / `retry` | у момент `def` (імпорт) | **один раз** |
| тіло `wrapper` | на кожен виклик | **щоразу** |

Декоратор, який лише **реєструє** і повертає `fn` без обгортки — цілком нормальний і дуже поширений патерн: `@app.get("/users")` у FastAPI, `@pytest.fixture`, `@app.task` у Celery. Вони не змінюють функцію, вони **пишуть її в реєстр на імпорті**. Саме тому роутинг FastAPI «просто працює».

**Наслідок для продакшену:** важка робота в тілі декоратора (читання конфігу, конекшн до БД, HTTP) б'є по **часу імпорту**, а не по часу виклику. Класична причина повільного старту сервісу.

> "A decorator with arguments is three levels: the factory takes the config, returns the decorator, which returns the wrapper. Two different times matter — the decorator body runs once at import, the wrapper on every call, so anything expensive at decoration time becomes startup cost. I always use `functools.wraps`, otherwise the function's name and docstring are replaced by the wrapper's and introspection breaks — that's what FastAPI and pytest rely on."

---

## Швидкі відповіді, якщо копнуть глибше

**`__getattr__` vs `__getattribute__`** — `__getattribute__` перехоплює **кожен** доступ; `__getattr__` викликається **тільки коли звичайний пошук провалився**. Для проксі/ліниві атрибути беруть `__getattr__`, бо `__getattribute__` легко зробити нескінченну рекурсію.

**`classmethod` vs `staticmethod`** — обидва дескриптори. `classmethod` отримує клас першим аргументом і **бачить спадкоємця** (тому альтернативні конструктори роблять на ньому: `cls(...)`, а не `MyClass(...)`). `staticmethod` не отримує нічого — це просто функція в неймспейсі класу.

**`__init_subclass__`** — хук, що виконується при створенні **підкласу**. Легка альтернатива метаклясу для реєстрації плагінів чи валідації, що дитина визначила потрібні атрибути.

**Метакласи** — «клас класу». Скажи честно: у продакшені майже ніколи не потрібні, `__init_subclass__` і дескриптори покривають 95%. Знати треба, що `type` — метаклас за замовчуванням, і що Pydantic/SQLAlchemy/Django ORM на них побудовані.

**Dunder, які варто назвати:** `__eq__` + `__hash__` (**завжди в парі** — визначив `__eq__` без `__hash__`, і об'єкт став нехешованим), `__repr__` для логів, `__enter__`/`__exit__` для контекст-менеджера, `__aenter__`/`__aexit__` для async, `__iter__`/`__next__`, `__call__`.

**Чому `__eq__` без `__hash__` ламає** — Python ставить `__hash__ = None`, і об'єкт більше не можна покласти в `set` чи використати ключем dict. Для іммутабельних value-об'єктів пиши `@dataclass(frozen=True)` — вона згенерує обидва.
