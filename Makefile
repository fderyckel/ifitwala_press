.PHONY: help install-dev lint format format-check test js-check js-check-hook ci pre-commit-install pre-commit-run

PYTHON ?= python3
NODE ?= node

help:
	@printf '%s\n' \
		'install-dev         Install local dev tooling' \
		'lint                Run Ruff lint checks' \
		'format              Apply Ruff formatting and safe fixes' \
		'format-check        Check formatting without changing files' \
		'test                Run pytest' \
		'js-check            Run Node syntax checks on Desk/page JavaScript' \
		'js-check-hook       Run JS syntax checks when Node is available locally' \
		'ci                  Run the local CI command set' \
		'pre-commit-install  Install pre-commit and pre-push hooks' \
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

js-check:
	@PATH="/opt/homebrew/bin:/usr/local/bin:$$PATH"; \
	NODE_BIN="$$(command -v $(NODE) 2>/dev/null || command -v nodejs 2>/dev/null || true)"; \
	if [ -z "$$NODE_BIN" ] && [ -n "$$NVM_DIR" ]; then \
		NODE_BIN="$$(find "$$NVM_DIR/versions/node" -maxdepth 2 -path "*/bin/node" 2>/dev/null | sort -V | tail -n 1)"; \
	fi; \
	if [ -z "$$NODE_BIN" ]; then \
		NODE_BIN="$$(find "$$HOME/.nvm/versions/node" -maxdepth 2 -path "*/bin/node" 2>/dev/null | sort -V | tail -n 1)"; \
	fi; \
	[ -n "$$NODE_BIN" ] || { printf '%s\n' 'node or nodejs is required for js-check; install Node 24 or ensure it is available in /opt/homebrew/bin, /usr/local/bin, or ~/.nvm'; exit 1; }; \
	find ifitwala_press -type f \( -path '*/public/js/*.js' -o -path '*/page/*/*.js' \) -print | sort | while read -r file; do \
		"$$NODE_BIN" --check "$$file"; \
	done

js-check-hook:
	@PATH="/opt/homebrew/bin:/usr/local/bin:$$PATH"; \
	NODE_BIN="$$(command -v $(NODE) 2>/dev/null || command -v nodejs 2>/dev/null || true)"; \
	if [ -z "$$NODE_BIN" ] && [ -n "$$NVM_DIR" ]; then \
		NODE_BIN="$$(find "$$NVM_DIR/versions/node" -maxdepth 2 -path "*/bin/node" 2>/dev/null | sort -V | tail -n 1)"; \
	fi; \
	if [ -z "$$NODE_BIN" ]; then \
		NODE_BIN="$$(find "$$HOME/.nvm/versions/node" -maxdepth 2 -path "*/bin/node" 2>/dev/null | sort -V | tail -n 1)"; \
	fi; \
	if [ -z "$$NODE_BIN" ]; then \
		printf '%s\n' 'Skipping js-check hook locally because node/nodejs is not available; GitHub CI still enforces make js-check.'; \
		exit 0; \
	fi; \
	find ifitwala_press -type f \( -path '*/public/js/*.js' -o -path '*/page/*/*.js' \) -print | sort | while read -r file; do \
		"$$NODE_BIN" --check "$$file"; \
	done

ci: lint format-check test js-check

pre-commit-install:
	$(PYTHON) -m pre_commit install --hook-type pre-commit --hook-type pre-push

pre-commit-run:
	$(PYTHON) -m pre_commit run --all-files
