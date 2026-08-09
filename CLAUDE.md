# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`ihroteka-converter` — a zero-runtime-dependency Python library that converts Markdown into Steam-compatible BBCode markup. Python >= 3.10, pinned to 3.13 for development (`.python-version`). Built with hatchling, published to PyPI.

Public API is a single function:

```python
from ihroteka_converter import convert  # convert(markdown_text: str) -> str
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
uv run pytest tests/test_main.py::test_convert
uv run pytest -k inline_bold
uv run pytest --no-cov -x           # skip the coverage report configured in addopts
```

`[tool.pytest.ini_options].addopts` always adds `--cov=src --cov-report=term-missing`; `[tool.coverage.run].omit` excludes `*/__init__.py`.

## Architecture

Two source files only:

- `src/ihroteka_converter/__init__.py` — re-exports `convert`, resolves `__version__` via `importlib.metadata.version("ihroteka-converter")`
- `src/ihroteka_converter/__main__.py` — the entire conversion pipeline

Despite the name, `__main__.py` is **not** a CLI entry point; there is no `[project.scripts]`. It is just where the implementation lives.

### Conversion pipeline

`convert()` splits input with `splitlines()` and feeds each line to `_process_line()`, then `_close_remaining_blocks()` flushes any unterminated code block, list, or quote at EOF.

`_process_line()` dispatch order matters:

1. If inside a fenced code block → accumulate until the closing fence
2. Opening ` ``` ` → enter code-block mode
3. Blank line → close all open lists and quotes
4. `_check_list_continuation()` → closes lists when a non-list, non-indented-quote line appears
5. `_extract_quotes()` strips leading `>` and sets quote depth
6. Heading → horizontal rule → list item (first match wins, so `* * *` is an HR, not a list)
7. Fallback: plain paragraph line

Every block handler routes its text through `_convert_inline_elements()`.

### State

`ConverterState` (a dataclass) is threaded through every handler: `lines` (output buffer), `list_stack` of `(list_type, indent_spaces)` tuples, `current_quote_level`, `inside_code_block`, `code_block_accumulator`. List type `"ol"` maps to `[olist]`, anything else to `[list]`. `_adjust_list_stack()` / `_convert_list_dedent()` / `_convert_list_same_level()` handle nesting by comparing tab-expanded (width 4) indent widths, and swap the wrapper tag when the marker type changes at the same level.

### Inline conversion order

`_convert_inline_elements()` order is load-bearing. Code spans are extracted **first** into `@@CODE{n}@@` placeholders so that bold/italic/link patterns cannot mangle code content, and restored **last**. Between them: images before links (so `![alt](url)` is not eaten by the link regex), then bold before italic (so `***x***` and `**x**` are consumed before the single-`*` italic pattern).

All regexes are module-level `_PATTERN_*` constants at the top of the file.

### Known limitations of the current implementation

- Headings clamp at `[h3]`: `_try_convert_heading` does `min(len(hashes), 3)` since Steam supports only three levels. `####`+ all render as `[h3]`.
- Only **fenced** code blocks are recognized. Indented (4-space) code blocks are not, despite what the README's feature list says.
- The fence info string (` ```python `) is discarded — no language is emitted.

## Tests

`tests/test_main.py` (~550 lines) is the whole suite. It imports the **private** functions (`_convert_inline_bold`, `_adjust_list_stack`, `_extract_quotes`, …) directly by name, so renaming any internal helper breaks the tests — rename in both places. Most tests are `@pytest.mark.parametrize`d tables of `(input, expected)`; end-to-end behavior is covered by `test_convert`, `test_complex_scenarios`, and `test_edge_cases`.

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
- `.github/workflows/release.yaml` — `workflow_dispatch` only, with an optional `version` override input. Three chained jobs: `tag` (git-cliff resolves the bumped version, `uv version` writes it, regenerates `CHANGELOG.md`, commits `release: vX.Y.Z`, tags, pushes to `main`) → `release` (GitHub Release with `git-cliff --latest` body) → `publish` (`uv build` + `uv publish`). Requires the `PYPI_TOKEN` secret.
- `.github/workflows/labels.yaml` — syncs `.github/labels.yaml` to the repo. Requires the `GH_TOKEN` secret.
