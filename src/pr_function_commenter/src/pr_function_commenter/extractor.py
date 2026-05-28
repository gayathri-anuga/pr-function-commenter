from __future__ import annotations

from dataclasses import dataclass

from .languages import LanguageSpec


@dataclass(frozen=True)
class FunctionBlock:
    name: str
    start_line: int
    end_line: int
    start_index: int
    end_index: int
    code: str
    has_leading_comment: bool


def extract_changed_functions(code: str, changed_lines: set[int], language: LanguageSpec) -> list[FunctionBlock]:
    lines = code.splitlines(keepends=True)
    line_starts = _line_start_indexes(lines)
    functions: list[FunctionBlock] = []

    for index, line in enumerate(lines, start=1):
        name = _match_function_name(line, language)
        if not name:
            continue

        end_line = _find_block_end(lines, index, language)
        if not any(index <= changed_line <= end_line for changed_line in changed_lines):
            continue

        start_index = line_starts[index - 1]
        end_index = line_starts[end_line] if end_line < len(line_starts) else len(code)
        functions.append(
            FunctionBlock(
                name=name,
                start_line=index,
                end_line=end_line,
                start_index=start_index,
                end_index=end_index,
                code=code[start_index:end_index],
                has_leading_comment=_has_leading_comment(lines, index, language),
            )
        )

    return functions


def _match_function_name(line: str, language: LanguageSpec) -> str | None:
    for pattern in language.function_patterns:
        match = pattern.search(line)
        if match:
            return match.group(1)
    return None


def _line_start_indexes(lines: list[str]) -> list[int]:
    starts: list[int] = []
    offset = 0
    for line in lines:
        starts.append(offset)
        offset += len(line)
    return starts


def _find_block_end(lines: list[str], start_line: int, language: LanguageSpec) -> int:
    if language.name == "python":
        return _find_indented_block_end(lines, start_line)
    if language.name == "ruby":
        return _find_keyword_block_end(lines, start_line)
    return _find_brace_block_end(lines, start_line)


def _find_indented_block_end(lines: list[str], start_line: int) -> int:
    start_indent = len(lines[start_line - 1]) - len(lines[start_line - 1].lstrip())
    end_line = start_line

    for index in range(start_line, len(lines)):
        line = lines[index]
        if line.strip() == "":
            end_line = index + 1
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= start_indent:
            break
        end_line = index + 1

    return end_line


def _find_keyword_block_end(lines: list[str], start_line: int) -> int:
    depth = 0
    for index in range(start_line - 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith(("def ", "class ", "module ", "if ", "unless ", "case ", "begin", "do")):
            depth += 1
        if stripped == "end":
            depth -= 1
            if depth <= 0:
                return index + 1
    return len(lines)


def _find_brace_block_end(lines: list[str], start_line: int) -> int:
    depth = 0
    seen_open = False

    for index in range(start_line - 1, len(lines)):
        line = _strip_line_comment(lines[index])
        depth += line.count("{")
        if "{" in line:
            seen_open = True
        depth -= line.count("}")
        if seen_open and depth <= 0:
            return index + 1

    return min(start_line + 40, len(lines))


def _strip_line_comment(line: str) -> str:
    return line.split("//", 1)[0]


def _has_leading_comment(lines: list[str], start_line: int, language: LanguageSpec) -> bool:
    index = start_line - 2
    while index >= 0 and lines[index].strip() == "":
        index -= 1
    if index < 0:
        return False
    stripped = lines[index].strip()
    return stripped.startswith(language.line_comment) or stripped.endswith("*/")
