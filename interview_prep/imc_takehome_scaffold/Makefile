.PHONY: install test lint typecheck check run docker-build clean
install:       ; python3 -m venv .venv && ./.venv/bin/pip install -e ".[dev]"
test:          ; ./.venv/bin/pytest
lint:          ; ./.venv/bin/ruff check src tests && ./.venv/bin/ruff format --check src tests
typecheck:     ; ./.venv/bin/mypy src
check: lint typecheck test
run:           ; ./.venv/bin/game $(ARGS)
docker-build:  ; docker build -t game .
clean:         ; rm -rf .venv .pytest_cache .mypy_cache .ruff_cache **/__pycache__ .coverage
