<h1 align="left">
  <img src="https://raw.githubusercontent.com/pivoshenko/steamify/main/assets/logo.svg" alt="" height="40" align="left" style="vertical-align: middle; margin-right: 12px;">
  Steamify
</h1>

<p align="left">
  <a href="https://pypi.org/project/steamify">
    <img alt="Python" src="https://img.shields.io/pypi/pyversions/steamify?style=flat-square&logo=python&logoColor=white&color=4856CD&label=Python">
  </a>
  <a href="https://pypi.org/project/steamify">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/steamify?style=flat-square&logo=pypi&logoColor=white&color=4856CD&label=PyPI">
  </a>
  <a href="https://github.com/pivoshenko/steamify/actions/workflows/ci.yaml">
    <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/pivoshenko/steamify/ci.yaml?label=CI&style=flat-square&logo=githubactions&logoColor=white&color=0A6847">
  </a>
  <a href="https://docs.astral.sh/ruff">
    <img alt="Ruff" src="https://img.shields.io/badge/Style-ruff-black.svg?style=flat-square&logo=ruff&logoColor=white&color=D7FF64">
  </a>
  <a href="https://stand-with-ukraine.pp.ua">
    <img alt="StandWithUkraine" src="https://img.shields.io/badge/Support-Ukraine-FFC93C?style=flat-square&labelColor=07689F">
  </a>
</p>

## Overview

A lightweight package with zero runtime dependencies for converting Markdown into Steam-compatible
markup, and back again.

## Features

### Markdown to Steam

- Headings (`#` through `######`) to `[h1]` through `[h3]`, since Steam caps at three levels, including
  Setext (`===` / `---`) headings
- Bold, italic, strikethrough, underline (`<u>`), inline code, and `||spoiler||` to `[u]` / `[spoiler]`
- Links and images to `[url]` / `[img]`, including autolinks (`<https://…>`), reference-style links,
  and images wrapped in links
- Ordered and unordered lists (nested), with `- [ ]` / `- [x]` task lists rendered as `☐` / `☑`
- Blockquotes (nested)
- GitHub-flavored pipe tables to `[table]` / `[tr]` / `[th]` / `[td]`
- Fenced code blocks (three or more backticks, or `~~~`) to `[code]`, preserving shorter fences
  nested inside a longer one
- Inline code spans delimited by any number of backticks
- Horizontal rules to `[hr][/hr]`

### Steam to Markdown

- `[h1]` through `[h6]` to `#` through `######`
- `[b]`, `[i]`, `[u]`, `[strike]`, `[code]` to `**`, `*`, `<u>`, `~~`, backticks
- `[spoiler]` to `||…||`
- `[url]` / `[img]` to Markdown links and images
- `[list]` / `[olist]` (nested) to `-` / `1.`, with `☑` / `☐` restored to task-list markers
- `[quote]` (nested) to `>`
- `[table]` / `[tr]` / `[th]` / `[td]` to GitHub-flavored pipe tables
- `[hr][/hr]` to `---`
- Steam-only tags such as `[noparse]`, `[quote=author]`, and `[previewyoutube]` have no Markdown
  equivalent, so they pass through verbatim rather than being dropped

## Installation

Install with pip or uv:

```shell
pip install -U steamify

uv add steamify
```

## Usage

```python
from steamify import to_steam

md_text = """
# My Game Guide

Welcome to the **best** game ever!

## Features

- Easy to learn
- *Beautiful* graphics
- ~~Microtransactions~~ Free to play!

Check out the [wiki](https://example.com) for tips.
"""

steam_text = to_steam(md_text)
print(steam_text)

# [h1]My Game Guide[/h1]

# Welcome to the [b]best[/b] game ever!

# [h2]Features[/h2]

# [list]
# [*] Easy to learn
# [*] [i]Beautiful[/i] graphics
# [*] [strike]Microtransactions[/strike] Free to play!
# [/list]

# Check out the [url=https://example.com]wiki[/url] for tips.
```

Converting the other way:

```python
from steamify import to_markdown

steam_text = """
[h1]Patch Notes[/h1]

[list]
[*] Fixed [b]crash[/b] on startup
[*] [spoiler]Secret boss[/spoiler] added
[/list]
"""

md_text = to_markdown(steam_text)
print(md_text)

# # Patch Notes

# - Fixed **crash** on startup
# - [spoiler]Secret boss[/spoiler] added
```

## Command line

The package installs a `steamify` console script alongside the library, and `python -m steamify` does
the same thing.

```shell
steamify guide.md -o guide.txt              # Markdown file to Steam file
steamify guide.md                           # Markdown file to stdout
steamify --to-markdown guide.txt            # Steam file back to Markdown
cat guide.md | steamify                     # stdin to stdout
steamify -e latin-1 guide.md -o guide.txt   # read and write as latin-1
```

Conventions:

- `-` or an omitted argument means stdin; `-o -` or no `-o` means stdout.
- The default direction is Markdown to Steam. `--to-markdown` reverses it.
- `--encoding` applies to files and to stdin/stdout bytes alike, so pipes honor it too.
- Failures print a single `steamify: <message>` line on stderr and exit with code 1.
