# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`steamify` — a zero-runtime-dependency Python library converting Markdown to Steam-compatible BBCode markup and back. Python >= 3.10, dev pinned to 3.13 (`.python-version`). Built with hatchling, published to PyPI.

The entire public API is two functions:

```python
from steamify import to_steam      # to_steam(markdown_text: str) -> str
from steamify import to_markdown   # to_markdown(steam_text: str) -> str
```

There is no CLI, no `__main__.py`, no `[project.scripts]` — the package is import-only.

## Commands

All workflows go through the `justfile`:

```shell
just install   # uv sync --all-groups --all-extras
just format    # pyupgrade --py310-plus over all .py, then ruff check --fix, then ruff format
just lint      # uvx ruff check . && uvx ty check .
just test      # uv run pytest . (skipped if a .no-tests sentinel file exists)
just audit     # uvx pip-audit
just check     # lint + test
just update    # uv lock --upgrade && uvx uv-upsync
```

Note: `format`, `lint`, and `audit` run tools via `uvx` (ephemeral envs); only `test` runs inside the project venv via `uv run`.

Single test / subset:

```shell
uv run pytest tests/test_steam.py::test_to_steam
uv run pytest -k inline_bold
uv run pytest --no-cov -x    # bypass coverage configured in addopts
```

pytest `addopts` always injects `--cov=src --cov-report=term-missing`; coverage omits `*/__init__.py`.

## Architecture

Two mirror-image modules, each named for the format it **produces**:

- `src/steamify/steam.py` — Markdown → Steam pipeline (`to_steam`, `SteamState`)
- `src/steamify/markdown.py` — Steam → Markdown pipeline (`to_markdown`, `MarkdownState`)
- `src/steamify/__init__.py` — re-exports both; `__version__` resolved via `importlib.metadata`

Both pipelines share one shape: `to_*()` splits input with `splitlines()`, feeds each line through `_process_line(line, state)`, then `_close_remaining_blocks()` flushes unterminated code blocks/lists/quotes at EOF. Line handlers are `_try_convert_*` predicates returning `True` when they consume the line — **dispatch order in `_process_line` matters** (code block > quotes > lists > heading > hr > plain text). All inline formatting funnels through `_convert_inline_elements()`, which protects code spans first by swapping them for `@@CODE{n}@@` placeholders, converts images/links/bold/italic/strikethrough, then restores spans — so code-span protection ordering is load-bearing.

When changing one direction, check whether the mirror module needs the symmetric change.

Domain asymmetries to keep in mind (see README for the full list):

- Steam caps headings at `[h3]`; Markdown `####`+ collapses to `[h3]` going in, but `[h4]`-`[h6]` map back to `####`-`######`
- Steam-only tags (`[spoiler]`, `[noparse]`, `[table]`, `[u]`) pass through `to_markdown` verbatim, never dropped
- List state is a stack of `(type, indent)` tuples in `SteamState` vs `(type, item_counter)` in `MarkdownState`

## Tests

`tests/test_steam.py` and `tests/test_markdown.py` (no `__init__.py`; `INP001`/`S101` are per-file-ignored). Tests import and exercise private `_`-prefixed functions directly, heavily parametrized — follow that pattern for new handlers.

## Conventions

- Ruff with `select = ["ALL"]`, line length 100, `fix = true` + `unsafe-fixes = true`; isort forces single-line imports, length-sorted, with `from __future__ import annotations` required in every file, two blank lines after imports
- Typecheck is `ty` (not mypy/pyright)
- Conventional Commits enforced by cliff.toml (`filter_unconventional = true`): non-conventional commit subjects are silently dropped from the changelog. Branch names follow `<type>/<short-description>` (CONTRIBUTING.md)

## CI and release

- CI (`.github/workflows/ci.yaml`): runs `just install`, `just lint`, `just audit`, `just test` on ubuntu-24.04-arm with Python 3.13 — all four must pass
- Release (`.github/workflows/release.yaml`): manual `workflow_dispatch` only. Version is auto-bumped by `git-cliff --bumped-version` from conventional commits (feat → minor, breaking → major) unless overridden via input; the workflow runs `uv version`, regenerates CHANGELOG.md, commits `release: vX.Y.Z`, tags, creates a GitHub release, and publishes to PyPI via `uv publish --trusted-publishing always`
- `CHANGELOG.md` and the `version` field in pyproject.toml are release-workflow-owned — never edit them by hand
