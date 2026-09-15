# Annotated copy of the IMC take-home

**The submitted code is untouched** at `~/Downloads/imc_task`. This is a reading copy: the live
lines are byte-identical, everything added is a comment. Open `app/balances.py` first.

Each comment is one of:
- plain note — why the line is there and what the rejected alternative was
- `SHIPPED GAP` — a real weakness in what IMC received
- `ALTERNATIVE` — working replacement code, commented out

**All commented-out code in here was executed and checked** (5,000 random zero-sum vectors:
every version replay-correct, n−1 bound holds, heap version produces the same transfer count as
the shipped greedy).

## The headline

Greedy was the **right** engineering choice. The word "fewest" was wrong — in `README.md` *and*
`pyproject.toml:4`. Don't apologise for the algorithm; correct the claim.

The cheap fix is an exact-pair pass before greedy (`app/balances.py`, ALTERNATIVE 1). Measured
against the brute-forced true optimum over 3,925 random vectors:

| | result |
|---|---|
| fewer transfers than plain greedy | **71** |
| more transfers than plain greedy | **0** |
| exactly optimal | **3,910 / 3,925 (99.6%)** |
| the known counterexample `A=-4 B=-3 C=2 D=2 E=3` | **4 → 3**, which is optimal |

Still a heuristic — taking pairs greedily is not proven to maximise the number of disjoint
zero-sum subsets. Say that if asked.

## Line to use in the interview

> "Greedy was the right call at this scale and I'd make it again. What was wrong is the word
> 'fewest' in my README — the real bound is n−1, and the true minimum is set partition, so
> NP-hard. If you wanted to close most of that gap cheaply, a ten-line pass that settles exact
> opposite pairs before the greedy loop fixes my own counterexample and never made it worse over
> a few thousand random vectors. I left it out because the saving is in the noise against 5,702
> transfers, but I should have described what the code actually guarantees."

## Also not shipped, one line each

`Dockerfile` runs as root — no `USER` directive. For a trading firm:

```dockerfile
RUN useradd --create-home --uid 10001 app
USER app
```

No `[tool.mypy]`, no `typecheck` target in the Makefile, no mypy pre-commit hook, and ruff does
not select `ANN` — so the zero annotations in `app/` go unnoticed. `mypy` is in dev-deps anyway.

No root `.gitignore`, so `.idea/` and the three tool caches shipped inside the zip, and there is
no git history in it.
