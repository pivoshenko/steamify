# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

ihroteka-converter — a lightweight Python library that converts Markdown into Steam-compatible BBCode markup. Zero runtime dependencies. Supports Python 3.10+.

Public API: `from ihroteka_converter import convert` — single `convert(markdown_text: str) -> str` function.

## Commands

```shell
just format    # pyupgrade + ruff format
just lint      # ty check + ruff check
just test      # pytest with coverage (html, term-missing, xml)
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
- Versioning managed by python-semantic-release
- Build backend: hatchling
