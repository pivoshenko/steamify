default:
    @just --list

install: install-package

install-package:
    uv sync --all-groups --all-extras

format: format-package

format-package:
    uv run ruff check --fix .
    uv run ruff format .

lint: lint-package

lint-package:
    uv run ruff check .
    uv run ty check .

audit: audit-package

audit-package:
    uv audit --preview-features audit-command

test: test-package

test-package:
    @[ -f .no-tests ] && echo "skipping (.no-tests sentinel)" || uv run pytest .

check: lint test

update: update-package

update-package:
    uv lock --upgrade
    uv run uv-upsync
