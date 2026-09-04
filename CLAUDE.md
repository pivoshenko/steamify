# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`steamify` — a zero-runtime-dependency Python library that converts Markdown into Steam-compatible BBCode markup and back. Python >= 3.10, pinned to 3.13 for development (`.python-version`). Built with hatchling, published to PyPI.

Public API is two functions:

```python
from steamify import to_markdown  # to_markdown(steam_text: str) -> str
from steamify import to_steam  # to_steam(markdown_text: str) -> str
```

## Commands

The `justfile` is the entry point for everything:

```shell
just install   # uv sync --all-groups --all-extras
just format    # pyupgrade --py310-plus over all .py, then ruff check --fix, then ruff format
just lint      # ruff check . && ty check .
just test      # uv run pytest . (no-ops if a .no-tests sentinel file exists)
just audit     # uvx pip-audit
just check     # lint + test
just update    # uv lock --upgrade && uvx uv-upsync
```

Note the split: `format`, `lint`, and `audit` run tools via `uvx` (ephemeral, ignores the project venv); only `test` runs inside the project env via `uv run`.

Run a single test or a subset:

```shell
uv run pytest tests/test_steam.py::test_to_steam
uv run pytest -k inline_bold
uv run pytest --no-cov -x           # skip the coverage report configured in addopts
```

`[tool.pytest.ini_options].addopts` always adds `--cov=src --cov-report=term-missing`; `[tool.coverage.run].omit` excludes `*/__init__.py`.

## Architecture

Three source files, one per direction:

- `src/steamify/__init__.py` — re-exports `to_steam` and `to_markdown`, resolves `__version__` via `importlib.metadata.version("steamify")`
- `src/steamify/steam.py` — the Markdown → Steam pipeline
- `src/steamify/markdown.py` — the Steam → Markdown pipeline

Each module is named for what it **produces**. There is no `__main__.py` and no `[project.scripts]`, so `python -m steamify` fails with `No module named steamify.__main__`; the package is import-only.

Both pipelines share the same shape: a state dataclass named for what the module produces (`SteamState`, `MarkdownState`) and threaded through line handlers, `_try_convert_*` predicates that return `True` when they consume a line, and a single `_convert_inline_elements()` funnel. When editing one direction, check whether the mirror needs the same change.

### Markdown → Steam pipeline

`to_steam()` splits input with `splitlines()` and feeds each line to `_process_line()`, then `_close_remaining_blocks()` flushes any unterminated code block, list, or quote at EOF.

`_process_line()` dispatch order matters:

1. If inside a fenced code block → accumulate until the closing fence
2. Opening ` ``` ` → enter code-block mode
3. Blank line → close all open lists and quotes
4. `_check_list_continuation()` → closes lists when a non-list, non-indented-quote line appears
5. `_extract_quotes()` strips leading `>` and sets quote depth
6. Heading → horizontal rule → list item (first match wins, so `* * *` is an HR, not a list)
7. Fallback: plain paragraph line

Every block handler routes its text through `_convert_inline_elements()`.

### Steam → Markdown pipeline

`to_markdown()` mirrors it: `_process_line()` dispatches on a stripped line, and the `_try_convert_*` handlers are chained with `or` (first match wins) rather than sequential early returns, to stay under ruff's `PLR0911` return limit.

1. If inside a `[code]` block → accumulate until `[/code]`
2. Blank line → emit blank
3. `_try_convert_code_block_open()` — a `[code]` left unclosed on its line opens a block; a `[code]…[/code]` pair on one line is left to the inline pass
4. `_try_convert_quote_level()` — a line made **only** of `[quote]`/`[/quote]` tokens adjusts depth and emits nothing (`close_quotes()` on the forward side can emit several on one line)
5. List open → list close → `[*]` item
6. Heading → horizontal rule
7. Fallback: plain paragraph line

Anything unrecognized falls through untouched, which is what makes `[spoiler]`, `[noparse]`, `[table]`, and `[u]` survive verbatim.

`MarkdownState.prefix()` wraps every emitted line in `"> " * current_quote_level`, so quote depth is applied at write time rather than tracked in the output buffer. Nested list depth is `len(list_stack) - 1`, rendered as 2 spaces per level (`_INDENT_WIDTH`); `[olist]` items get their number from a per-frame counter stored in the `list_stack` tuple.

### State

`SteamState` (`steam.py`) is threaded through every handler: `lines` (output buffer), `list_stack` of `(list_type, indent_spaces)` tuples, `current_quote_level`, `inside_code_block`, `code_block_accumulator`. List type `"ol"` maps to `[olist]`, anything else to `[list]`. `_adjust_list_stack()` / `_convert_list_dedent()` / `_convert_list_same_level()` handle nesting by comparing tab-expanded (width 4) indent widths, and swap the wrapper tag when the marker type changes at the same level.

`MarkdownState` (`markdown.py`) is the mirror: `lines`, `list_stack` of `(list_type, item_number)` tuples, `current_quote_level`, `inside_code_block`, `code_block_accumulator`. Note the `list_stack` tuple holds a **counter**, not an indent width — that is the one place the two states diverge in meaning.

### Inline conversion order

`_convert_inline_elements()` order is load-bearing. Code spans are extracted **first** into `@@CODE{n}@@` placeholders so that bold/italic/link patterns cannot mangle code content, and restored **last**. Between them: images before links (so `![alt](url)` is not eaten by the link regex), then bold before italic (so `***x***` and `**x**` are consumed before the single-`*` italic pattern).

All regexes are module-level `_PATTERN_*` constants at the top of the file.

### Known limitations of the current implementation

- Headings clamp at `[h3]`: `_try_convert_heading` does `min(len(hashes), 3)` since Steam supports only three levels. `####`+ all render as `[h3]`.
- Only **fenced** code blocks are recognized. Indented (4-space) code blocks are not.
- The fence info string (` ```python `) is discarded — no language is emitted.
- `to_markdown()` normalizes rather than preserves: `[img]` carries no alt text so it returns `![]()`, a single-line `[code]…[/code]` returns as an inline span rather than a fence, and nested quotes come back as `> > ` rather than `>> `. All three re-convert to identical Steam markup, so `to_steam(to_markdown(steam)) == steam` holds — that round-trip identity is asserted by `test_round_trip_is_stable` and is the property to protect when changing either direction.

## Tests

`tests/test_steam.py` (~550 lines) and `tests/test_markdown.py` (~370 lines) are the whole suite, one per direction. Both import the **private** functions (`_convert_inline_bold`, `_adjust_list_stack`, `_extract_quotes`, …) directly by name, so renaming any internal helper breaks the tests — rename in both places. Most tests are `@pytest.mark.parametrize`d tables of `(input, expected)`; end-to-end behavior is covered by `test_to_steam` / `test_to_markdown`, `test_complex_scenarios`, `test_edge_cases`, and — in `test_markdown.py` only — `test_round_trip_is_stable`.

## Code style

- Ruff with `select = ["ALL"]` — every rule on, ignoring only `COM812`, `CPY001`, `D102`, `D103`, `D203`, `D212`. Docstrings on public functions are effectively optional (`D102`/`D103` off) but module docstrings are required.
- `from __future__ import annotations` is a ruff-enforced required import in every file.
- One import per line (`force-single-line`), length-sorted, 1 blank line between import types, 2 blank lines after the import block.
- Line length 100 (ruff) — note `.editorconfig` says 120 for non-Python files; Python is 4-space indent.
- `tests/*.py` additionally ignores `INP001` and `S101`.
- Module docstrings follow the pattern `"""Module that contains ..."""`; `__init__.py` uses `"""Package that contains ..."""`.
- The codebase prefers `match` statements over `if/elif` chains for tag selection.

## Release and conventions

- Conventional Commits, enforced in spirit by `cliff.toml` (`filter_unconventional = true` — non-conforming commits vanish from the changelog). Branches: `<type>/<kebab-description>`. Full table of type prefixes is in `CONTRIBUTING.md`.
- Version lives only in `pyproject.toml` `[project] version`; `git-cliff` `[bump]` bumps minor on `feat`, major on breaking.
- `.github/workflows/ci.yaml` — push to `main`, PRs, manual. Single `ci` job on `ubuntu-24.04-arm`: `just install` → `just lint` → `just audit` → `just test`. Concurrency cancels in-flight PR runs.
- `.github/workflows/release.yaml` — `workflow_dispatch` only, with an optional `version` override input. Three chained jobs: `tag` (git-cliff resolves the bumped version, `uv version` writes it, regenerates `CHANGELOG.md`, commits `release: vX.Y.Z`, tags, pushes to `main`) → `release` (GitHub Release with `git-cliff --latest` body) → `publish` (`uv build` + `uv publish --trusted-publishing always`). Uses PyPI trusted publishing (OIDC), so no PyPI token secret is needed.
- `.github/workflows/labels.yaml` — syncs `.github/labels.yaml` to the repo. Requires the `GH_TOKEN` secret.
