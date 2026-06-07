default:
    @just --list

install:
    uv sync --all-groups --all-extras

format:
    find src -type f -name '*.py' | xargs uvx pyupgrade --py310-plus
    find tests -type f -name '*.py' | xargs uvx pyupgrade --py310-plus
    uvx ruff check --fix .
    uvx ruff format .

lint:
    uvx ruff check .
    uvx ruff format --check .
    uvx ty check .

test:
    uvx pytest .

audit:
    uvx pip-audit

check: lint test

update:
    uvx uv-upsync
    uv sync
