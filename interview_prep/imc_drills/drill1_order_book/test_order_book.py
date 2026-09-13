import pytest

from order_book import OrderBook


@pytest.fixture
def book():
    return OrderBook()


def test_empty_book_has_no_best_prices(book):
    assert book.best_bid() is None
    assert book.best_ask() is None


def test_resting_order_sets_best_price(book):
    assert book.add_limit_order("a", "buy", 100, 10) == []
    assert book.best_bid() == 100
    assert book.best_ask() is None
    assert book.depth("buy", 100) == 10


def test_no_match_when_spread_is_not_crossed(book):
    book.add_limit_order("a", "buy", 99, 10)
    trades = book.add_limit_order("b", "sell", 101, 10)
    assert trades == []
    assert book.best_bid() == 99
    assert book.best_ask() == 101


def test_full_fill_executes_at_maker_price(book):
    book.add_limit_order("maker", "sell", 100, 10)
    trades = book.add_limit_order("taker", "buy", 105, 10)
    assert len(trades) == 1
    t = trades[0]
    assert (t.maker_id, t.taker_id, t.price, t.quantity) == ("maker", "taker", 100, 10)
    assert book.best_ask() is None
    assert book.best_bid() is None


def test_partial_fill_leaves_remainder_resting(book):
    book.add_limit_order("maker", "sell", 100, 4)
    trades = book.add_limit_order("taker", "buy", 100, 10)
    assert [(t.maker_id, t.quantity) for t in trades] == [("maker", 4)]
    assert book.best_ask() is None
    assert book.best_bid() == 100
    assert book.depth("buy", 100) == 6


def test_maker_partially_filled_stays_with_reduced_quantity(book):
    book.add_limit_order("maker", "sell", 100, 10)
    trades = book.add_limit_order("taker", "buy", 100, 3)
    assert [(t.maker_id, t.quantity) for t in trades] == [("maker", 3)]
    assert book.best_ask() == 100
    assert book.depth("sell", 100) == 7


def test_time_priority_within_a_price_level(book):
    book.add_limit_order("first", "sell", 100, 5)
    book.add_limit_order("second", "sell", 100, 5)
    trades = book.add_limit_order("taker", "buy", 100, 7)
    assert [(t.maker_id, t.quantity) for t in trades] == [("first", 5), ("second", 2)]
    assert book.depth("sell", 100) == 3


def test_price_priority_across_levels_cheapest_ask_first(book):
    book.add_limit_order("expensive", "sell", 102, 5)
    book.add_limit_order("cheap", "sell", 100, 5)
    trades = book.add_limit_order("taker", "buy", 102, 8)
    assert [(t.maker_id, t.price, t.quantity) for t in trades] == [
        ("cheap", 100, 5),
        ("expensive", 102, 3),
    ]


def test_price_priority_for_a_sell_takes_highest_bid_first(book):
    book.add_limit_order("low", "buy", 99, 5)
    book.add_limit_order("high", "buy", 101, 5)
    trades = book.add_limit_order("taker", "sell", 99, 8)
    assert [(t.maker_id, t.price, t.quantity) for t in trades] == [
        ("high", 101, 5),
        ("low", 99, 3),
    ]


def test_incoming_order_stops_at_its_limit_price(book):
    book.add_limit_order("cheap", "sell", 100, 5)
    book.add_limit_order("expensive", "sell", 110, 5)
    trades = book.add_limit_order("taker", "buy", 100, 10)
    assert [(t.maker_id, t.quantity) for t in trades] == [("cheap", 5)]
    assert book.best_bid() == 100
    assert book.depth("buy", 100) == 5
    assert book.best_ask() == 110


def test_cancel_removes_resting_order(book):
    book.add_limit_order("a", "buy", 100, 10)
    assert book.cancel("a") is True
    assert book.best_bid() is None
    assert book.depth("buy", 100) == 0


def test_cancel_unknown_order_is_false(book):
    assert book.cancel("nope") is False


def test_cancel_is_idempotent(book):
    book.add_limit_order("a", "sell", 100, 1)
    assert book.cancel("a") is True
    assert book.cancel("a") is False


def test_best_price_recovers_after_cancelling_the_top(book):
    """This is the lazy-deletion trap: the heap still holds the cancelled price."""
    book.add_limit_order("top", "buy", 105, 5)
    book.add_limit_order("second", "buy", 100, 5)
    book.cancel("top")
    assert book.best_bid() == 100


def test_cancelled_order_does_not_trade(book):
    book.add_limit_order("ghost", "sell", 100, 5)
    book.add_limit_order("real", "sell", 101, 5)
    book.cancel("ghost")
    trades = book.add_limit_order("taker", "buy", 101, 5)
    assert [(t.maker_id, t.price) for t in trades] == [("real", 101)]


def test_empty_price_level_is_removed_not_left_behind(book):
    book.add_limit_order("a", "sell", 100, 5)
    book.add_limit_order("taker", "buy", 100, 5)
    assert book.depth("sell", 100) == 0
    assert book.best_ask() is None


def test_sweeps_multiple_levels_and_rests_remainder(book):
    book.add_limit_order("a", "sell", 100, 2)
    book.add_limit_order("b", "sell", 101, 2)
    book.add_limit_order("c", "sell", 102, 2)
    trades = book.add_limit_order("taker", "buy", 102, 10)
    assert [(t.maker_id, t.quantity) for t in trades] == [("a", 2), ("b", 2), ("c", 2)]
    assert book.best_bid() == 102
    assert book.depth("buy", 102) == 4
    assert book.best_ask() is None


def test_rejects_bad_side(book):
    with pytest.raises(ValueError):
        book.add_limit_order("a", "sideways", 100, 1)


def test_rejects_non_positive_quantity(book):
    with pytest.raises(ValueError):
        book.add_limit_order("a", "buy", 100, 0)
