"""Concrete MoveSource implementations. The seam that keeps the core deterministic."""

from __future__ import annotations

import random
from collections.abc import Iterable, Iterator

from game.domain.rules import Move


class RandomMoveSource:
    def __init__(self, rng: random.Random | None = None) -> None:
        # Injected so a test can pass random.Random(42) and get a repeatable game.
        self._rng = rng or random.Random()

    def next_move(self) -> Move:
        return self._rng.choice(list(Move))


class ScriptedMoveSource:
    """Plays a fixed sequence. Used by tests, and by the CLI in --script mode."""

    def __init__(self, moves: Iterable[Move]) -> None:
        self._moves: Iterator[Move] = iter(list(moves))

    def next_move(self) -> Move:
        try:
            return next(self._moves)
        except StopIteration as exc:
            raise RuntimeError("scripted source exhausted") from exc
