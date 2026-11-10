"""Module that contains the command-line interface."""

from __future__ import annotations

import sys
import argparse

from pathlib import Path
from typing import TYPE_CHECKING

from steamify import __version__
from steamify import to_markdown
from steamify import to_steam


if TYPE_CHECKING:
    from collections.abc import Sequence


_STDIO = "-"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="steamify",
        description=(
            "Convert Markdown into Steam-compatible markup, or back again. "
            "A dash ('-') means stdin for input and stdout for output."
        ),
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=_STDIO,
        help="input file to read; '-' or omitted reads from stdin",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=_STDIO,
        help="output file to write; '-' writes to stdout (default: stdout)",
    )
    parser.add_argument(
        "--to-markdown",
        action="store_true",
        help="convert Steam markup into Markdown instead of Markdown into Steam",
    )
    parser.add_argument(
        "-e",
        "--encoding",
        default="utf-8",
        help="encoding used for both reading and writing (default: utf-8)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _read_input(source: str, encoding: str) -> str:
    if source == _STDIO:
        return _read_stdin(encoding)
    return Path(source).read_text(encoding=encoding)


def _read_stdin(encoding: str) -> str:
    buffer = getattr(sys.stdin, "buffer", None)
    if buffer is None:
        return sys.stdin.read()
    return buffer.read().decode(encoding)


def _write_output(destination: str, text: str, encoding: str) -> None:
    if destination == _STDIO:
        _write_stdout(text, encoding)
        return
    Path(destination).write_text(text, encoding=encoding)


def _write_stdout(text: str, encoding: str) -> None:
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is None:
        sys.stdout.write(text)
        return
    sys.stdout.flush()
    buffer.write(text.encode(encoding))
    buffer.flush()


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        source = _read_input(arguments.input, arguments.encoding)
    except (OSError, UnicodeError) as exc:
        sys.stderr.write(f"steamify: {exc}\n")
        return 1
    converted = to_markdown(source) if arguments.to_markdown else to_steam(source)
    if converted and not converted.endswith("\n"):
        converted += "\n"
    try:
        _write_output(arguments.output, converted, arguments.encoding)
    except (OSError, UnicodeError) as exc:
        sys.stderr.write(f"steamify: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
