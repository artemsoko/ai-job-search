"""Reference solution. dict of price levels + two lazy heaps + order index."""
from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass


@dataclass
class Trade:
    maker_id: str
    taker_id: str
    price: int
    quantity: int


@dataclass
class _Resting:
    order_id: str
    side: str
    price: int
    quantity: int
    live: bool = True


class OrderBook:
    def __init__(self) -> None:
        self._levels: dict[tuple[str, int], deque[_Resting]] = {}
        self._bid_heap: list[int] = []          # max-heap via negated price
        self._ask_heap: list[int] = []          # min-heap
        self._orders: dict[str, _Resting] = {}

    # ---- helpers -------------------------------------------------------
    def _level(self, side: str, price: int) -> deque[_Resting]:
        return self._levels.setdefault((side, price), deque())

    def _prune(self, side: str) -> None:
        """Lazy deletion: drop heap tops whose level no longer has live quantity."""
        heap = self._bid_heap if side == "buy" else self._ask_heap
        while heap:
            price = -heap[0] if side == "buy" else heap[0]
            if self.depth(side, price) > 0:
                return
            heapq.heappop(heap)
            self._levels.pop((side, price), None)

    def _push_price(self, side: str, price: int) -> None:
        heap = self._bid_heap if side == "buy" else self._ask_heap
        heapq.heappush(heap, -price if side == "buy" else price)

    # ---- API -----------------------------------------------------------
    @staticmethod
    def _check(side: str, quantity: int) -> None:
        if side not in ("buy", "sell"):
            raise ValueError(f"bad side: {side!r}")
        if quantity <= 0:
            raise ValueError("quantity must be positive")

    def _crosses(self, other: str, best: int, price: int | None) -> bool:
        if price is None:                      # market order: any price crosses
            return True
        return best <= price if other == "sell" else best >= price

    def _fillable(self, side: str, price: int | None) -> int:
        """How much could be filled RIGHT NOW, without mutating anything.

        This is the first of FOK's two passes. It walks the opposite side's live levels and
        sums the depth of every level that crosses.
        """
        other = "sell" if side == "buy" else "buy"
        total = 0
        for (lvl_side, lvl_price), queue in self._levels.items():
            if lvl_side != other:
                continue
            if self._crosses(other, lvl_price, price):
                total += sum(o.quantity for o in queue if o.live)
        return total

    def _execute(
        self, order_id: str, side: str, price: int | None, quantity: int, *, rest: bool
    ) -> list[Trade]:
        """The single matching loop. `price=None` is a market order.
        `rest=False` discards any remainder instead of resting it (market / IOC / FOK)."""
        other = "sell" if side == "buy" else "buy"
        trades: list[Trade] = []
        remaining = quantity

        while remaining > 0:
            self._prune(other)
            best = self.best_ask() if other == "sell" else self.best_bid()
            if best is None or not self._crosses(other, best, price):
                break
            queue = self._level(other, best)
            while queue and remaining > 0:
                maker = queue[0]
                if not maker.live or maker.quantity == 0:
                    queue.popleft()
                    continue
                traded = min(remaining, maker.quantity)
                maker.quantity -= traded
                remaining -= traded
                trades.append(Trade(maker.order_id, order_id, best, traded))
                if maker.quantity == 0:
                    maker.live = False
                    self._orders.pop(maker.order_id, None)
                    queue.popleft()
            if not queue:
                self._levels.pop((other, best), None)

        if remaining > 0 and rest:
            assert price is not None
            self._rest(order_id, side, price, remaining)
        return trades

    def _rest(self, order_id: str, side: str, price: int, quantity: int) -> None:
        resting = _Resting(order_id, side, price, quantity)
        existing = self._levels.get((side, price))
        self._level(side, price).append(resting)
        self._orders[order_id] = resting
        if not existing:
            self._push_price(side, price)

    def add_limit_order(self, order_id: str, side: str, price: int, quantity: int) -> list[Trade]:
        self._check(side, quantity)
        return self._execute(order_id, side, price, quantity, rest=True)

    def cancel(self, order_id: str) -> bool:
        # O(1): one dict pop plus a flag. No scan of the level.
        order = self._orders.pop(order_id, None)
        if order is None or not order.live:
            return False
        order.live = False
        order.quantity = 0
        return True

    def best_bid(self) -> int | None:
        self._prune("buy")
        return -self._bid_heap[0] if self._bid_heap else None

    def best_ask(self) -> int | None:
        self._prune("sell")
        return self._ask_heap[0] if self._ask_heap else None

    def depth(self, side: str, price: int) -> int:
        return sum(o.quantity for o in self._levels.get((side, price), ()) if o.live)

    # ---- STAGE 2 --------------------------------------------------------
    def add_market_order(self, order_id: str, side: str, quantity: int) -> list[Trade]:
        self._check(side, quantity)
        return self._execute(order_id, side, None, quantity, rest=False)

    def add_ioc_order(self, order_id: str, side: str, price: int, quantity: int) -> list[Trade]:
        self._check(side, quantity)
        return self._execute(order_id, side, price, quantity, rest=False)

    def add_fok_order(self, order_id: str, side: str, price: int, quantity: int) -> list[Trade]:
        self._check(side, quantity)
        # PASS 1: decide without touching anything.
        if self._fillable(side, price) < quantity:
            return []
        # PASS 2: now it is safe to mutate -- we know it completes.
        return self._execute(order_id, side, price, quantity, rest=False)

    def modify(self, order_id: str, new_quantity: int) -> bool:
        order = self._orders.get(order_id)
        if order is None or not order.live:
            return False
        if new_quantity <= 0:
            return self.cancel(order_id)
        if new_quantity <= order.quantity:
            order.quantity = new_quantity          # keeps its place in the deque
            return True
        # Increasing: retire the old node and re-queue at the back of the level.
        order.live = False
        order.quantity = 0
        self._rest(order_id, order.side, order.price, new_quantity)
        return True
