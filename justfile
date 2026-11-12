default:
    @just --list

install:
    uv sync --all-groups --all-extras

format:
    uv run ruff check --fix .
    uv run ruff format .

lint:
    uv run ruff check .
    uv run ty check .

audit:
    uv audit --preview-features audit-command

test:
    @[ -f .no-tests ] && echo "skipping (.no-tests sentinel)" || uv run pytest .

check: lint test

update:
    uv lock --upgrade
    uv run uv-upsync
