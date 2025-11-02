"""A lightweight package for converting Markdown into Steam-compatible markup."""

from __future__ import annotations

import re

from dataclasses import dataclass
from dataclasses import field


_PATTERN_CODE_SPAN = re.compile(r"`([^`]+?)`")
_PATTERN_IMAGE = re.compile(r'!\[.*?\]\(([^)\s"]+)(?:\s+"[^"]*")?\)')
_PATTERN_LINK = re.compile(r'\[([^]]+)\]\(([^)\s"]+)(?:\s+"[^"]*")?\)')
_PATTERN_BOLD_ITALIC_STAR = re.compile(r"\*\*\*(.*?)\*\*\*")
_PATTERN_BOLD_ITALIC_UNDER = re.compile(r"___(.*?)___")
_PATTERN_BOLD_STAR = re.compile(r"\*\*(.*?)\*\*")
_PATTERN_BOLD_UNDER = re.compile(r"__(.*?)__")
_PATTERN_ITALIC = re.compile(r"\*(.*?)\*")
_PATTERN_STRIKETHROUGH = re.compile(r"~~(.*?)~~")

_PATTERN_HEADING = re.compile(r"^(#{1,6})\s+(.*)")
_PATTERN_HR_DASH = re.compile(r"^(-\s?){3,}$")
_PATTERN_HR_UNDERSCORE = re.compile(r"^(_\s?){3,}$")
_PATTERN_HR_STAR = re.compile(r"^(\*\s?){3,}$")
_PATTERN_LIST_ITEM = re.compile(r"^(\s*)([-+*]|\d+\.)\s+(.*)")
_PATTERN_LIST_MARKER = re.compile(r"^\s*([-+*]|\d+\.)\s+")


@dataclass
class ConverterState:  # noqa: D101
    lines: list[str] = field(default_factory=list)
    list_stack: list[tuple[str, int]] = field(default_factory=list)
    current_quote_level: int = 0
    inside_code_block: bool = False
    code_block_accumulator: list[str] = field(default_factory=list)

    def add_line(self, line: str) -> None:
        self.lines.append(line)

    def close_lists(self) -> None:
        while self.list_stack:
            list_type, _ = self.list_stack.pop()
            match list_type:
                case "ol":
                    tag = "olist"
                case _:
                    tag = "list"
            self.add_line(f"[/{tag}]")

    def close_quotes(self) -> None:
        if self.current_quote_level > 0:
            self.add_line("[/quote]" * self.current_quote_level)
            self.current_quote_level = 0

    def build(self) -> str:
        return "\n".join(self.lines)


def convert(markdown_text: str) -> str:
    """Convert Markdown text to Steam-compatible markup."""
    state = ConverterState()
    lines = markdown_text.splitlines()

    for md_line in lines:
        _process_line(md_line, state)

    _close_remaining_blocks(state)

    return state.build()


def _close_remaining_blocks(state: ConverterState) -> None:
    if state.inside_code_block:
        code_content = "\n".join(state.code_block_accumulator)
        state.add_line(f"[code]{code_content}[/code]")

    state.close_lists()
    state.close_quotes()


def _process_line(md_line: str, state: ConverterState) -> None:
    # Handle code blocks first (they have highest priority)
    if state.inside_code_block:
        _convert_code_block_content(md_line, state)
        return

    if md_line.strip().startswith("```"):
        state.inside_code_block = True
        state.code_block_accumulator.clear()
        return

    # Handle empty lines
    if md_line.strip() == "":
        _convert_empty_line(state)
        return

    # Check if we need to close lists (non-list line detected)
    _check_list_continuation(md_line, state)

    # Extract and handle quote markers
    line_content, quote_depth = _extract_quotes(md_line)
    _convert_quote_level(quote_depth, state)

    # Try to handle as special block elements
    if _try_convert_heading(line_content, state):
        return
    if _try_convert_horizontal_rule(line_content, state):
        return
    if _try_convert_list_item(line_content, state):
        return

    # Default: convert as regular paragraph with inline elements
    state.add_line(_convert_inline_elements(line_content))


def _convert_code_block_content(md_line: str, state: ConverterState) -> None:
    if md_line.strip().startswith("```"):
        state.inside_code_block = False
        code_content = "\n".join(state.code_block_accumulator)
        state.add_line(f"[code]{code_content}[/code]")
        state.code_block_accumulator.clear()

    else:
        state.code_block_accumulator.append(md_line)


def _convert_empty_line(state: ConverterState) -> None:
    state.close_lists()
    state.close_quotes()
    state.add_line("")


def _adjust_list_stack(list_type: str, indent_spaces: int, state: ConverterState) -> None:
    if not state.list_stack:
        state.list_stack.append((list_type, indent_spaces))
        match list_type:
            case "ol":
                tag = "olist"
            case _:
                tag = "list"
        state.add_line(f"[{tag}]")
        return

    current_indent = state.list_stack[-1][1]

    if indent_spaces > current_indent:
        # Nested list
        state.list_stack.append((list_type, indent_spaces))
        match list_type:
            case "ol":
                tag = "olist"
            case _:
                tag = "list"
        state.add_line(f"[{tag}]")

    elif indent_spaces < current_indent:
        # Dedent
        _convert_list_dedent(list_type, indent_spaces, state)

    else:
        # Same level, possibly different type
        _convert_list_same_level(list_type, indent_spaces, state)


def _check_list_continuation(md_line: str, state: ConverterState) -> None:
    if not state.list_stack:
        return

    if not _PATTERN_LIST_MARKER.match(md_line):
        leading_spaces = len(md_line) - len(md_line.lstrip(" "))
        first_char = md_line.lstrip(" ")[:1]
        is_quote_and_indented = first_char == ">" and leading_spaces > state.list_stack[-1][1]
        if not is_quote_and_indented:
            state.close_lists()


def _convert_list_dedent(list_type: str, indent_spaces: int, state: ConverterState) -> None:
    while state.list_stack and indent_spaces < state.list_stack[-1][1]:
        prev_type, _ = state.list_stack.pop()
        match prev_type:
            case "ol":
                tag = "olist"
            case _:
                tag = "list"
        state.add_line(f"[/{tag}]")

    if state.list_stack and state.list_stack[-1][1] == indent_spaces:
        if state.list_stack[-1][0] != list_type:
            # Same indent, different type: close and reopen
            prev_type, _ = state.list_stack.pop()
            match prev_type:
                case "ol":
                    old_tag = "olist"
                case _:
                    old_tag = "list"
            match list_type:
                case "ol":
                    new_tag = "olist"
                case _:
                    new_tag = "list"
            state.add_line(f"[/{old_tag}]")
            state.list_stack.append((list_type, indent_spaces))
            state.add_line(f"[{new_tag}]")

    else:
        # New list at this indent level
        state.list_stack.append((list_type, indent_spaces))
        match list_type:
            case "ol":
                tag = "olist"
            case _:
                tag = "list"
        state.add_line(f"[{tag}]")


def _convert_list_same_level(list_type: str, indent_spaces: int, state: ConverterState) -> None:
    if state.list_stack[-1][0] != list_type:
        # Different list type at same level
        prev_type, _ = state.list_stack.pop()
        match prev_type:
            case "ol":
                old_tag = "olist"
            case _:
                old_tag = "list"
        match list_type:
            case "ol":
                new_tag = "olist"
            case _:
                new_tag = "list"
        state.add_line(f"[/{old_tag}]")
        state.list_stack.append((list_type, indent_spaces))
        state.add_line(f"[{new_tag}]")


def _try_convert_list_item(line_content: str, state: ConverterState) -> bool:
    match = _PATTERN_LIST_ITEM.match(line_content)
    if not match:
        return False

    indent_str = match.group(1)
    marker = match.group(2)
    item_text = match.group(3)
    indent_spaces = len(indent_str.expandtabs(4))
    list_type = "ol" if marker.rstrip(".").isdigit() else "ul"

    _adjust_list_stack(list_type, indent_spaces, state)

    converted_item = _convert_inline_elements(item_text)
    state.add_line(f"[*] {converted_item}")

    return True


def _convert_quote_level(quote_depth: int, state: ConverterState) -> None:
    match quote_depth:
        case 0:
            state.close_quotes()
        case _:
            if quote_depth > state.current_quote_level:
                for _ in range(state.current_quote_level, quote_depth):
                    state.add_line("[quote]")
            elif quote_depth < state.current_quote_level:
                for _ in range(quote_depth, state.current_quote_level):
                    state.add_line("[/quote]")
            state.current_quote_level = quote_depth


def _extract_quotes(md_line: str) -> tuple[str, int]:
    stripped_line = md_line
    quote_depth = 0

    while stripped_line.startswith(">"):
        quote_depth += 1
        stripped_line = stripped_line.removeprefix(">").removeprefix(" ")

    return stripped_line, quote_depth


def _try_convert_heading(line_content: str, state: ConverterState) -> bool:
    match = _PATTERN_HEADING.match(line_content)
    if not match:
        return False

    level = min(len(match.group(1)), 3)  # Steam supports h1-h3
    heading_text = match.group(2)
    converted_heading = _convert_inline_elements(heading_text)
    state.add_line(f"[h{level}]{converted_heading}[/h{level}]")

    return True


def _try_convert_horizontal_rule(line_content: str, state: ConverterState) -> bool:
    if (
        _PATTERN_HR_DASH.match(line_content)
        or _PATTERN_HR_UNDERSCORE.match(line_content)
        or _PATTERN_HR_STAR.match(line_content)
    ):
        state.add_line("[hr][/hr]")
        return True

    return False


def _convert_inline_bold(text: str) -> str:
    """Convert inline bold: **text** -> [b]text[/b]."""
    text = _PATTERN_BOLD_ITALIC_STAR.sub(r"[b][i]\1[/i][/b]", text)
    text = _PATTERN_BOLD_ITALIC_UNDER.sub(r"[b][i]\1[/i][/b]", text)
    text = _PATTERN_BOLD_STAR.sub(r"[b]\1[/b]", text)
    return _PATTERN_BOLD_UNDER.sub(r"[b]\1[/b]", text)


def _convert_inline_elements(text: str) -> str:
    text, code_spans = _convert_inline_code_spans(text)
    text = _convert_inline_images(text)
    text = _convert_inline_links(text)
    text = _convert_inline_bold(text)
    text = _convert_inline_italic(text)
    text = _convert_inline_strikethrough(text)
    text = _render_inline_code_spans(text, code_spans)
    return text.strip()


def _convert_inline_code_spans(text: str) -> tuple[str, list[str]]:
    """Convert inline code spans: ``code`` -> @@CODE{index}@@."""
    code_spans: list[str] = []

    def code_span_repl(match: re.Match) -> str:  # type: ignore[type-arg]
        code_content = match.group(1)
        code_spans.append(code_content)
        return f"@@CODE{len(code_spans) - 1}@@"

    text = _PATTERN_CODE_SPAN.sub(code_span_repl, text)
    return text, code_spans


def _convert_inline_images(text: str) -> str:
    """Convert inline images: ![alt](URL) -> [img]URL[/img]."""
    return _PATTERN_IMAGE.sub(r"[img]\1[/img]", text)


def _convert_inline_italic(text: str) -> str:
    """Convert inline italic: *text* -> [i]text[/i]."""
    return _PATTERN_ITALIC.sub(r"[i]\1[/i]", text)


def _convert_inline_links(text: str) -> str:
    """Convert inline links: [text](URL) -> [url=URL]text[/url]."""

    def link_repl(match: re.Match) -> str:  # type: ignore[type-arg]
        link_text = match.group(1)
        url = match.group(2)
        return f"[url={url}]{link_text}[/url]"

    return _PATTERN_LINK.sub(link_repl, text)


def _convert_inline_strikethrough(text: str) -> str:
    """Convert inline strikethrough: ~~text~~ -> [strike]text[/strike]."""
    return _PATTERN_STRIKETHROUGH.sub(r"[strike]\1[/strike]", text)


def _render_inline_code_spans(text: str, code_spans: list[str]) -> str:
    """Render inline code spans: @@CODE{index}@@ -> [code]code[/code]."""

    def render_repl(match: re.Match) -> str:  # type: ignore[type-arg]
        idx = int(match.group(1))
        return f"[code]{code_spans[idx]}[/code]"

    return re.sub(r"@@CODE(\d+)@@", render_repl, text)
