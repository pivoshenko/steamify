"""Module that contains tests for the command-line interface."""

from __future__ import annotations

import io

from typing import TYPE_CHECKING

import pytest

from steamify import __version__
from steamify.__main__ import main


if TYPE_CHECKING:
    from pathlib import Path


def test_stdin_to_stdout(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("# Title"))
    result = main([])
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == "[h1]Title[/h1]\n"


def test_file_to_file(tmp_path: Path) -> None:
    source = tmp_path / "guide.md"
    destination = tmp_path / "out.txt"
    source.write_text("# Title\n", encoding="utf-8")
    result = main([str(source), "-o", str(destination)])
    assert result == 0
    assert destination.read_text(encoding="utf-8") == "[h1]Title[/h1]\n"


def test_stdin_to_stdout_to_markdown(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("[h1]Title[/h1]"))
    result = main(["-", "--to-markdown"])
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == "# Title\n"


def test_stdin_to_stdout_with_encoding(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("**中文**"))
    result = main(["-", "--encoding", "utf-8"])
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == "[b]中文[/b]\n"


def test_missing_input_file_reports_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing.md"
    result = main([str(missing)])
    captured = capsys.readouterr()
    assert result == 1
    assert captured.err.startswith("steamify:")
    assert captured.out == ""


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert captured.out == f"steamify {__version__}\n"


def test_no_argument_reads_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["steamify"])
    monkeypatch.setattr("sys.stdin", io.StringIO("*italic*"))
    result = main()
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out == "[i]italic[/i]\n"
