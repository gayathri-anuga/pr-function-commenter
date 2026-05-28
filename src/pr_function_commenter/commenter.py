from __future__ import annotations

from .extractor import FunctionBlock
from .languages import LanguageSpec


def apply_comments(
    code: str,
    functions: list[FunctionBlock],
    comments_by_function: dict[str, str],
    language: LanguageSpec,
) -> str:
    updated = code

    for function in sorted(functions, key=lambda item: item.start_index, reverse=True):
        if function.has_leading_comment:
            continue
        comment = comments_by_function.get(function.name)
        if not comment:
            continue
        indent = _indent_at(code, function.start_index)
        formatted = _format_comment(comment, indent, language)
        updated = updated[: function.start_index] + formatted + updated[function.start_index :]

    return updated


def _format_comment(comment: str, indent: str, language: LanguageSpec) -> str:
    cleaned = " ".join(
        comment.replace("/*", "")
        .replace("*/", "")
        .replace("//", "")
        .replace("#", "")
        .split()
    )
    return f"{indent}{language.line_comment} {cleaned}\n"


def _indent_at(code: str, index: int) -> str:
    line_start = code.rfind("\n", 0, index) + 1
    prefix = code[line_start:index]
    return prefix[: len(prefix) - len(prefix.lstrip())]
