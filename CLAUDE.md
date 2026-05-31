# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

ihroteka-converter — a lightweight Python library that converts Markdown into Steam-compatible BBCode markup. Zero runtime dependencies. Supports Python 3.10+.

Public API: `from ihroteka_converter import convert` — single `convert(markdown_text: str) -> str` function.

## Commands

```shell
just install   # uv sync --all-groups --all-extras
just format    # pyupgrade + ruff format
just lint      # ty check + ruff check
just test      # pytest with coverage (term-missing)
just audit     # uv audit
just check     # lint + test + audit
just update    # uv lock --upgrade + uvx uv-upsync
```

All commands use `uv run` under the hood. Run a single test: `uv run pytest tests/test_main.py::test_name -x`.

## Architecture

All conversion logic lives in a single module: `src/ihroteka_converter/__main__.py`. `__init__.py` re-exports `convert` and holds `__version__`.

**Conversion pipeline:** `convert()` → iterates lines → `_process_line()` dispatches to block-level handlers (code blocks, headings, horizontal rules, lists, quotes) → each handler calls `_convert_inline_elements()` for inline formatting (bold, italic, strikethrough, links, images, code spans).

**State management:** `ConverterState` dataclass tracks output lines, nested list stack, quote depth, and code block accumulation. Lists and quotes are closed automatically on empty lines or context switches.

**Inline code spans** are extracted first (replaced with `@@CODE{n}@@` placeholders) to prevent other inline patterns from modifying code content, then restored last.

## Code Style

- Ruff with `select = ["ALL"]` — every rule enabled, few explicit ignores
- `from __future__ import annotations` required in every file (enforced by ruff isort)
- Single imports per line, length-sorted, 2 blank lines after imports
- Line length: 100
- Tests use parametrized pytest; test file mirrors internal function names

## Conventions

- Conventional Commits (`feat`, `fix`, `docs`, `refactor`, etc.)
- Versioning + changelog managed by git-cliff (`cliff.toml`); release pipeline = `uv version` + `uv build` + `uv publish`
- `__version__` resolves at runtime via `importlib.metadata.version("ihroteka-converter")`; single source of truth is `pyproject.toml` `[project] version`
- Build backend: hatchling

## GitHub Workflows

- `.github/workflows/ci.yaml` — PR gate. Runs on push to `main`, PRs, manual dispatch. Steps: checkout → setup just + uv (Python 3.13) → `just install` → `just lint` → `just test` → `just audit`. Concurrency cancels in-progress PR runs.
- `.github/workflows/release.yaml` — Manual dispatch only (`workflow_dispatch` with optional `version` input). Three jobs:
  1. **tag** — git-cliff resolves bumped version, `uv version` updates `pyproject.toml`, git-cliff regenerates `CHANGELOG.md`, commits + tags `v<semver>`, pushes to `main`.
  2. **release** — generates latest-only changelog body, creates GitHub Release for the tag.
  3. **publish** — `uv build` + `uv publish --token $PYPI_TOKEN`.
  Required secrets: `GH_TOKEN`, `PYPI_TOKEN`.
- `.github/workflows/labels.yaml` — syncs `.github/labels.yaml` to the GitHub repository on changes or manual dispatch via `crazy-max/ghaction-github-labeler@v6`. Required secret: `GH_TOKEN`.
