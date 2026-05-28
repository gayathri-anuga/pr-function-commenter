from __future__ import annotations

import ast

from .languages import LanguageSpec


def validate_comment_only_change(before: str, after: str, language: LanguageSpec) -> tuple[bool, list[str]]:
    errors: list[str] = []

    if language.name == "python" and not _python_ast_equivalent(before, after):
        errors.append("Python AST changed after comment insertion.")

    if _strip_comment_only_lines(before, language) != _strip_comment_only_lines(after, language):
        errors.append("Diff contains non-comment code or formatting changes.")

    return len(errors) == 0, errors


def _python_ast_equivalent(before: str, after: str) -> bool:
    try:
        before_ast = ast.dump(ast.parse(before), include_attributes=False)
        after_ast = ast.dump(ast.parse(after), include_attributes=False)
    except SyntaxError:
        return False
    return before_ast == after_ast


def _strip_comment_only_lines(code: str, language: LanguageSpec) -> list[str]:
    output: list[str] = []
    in_block_comment = False

    for line in code.splitlines():
        stripped = line.strip()

        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue

        if stripped.startswith("/*"):
            if "*/" not in stripped:
                in_block_comment = True
            continue

        if stripped.startswith(language.line_comment):
            continue

        output.append(line)

    return output
