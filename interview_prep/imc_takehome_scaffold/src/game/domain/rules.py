"""Pure game rules. No IO, no randomness, no framework — so it is trivially testable.

REPLACE the specifics with whatever game IMC asks for. Keep the SHAPE:
  * an enum or value object for the moves
  * a beats-table (data), not a chain of if/elif (code)
  * one function that decides an outcome

Why the data-driven table matters, and say this in your README: adding a new move is a change to
DATA, not to logic. That is the open/closed principle, and it is what the "visitor pattern" hint
in their assignment is probing.
"""

from __future__ import annotations

from enum import Enum


class Move(Enum):
    ROCK = "rock"
    PAPER = "paper"
    SCISSORS = "scissors"


class Outcome(Enum):
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"


# move -> the moves it beats. Extending the game = adding a row here.
BEATS: dict[Move, frozenset[Move]] = {
    Move.ROCK: frozenset({Move.SCISSORS}),
    Move.PAPER: frozenset({Move.ROCK}),
    Move.SCISSORS: frozenset({Move.PAPER}),
}


def resolve(first: Move, second: Move) -> Outcome:
    """Outcome from the perspective of `first`."""
    if first is second:
        return Outcome.DRAW
    return Outcome.WIN if second in BEATS[first] else Outcome.LOSS
