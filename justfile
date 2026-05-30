default:
    @just --list

install:
    uv sync --all-groups --all-extras

format:
    find src -type f -name '*.py' | xargs uv run pyupgrade --py310-plus
    find tests -type f -name '*.py' | xargs uv run pyupgrade --py310-plus
    uv run ruff format .

lint:
    uv run ty check .
    uv run ruff check .

test:
    uv run pytest .

audit:
    uv audit

check: lint test audit

update:
    uv lock --upgrade
    uvx uv-upsync

release version:
    @echo "TODO: implement release flow for {{ version }}"
