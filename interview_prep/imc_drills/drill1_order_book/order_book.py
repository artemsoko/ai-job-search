"""Limit order book with price-time priority.

Implement every method marked NotImplementedError. Run the tests and fix them one at a time.

Requirements (this is the spec you would be handed):
  * Two sides: "buy" (bids) and "sell" (asks).
  * A new order is matched immediately against the opposite side, as far as it can be:
      - a buy matches asks priced <= the buy's price, cheapest ask first
      - a sell matches bids priced >= the sell's price, highest bid first
  * Within one price level, older orders fill first (FIFO / time priority).
  * Any unfilled remainder rests in the book at its limit price.
  * A trade executes at the price of the order ALREADY resting in the book (the maker's price).
  * cancel(order_id) removes a resting order; returns True if it was there, False otherwise.
  * best_bid()/best_ask() return the best resting price, or None if that side is empty.

Think about, and be ready to say out loud:
  * Why a heap for best price rather than sorting the price levels on every query.
  * Why the heap can hold stale prices, and how you handle that (lazy deletion).
  * Why a deque per price level rather than a list.
  * What cancel costs, and why you do not remove from the heap.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Trade:
    """One execution. maker_id rested in the book; taker_id was the incoming order."""
    maker_id: str
    taker_id: str
    price: int
    quantity: int


class OrderBook:
    def __init__(self) -> None:
        # Set up your structures here. Suggested shape, but argue for your own:
        #   self._levels: dict[tuple[str, int], deque[list]]  side+price -> FIFO of orders
        #   self._bid_heap: list[int]   max-heap via negated prices
        #   self._ask_heap: list[int]   min-heap
        #   self._orders: dict[str, ...]  order_id -> where it lives, for O(1) cancel
        pass

    def add_limit_order(self, order_id: str, side: str, price: int, quantity: int) -> list[Trade]:
        """Match as much as possible, rest the remainder. Return trades oldest-first."""
        raise NotImplementedError

    def cancel(self, order_id: str) -> bool:
        raise NotImplementedError

    def best_bid(self) -> int | None:
        raise NotImplementedError

    def best_ask(self) -> int | None:
        raise NotImplementedError

    def depth(self, side: str, price: int) -> int:
        """Total resting quantity at one price level. 0 if nothing rests there."""
        raise NotImplementedError

    # ------------------------------------------------------------------ STAGE 2
    # Do NOT start these until every test in test_order_book.py passes.
    # These are the follow-ups the research says carry HALF the grade.

    def add_market_order(self, order_id: str, side: str, quantity: int) -> list[Trade]:
        """No limit price. Sweep the opposite side until filled or the book is empty.
        Any unfilled remainder is DISCARDED -- a market order never rests."""
        raise NotImplementedError

    def add_ioc_order(self, order_id: str, side: str, price: int, quantity: int) -> list[Trade]:
        """Immediate-or-cancel: match what you can at this price or better, discard the rest.
        Never rests in the book."""
        raise NotImplementedError

    def add_fok_order(self, order_id: str, side: str, price: int, quantity: int) -> list[Trade]:
        """Fill-or-kill: all of it, or none of it.

        The trap: you must decide BEFORE mutating anything. If the book cannot fill the whole
        quantity at this price or better, return [] and leave the book EXACTLY as it was.
        That is the two-pass requirement."""
        raise NotImplementedError

    def modify(self, order_id: str, new_quantity: int) -> bool:
        """Change a resting order's quantity. Returns False if the id is not resting.

        Exchange convention, and the thing being tested:
          * reducing quantity KEEPS time priority (you are giving liquidity back)
          * increasing quantity LOSES it -- the order goes to the back of its level
        new_quantity <= 0 is a cancel."""
        raise NotImplementedError
