.PHONY: help install-dev lint format format-check test ci pre-commit-install pre-commit-run

PYTHON ?= python3

help:
	@printf '%s\n' \
		'install-dev         Install local dev tooling' \
		'lint                Run Ruff lint checks' \
		'format              Apply Ruff formatting and safe fixes' \
		'format-check        Check formatting without changing files' \
		'test                Run pytest' \
		'ci                  Run the local CI command set' \
		'pre-commit-install  Install git hooks' \
		'pre-commit-run      Run all pre-commit hooks'

install-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[dev]'

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

format-check:
	$(PYTHON) -m ruff format --check .

test:
	$(PYTHON) -m pytest

ci: lint format-check test

pre-commit-install:
	$(PYTHON) -m pre_commit install

pre-commit-run:
	$(PYTHON) -m pre_commit run --all-files
