"""Module that contains the Steam-markup-to-Markdown conversion pipeline."""

from __future__ import annotations

import re

from dataclasses import dataclass
from dataclasses import field


_PATTERN_CODE_SPAN = re.compile(r"\[code\](.*?)\[/code\]")
_PATTERN_IMAGE = re.compile(r"\[img\](.*?)\[/img\]")
_PATTERN_LINK = re.compile(r"\[url=([^]]*)\](.*?)\[/url\]")
_PATTERN_BOLD_ITALIC = re.compile(r"\[b\]\[i\](.*?)\[/i\]\[/b\]")
_PATTERN_BOLD = re.compile(r"\[b\](.*?)\[/b\]")
_PATTERN_ITALIC = re.compile(r"\[i\](.*?)\[/i\]")
_PATTERN_STRIKETHROUGH = re.compile(r"\[strike\](.*?)\[/strike\]")
_PATTERN_UNDERLINE = re.compile(r"\[u\](.*?)\[/u\]")
_PATTERN_SPOILER = re.compile(r"\[spoiler\](.*?)\[/spoiler\]")

_PATTERN_HEADING = re.compile(r"^\[h([1-6])\](.*)\[/h\1\]$")
_PATTERN_HORIZONTAL_RULE = re.compile(r"^\[hr\]\[/hr\]$")
_PATTERN_LIST_OPEN = re.compile(r"^\[(list|olist)\]$")
_PATTERN_LIST_CLOSE = re.compile(r"^\[/(list|olist)\]$")
_PATTERN_LIST_ITEM = re.compile(r"^\[\*\]\s?(.*)")
_PATTERN_QUOTE_ONLY = re.compile(r"^(?:\[/?quote\])+$")
_PATTERN_QUOTE_TOKEN = re.compile(r"\[(/?)quote\]")
_PATTERN_TASK_CHECKBOX = re.compile(r"^(☑|☐)\s*(.*)$")
_PATTERN_TABLE_OPEN = re.compile(r"\[table(?:\s+[^\]]*)?\]")
_PATTERN_TABLE_CLOSE = re.compile(r"\[/table\]")
_PATTERN_TABLE_ROW = re.compile(r"\[tr\](.*?)\[/tr\]", re.DOTALL)
_PATTERN_TABLE_CELL = re.compile(r"\[(th|td)\](.*?)\[/\1\]", re.DOTALL)
_PATTERN_BACKTICK_RUN = re.compile(r"`+")

_INDENT_WIDTH = 2


@dataclass
class MarkdownState:
    lines: list[str] = field(default_factory=list)
    list_stack: list[tuple[str, int]] = field(default_factory=list)
    current_quote_level: int = 0
    inside_code_block: bool = False
    code_block_accumulator: list[str] = field(default_factory=list)
    inside_table: bool = False
    table_accumulator: list[str] = field(default_factory=list)

    def add_line(self, line: str) -> None:
        self.lines.append(line)

    def prefix(self, text: str) -> str:
        return "> " * self.current_quote_level + text

    def build(self) -> str:
        return "\n".join(self.lines)


def to_markdown(steam_text: str) -> str:
    """Convert Steam-compatible markup to Markdown text."""
    state = MarkdownState()
    lines = steam_text.splitlines()

    for steam_line in lines:
        _process_line(steam_line, state)

    _close_remaining_blocks(state)

    return state.build()


def _close_remaining_blocks(state: MarkdownState) -> None:
    if state.inside_table:
        _flush_table(state)

    if state.inside_code_block:
        state.inside_code_block = False
        _flush_code_block(state)

    state.list_stack.clear()
    state.current_quote_level = 0


def _process_line(steam_line: str, state: MarkdownState) -> None:
    if state.inside_code_block:
        _convert_code_block_content(steam_line, state)
        return

    if state.inside_table:
        _convert_table_content(steam_line, state)
        return

    line_content = steam_line.strip()

    if line_content == "":
        state.add_line(state.prefix("").rstrip())
        return

    if (
        _try_convert_code_block_open(line_content, state)
        or _try_convert_table_open(line_content, state)
        or _try_convert_quote_level(line_content, state)
        or _try_convert_list_open(line_content, state)
        or _try_convert_list_close(line_content, state)
        or _try_convert_list_item(line_content, state)
        or _try_convert_heading(line_content, state)
        or _try_convert_horizontal_rule(line_content, state)
    ):
        return

    state.add_line(state.prefix(_convert_inline_elements(line_content)))


def _flush_code_block(state: MarkdownState) -> None:
    fence = _code_fence(state.code_block_accumulator)
    state.add_line(state.prefix(fence))

    for code_line in state.code_block_accumulator:
        state.add_line(state.prefix(code_line))

    state.add_line(state.prefix(fence))
    state.code_block_accumulator.clear()


def _code_fence(code_lines: list[str]) -> str:
    longest_run = max(
        (
            len(match.group(0))
            for line in code_lines
            for match in _PATTERN_BACKTICK_RUN.finditer(line)
        ),
        default=0,
    )
    return "`" * max(3, longest_run + 1)


def _try_convert_code_block_open(line_content: str, state: MarkdownState) -> bool:
    """Enter code-block mode on a `[code]` tag left unclosed on its own line."""
    if "[code]" not in line_content:
        return False

    leading_text, _, remainder = line_content.partition("[code]")
    if "[/code]" in remainder:
        return False

    if leading_text.strip():
        state.add_line(state.prefix(_convert_inline_elements(leading_text)))

    state.inside_code_block = True
    state.code_block_accumulator.clear()

    if remainder:
        state.code_block_accumulator.append(remainder)

    return True


def _convert_code_block_content(steam_line: str, state: MarkdownState) -> None:
    if "[/code]" not in steam_line:
        state.code_block_accumulator.append(steam_line)
        return

    code_content, _, trailing_text = steam_line.partition("[/code]")
    if code_content:
        state.code_block_accumulator.append(code_content)

    state.inside_code_block = False
    _flush_code_block(state)

    if trailing_text.strip():
        state.add_line(state.prefix(_convert_inline_elements(trailing_text)))


def _try_convert_table_open(line_content: str, state: MarkdownState) -> bool:
    match = _PATTERN_TABLE_OPEN.search(line_content)
    if not match:
        return False

    code_start = line_content.find("[code]")
    if code_start != -1 and code_start < match.start() and "[/code]" in line_content[code_start:]:
        return False

    leading_text = line_content[: match.start()].strip()
    if leading_text:
        state.add_line(state.prefix(_convert_inline_elements(leading_text)))

    remainder = line_content[match.end() :]
    state.inside_table = True
    state.table_accumulator.clear()

    close_match = _PATTERN_TABLE_CLOSE.search(remainder)
    if close_match:
        table_text = remainder[: close_match.start()]
        trailing_text = remainder[close_match.end() :]
        if table_text:
            state.table_accumulator.append(table_text)
        _flush_table(state)
        if trailing_text.strip():
            state.add_line(state.prefix(_convert_inline_elements(trailing_text.strip())))
    elif remainder:
        state.table_accumulator.append(remainder)

    return True


def _convert_table_content(steam_line: str, state: MarkdownState) -> None:
    close_match = _PATTERN_TABLE_CLOSE.search(steam_line)
    if close_match is None:
        state.table_accumulator.append(steam_line)
        return

    table_text = steam_line[: close_match.start()]
    trailing_text = steam_line[close_match.end() :]
    if table_text:
        state.table_accumulator.append(table_text)

    _flush_table(state)

    if trailing_text.strip():
        state.add_line(state.prefix(_convert_inline_elements(trailing_text.strip())))


def _flush_table(state: MarkdownState) -> None:
    table_text = "\n".join(state.table_accumulator)
    state.inside_table = False
    state.table_accumulator.clear()

    for table_line in _render_markdown_table(table_text):
        state.add_line(state.prefix(table_line))


def _render_markdown_table(table_text: str) -> list[str]:
    rows = _parse_table_rows(table_text)
    if not rows:
        return []

    first_row = rows[0]
    header_cells = [content for tag, content in first_row if tag == "th"]
    first_row_data = [content for tag, content in first_row if tag == "td"]
    has_header = bool(header_cells)

    body_rows = ([first_row_data] if first_row_data else []) + [
        [content for _, content in row] for row in rows[1:]
    ]
    column_count = max([len(header_cells), *(len(row) for row in body_rows)])
    if column_count == 0:
        return []

    if has_header:
        header_cells = (header_cells + [""] * column_count)[:column_count]
    else:
        header_cells = [""] * column_count

    lines = [_render_table_row([_convert_inline_elements(cell) for cell in header_cells])]
    lines.append("| " + " | ".join(["---"] * column_count) + " |")

    for row in body_rows:
        padded_cells = (row + [""] * column_count)[:column_count]
        lines.append(_render_table_row([_convert_inline_elements(cell) for cell in padded_cells]))

    return lines


def _parse_table_rows(table_text: str) -> list[list[tuple[str, str]]]:
    rows: list[list[tuple[str, str]]] = []
    for row_match in _PATTERN_TABLE_ROW.finditer(table_text):
        cells = [
            (cell_match.group(1), cell_match.group(2))
            for cell_match in _PATTERN_TABLE_CELL.finditer(row_match.group(1))
        ]
        if cells:
            rows.append(cells)
    return rows


def _render_table_row(cells: list[str]) -> str:
    rendered = " | ".join(_escape_table_pipes(_clean_table_cell(cell)) for cell in cells)
    return f"| {rendered} |"


def _clean_table_cell(cell: str) -> str:
    return " ".join(cell.split()).strip()


def _escape_table_pipes(text: str) -> str:
    output: list[str] = []
    index = 0
    code_run = 0

    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            output.append(text[index : index + 2])
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
            output.append(text[index:end])
            index = end
            continue
        output.append("\\|" if char == "|" and code_run == 0 else char)
        index += 1

    return "".join(output)


def _try_convert_quote_level(line_content: str, state: MarkdownState) -> bool:
    if not _PATTERN_QUOTE_ONLY.match(line_content):
        return False

    for token in _PATTERN_QUOTE_TOKEN.finditer(line_content):
        if token.group(1):
            state.current_quote_level = max(0, state.current_quote_level - 1)
        else:
            state.current_quote_level += 1

    return True


def _try_convert_list_open(line_content: str, state: MarkdownState) -> bool:
    match = _PATTERN_LIST_OPEN.match(line_content)
    if not match:
        return False

    state.list_stack.append((match.group(1), 0))

    return True


def _try_convert_list_close(line_content: str, state: MarkdownState) -> bool:
    if not _PATTERN_LIST_CLOSE.match(line_content):
        return False

    if state.list_stack:
        state.list_stack.pop()

    return True


def _try_convert_list_item(line_content: str, state: MarkdownState) -> bool:
    match = _PATTERN_LIST_ITEM.match(line_content)
    if not match:
        return False

    if not state.list_stack:
        state.list_stack.append(("list", 0))

    list_type, item_number = state.list_stack[-1]
    item_number += 1
    state.list_stack[-1] = (list_type, item_number)

    match list_type:
        case "olist":
            marker = f"{item_number}."
        case _:
            marker = "-"

    indent = " " * (_INDENT_WIDTH * (len(state.list_stack) - 1))
    item_text = _convert_inline_elements(match.group(1))
    item_text = _restore_task_checkbox(item_text)
    state.add_line(state.prefix(f"{indent}{marker} {item_text}"))

    return True


def _restore_task_checkbox(item_text: str) -> str:
    match = _PATTERN_TASK_CHECKBOX.match(item_text)
    if not match:
        return item_text

    checkbox = "[x]" if match.group(1) == "☑" else "[ ]"
    remainder = match.group(2).strip()
    return f"{checkbox} {remainder}".rstrip()


def _try_convert_heading(line_content: str, state: MarkdownState) -> bool:
    match = _PATTERN_HEADING.match(line_content)
    if not match:
        return False

    level = int(match.group(1))
    heading_text = _convert_inline_elements(match.group(2))
    state.add_line(state.prefix(f"{'#' * level} {heading_text}"))

    return True


def _try_convert_horizontal_rule(line_content: str, state: MarkdownState) -> bool:
    if not _PATTERN_HORIZONTAL_RULE.match(line_content):
        return False

    state.add_line(state.prefix("---"))

    return True


def _convert_inline_bold(text: str) -> str:
    """Convert inline bold: [b]text[/b] -> **text**."""
    text = _PATTERN_BOLD_ITALIC.sub(r"***\1***", text)
    return _PATTERN_BOLD.sub(r"**\1**", text)


def _convert_inline_elements(text: str) -> str:
    text, code_spans = _convert_inline_code_spans(text)
    text = _convert_inline_images(text)
    text = _convert_inline_links(text)
    text = _convert_inline_bold(text)
    text = _convert_inline_italic(text)
    text = _convert_inline_strikethrough(text)
    text = _convert_inline_underline(text)
    text = _convert_inline_spoiler(text)
    text = _render_inline_code_spans(text, code_spans)
    return text.strip()


def _convert_inline_code_spans(text: str) -> tuple[str, list[str]]:
    """Convert inline code spans: [code]code[/code] -> @@CODE{index}@@."""
    code_spans: list[str] = []

    def code_span_repl(match: re.Match) -> str:
        code_content = match.group(1)
        code_spans.append(code_content)
        return f"@@CODE{len(code_spans) - 1}@@"

    text = _PATTERN_CODE_SPAN.sub(code_span_repl, text)
    return text, code_spans


def _convert_inline_images(text: str) -> str:
    """Convert inline images: [img]URL[/img] -> ![](URL)."""
    return _PATTERN_IMAGE.sub(r"![](\1)", text)


def _convert_inline_italic(text: str) -> str:
    """Convert inline italic: [i]text[/i] -> *text*."""
    return _PATTERN_ITALIC.sub(r"*\1*", text)


def _convert_inline_links(text: str) -> str:
    """Convert inline links: [url=URL]text[/url] -> [text](URL)."""

    def link_repl(match: re.Match) -> str:
        url = match.group(1)
        link_text = match.group(2)
        return f"[{link_text}]({url})"

    return _PATTERN_LINK.sub(link_repl, text)


def _convert_inline_strikethrough(text: str) -> str:
    """Convert inline strikethrough: [strike]text[/strike] -> ~~text~~."""
    return _PATTERN_STRIKETHROUGH.sub(r"~~\1~~", text)


def _convert_inline_underline(text: str) -> str:
    """Convert inline underline: [u]text[/u] -> <u>text</u>."""
    return _PATTERN_UNDERLINE.sub(r"<u>\1</u>", text)


def _convert_inline_spoiler(text: str) -> str:
    """Convert inline spoiler: [spoiler]text[/spoiler] -> ||text||."""
    return _PATTERN_SPOILER.sub(r"||\1||", text)


def _render_inline_code_spans(text: str, code_spans: list[str]) -> str:
    """Render inline code spans: @@CODE{index}@@ -> `code`."""

    def render_repl(match: re.Match) -> str:
        idx = int(match.group(1))
        return _render_code_span(code_spans[idx])

    return re.sub(r"@@CODE(\d+)@@", render_repl, text)


def _render_code_span(content: str) -> str:
    longest_run = max(
        (len(match.group(0)) for match in _PATTERN_BACKTICK_RUN.finditer(content)),
        default=0,
    )
    fence = "`" * (longest_run + 1)

    if content and not content.strip():
        return f"{fence}{content}{fence}"
    if content.startswith(("`", " ")) or content.endswith(("`", " ")):
        return f"{fence} {content} {fence}"
    return f"{fence}{content}{fence}"
