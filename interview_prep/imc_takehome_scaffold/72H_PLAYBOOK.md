# IMC take-home — the 72-hour plan

The clock starts when they send the task. Average candidate spends ~5 hours; you have 72. The
algorithm will be trivial. **The entire test is whether you can ship production-quality code
around it**, which is exactly your ground.

This scaffold already passes `make check` — ruff, ruff-format, strict mypy, 19 tests, 96%
coverage. So you start from green, not from an empty directory.

## Hour 0 — read, do not code (30 min)

- Read the task twice. Write down every requirement as a bullet, verbatim.
- Note anything ambiguous. **You will state your assumption in the README rather than guess
  silently** — that is a maturity signal, and they may be watching for it deliberately.
- Decide what the "moves"/"entities" of this task are, and what the rules table looks like.

## Hour 0.5–2 — make the domain correct

- Copy the scaffold: `cp -r imc_takehome_scaffold ~/imc-assignment && cd ~/imc-assignment`
- Rename `game` to whatever the task is about if the name matters. `sed` across `pyproject.toml`,
  `src/`, `tests/` and the Makefile.
- Rewrite `domain/rules.py` for the real task. Keep the shape: enum plus data table plus one
  resolve function.
- Rewrite `tests/test_rules.py` first, then make it pass. **Write the parametrised truth table.**
- Keep the structural-invariant tests if they translate; they are the ones that impress.

## Hour 2–3.5 — application layer

- Adapt `application/play.py`. Keep the Protocol port and the injected randomness seam.
- Adapt `tests/test_play.py`. Keep the determinism test with a fixed seed.

## Hour 3.5–4.5 — adapters and CLI

- Adapt `adapters/cli.py` for whatever interface the task asks for.
- Keep: non-zero exit code on bad input, `--seed` for reproducibility, clear error to stderr.
- Adapt `tests/test_cli.py`.

## Hour 4.5–5.5 — the README, which is half the grade

Fill in the Design decisions section properly. Specifically:

1. **Why this layering.**
2. **How the design is extensible**, with a concrete example of adding a new case.
3. **An alternative you rejected and why** — this is the single highest-value paragraph in the
   whole submission. The scaffold's visitor-pattern paragraph is a template; make it true for the
   real task.
4. **Any assumption you made** where the spec was ambiguous.
5. **What you would do differently with more time.**

## Hour 5.5–6 — final gate

```bash
make check          # must be green
make docker-build   # must build
git log --oneline   # must read like a sequence of decisions
```

- **Commit history matters.** Not one "initial commit". Something like: scaffold → domain rules +
  tests → application layer → CLI → docker + docs. Six to ten meaningful commits.
- Read your own diff top to bottom once. You will be challenged on specific lines.

## Then stop

Do not spend 20 hours on it. Extra polish past this point has diminishing returns, and the
60-minute interview afterwards is where the marks actually are.

## Rules for using Claude Code on this

IMC's guidance: *"you can Google or use open source as you go, but make sure the work you do is
your own."* There is no AI ban on the take-home (unlike the live station, where Riccardo
confirmed AI is not allowed).

So use it — but **you will be challenged on specific choices in the 60-minute interview with two
Senior Python Engineers**. For every non-obvious line, be able to answer "why this and not the
obvious alternative". If you cannot, rewrite it until you can. "The tool suggested it" is a fail.

## The traps

- **Over-engineering.** They asked for simple, understandable, extensible. A plugin registry and
  an abstract factory for rock-paper-scissors reads as bad judgement, not skill. The rejected
  alternative in the README is how you show you considered more and chose less.
- **Under-testing.** *"Testing is important to us"* is in their own document. A single happy-path
  test is a fail.
- **No README.** Silent code that works still loses.
- **Forgetting the seed.** If your game cannot be replayed deterministically, you cannot test it,
  and they will notice.
