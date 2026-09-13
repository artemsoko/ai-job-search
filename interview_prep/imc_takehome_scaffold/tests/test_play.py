import random

import pytest

from game.adapters.sources import RandomMoveSource, ScriptedMoveSource
from game.application.play import Game, Scoreboard
from game.domain.rules import Move, Outcome


def test_scoreboard_counts_each_outcome():
    s = Scoreboard()
    for o in (Outcome.WIN, Outcome.WIN, Outcome.LOSS, Outcome.DRAW):
        s.record(o)
    assert (s.wins, s.losses, s.draws) == (2, 1, 1)


def test_scripted_game_is_fully_deterministic():
    g = Game(
        player=ScriptedMoveSource([Move.ROCK, Move.PAPER]),
        opponent=ScriptedMoveSource([Move.SCISSORS, Move.SCISSORS]),
    )
    outcomes = [r.outcome for r in g.play(2)]
    assert outcomes == [Outcome.WIN, Outcome.LOSS]
    assert (g.scoreboard.wins, g.scoreboard.losses) == (1, 1)


def test_seeded_random_game_is_reproducible():
    def run():
        rng = random.Random(42)
        g = Game(player=RandomMoveSource(rng), opponent=RandomMoveSource(rng))
        return [(r.first, r.second) for r in g.play(5)]

    assert run() == run()


def test_zero_rounds_rejected():
    g = Game(player=ScriptedMoveSource([]), opponent=ScriptedMoveSource([]))
    with pytest.raises(ValueError):
        g.play(0)


def test_exhausted_script_raises_clearly():
    g = Game(player=ScriptedMoveSource([Move.ROCK]), opponent=ScriptedMoveSource([Move.ROCK]))
    g.play_round()
    with pytest.raises(RuntimeError, match="exhausted"):
        g.play_round()
