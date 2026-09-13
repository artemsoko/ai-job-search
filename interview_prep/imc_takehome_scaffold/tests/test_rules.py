import pytest

from game.domain.rules import BEATS, Move, Outcome, resolve


@pytest.mark.parametrize("move", list(Move))
def test_same_move_is_a_draw(move):
    assert resolve(move, move) is Outcome.DRAW


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        (Move.ROCK, Move.SCISSORS, Outcome.WIN),
        (Move.ROCK, Move.PAPER, Outcome.LOSS),
        (Move.PAPER, Move.ROCK, Outcome.WIN),
        (Move.PAPER, Move.SCISSORS, Outcome.LOSS),
        (Move.SCISSORS, Move.PAPER, Outcome.WIN),
        (Move.SCISSORS, Move.ROCK, Outcome.LOSS),
    ],
)
def test_full_outcome_table(first, second, expected):
    assert resolve(first, second) is expected


def test_every_move_beats_and_loses_to_the_same_count():
    """A structural invariant: the game is fair. Catches a typo'd BEATS table."""
    beaten_by = {m: sum(m in wins for wins in BEATS.values()) for m in Move}
    assert len({len(BEATS[m]) for m in Move}) == 1
    assert len(set(beaten_by.values())) == 1


def test_resolve_is_antisymmetric():
    for a in Move:
        for b in Move:
            if a is b:
                continue
            forward, backward = resolve(a, b), resolve(b, a)
            assert {forward, backward} == {Outcome.WIN, Outcome.LOSS}
