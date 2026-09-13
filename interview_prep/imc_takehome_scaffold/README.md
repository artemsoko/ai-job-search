# [Game name]

<!-- TEMPLATE. Rewrite for the actual task, but KEEP the Design decisions section — that is the
     part IMC challenges you on in the 60-minute interview, and pre-arming it is free marks. -->

A [one-sentence description of what the task asked for].

## Running it

```bash
make install          # creates .venv and installs the package with dev extras
make run ARGS="--rounds 5 --seed 42"
make check            # lint + format check + strict type check + tests with coverage
make docker-build && docker run --rm game --rounds 3
```

## Design decisions

### Layering
Three layers, dependencies pointing inwards only:

- `domain/` — the rules. Pure functions and value objects, no IO, no randomness, no framework.
  Testable without any setup.
- `application/` — orchestration. Depends on the domain and on **ports** (Protocols), never on a
  concrete adapter.
- `adapters/` — the only place IO lives: CLI parsing, printing, random number generation.

The point is that the rules can be tested and reasoned about with nothing mocked, and the CLI can
be replaced by an HTTP handler without touching them.

### Extensibility: adding a move is a data change, not a code change
The outcome rules live in a `BEATS` table mapping each move to the set of moves it defeats. Adding
Lizard and Spock means adding rows to that table and members to the enum — `resolve()` does not
change. That is the open/closed principle expressed as data rather than as a class hierarchy.

I considered a visitor / double-dispatch implementation. It buys the same extensibility but costs
a class per move and an accept/visit pair per pairing, which for a rules table of this size is
more indirection than the problem earns. If the rules grew behaviour per move — different scoring,
different side effects — I would switch to it. **Trade-off consciously made, not overlooked.**

### Determinism: randomness is injected, never called
`MoveSource` is a Protocol. `RandomMoveSource` takes an injected `random.Random`, so a test can
pass `random.Random(42)` and get a byte-identical game. `ScriptedMoveSource` removes randomness
entirely for the rules tests. This is why there is not a single mock in the test suite.

### Error handling
Invalid input fails fast with a clear message and a non-zero exit code. No bare `except`. An
exhausted scripted source raises `RuntimeError` with a message that says what happened, rather
than a confusing `StopIteration` escaping from a generator.

### Testing strategy
- A **parametrised truth table** over every move pairing, so a typo in `BEATS` cannot pass.
- **Structural invariant tests** — every move beats and is beaten by the same number of moves, and
  `resolve` is antisymmetric. These catch a wrong rules table even if the explicit cases were
  written wrong too.
- **CLI tests** asserting exit codes and reproducibility under a fixed seed.

Coverage is reported on every `make check`; it currently sits at 96%. The uncovered lines are
argument-parsing error branches.

### What I would do differently with more time
- [Fill this in honestly. One or two items. It reads as maturity, not weakness.]

## Layout

```
src/game/
  domain/rules.py         pure rules, the BEATS table
  application/play.py     Game, Scoreboard, the MoveSource port
  adapters/sources.py     Random and Scripted move sources
  adapters/cli.py         argparse + printing
tests/                    rules, application, CLI
```
