# CLAUDE.md

`steamify` is a published PyPI library that converts Markdown to Steam's BBCode-style markup and
back, exposing exactly two public functions, `to_steam` and `to_markdown`. `README.md` lists the
supported constructs; `CONTRIBUTING.md` covers commands, branches, commits, and CI.

## Constraints

- **Zero runtime dependencies is a product constraint, not an accident.** Everything is built on `re`
  and the standard library. Do not add a runtime dependency without the maintainer asking for one
- **`requires-python = ">=3.10"` is the supported floor**, even though `.python-version` pins 3.13
  for local development and CI. `just format` enforces it by running `pyupgrade --py310-plus`
- **Run `just check` before proposing a change is done** (`just --list` for the rest). Type checking
  is `ty`, not mypy
- **Never hand-edit `version` in `pyproject.toml` or `CHANGELOG.md`.** The Release workflow
  (`workflow_dispatch` only) derives both from the commit history with git-cliff
- **`AGENTS.md` is a symlink to this file.** Edit `CLAUDE.md`; writing `AGENTS.md` directly replaces
  the symlink with a regular file
- **`.no-tests` is an untracked sentinel that makes `just test` a no-op.** Do not create it unless
  deliberately silencing the suite
- Ruff runs `select = ["ALL"]` - assume a new rule will fire and run `just format` before `just lint`
- `just format` and `just lint` reach ruff and ty through `uvx` (ambient, latest) while `just test`
  runs through `uv run` (project venv). A ruff version skew between the two is therefore possible and
  is not a bug to chase
- Coverage is reported, not gated - there is no `fail_under`, so `term-missing` output blocks nothing
- `__init__.py` sets `__version__` from `importlib.metadata.version("steamify")`, so the package must
  be installed (editable is fine) for import to work

## Invariants

`steam.py` (Markdown -> Steam) and `markdown.py` (Steam -> Markdown) are deliberate mirror images of
each other. When editing one, check whether the other needs the symmetric change.

- **The `_try_convert_*` contract** - each returns `True` if it consumed the line and `False` if it
  did not apply, and `_process_line` relies on that to short-circuit. Order matters: in `markdown.py`
  the chain is a single `or` expression, and code-block detection must come first so markup inside a
  `[code]` block is never interpreted
- **The `@@CODE{n}@@` sandwich** - inside `_convert_inline_elements`, `_convert_inline_code_spans`
  pulls every code span out and leaves a sentinel, the other inline conversions run on the
  sentinel-bearing text, then `_render_inline_code_spans` substitutes the originals back wrapped in
  the target syntax. This is what stops `**bold**` inside `` `code` `` from being mangled, so any new
  inline conversion must be inserted **between** the extract and render steps or code spans stop
  being protected
- **`list_stack` diverges between the modules** - it is a `list[tuple[str, int]]` in both, but the
  second element is the source indent width in spaces in `steam.py`, used to decide
  open/close/dedent, and the running item counter in `markdown.py`, used to number `[olist]` entries

### Deliberate Asymmetries

These look like bugs but are intended; tests lock them in:

- `to_steam` clamps headings to h1-h3 because Steam only supports three heading levels, while
  `to_markdown` maps `[h1]`-`[h6]` to `#`-`######`
- Steam-only tags with no Markdown equivalent pass through verbatim rather than being stripped - see
  `test_unmappable_tags_pass_through`
- The round-trip guarantee is convergence, not identity: `to_steam(to_markdown(steam)) == steam`
  after the first pass, enforced by `test_round_trip_is_stable`. Markdown -> Steam -> Markdown is not
  required to return the original string

## Adding a New Construct

1. Add the compiled pattern to the `_PATTERN_*` block at the top of the module, not inline in a
   function
2. Block-level: write another `_try_convert_*` and insert it at the right position in the
   `_process_line` chain, never ahead of code-block detection
3. Inline: add the conversion between the extract and render halves of `_convert_inline_elements`
4. Make the symmetric change in the sibling module, or establish why it does not apply
5. Add cases to the existing `test_complex_scenarios` / `test_edge_cases` parametrize blocks

## Tests

The suite is **white-box**: private functions are imported directly by name and tested individually,
alongside end-to-end `to_steam` / `to_markdown` cases. Renaming a private helper breaks tests, which
is intentional. Heavy use of `@pytest.mark.parametrize` with `(input, expected)` tuples - add cases
to an existing parametrize list rather than writing a new test function when the shape fits.
