"""Module that contains tests for the markdown module."""

from __future__ import annotations

import pytest

from steamify.markdown import MarkdownState
from steamify.markdown import _close_remaining_blocks
from steamify.markdown import _convert_code_block_content
from steamify.markdown import _convert_inline_bold
from steamify.markdown import _convert_inline_code_spans
from steamify.markdown import _convert_inline_elements
from steamify.markdown import _convert_inline_images
from steamify.markdown import _convert_inline_italic
from steamify.markdown import _convert_inline_links
from steamify.markdown import _convert_inline_strikethrough
from steamify.markdown import _flush_code_block
from steamify.markdown import _process_line
from steamify.markdown import _render_inline_code_spans
from steamify.markdown import _try_convert_code_block_open
from steamify.markdown import _try_convert_heading
from steamify.markdown import _try_convert_horizontal_rule
from steamify.markdown import _try_convert_list_close
from steamify.markdown import _try_convert_list_item
from steamify.markdown import _try_convert_list_open
from steamify.markdown import _try_convert_quote_level
from steamify.markdown import to_markdown
from steamify.steam import to_steam


def test_add_line() -> None:
    state = MarkdownState()
    state.add_line("line1")
    state.add_line("line2")
    assert state.lines == ["line1", "line2"]


def test_build() -> None:
    state = MarkdownState()
    state.add_line("line1")
    state.add_line("line2")
    assert state.build() == "line1\nline2"


@pytest.mark.parametrize(
    ("quote_level", "expected"),
    [
        (0, "text"),
        (1, "> text"),
        (2, "> > text"),
    ],
)
def test_prefix(quote_level: int, expected: str) -> None:
    state = MarkdownState(current_quote_level=quote_level)
    assert state.prefix("text") == expected


@pytest.mark.parametrize(
    ("steam", "expected"),
    [
        ("[h1]Heading 1[/h1]", "# Heading 1"),
        ("[h2]Heading 2[/h2]", "## Heading 2"),
        ("[h3]Heading 3[/h3]", "### Heading 3"),
        ("[b]bold[/b]", "**bold**"),
        ("[i]italic[/i]", "*italic*"),
        ("[b][i]bold italic[/i][/b]", "***bold italic***"),
        ("[strike]strike[/strike]", "~~strike~~"),
        ("[code]code[/code]", "`code`"),
        ("[url=url]text[/url]", "[text](url)"),
        ("[img]url[/img]", "![](url)"),
        ("[hr][/hr]", "---"),
        ("[list]\n[*] item\n[/list]", "- item"),
        ("[olist]\n[*] item\n[/olist]", "1. item"),
        ("[quote]\nquote\n[/quote]", "> quote"),
        ("line1\nline2", "line1\nline2"),
        ("line1\n\nline2", "line1\n\nline2"),
    ],
)
def test_to_markdown(steam: str, expected: str) -> None:
    assert to_markdown(steam) == expected


@pytest.mark.parametrize(
    ("steam", "expected"),
    [
        ("[olist]\n[*] one\n[*] two\n[*] three\n[/olist]", "1. one\n2. two\n3. three"),
        ("[list]\n[*] one\n[*] two\n[/list]", "- one\n- two"),
        (
            "[list]\n[*] outer\n[list]\n[*] inner\n[/list]\n[/list]",
            "- outer\n  - inner",
        ),
        (
            "[list]\n[*] outer\n[olist]\n[*] inner\n[/olist]\n[/list]",
            "- outer\n  1. inner",
        ),
        (
            "[quote]\nlevel1\n[quote]\nlevel2\n[/quote]\nlevel1 again\n[/quote]",
            "> level1\n> > level2\n> level1 again",
        ),
        ("[code]line1\nline2\nline3[/code]", "```\nline1\nline2\nline3\n```"),
        ("[h1][b]Bold[/b] Heading[/h1]", "# **Bold** Heading"),
        ("[url=url][b]bold link[/b][/url]", "[**bold link**](url)"),
        ("[list]\n[*] [b]bold[/b] and [i]italic[/i]\n[/list]", "- **bold** and *italic*"),
        ("[h1][code]code[/code] in heading[/h1]", "# `code` in heading"),
        ("[code]code1[/code] and [code]code2[/code]", "`code1` and `code2`"),
    ],
)
def test_complex_scenarios(steam: str, expected: str) -> None:
    assert to_markdown(steam) == expected


@pytest.mark.parametrize(
    "steam",
    [
        "[spoiler]hidden[/spoiler]",
        "[noparse]**literal**[/noparse]",
        "[u]underline[/u]",
        "[table][tr][th]head[/th][/tr][/table]",
        "[previewyoutube=id][/previewyoutube]",
    ],
)
def test_unmappable_tags_pass_through(steam: str) -> None:
    """Steam-only tags have no Markdown equivalent, so they survive verbatim."""
    assert to_markdown(steam) == steam


@pytest.mark.parametrize(
    ("steam", "expected"),
    [
        ("", ""),
        ("\n\n\n", "\n\n"),
        ("[code]unterminated", "```\nunterminated\n```"),
        ("text [code]unterminated", "text\n```\nunterminated\n```"),
        ("[code]line1\nline2[/code] trailing", "```\nline1\nline2\n```\ntrailing"),
        ("[*] orphan item", "- orphan item"),
        ("[/list]", ""),
        ("[/quote]", ""),
        ("[h4]Heading 4[/h4]", "#### Heading 4"),
        ("[url=]empty[/url]", "[empty]()"),
    ],
)
def test_edge_cases(steam: str, expected: str) -> None:
    assert to_markdown(steam) == expected


@pytest.mark.parametrize(
    "markdown",
    [
        "# Heading",
        "**bold** and *italic* and ~~strike~~",
        "- one\n- two",
        "1. one\n2. two",
        "- outer\n  - inner",
        "> quote",
        "> level1\n>> level2",
        "```\nline1\nline2\n```",
        "[text](url)",
        "---",
        "[spoiler]hidden[/spoiler]",
        "# Guide\n\nSome **text**\n\n- item\n\n> quote",
    ],
)
def test_round_trip_is_stable(markdown: str) -> None:
    """A Markdown -> Steam -> Markdown -> Steam cycle converges after the first pass."""
    steam = to_steam(markdown)
    assert to_steam(to_markdown(steam)) == steam


def test_close_remaining_blocks_flushes_unterminated_code() -> None:
    state = MarkdownState(inside_code_block=True, code_block_accumulator=["code"])
    _close_remaining_blocks(state)
    assert state.lines == ["```", "code", "```"]
    assert not state.inside_code_block


def test_close_remaining_blocks_resets_state() -> None:
    state = MarkdownState(list_stack=[("list", 1)], current_quote_level=2)
    _close_remaining_blocks(state)
    assert state.list_stack == []
    assert state.current_quote_level == 0


def test_flush_code_block_clears_accumulator() -> None:
    state = MarkdownState(code_block_accumulator=["a", "b"])
    _flush_code_block(state)
    assert state.lines == ["```", "a", "b", "```"]
    assert state.code_block_accumulator == []


@pytest.mark.parametrize(
    ("line", "expected_result", "expected_inside"),
    [
        ("[code]open", True, True),
        ("[code]closed[/code]", False, False),
        ("plain text", False, False),
    ],
)
def test_try_convert_code_block_open(
    line: str,
    expected_result: bool,  # noqa: FBT001
    expected_inside: bool,  # noqa: FBT001
) -> None:
    state = MarkdownState()
    assert _try_convert_code_block_open(line, state) is expected_result
    assert state.inside_code_block is expected_inside


def test_convert_code_block_content_accumulates() -> None:
    state = MarkdownState(inside_code_block=True)
    _convert_code_block_content("code line", state)
    assert state.code_block_accumulator == ["code line"]
    assert state.inside_code_block


@pytest.mark.parametrize(
    ("line", "expected_level"),
    [
        ("[quote]", 1),
        ("[quote][quote]", 2),
        ("[/quote]", 0),
        ("[/quote][/quote]", 0),
    ],
)
def test_try_convert_quote_level(line: str, expected_level: int) -> None:
    state = MarkdownState()
    assert _try_convert_quote_level(line, state) is True
    assert state.current_quote_level == expected_level


def test_try_convert_quote_level_ignores_other_lines() -> None:
    state = MarkdownState()
    assert _try_convert_quote_level("[quote]text", state) is False
    assert state.current_quote_level == 0


@pytest.mark.parametrize(
    ("line", "expected_stack"),
    [
        ("[list]", [("list", 0)]),
        ("[olist]", [("olist", 0)]),
    ],
)
def test_try_convert_list_open(line: str, expected_stack: list[tuple[str, int]]) -> None:
    state = MarkdownState()
    assert _try_convert_list_open(line, state) is True
    assert state.list_stack == expected_stack


def test_try_convert_list_open_ignores_other_lines() -> None:
    state = MarkdownState()
    assert _try_convert_list_open("[*] item", state) is False


def test_try_convert_list_close_on_empty_stack() -> None:
    state = MarkdownState()
    assert _try_convert_list_close("[/list]", state) is True
    assert state.list_stack == []


def test_try_convert_list_close_ignores_other_lines() -> None:
    state = MarkdownState()
    assert _try_convert_list_close("[*] item", state) is False


def test_try_convert_list_item_increments_counter() -> None:
    state = MarkdownState(list_stack=[("olist", 0)])
    _try_convert_list_item("[*] one", state)
    _try_convert_list_item("[*] two", state)
    assert state.lines == ["1. one", "2. two"]
    assert state.list_stack == [("olist", 2)]


def test_try_convert_list_item_ignores_other_lines() -> None:
    state = MarkdownState()
    assert _try_convert_list_item("plain text", state) is False


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("[h1]text[/h1]", "# text"),
        ("[h6]text[/h6]", "###### text"),
    ],
)
def test_try_convert_heading(line: str, expected: str) -> None:
    state = MarkdownState()
    assert _try_convert_heading(line, state) is True
    assert state.lines == [expected]


@pytest.mark.parametrize(
    "line",
    [
        "[h1]mismatched[/h2]",
        "plain text",
    ],
)
def test_try_convert_heading_ignores_other_lines(line: str) -> None:
    state = MarkdownState()
    assert _try_convert_heading(line, state) is False


def test_try_convert_horizontal_rule() -> None:
    state = MarkdownState()
    assert _try_convert_horizontal_rule("[hr][/hr]", state) is True
    assert state.lines == ["---"]


def test_try_convert_horizontal_rule_ignores_other_lines() -> None:
    state = MarkdownState()
    assert _try_convert_horizontal_rule("[hr]", state) is False


def test_process_line_routes_code_block_content() -> None:
    state = MarkdownState(inside_code_block=True)
    _process_line("code", state)
    assert state.code_block_accumulator == ["code"]


def test_process_line_keeps_blank_lines() -> None:
    state = MarkdownState()
    _process_line("   ", state)
    assert state.lines == [""]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("[b]bold[/b]", "**bold**"),
        ("[b][i]both[/i][/b]", "***both***"),
        ("plain", "plain"),
    ],
)
def test_convert_inline_bold(text: str, expected: str) -> None:
    assert _convert_inline_bold(text) == expected


def test_convert_inline_italic() -> None:
    assert _convert_inline_italic("[i]italic[/i]") == "*italic*"


def test_convert_inline_strikethrough() -> None:
    assert _convert_inline_strikethrough("[strike]gone[/strike]") == "~~gone~~"


def test_convert_inline_images() -> None:
    assert _convert_inline_images("[img]url[/img]") == "![](url)"


def test_convert_inline_links() -> None:
    assert _convert_inline_links("[url=https://a.b]text[/url]") == "[text](https://a.b)"


def test_convert_inline_code_spans() -> None:
    text, code_spans = _convert_inline_code_spans("a [code]x[/code] b")
    assert text == "a @@CODE0@@ b"
    assert code_spans == ["x"]


def test_render_inline_code_spans() -> None:
    assert _render_inline_code_spans("a @@CODE0@@ b", ["x"]) == "a `x` b"


def test_convert_inline_elements_protects_code_content() -> None:
    """Markup inside a code span must not be converted."""
    assert _convert_inline_elements("[code][b]not bold[/b][/code]") == "`[b]not bold[/b]`"
