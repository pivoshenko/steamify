# Steamify

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

- Headings (`#` through `######`) to `[h1]` through `[h3]`, since Steam caps at three levels
- Bold, italic, strikethrough, inline code
- Links and images to `[url]` / `[img]`
- Ordered and unordered lists (nested)
- Blockquotes (nested)
- Fenced code blocks to `[code]`
- Horizontal rules to `[hr][/hr]`

### Steam to Markdown

- `[h1]` through `[h6]` to `#` through `######`
- `[b]`, `[i]`, `[strike]`, `[code]` to `**`, `*`, `~~`, backticks
- `[url]` / `[img]` to Markdown links and images
- `[list]` / `[olist]` (nested) to `-` / `1.`
- `[quote]` (nested) to `>`
- `[hr][/hr]` to `---`
- Steam-only tags such as `[spoiler]`, `[noparse]`, `[table]`, and `[u]` have no Markdown
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
