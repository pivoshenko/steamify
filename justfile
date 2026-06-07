default:
    @just --list

install:
    uv sync --all-groups --all-extras

format:
    find . -type f -name '*.py' -not -path '*/.venv/*' | xargs uvx pyupgrade --py310-plus
    uvx ruff check --fix .
    uvx ruff format .

lint:
    uvx ruff check .
    uvx ty check .

test:
    @[ -f .no-tests ] && echo "skipping (.no-tests sentinel)" || uv run pytest .

audit:
    uvx pip-audit

check: lint test

update:
    uv lock --upgrade
    uvx uv-upsync
