from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class LanguageSpec:
    name: str
    extensions: tuple[str, ...]
    line_comment: str
    function_patterns: tuple[re.Pattern[str], ...]


LANGUAGES: tuple[LanguageSpec, ...] = (
    LanguageSpec(
        name="python",
        extensions=(".py",),
        line_comment="#",
        function_patterns=(re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][\w]*)\s*\("),),
    ),
    LanguageSpec(
        name="javascript/typescript",
        extensions=(".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"),
        line_comment="//",
        function_patterns=(
            re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
            re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\("),
            re.compile(r"^\s*(?:public|private|protected|static|async|\s)*([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{"),
        ),
    ),
    LanguageSpec(
        name="java/csharp/kotlin",
        extensions=(".java", ".cs", ".kt", ".kts"),
        line_comment="//",
        function_patterns=(
            re.compile(
                r"^\s*(?:public|private|protected|internal|static|final|open|override|async|suspend|\s)+"
                r"[\w<>\[\]?,\s]+\s+([A-Za-z_][\w]*)\s*\("
            ),
            re.compile(r"^\s*fun\s+([A-Za-z_][\w]*)\s*\("),
        ),
    ),
    LanguageSpec(
        name="go",
        extensions=(".go",),
        line_comment="//",
        function_patterns=(re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_][\w]*)\s*\("),),
    ),
    LanguageSpec(
        name="ruby",
        extensions=(".rb",),
        line_comment="#",
        function_patterns=(re.compile(r"^\s*def\s+([A-Za-z_][\w!?=]*)"),),
    ),
    LanguageSpec(
        name="php",
        extensions=(".php",),
        line_comment="//",
        function_patterns=(re.compile(r"^\s*(?:public|private|protected|static|\s)*function\s+([A-Za-z_][\w]*)\s*\("),),
    ),
    LanguageSpec(
        name="rust",
        extensions=(".rs",),
        line_comment="//",
        function_patterns=(re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_][\w]*)\s*\("),),
    ),
)


def language_for_path(path: str) -> LanguageSpec | None:
    suffix = Path(path).suffix.lower()
    for language in LANGUAGES:
        if suffix in language.extensions:
            return language
    return None
