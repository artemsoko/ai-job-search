"""STAGE 2 -- the follow-ups that carry half the grade.

Do not start these until test_order_book.py is fully green.

Sourced from reports of how this question is actually run at market makers:
  * "Implement add, cancel, and match for a single-symbol book. Now make cancel O(1)."
    -- that follow-up "is the whole point of the question at most desks"
  * "Two orders arrive at the same price in the same microsecond. Which fills first,
    and how does your code decide?"  -> monotonic sequence, never a wall clock
  * order types: market, IOC, and FOK -- "particularly Fill-or-Kill's two-pass requirement"
  * "candidates who optimize match throughput but leave cancel as a linear scan
    have optimized the wrong end"
"""
import time

import pytest
from order_book import OrderBook, Trade


@pytest.fixture
def book():
    return OrderBook()


# --------------------------------------------------------------- tie-breaking
def test_tie_break_is_arrival_order_not_order_id(book):
    """If you sort a level by order_id anywhere, this fails.

    'z' arrives first at 100, then 'a'. Price-time priority means 'z' fills first,
    even though 'a' sorts earlier.
    """
    book.add_limit_order("z", "sell", 100, 5)
    book.add_limit_order("a", "sell", 100, 5)

    trades = book.add_limit_order("taker", "buy", 100, 5)

    assert [t.maker_id for t in trades] == ["z"]


def test_requeued_order_goes_to_the_back_not_the_front(book):
    book.add_limit_order("first", "sell", 100, 5)
    book.add_limit_order("second", "sell", 100, 5)
    book.add_limit_order("third", "sell", 100, 5)
    book.cancel("first")

    trades = book.add_limit_order("taker", "buy", 100, 10)

    assert [t.maker_id for t in trades] == ["second", "third"]


# ------------------------------------------------------------- market orders
def test_market_order_sweeps_every_level(book):
    book.add_limit_order("a1", "sell", 100, 3)
    book.add_limit_order("a2", "sell", 101, 3)
    book.add_limit_order("a3", "sell", 105, 3)

    trades = book.add_market_order("m", "buy", 7)

    assert [(t.maker_id, t.price, t.quantity) for t in trades] == [
        ("a1", 100, 3), ("a2", 101, 3), ("a3", 105, 1),
    ]
    assert book.depth("sell", 105) == 2


def test_market_order_never_rests(book):
    book.add_limit_order("a1", "sell", 100, 2)

    trades = book.add_market_order("m", "buy", 10)

    assert sum(t.quantity for t in trades) == 2
    assert book.best_bid() is None, "the unfilled 8 must be discarded, not rested"
    assert book.best_ask() is None


def test_market_order_on_an_empty_book_is_not_an_error(book):
    assert book.add_market_order("m", "buy", 10) == []
    assert book.best_bid() is None


# ----------------------------------------------------------------------- IOC
def test_ioc_fills_what_it_can_and_discards_the_rest(book):
    book.add_limit_order("a1", "sell", 100, 4)

    trades = book.add_ioc_order("ioc", "buy", 100, 10)

    assert sum(t.quantity for t in trades) == 4
    assert book.best_bid() is None, "IOC must not rest"


def test_ioc_respects_its_limit_price(book):
    book.add_limit_order("a1", "sell", 100, 4)
    book.add_limit_order("a2", "sell", 200, 4)

    trades = book.add_ioc_order("ioc", "buy", 150, 8)

    assert sum(t.quantity for t in trades) == 4
    assert book.depth("sell", 200) == 4, "must not cross above its own limit"


def test_ioc_that_cannot_touch_anything_returns_empty(book):
    book.add_limit_order("a1", "sell", 200, 4)

    assert book.add_ioc_order("ioc", "buy", 100, 4) == []
    assert book.depth("sell", 200) == 4


# ----------------------------------------------------------------------- FOK
def test_fok_fills_completely_when_it_can(book):
    book.add_limit_order("a1", "sell", 100, 3)
    book.add_limit_order("a2", "sell", 101, 3)

    trades = book.add_fok_order("fok", "buy", 101, 6)

    assert sum(t.quantity for t in trades) == 6
    assert book.best_ask() is None


def test_fok_leaves_the_book_UNTOUCHED_when_it_cannot_fill(book):
    """THE two-pass test. A one-pass implementation partially fills, then discovers it
    cannot finish -- and the book is already mutated. Check before you mutate."""
    book.add_limit_order("a1", "sell", 100, 3)
    book.add_limit_order("a2", "sell", 101, 3)

    trades = book.add_fok_order("fok", "buy", 101, 10)

    assert trades == [], "FOK must be all-or-nothing"
    assert book.depth("sell", 100) == 3, "book was mutated on a killed FOK"
    assert book.depth("sell", 101) == 3, "book was mutated on a killed FOK"
    assert book.best_ask() == 100


def test_fok_ignores_liquidity_above_its_limit_when_deciding(book):
    book.add_limit_order("a1", "sell", 100, 3)
    book.add_limit_order("a2", "sell", 500, 100)

    trades = book.add_fok_order("fok", "buy", 100, 10)

    assert trades == []
    assert book.depth("sell", 100) == 3
    assert book.depth("sell", 500) == 100


def test_fok_never_rests(book):
    book.add_limit_order("a1", "sell", 100, 10)

    book.add_fok_order("fok", "buy", 100, 10)

    assert book.best_bid() is None


# -------------------------------------------------------------------- modify
def test_reducing_quantity_keeps_time_priority(book):
    book.add_limit_order("first", "sell", 100, 10)
    book.add_limit_order("second", "sell", 100, 10)

    assert book.modify("first", 4) is True

    trades = book.add_limit_order("taker", "buy", 100, 4)
    assert [t.maker_id for t in trades] == ["first"], "reducing must not lose priority"
    assert book.depth("sell", 100) == 10


def test_increasing_quantity_loses_time_priority(book):
    book.add_limit_order("first", "sell", 100, 5)
    book.add_limit_order("second", "sell", 100, 5)

    assert book.modify("first", 8) is True

    trades = book.add_limit_order("taker", "buy", 100, 5)
    assert [t.maker_id for t in trades] == ["second"], "increasing must go to the back"


def test_modify_to_zero_is_a_cancel(book):
    book.add_limit_order("a1", "sell", 100, 5)

    assert book.modify("a1", 0) is True
    assert book.best_ask() is None
    assert book.cancel("a1") is False


def test_modify_unknown_order_is_false(book):
    assert book.modify("nope", 5) is False


def test_modify_a_filled_order_is_false(book):
    book.add_limit_order("a1", "sell", 100, 5)
    book.add_limit_order("taker", "buy", 100, 5)

    assert book.modify("a1", 10) is False


# ------------------------------------------------------- cancel must be O(1)
def test_cancel_cost_does_not_grow_with_level_size(book):
    """Indicative, not a proof -- but a linear scan fails it by a wide margin.

    Two levels, one with 200 resting orders and one with 20,000. Cancelling the LAST
    order added is the worst case for a scan from the front.
    """
    def cancel_last_of(n: int) -> float:
        b = OrderBook()
        for i in range(n):
            b.add_limit_order(f"o{i}", "sell", 100, 1)
        start = time.perf_counter()
        assert b.cancel(f"o{n - 1}") is True
        return time.perf_counter() - start

    small = min(cancel_last_of(200) for _ in range(5))
    large = min(cancel_last_of(20_000) for _ in range(5))

    # 100x more orders. O(1) stays flat; a front-to-back scan blows through this.
    assert large < small * 50 + 5e-5, (
        f"cancel looks linear in level size: {small:.9f}s at n=200 vs {large:.9f}s at "
        f"n=20000. Index order_id -> the node and unlink in O(1)."
    )


def test_cancel_does_not_leave_the_level_holding_dead_weight(book):
    """A tombstone-only cancel is fine for correctness, but if nothing ever reclaims the
    space, depth() and the match loop keep walking corpses. depth() must not count them."""
    for i in range(100):
        book.add_limit_order(f"o{i}", "sell", 100, 1)
    for i in range(99):
        book.cancel(f"o{i}")

    assert book.depth("sell", 100) == 1
    trades = book.add_limit_order("taker", "buy", 100, 1)
    assert [t.maker_id for t in trades] == ["o99"]
    assert book.best_ask() is None
