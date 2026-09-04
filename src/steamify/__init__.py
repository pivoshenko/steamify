"""Package that contains a lightweight converter between Markdown and Steam-compatible markup."""

from __future__ import annotations

from importlib.metadata import version

from steamify.markdown import to_markdown
from steamify.steam import to_steam


__version__ = version("steamify")
__all__ = ["to_markdown", "to_steam"]
