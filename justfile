default:
    @just --list

install:
    uv sync --all-groups --all-extras -U

format:
    uvx ruff check --fix .
    uvx ruff format .

lint:
    uvx ruff check .
    uvx ty check .

test:
    @[ -f .no-tests ] && echo "skipping (.no-tests sentinel)" || uv run pytest .

check: lint test

update:
    uv lock --upgrade
    uvx uv-upsync
