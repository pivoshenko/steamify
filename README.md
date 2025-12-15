<p align="center">
  <a href="https://opensource.org/licenses/MIT">
    <img alt="License" src="https://img.shields.io/pypi/l/ihroteka-converter?style=flat-square&logo=opensourceinitiative&logoColor=white&color=0A6847&label=License">
  </a>
  <a href="https://pypi.org/project/ihroteka-converter">
    <img alt="Python" src="https://img.shields.io/pypi/pyversions/ihroteka-converter?style=flat-square&logo=python&logoColor=white&color=4856CD&label=Python">
  </a>
  <a href="https://pypi.org/project/ihroteka-converter">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/ihroteka-converter?style=flat-square&logo=pypi&logoColor=white&color=4856CD&label=PyPI">
  </a>
  <a href="https://github.com/pivoshenko/ihroteka-converter/releases">
    <img alt="Release" src="https://img.shields.io/github/v/release/pivoshenko/ihroteka-converter?style=flat-square&logo=github&logoColor=white&color=4856CD&label=Release">
  </a>
</p>

<p align="center">
  <a href="https://semantic-release.gitbook.io">
    <img alt="Semantic_Release" src="https://img.shields.io/badge/Semantic_Release-angular-e10079?style=flat-square&logo=semanticrelease&logoColor=white&color=D83A56">
  </a>
  <a href="https://pycqa.github.io/isort">
    <img alt="Imports" src="https://img.shields.io/badge/Imports-isort-black.svg?style=flat-square&logo=improvmx&logoColor=white&color=637A9F&">
  </a>
  <a href="https://docs.astral.sh/ruff">
    <img alt="Ruff" src="https://img.shields.io/badge/Style-ruff-black.svg?style=flat-square&logo=ruff&logoColor=white&color=D7FF64">
  </a>
  <a href="https://mypy.readthedocs.io/en/stable/index.html">
    <img alt="mypy" src="https://img.shields.io/badge/mypy-checked-success.svg?style=flat-square&logo=pypy&logoColor=white&color=0A6847">
  </a>
</p>

<p align="center">
  <a href="https://github.com/pivoshenko/ihroteka-converter/actions/workflows/tests.yaml">
    <img alt="Tests" src="https://img.shields.io/github/actions/workflow/status/pivoshenko/ihroteka-converter/tests.yaml?label=Tests&style=flat-square&logo=pytest&logoColor=white&color=0A6847">
  </a>
  <a href="https://github.com/pivoshenko/ihroteka-converter/actions/workflows/linters.yaml">
    <img alt="Linters" src="https://img.shields.io/github/actions/workflow/status/pivoshenko/ihroteka-converter/linters.yaml?label=Linters&style=flat-square&logo=lintcode&logoColor=white&color=0A6847">
  </a>
  <a href="https://github.com/pivoshenko/ihroteka-converter/actions/workflows/release.yaml">
    <img alt="Release" src="https://img.shields.io/github/actions/workflow/status/pivoshenko/ihroteka-converter/release.yaml?label=Release&style=flat-square&logo=pypi&logoColor=white&color=0A6847">
  </a>
  <a href="https://codecov.io/gh/pivoshenko/ihroteka-converter" >
    <img alt="Codecov" src="https://img.shields.io/codecov/c/gh/pivoshenko/ihroteka-converter?token=cqRQxVnDR6&style=flat-square&logo=codecov&logoColor=white&color=0A6847&label=Coverage"/>
  </a>
</p>

<p align="center">
  <a href="https://pypi.org/project/ihroteka-converter">
    <img alt="Downloads" src="https://img.shields.io/pypi/dm/ihroteka-converter?style=flat-square&logo=pythonanywhere&logoColor=white&color=4856CD&label=Downloads">
  </a>
  <a href="https://github.com/pivoshenko/ihroteka-converter">
    <img alt="Stars" src="https://img.shields.io/github/stars/pivoshenko/ihroteka-converter?style=flat-square&logo=apachespark&logoColor=white&color=4856CD&label=Stars">
  </a>
</p>

<p align="center">
  <a href="https://stand-with-ukraine.pp.ua">
    <img alt="StandWithUkraine" src="https://img.shields.io/badge/Support-Ukraine-FFC93C?style=flat-square&labelColor=07689F">
  </a>
</p>

## Overview

A lightweight package for converting Markdown into Steam-compatible markup.

**About the name**

*Ihroteka* (pronounced [ee-hroh-teh-kah]) is a Ukrainian word formed from "hra" (game) and "teka" (a place of keeping, an archive).
It evokes the image of a living library of games - a space where experiences are gathered, preserved, and given structure.

## Installation

Proceed by installing the tool and running it:

```shell
pip install -U ihroteka-converter

uv add ihroteka-converter
```

## Examples

```python
from ihroteka_converter import convert

md_text = """
# My Game Guide

Welcome to the **best** game ever!

## Features

- Easy to learn
- *Beautiful* graphics
- ~~Microtransactions~~ Free to play!

Check out the [wiki](https://example.com) for tips.
"""

steam_text = convert(md_text)
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
