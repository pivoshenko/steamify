"""A lightweight package for converting Markdown into Steam-compatible markup."""

from __future__ import annotations

from importlib.metadata import version

from ihroteka_converter.__main__ import convert


__version__ = version("ihroteka-converter")
__all__ = ["convert"]
