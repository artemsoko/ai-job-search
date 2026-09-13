"""CLI adapter. Argument parsing and printing only — no rules here."""

from __future__ import annotations

import argparse
import random
import sys

from game.adapters.sources import RandomMoveSource, ScriptedMoveSource
from game.application.play import Game, MoveSource
from game.domain.rules import Move


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="game", description="Play a game.")
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--seed", type=int, help="seed the RNG for a reproducible game")
    p.add_argument("--script", help="comma-separated moves for the player, e.g. rock,paper")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rng = random.Random(args.seed)
    if args.script:
        try:
            moves = [Move(m.strip()) for m in args.script.split(",")]
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        player: MoveSource = ScriptedMoveSource(moves)
        rounds = len(moves)
    else:
        player = RandomMoveSource(rng)
        rounds = args.rounds

    game = Game(player=player, opponent=RandomMoveSource(rng))
    try:
        results = game.play(rounds)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    for i, r in enumerate(results, 1):
        print(f"round {i}: {r.first.value} vs {r.second.value} -> {r.outcome.value}")
    s = game.scoreboard
    print(f"result: {s.wins}W / {s.losses}L / {s.draws}D")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
