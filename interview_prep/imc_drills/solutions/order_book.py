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
    def add_limit_order(self, order_id: str, side: str, price: int, quantity: int) -> list[Trade]:
        if side not in ("buy", "sell"):
            raise ValueError(f"bad side: {side!r}")
        if quantity <= 0:
            raise ValueError("quantity must be positive")

        other = "sell" if side == "buy" else "buy"
        trades: list[Trade] = []
        remaining = quantity

        while remaining > 0:
            self._prune(other)
            best = self.best_ask() if other == "sell" else self.best_bid()
            if best is None:
                break
            crosses = best <= price if other == "sell" else best >= price
            if not crosses:
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

        if remaining > 0:
            resting = _Resting(order_id, side, price, remaining)
            existing = self._levels.get((side, price))
            self._level(side, price).append(resting)
            self._orders[order_id] = resting
            if not existing:
                self._push_price(side, price)
        return trades

    def cancel(self, order_id: str) -> bool:
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
