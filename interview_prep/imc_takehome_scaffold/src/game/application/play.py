"""Orchestration. Depends on the domain and on injected ports, never on a framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from game.domain.rules import Move, Outcome, resolve


class MoveSource(Protocol):
    """A port. The CLI supplies a human; tests supply a script; a bot supplies a strategy.

    Randomness lives BEHIND this seam, which is why the game is deterministic under test.
    """

    def next_move(self) -> Move: ...


@dataclass(frozen=True)
class RoundResult:
    first: Move
    second: Move
    outcome: Outcome


@dataclass
class Scoreboard:
    wins: int = 0
    losses: int = 0
    draws: int = 0

    def record(self, outcome: Outcome) -> None:
        match outcome:
            case Outcome.WIN:
                self.wins += 1
            case Outcome.LOSS:
                self.losses += 1
            case Outcome.DRAW:
                self.draws += 1


@dataclass
class Game:
    player: MoveSource
    opponent: MoveSource
    scoreboard: Scoreboard = field(default_factory=Scoreboard)

    def play_round(self) -> RoundResult:
        a, b = self.player.next_move(), self.opponent.next_move()
        outcome = resolve(a, b)
        self.scoreboard.record(outcome)
        return RoundResult(a, b, outcome)

    def play(self, rounds: int) -> list[RoundResult]:
        if rounds <= 0:
            raise ValueError("rounds must be positive")
        return [self.play_round() for _ in range(rounds)]
