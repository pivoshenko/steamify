"""Package that contains a lightweight converter from Markdown into Steam-compatible markup."""

from __future__ import annotations

from importlib.metadata import version

from steamify.steam import to_steam


__version__ = version("steamify")
__all__ = ["to_steam"]
