"""Module that contains the Markdown-to-Steam-markup conversion pipeline."""

from __future__ import annotations

import re

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Sequence


_PATTERN_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_PATTERN_LINKED_IMAGE = re.compile(
    r'\[!\[([^\]]*)\]\(\s*(?:<([^>\n]+)>|([^\s)]+))(?:\s+"[^"]*")?\s*\)\]'
    r'\(\s*(?:<([^>\n]+)>|([^\s)]+))(?:\s+"[^"]*")?\s*\)'
)
_PATTERN_REFERENCE_IMAGE = re.compile(r"!\[([^\]]*)\]\[([^\]]*)\]")
_PATTERN_IMAGE = re.compile(
    r"!\[([^\]]*)\]\(\s*(?:<([^>\n]+)>|((?:[^\s()]|\([^\s()]*\))+))"
    r'(?:\s+"[^"]*")?\s*\)'
)
_PATTERN_AUTOLINK = re.compile(r"<((?:https?://|mailto:)[^>\s]+|[^>\s@]+@[^>\s@]+\.[^>\s@]+)>")
_PATTERN_LINK = re.compile(
    r"\[([^\]]+)\]\(\s*(?:<([^>\n]+)>|((?:[^\s()]|\([^\s()]*\))+))"
    r'(?:\s+"[^"]*")?\s*\)'
)
_PATTERN_REFERENCE_LINK = re.compile(r"\[([^\]]+)\]\[([^\]]*)\]")
_PATTERN_BOLD_ITALIC_STAR = re.compile(r"\*\*\*(.*?)\*\*\*")
_PATTERN_BOLD_ITALIC_UNDER = re.compile(r"___(.*?)___")
_PATTERN_BOLD_STAR = re.compile(r"\*\*(.*?)\*\*")
_PATTERN_BOLD_UNDER = re.compile(r"__(.*?)__")
_PATTERN_ITALIC = re.compile(r"\*(.*?)\*")
_PATTERN_ITALIC_UNDER = re.compile(r"(?<!\w)_(?!_)(.+?)(?<!_)_(?!\w)")
_PATTERN_STRIKETHROUGH = re.compile(r"~~(.*?)~~")
_PATTERN_UNDERLINE_HTML = re.compile(r"<u>(.*?)</u>", re.IGNORECASE)
_PATTERN_SPOILER = re.compile(r"\|\|(.*?)\|\|")

_PATTERN_HEADING = re.compile(r"^(#{1,6})\s+(.*)")
_PATTERN_HEADING_CLOSING = re.compile(r"\s+#+\s*$")
_PATTERN_HR_DASH = re.compile(r"^(-\s?){3,}$")
_PATTERN_HR_UNDERSCORE = re.compile(r"^(_\s?){3,}$")
_PATTERN_HR_STAR = re.compile(r"^(\*\s?){3,}$")
_PATTERN_LIST_ITEM = re.compile(r"^(\s*)([-+*]|\d+\.)\s+(.*)")
_PATTERN_LIST_MARKER = re.compile(r"^\s*([-+*]|\d+\.)\s+")
_PATTERN_TASK_ITEM = re.compile(r"^\[([ xX])\](?:\s+(.*))?$")
_PATTERN_TABLE_SEPARATOR_CELL = re.compile(r":?-+:?")
_PATTERN_REFERENCE_DEFINITION = re.compile(
    r'^\s{0,3}\[([^\]^][^\]]*)\]:\s*(?:<([^>\s]+)>|(\S+))(?:\s+"[^"]*")?\s*$'
)
_PATTERN_SETEXT_H1 = re.compile(r"^=+\s*$")
_PATTERN_SETEXT_H2 = re.compile(r"^-+\s*$")


@dataclass
class SteamState:
    lines: list[str] = field(default_factory=list)
    list_stack: list[tuple[str, int]] = field(default_factory=list)
    current_quote_level: int = 0
    inside_code_block: bool = False
    code_block_accumulator: list[str] = field(default_factory=list)
    code_fence_char: str = ""
    code_fence_length: int = 0
    references: dict[str, str] = field(default_factory=dict)

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


def to_steam(markdown_text: str) -> str:
    """Convert Markdown text to Steam-compatible markup."""
    references, lines = _extract_reference_definitions(markdown_text.splitlines())
    state = SteamState(references=references)

    index = 0
    while index < len(lines):
        next_index = _convert_table_block(lines, index, state)
        if next_index is not None:
            index = next_index
            continue

        if _try_convert_setext_heading(lines, index, state):
            index += 2
            continue

        _process_line(lines[index], state)
        index += 1

    _close_remaining_blocks(state)

    return state.build()


def _close_remaining_blocks(state: SteamState) -> None:
    if state.inside_code_block:
        code_content = "\n".join(state.code_block_accumulator)
        state.add_line(f"[code]{code_content}[/code]")
        state.inside_code_block = False
        state.code_fence_char = ""
        state.code_fence_length = 0

    state.close_lists()
    state.close_quotes()


def _process_line(md_line: str, state: SteamState) -> None:
    if state.inside_code_block:
        _convert_code_block_content(md_line, state)
        return

    fence_match = _PATTERN_FENCE.match(md_line.lstrip("\u200b\ufeff"))
    if fence_match:
        fence = fence_match.group(1)
        state.inside_code_block = True
        state.code_block_accumulator.clear()
        state.code_fence_char = fence[0]
        state.code_fence_length = len(fence)
        return

    if md_line.strip() == "":
        _convert_empty_line(state)
        return

    _check_list_continuation(md_line, state)

    line_content, quote_depth = _extract_quotes(md_line)
    _convert_quote_level(quote_depth, state)

    if _try_convert_heading(line_content, state):
        return
    if _try_convert_horizontal_rule(line_content, state):
        return
    if _try_convert_list_item(line_content, state):
        return

    state.add_line(_convert_inline_elements(line_content, state.references))


def _convert_code_block_content(md_line: str, state: SteamState) -> None:
    if _is_fence_close(md_line, state.code_fence_char, state.code_fence_length):
        state.inside_code_block = False
        code_content = "\n".join(state.code_block_accumulator)
        state.add_line(f"[code]{code_content}[/code]")
        state.code_block_accumulator.clear()
        state.code_fence_char = ""
        state.code_fence_length = 0

    else:
        state.code_block_accumulator.append(md_line)


def _is_fence_close(line: str, fence_char: str, fence_length: int) -> bool:
    stripped = line.strip().strip("\u200b\ufeff")
    if not stripped or len(stripped) < fence_length:
        return False
    return all(char == fence_char for char in stripped)


def _convert_empty_line(state: SteamState) -> None:
    state.close_lists()
    state.close_quotes()
    state.add_line("")


def _adjust_list_stack(list_type: str, indent_spaces: int, state: SteamState) -> None:
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
        state.list_stack.append((list_type, indent_spaces))
        match list_type:
            case "ol":
                tag = "olist"
            case _:
                tag = "list"
        state.add_line(f"[{tag}]")

    elif indent_spaces < current_indent:
        _convert_list_dedent(list_type, indent_spaces, state)

    else:
        _convert_list_same_level(list_type, indent_spaces, state)


def _check_list_continuation(md_line: str, state: SteamState) -> None:
    if not state.list_stack:
        return

    if not _PATTERN_LIST_MARKER.match(md_line):
        leading_spaces = len(md_line) - len(md_line.lstrip(" "))
        first_char = md_line.lstrip(" ")[:1]
        is_quote_and_indented = first_char == ">" and leading_spaces > state.list_stack[-1][1]
        if not is_quote_and_indented:
            state.close_lists()


def _convert_list_dedent(list_type: str, indent_spaces: int, state: SteamState) -> None:
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
        state.list_stack.append((list_type, indent_spaces))
        match list_type:
            case "ol":
                tag = "olist"
            case _:
                tag = "list"
        state.add_line(f"[{tag}]")


def _convert_list_same_level(list_type: str, indent_spaces: int, state: SteamState) -> None:
    if state.list_stack[-1][0] != list_type:
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


def _try_convert_list_item(line_content: str, state: SteamState) -> bool:
    match = _PATTERN_LIST_ITEM.match(line_content)
    if not match:
        return False

    indent_str = match.group(1)
    marker = match.group(2)
    item_text = match.group(3)
    indent_spaces = len(indent_str.expandtabs(4))
    list_type = "ol" if marker.rstrip(".").isdigit() else "ul"

    _adjust_list_stack(list_type, indent_spaces, state)

    item_text = _convert_task_checkbox(item_text)
    converted_item = _convert_inline_elements(item_text, state.references)
    state.add_line(f"[*] {converted_item}")

    return True


def _convert_task_checkbox(item_text: str) -> str:
    """Render GFM task-list markers as Unicode checkboxes, which Steam displays."""
    match = _PATTERN_TASK_ITEM.match(item_text)
    if not match:
        return item_text

    checkbox = "☑" if match.group(1).lower() == "x" else "☐"
    remainder = match.group(2) or ""
    return f"{checkbox} {remainder}".rstrip()


def _convert_quote_level(quote_depth: int, state: SteamState) -> None:
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


def _try_convert_heading(line_content: str, state: SteamState) -> bool:
    match = _PATTERN_HEADING.match(line_content)
    if not match:
        return False

    level = min(len(match.group(1)), 3)  # Steam supports h1-h3
    heading_text = _PATTERN_HEADING_CLOSING.sub("", match.group(2))
    converted_heading = _convert_inline_elements(heading_text, state.references)
    state.add_line(f"[h{level}]{converted_heading}[/h{level}]")

    return True


def _try_convert_horizontal_rule(line_content: str, state: SteamState) -> bool:
    if (
        _PATTERN_HR_DASH.match(line_content)
        or _PATTERN_HR_UNDERSCORE.match(line_content)
        or _PATTERN_HR_STAR.match(line_content)
    ):
        state.add_line("[hr][/hr]")
        return True

    return False


def _try_convert_setext_heading(lines: Sequence[str], index: int, state: SteamState) -> bool:
    if state.inside_code_block or index + 1 >= len(lines):
        return False

    line_content, quote_depth = _extract_quotes(lines[index])
    line_content = line_content.strip()
    if quote_depth != 0 or not line_content or _looks_like_block_start(line_content):
        return False

    underline = lines[index + 1].strip()
    if _PATTERN_SETEXT_H1.fullmatch(underline):
        level = 1
    elif _PATTERN_SETEXT_H2.fullmatch(underline):
        level = 2
    else:
        return False

    converted = _convert_inline_elements(line_content, state.references)
    state.close_lists()
    state.close_quotes()
    state.add_line(f"[h{level}]{converted}[/h{level}]")

    return True


def _looks_like_block_start(line_content: str) -> bool:
    return bool(
        _PATTERN_HEADING.match(line_content)
        or _PATTERN_FENCE.match(line_content)
        or _PATTERN_LIST_ITEM.match(line_content)
        or _PATTERN_HR_DASH.match(line_content)
        or _PATTERN_HR_UNDERSCORE.match(line_content)
        or _PATTERN_HR_STAR.match(line_content)
    )


def _convert_table_block(lines: Sequence[str], index: int, state: SteamState) -> int | None:
    if state.inside_code_block or index + 1 >= len(lines):
        return None

    header_line, header_depth = _extract_quotes(lines[index])
    separator_line, separator_depth = _extract_quotes(lines[index + 1])
    if header_depth != separator_depth:
        return None
    if not _is_table_start(header_line, separator_line):
        return None

    header_cells = _split_table_row(header_line)
    column_count = len(header_cells)
    if column_count == 0:
        return None

    state.close_lists()
    _convert_quote_level(header_depth, state)
    state.add_line("[table]")

    if any(cell for cell in header_cells):
        _emit_table_row("th", header_cells, state)

    cursor = index + 2
    while cursor < len(lines):
        body_line, body_depth = _extract_quotes(lines[cursor])
        if body_depth != header_depth or not _is_table_body_row(body_line):
            break
        body_cells = _split_table_row(body_line)
        body_cells = (body_cells + [""] * column_count)[:column_count]
        _emit_table_row("td", body_cells, state)
        cursor += 1

    state.add_line("[/table]")

    return cursor


def _is_table_start(header_line: str, separator_line: str) -> bool:
    header = header_line.strip()
    separator = separator_line.strip()
    if not header or not separator or not _has_unescaped_pipe(header):
        return False
    if _looks_like_block_start(header):
        return False

    header_cells = _split_table_row(header)
    separator_cells = _split_table_row(separator)
    if not header_cells or len(header_cells) != len(separator_cells):
        return False

    return all(_PATTERN_TABLE_SEPARATOR_CELL.fullmatch(cell) for cell in separator_cells)


def _is_table_body_row(line_content: str) -> bool:
    content = line_content.strip()
    if not content or not _has_unescaped_pipe(content):
        return False
    return not _looks_like_block_start(content)


def _emit_table_row(cell_tag: str, cells: list[str], state: SteamState) -> None:
    converted_cells = [
        _convert_inline_elements(cell.replace("\\|", "|"), state.references) for cell in cells
    ]
    row = "[tr]" + "".join(f"[{cell_tag}]{cell}[/{cell_tag}]" for cell in converted_cells) + "[/tr]"
    state.add_line(row)


def _split_table_row(line_content: str) -> list[str]:
    """Split a GFM table row without breaking escaped or code-span pipes."""
    text = line_content.strip()
    text = text.removeprefix("|")
    if text.endswith("|") and not _is_escaped(text, len(text) - 1):
        text = text[:-1]

    cells: list[str] = []
    current: list[str] = []
    index = 0
    code_run = 0

    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            current.append(text[index : index + 2])
            index += 2
            continue
        if char == "`":
            end = index
            while end < len(text) and text[end] == "`":
                end += 1
            run_length = end - index
            if code_run == 0:
                code_run = run_length
            elif code_run == run_length:
                code_run = 0
            current.append(text[index:end])
            index = end
            continue
        if char == "|" and code_run == 0:
            cells.append("".join(current).strip())
            current = []
            index += 1
            continue
        current.append(char)
        index += 1

    cells.append("".join(current).strip())
    return cells


def _has_unescaped_pipe(text: str) -> bool:
    index = 0
    code_run = 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "`":
            end = index
            while end < len(text) and text[end] == "`":
                end += 1
            run_length = end - index
            if code_run == 0:
                code_run = run_length
            elif code_run == run_length:
                code_run = 0
            index = end
            continue
        if char == "|" and code_run == 0:
            return True
        index += 1
    return False


def _is_escaped(text: str, index: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def _extract_reference_definitions(lines: Sequence[str]) -> tuple[dict[str, str], list[str]]:
    """Collect link reference definitions and drop their lines from the document."""
    references: dict[str, str] = {}
    output: list[str] = []
    fence_char = ""
    fence_length = 0

    for line in lines:
        if fence_char:
            output.append(line)
            if _is_fence_close(line, fence_char, fence_length):
                fence_char = ""
            continue

        fence_match = _PATTERN_FENCE.match(line.lstrip("\u200b\ufeff"))
        if fence_match:
            fence = fence_match.group(1)
            fence_char = fence[0]
            fence_length = len(fence)
            output.append(line)
            continue

        definition = _PATTERN_REFERENCE_DEFINITION.match(line)
        if definition:
            label = _normalize_reference_label(definition.group(1))
            url = definition.group(2) or definition.group(3)
            if label and url:
                references[label] = url
                continue

        output.append(line)

    return references, output


def _normalize_reference_label(label: str) -> str:
    return " ".join(label.lower().split())


def _convert_inline_bold(text: str) -> str:
    """Convert inline bold: **text** -> [b]text[/b]."""
    text = _PATTERN_BOLD_ITALIC_STAR.sub(r"[b][i]\1[/i][/b]", text)
    text = _PATTERN_BOLD_ITALIC_UNDER.sub(r"[b][i]\1[/i][/b]", text)
    text = _PATTERN_BOLD_STAR.sub(r"[b]\1[/b]", text)
    return _PATTERN_BOLD_UNDER.sub(r"[b]\1[/b]", text)


def _convert_inline_elements(text: str, references: dict[str, str] | None = None) -> str:
    text, code_spans = _convert_inline_code_spans(text)
    text = _convert_inline_linked_images(text)
    text = _convert_inline_reference_images(text, references)
    text = _convert_inline_images(text)
    text = _convert_inline_links(text)
    text = _convert_inline_reference_links(text, references)
    text = _convert_inline_autolinks(text)
    text = _convert_inline_bold(text)
    text = _convert_inline_italic(text)
    text = _convert_inline_strikethrough(text)
    text = _convert_inline_underline(text)
    text = _convert_inline_spoiler(text)
    text = _render_inline_code_spans(text, code_spans)
    return text.strip()


def _convert_inline_code_spans(text: str) -> tuple[str, list[str]]:
    """Convert inline code spans: ``code`` -> @@CODE{index}@@."""
    code_spans: list[str] = []
    output: list[str] = []
    index = 0

    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            output.append(text[index : index + 2])
            index += 2
            continue
        if char != "`":
            output.append(char)
            index += 1
            continue

        run_end = index
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        run_length = run_end - index
        close_index = _find_closing_backtick_run(text, run_end, run_length)
        if close_index == -1:
            output.append(text[index:run_end])
            index = run_end
            continue

        code_spans.append(_normalize_code_span_content(text[run_end:close_index]))
        output.append(f"@@CODE{len(code_spans) - 1}@@")
        index = close_index + run_length

    return "".join(output), code_spans


def _find_closing_backtick_run(text: str, start: int, run_length: int) -> int:
    needle = "`" * run_length
    position = start
    while True:
        position = text.find(needle, position)
        if position == -1:
            return -1
        end = position + run_length
        before_ok = position == 0 or text[position - 1] != "`"
        after_ok = end == len(text) or text[end] != "`"
        if before_ok and after_ok:
            return position
        while position < len(text) and text[position] == "`":
            position += 1


def _normalize_code_span_content(content: str) -> str:
    if content.startswith(" ") and content.endswith(" ") and content.strip():
        return content[1:-1]
    return content.replace("\n", " ")


def _convert_inline_linked_images(text: str) -> str:
    """Convert linked images: [![alt](image)](link) -> [url=link][img]image[/img][/url]."""

    def image_repl(match: re.Match) -> str:
        image_url = match.group(2) or match.group(3)
        link_url = match.group(4) or match.group(5)
        return f"[url={link_url}][img]{image_url}[/img][/url]"

    return _PATTERN_LINKED_IMAGE.sub(image_repl, text)


def _convert_inline_reference_images(text: str, references: dict[str, str] | None) -> str:
    """Convert reference images: ![alt][id] -> [img]URL[/img]."""
    if not references:
        return text

    def image_repl(match: re.Match) -> str:
        label = match.group(2) or match.group(1)
        url = references.get(_normalize_reference_label(label))
        if url is None:
            return match.group(0)
        return f"[img]{url}[/img]"

    return _PATTERN_REFERENCE_IMAGE.sub(image_repl, text)


def _convert_inline_images(text: str) -> str:
    """Convert inline images: ![alt](URL) -> [img]URL[/img]."""

    def image_repl(match: re.Match) -> str:
        url = match.group(2) or match.group(3)
        return f"[img]{url}[/img]"

    return _PATTERN_IMAGE.sub(image_repl, text)


def _convert_inline_autolinks(text: str) -> str:
    """Convert autolinks: <https://example.com> -> [url=https://example.com]...[/url]."""

    def autolink_repl(match: re.Match) -> str:
        value = match.group(1)
        if value.lower().startswith("mailto:"):
            return f"[url={value}]{value[7:]}[/url]"
        if "@" in value and "://" not in value:
            return f"[url=mailto:{value}]{value}[/url]"
        return f"[url={value}]{value}[/url]"

    return _PATTERN_AUTOLINK.sub(autolink_repl, text)


def _convert_inline_italic(text: str) -> str:
    """Convert inline italic: *text* and _text_ -> [i]text[/i]."""
    text = _PATTERN_ITALIC.sub(r"[i]\1[/i]", text)
    return _PATTERN_ITALIC_UNDER.sub(r"[i]\1[/i]", text)


def _convert_inline_links(text: str) -> str:
    """Convert inline links: [text](URL) -> [url=URL]text[/url]."""

    def link_repl(match: re.Match) -> str:
        link_text = match.group(1)
        url = match.group(2) or match.group(3)
        return f"[url={url}]{link_text}[/url]"

    return _PATTERN_LINK.sub(link_repl, text)


def _convert_inline_reference_links(text: str, references: dict[str, str] | None) -> str:
    """Convert reference links: [text][id] -> [url=URL]text[/url]."""
    if not references:
        return text

    def link_repl(match: re.Match) -> str:
        label = match.group(2) or match.group(1)
        url = references.get(_normalize_reference_label(label))
        if url is None:
            return match.group(0)
        return f"[url={url}]{match.group(1)}[/url]"

    return _PATTERN_REFERENCE_LINK.sub(link_repl, text)


def _convert_inline_strikethrough(text: str) -> str:
    """Convert inline strikethrough: ~~text~~ -> [strike]text[/strike]."""
    return _PATTERN_STRIKETHROUGH.sub(r"[strike]\1[/strike]", text)


def _convert_inline_underline(text: str) -> str:
    """Convert HTML underline: <u>text</u> -> [u]text[/u]."""
    return _PATTERN_UNDERLINE_HTML.sub(r"[u]\1[/u]", text)


def _convert_inline_spoiler(text: str) -> str:
    """Convert the ||spoiler|| extension: ||text|| -> [spoiler]text[/spoiler]."""
    return _PATTERN_SPOILER.sub(r"[spoiler]\1[/spoiler]", text)


def _render_inline_code_spans(text: str, code_spans: list[str]) -> str:
    """Render inline code spans: @@CODE{index}@@ -> [code]code[/code]."""

    def render_repl(match: re.Match) -> str:
        idx = int(match.group(1))
        return f"[code]{code_spans[idx]}[/code]"

    return re.sub(r"@@CODE(\d+)@@", render_repl, text)
