# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
just lint       # ty check + ruff check + commitizen commit lint
just test       # pytest with coverage
just format     # pyupgrade + ruff format

uv audit        # dependency vulnerability scan
uv sync --all-groups --all-extras  # install all dependencies
```

Run a single test by name:
```bash
uv run pytest tests/test_main.py::test_convert -v
```

## Architecture

Single-module library (`src/ihroteka_converter/__main__.py`). The public API is one function:

```python
from ihroteka_converter import convert
result = convert(markdown_text)  # -> Steam BBCode string
```

**Core flow:** `convert()` iterates lines → `_process_line()` dispatches each line → `_close_remaining_blocks()` flushes any open state.

**`ConverterState` dataclass** carries all mutable state across lines:
- `lines` — accumulated output lines
- `list_stack` — stack of `(type, indent)` tuples tracking open `[list]`/`[olist]` tags
- `current_quote_level` — tracks open `[quote]` nesting depth
- `inside_code_block` / `code_block_accumulator` — buffers fenced code blocks until closing ` ``` `

**Inline element processing** uses a placeholder pattern to protect code spans from further substitution: backtick content is extracted to `@@CODE{n}@@` tokens, other inline transforms run (bold, italic, links, images, strikethrough), then tokens are rendered back as `[code]...[/code]`.

**Steam BBCode constraints to keep in mind:** headings cap at `h3` (h4–h6 map to `[h3]`), no native table support.

## Versioning and release

Releases are triggered manually via `workflow_dispatch` on the Release workflow. Version is auto-detected from conventional commits using `python-semantic-release`. Commit parser: `feat` → major, `fix`/`perf`/`refactor` → minor, `docs`/`style` → patch.
