"""Tests for the main module."""

from __future__ import annotations

import pytest

from ihroteka_converter.__main__ import ConverterState
from ihroteka_converter.__main__ import _adjust_list_stack
from ihroteka_converter.__main__ import _check_list_continuation
from ihroteka_converter.__main__ import _close_remaining_blocks
from ihroteka_converter.__main__ import _convert_code_block_content
from ihroteka_converter.__main__ import _convert_empty_line
from ihroteka_converter.__main__ import _convert_inline_bold
from ihroteka_converter.__main__ import _convert_inline_code_spans
from ihroteka_converter.__main__ import _convert_inline_elements
from ihroteka_converter.__main__ import _convert_inline_images
from ihroteka_converter.__main__ import _convert_inline_italic
from ihroteka_converter.__main__ import _convert_inline_links
from ihroteka_converter.__main__ import _convert_inline_strikethrough
from ihroteka_converter.__main__ import _convert_list_dedent
from ihroteka_converter.__main__ import _convert_list_same_level
from ihroteka_converter.__main__ import _convert_quote_level
from ihroteka_converter.__main__ import _extract_quotes
from ihroteka_converter.__main__ import _process_line
from ihroteka_converter.__main__ import _render_inline_code_spans
from ihroteka_converter.__main__ import _try_convert_heading
from ihroteka_converter.__main__ import _try_convert_horizontal_rule
from ihroteka_converter.__main__ import _try_convert_list_item
from ihroteka_converter.__main__ import convert


def test_add_line() -> None:
    state = ConverterState()
    state.add_line("line1")
    state.add_line("line2")
    assert state.lines == ["line1", "line2"]


@pytest.mark.parametrize(
    ("list_stack", "expected_lines", "expected_stack"),
    [
        ([], [], []),
        ([("ul", 0)], ["[/list]"], []),
        ([("ol", 0)], ["[/olist]"], []),
        ([("ul", 0), ("ol", 2)], ["[/olist]", "[/list]"], []),
        ([("ul", 0), ("ul", 2), ("ol", 4)], ["[/olist]", "[/list]", "[/list]"], []),
    ],
)
def test_close_lists(
    list_stack: list[tuple[str, int]],
    expected_lines: list[str],
    expected_stack: list[tuple[str, int]],
) -> None:
    state = ConverterState()
    state.list_stack = list_stack.copy()
    state.close_lists()
    assert state.lines == expected_lines
    assert state.list_stack == expected_stack


@pytest.mark.parametrize(
    ("quote_level", "expected_line"),
    [
        (0, ""),
        (1, "[/quote]"),
        (2, "[/quote][/quote]"),
        (3, "[/quote][/quote][/quote]"),
    ],
)
def test_close_quotes(quote_level: int, expected_line: str) -> None:
    state = ConverterState()
    state.current_quote_level = quote_level
    state.close_quotes()
    assert state.build() == expected_line
    assert state.current_quote_level == 0


@pytest.mark.parametrize(
    ("lines", "expected_lines"),
    [
        ([], ""),
        (["line1"], "line1"),
        (["line1", "line2"], "line1\nline2"),
        (["a", "b", "c"], "a\nb\nc"),
    ],
)
def test_build(lines: list[str], expected_lines: str) -> None:
    state = ConverterState()
    state.lines = lines
    assert state.build() == expected_lines


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        ("", ""),
        ("Hello, World!", "Hello, World!"),
        ("# Heading 1", "[h1]Heading 1[/h1]"),
        ("## Heading 2", "[h2]Heading 2[/h2]"),
        ("### Heading 3", "[h3]Heading 3[/h3]"),
        ("#### Heading 4", "[h3]Heading 4[/h3]"),
        ("**bold**", "[b]bold[/b]"),
        ("__bold__", "[b]bold[/b]"),
        ("*italic*", "[i]italic[/i]"),
        ("***bold italic***", "[b][i]bold italic[/i][/b]"),
        ("___bold italic___", "[b][i]bold italic[/i][/b]"),
        ("~~strike~~", "[strike]strike[/strike]"),
        ("`code`", "[code]code[/code]"),
        ("[text](url)", "[url=url]text[/url]"),
        ("![alt](url)", "[img]url[/img]"),
        ("```\ncode\n```", "[code]code[/code]"),
        ("```python\ncode\n```", "[code]code[/code]"),
        ("---", "[hr][/hr]"),
        ("___", "[hr][/hr]"),
        ("***", "[hr][/hr]"),
        ("- item", "[list]\n[*] item\n[/list]"),
        ("* item", "[list]\n[*] item\n[/list]"),
        ("1. item", "[olist]\n[*] item\n[/olist]"),
        ("> quote", "[quote]\nquote\n[/quote]"),
        ("line1\nline2", "line1\nline2"),
        ("line1\n\nline2", "line1\n\nline2"),
    ],
)
def test_convert(markdown: str, expected: str) -> None:
    assert convert(markdown) == expected


@pytest.mark.parametrize(
    ("text", "expected_text"),
    [
        ("no bold", "no bold"),
        ("**bold**", "[b]bold[/b]"),
        ("__bold__", "[b]bold[/b]"),
        ("***bold italic***", "[b][i]bold italic[/i][/b]"),
        ("___bold italic___", "[b][i]bold italic[/i][/b]"),
        ("**bold1** and **bold2**", "[b]bold1[/b] and [b]bold2[/b]"),
        ("text **bold** text", "text [b]bold[/b] text"),
    ],
)
def test_convert_inline_bold(text: str, expected_text: str) -> None:
    assert _convert_inline_bold(text) == expected_text


@pytest.mark.parametrize(
    ("text", "expected_text"),
    [
        ("no italic", "no italic"),
        ("*italic*", "[i]italic[/i]"),
        ("*italic1* and *italic2*", "[i]italic1[/i] and [i]italic2[/i]"),
    ],
)
def test_convert_inline_italic(text: str, expected_text: str) -> None:
    assert _convert_inline_italic(text) == expected_text


@pytest.mark.parametrize(
    ("text", "expected_text"),
    [
        ("no strike", "no strike"),
        ("~~strike~~", "[strike]strike[/strike]"),
        (
            "~~strike1~~ and ~~strike2~~",
            "[strike]strike1[/strike] and [strike]strike2[/strike]",
        ),
    ],
)
def test_convert_inline_strikethrough(text: str, expected_text: str) -> None:
    assert _convert_inline_strikethrough(text) == expected_text


@pytest.mark.parametrize(
    ("text", "expected_text"),
    [
        ("no link", "no link"),
        ("[text](url)", "[url=url]text[/url]"),
        (
            "[link1](url1) and [link2](url2)",
            "[url=url1]link1[/url] and [url=url2]link2[/url]",
        ),
        (
            '[text](url "title")',
            "[url=url]text[/url]",
        ),
    ],
)
def test_convert_inline_links(text: str, expected_text: str) -> None:
    assert _convert_inline_links(text) == expected_text


@pytest.mark.parametrize(
    ("text", "expected_text"),
    [
        ("no image", "no image"),
        ("![alt](url)", "[img]url[/img]"),
        ("![alt1](url1) and ![alt2](url2)", "[img]url1[/img] and [img]url2[/img]"),
        ('![alt](url "title")', "[img]url[/img]"),
    ],
)
def test_convert_inline_images(text: str, expected_text: str) -> None:
    assert _convert_inline_images(text) == expected_text


@pytest.mark.parametrize(
    ("text", "expected_text", "expected_spans"),
    [
        ("no code", "no code", []),
        ("`code`", "@@CODE0@@", ["code"]),
        ("`code1` and `code2`", "@@CODE0@@ and @@CODE1@@", ["code1", "code2"]),
        ("text `code` text", "text @@CODE0@@ text", ["code"]),
    ],
)
def test_convert_inline_code_spans(
    text: str,
    expected_text: str,
    expected_spans: list[str],
) -> None:
    result_text, result_spans = _convert_inline_code_spans(text)
    assert result_text == expected_text
    assert result_spans == expected_spans


@pytest.mark.parametrize(
    ("text", "code_spans", "expected_text"),
    [
        ("no code", [], "no code"),
        ("@@CODE0@@", ["code"], "[code]code[/code]"),
        (
            "@@CODE0@@ and @@CODE1@@",
            ["code1", "code2"],
            "[code]code1[/code] and [code]code2[/code]",
        ),
        ("text @@CODE0@@ text", ["code"], "text [code]code[/code] text"),
    ],
)
def test_render_inline_code_spans(
    text: str,
    code_spans: list[str],
    expected_text: str,
) -> None:
    assert _render_inline_code_spans(text, code_spans) == expected_text


@pytest.mark.parametrize(
    ("text", "expected_text"),
    [
        ("plain text", "plain text"),
        ("**bold**", "[b]bold[/b]"),
        ("*italic*", "[i]italic[/i]"),
        ("`code`", "[code]code[/code]"),
        ("[link](url)", "[url=url]link[/url]"),
        ("![alt](url)", "[img]url[/img]"),
        ("~~strike~~", "[strike]strike[/strike]"),
        ("**bold** *italic* `code`", "[b]bold[/b] [i]italic[/i] [code]code[/code]"),
        ("`**code**`", "[code]**code**[/code]"),
    ],
)
def test_convert_inline_elements(text: str, expected_text: str) -> None:
    assert _convert_inline_elements(text) == expected_text


@pytest.mark.parametrize(
    ("line", "expected", "expected_lines"),
    [
        ("# Heading 1", True, ["[h1]Heading 1[/h1]"]),
        ("## Heading 2", True, ["[h2]Heading 2[/h2]"]),
        ("### Heading 3", True, ["[h3]Heading 3[/h3]"]),
        ("#### Heading 4", True, ["[h3]Heading 4[/h3]"]),
        ("##### Heading 5", True, ["[h3]Heading 5[/h3]"]),
        ("###### Heading 6", True, ["[h3]Heading 6[/h3]"]),
        ("# **Bold Heading**", True, ["[h1][b]Bold Heading[/b][/h1]"]),
        ("not a heading", False, []),
        ("#no space", False, []),
    ],
)
def test_try_convert_heading(
    line: str,
    expected: bool,  # noqa: FBT001
    expected_lines: list[str],
) -> None:
    state = ConverterState()
    result = _try_convert_heading(line, state)
    assert result == expected
    assert state.lines == expected_lines


@pytest.mark.parametrize(
    ("line", "expected", "expected_line"),
    [
        ("---", True, "[hr][/hr]"),
        ("- - -", True, "[hr][/hr]"),
        ("___", True, "[hr][/hr]"),
        ("_ _ _", True, "[hr][/hr]"),
        ("***", True, "[hr][/hr]"),
        ("* * *", True, "[hr][/hr]"),
        ("not a rule", False, ""),
        ("--", False, ""),
        ("- -", False, ""),
    ],
)
def test_try_convert_horizontal_rule(
    line: str,
    expected: bool,  # noqa: FBT001
    expected_line: str,
) -> None:
    state = ConverterState()
    result = _try_convert_horizontal_rule(line, state)
    assert result == expected
    assert state.build() == expected_line


@pytest.mark.parametrize(
    ("line", "expected_content", "expected_depth"),
    [
        ("no quote", "no quote", 0),
        ("> quote", "quote", 1),
        (">> nested quote", "nested quote", 2),
        (">>> deeply nested", "deeply nested", 3),
        (">no space", "no space", 1),
        ("> > quote", "quote", 2),
    ],
)
def test_extract_quotes(line: str, expected_content: str, expected_depth: int) -> None:
    content, depth = _extract_quotes(line)
    assert content == expected_content
    assert depth == expected_depth


@pytest.mark.parametrize(
    ("current_level", "new_level", "expected_lines"),
    [
        (0, 0, []),
        (0, 1, ["[quote]"]),
        (0, 2, ["[quote]", "[quote]"]),
        (1, 0, ["[/quote]"]),
        (2, 0, ["[/quote][/quote]"]),
        (1, 2, ["[quote]"]),
        (2, 1, ["[/quote]"]),
        (1, 1, []),
    ],
)
def test_convert_quote_level(
    current_level: int,
    new_level: int,
    expected_lines: list[str],
) -> None:
    state = ConverterState()
    state.current_quote_level = current_level
    _convert_quote_level(new_level, state)
    assert state.lines == expected_lines
    if new_level == 0:
        assert state.current_quote_level == 0
    else:
        assert state.current_quote_level == new_level


@pytest.mark.parametrize(
    ("line", "expected", "expected_item"),
    [
        ("- item", True, "[*] item"),
        ("* item", True, "[*] item"),
        ("+ item", True, "[*] item"),
        ("1. item", True, "[*] item"),
        ("2. item", True, "[*] item"),
        ("  - nested", True, "[*] nested"),
        ("- **bold** item", True, "[*] [b]bold[/b] item"),
        ("not a list", False, None),
    ],
)
def test_try_convert_list_item(
    line: str,
    expected: bool,  # noqa: FBT001
    expected_item: str | None,
) -> None:
    state = ConverterState()
    result = _try_convert_list_item(line, state)
    assert result == expected
    if expected_item:
        assert expected_item in state.lines


@pytest.mark.parametrize(
    ("list_type", "indent", "existing_stack", "expected_tag"),
    [
        ("ul", 0, [], "[list]"),
        ("ol", 0, [], "[olist]"),
        ("ul", 2, [("ul", 0)], "[list]"),
        ("ol", 2, [("ul", 0)], "[olist]"),
    ],
)
def test_adjust_list_stack_new_list(
    list_type: str,
    indent: int,
    existing_stack: list[tuple[str, int]],
    expected_tag: str,
) -> None:
    state = ConverterState()
    state.list_stack = existing_stack.copy()
    _adjust_list_stack(list_type, indent, state)
    assert expected_tag in state.lines


@pytest.mark.parametrize(
    ("line", "list_stack", "should_close"),
    [
        ("not a list", [("ul", 0)], True),
        ("- item", [("ul", 0)], False),
        ("", [("ul", 0)], True),
        ("> quote", [("ul", 0)], True),
        (">   quote", [("ul", 0)], True),
    ],
)
def test_check_list_continuation(
    line: str,
    list_stack: list[tuple[str, int]],
    should_close: bool,  # noqa: FBT001
) -> None:
    state = ConverterState()
    state.list_stack = list_stack.copy()
    _check_list_continuation(line, state)
    if should_close:
        assert len(state.list_stack) == 0
    else:
        assert len(state.list_stack) > 0


def test_convert_list_dedent() -> None:
    state = ConverterState()
    state.list_stack = [("ul", 0), ("ul", 2), ("ul", 4)]
    _convert_list_dedent("ul", 0, state)
    assert len(state.list_stack) == 1
    assert "[/list]" in state.lines


def test_convert_list_same_level_different_type() -> None:
    state = ConverterState()
    state.list_stack = [("ul", 0)]
    _convert_list_same_level("ol", 0, state)
    assert state.list_stack[-1][0] == "ol"
    assert "[/list]" in state.lines
    assert "[olist]" in state.lines


def test_convert_code_block_content_inside_block() -> None:
    state = ConverterState()
    state.inside_code_block = True
    _convert_code_block_content("code line", state)
    assert state.code_block_accumulator == ["code line"]
    assert state.inside_code_block


def test_convert_code_block_content_closing() -> None:
    state = ConverterState()
    state.inside_code_block = True
    state.code_block_accumulator = ["line1", "line2"]
    _convert_code_block_content("```", state)
    assert not state.inside_code_block
    assert state.code_block_accumulator == []
    assert "[code]line1\nline2[/code]" in state.lines


def test_convert_empty_line() -> None:
    state = ConverterState()
    state.list_stack = [("ul", 0)]
    state.current_quote_level = 1
    _convert_empty_line(state)
    assert len(state.list_stack) == 0
    assert state.current_quote_level == 0
    assert "" in state.lines


def test_close_remaining_blocks_with_code_block() -> None:
    state = ConverterState()
    state.inside_code_block = True
    state.code_block_accumulator = ["code"]
    _close_remaining_blocks(state)
    assert "[code]code[/code]" in state.lines


def test_close_remaining_blocks_with_lists() -> None:
    state = ConverterState()
    state.list_stack = [("ul", 0)]
    _close_remaining_blocks(state)
    assert "[/list]" in state.lines


def test_close_remaining_blocks_with_quotes() -> None:
    state = ConverterState()
    state.current_quote_level = 2
    _close_remaining_blocks(state)
    assert "[/quote][/quote]" in state.lines


@pytest.mark.parametrize(
    ("line", "expected_pattern"),
    [
        ("# Heading", "[h1]Heading[/h1]"),
        ("- item", "[list]"),
        ("> quote", "[quote]"),
        ("plain text", "plain text"),
        ("---", "[hr][/hr]"),
        ("```", None),
    ],
)
def test_process_line(line: str, expected_pattern: str | None) -> None:
    state = ConverterState()
    _process_line(line, state)
    if expected_pattern:
        assert any(expected_pattern in output_line for output_line in state.lines)


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        (
            "- item1\n  - nested1\n  - nested2\n- item2",
            "[list]\n[*] item1\n[list]\n[*] nested1\n[*] nested2\n[/list]\n[*] item2\n[/list]",
        ),
        ("- item1\n1. item2", "[list]\n[*] item1\n[/list]\n[olist]\n[*] item2\n[/olist]"),
        (
            "> level1\n>> level2\n> level1 again",
            "[quote]\nlevel1\n[quote]\nlevel2\n[/quote]\nlevel1 again\n[/quote]",
        ),
        ("```\nline1\nline2\nline3\n```", "[code]line1\nline2\nline3[/code]"),
        ("para1\n\npara2\n\npara3", "para1\n\npara2\n\npara3"),
        ("- **bold** and *italic*", "[list]\n[*] [b]bold[/b] and [i]italic[/i]\n[/list]"),
        ("# **Bold** Heading", "[h1][b]Bold[/b] Heading[/h1]"),
        ("[**bold link**](url)", "[url=url][b]bold link[/b][/url]"),
    ],
)
def test_complex_scenarios(markdown: str, expected: str) -> None:
    assert convert(markdown) == expected


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        ("", ""),
        ("\n\n\n", "\n\n"),
        ("# `code` in heading", "[h1][code]code[/code] in heading[/h1]"),
        ("`code1` and `code2`", "[code]code1[/code] and [code]code2[/code]"),
        ("***nested***", "[b][i]nested[/i][/b]"),
        ("**unclosed", "[i][/i]unclosed"),
        ("---\n\n---", "[hr][/hr]\n\n[hr][/hr]"),
    ],
)
def test_edge_cases(markdown: str, expected: str) -> None:
    result = convert(markdown)
    assert result == expected
