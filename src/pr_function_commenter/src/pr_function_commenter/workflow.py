from __future__ import annotations

from dataclasses import dataclass

from .commenter import apply_comments
from .diff import changed_lines_from_patch
from .extractor import FunctionBlock, extract_changed_functions
from .languages import language_for_path
from .validation import validate_comment_only_change


@dataclass(frozen=True)
class FileResult:
    file: str
    status: str
    functions: list[str]
    attempts: int = 0
    reason: str = ""
    updated_code: str = ""


def generate_validated_file(
    file_path: str,
    original_code: str,
    functions: list[FunctionBlock],
    language,
    comment_generator,
    max_attempts: int,
) -> FileResult:
    retry_context = ""

    for attempt in range(1, max_attempts + 1):
        comments = comment_generator.generate(file_path, language.name, functions, retry_context)
        updated_code = apply_comments(original_code, functions, comments, language)
        valid, errors = validate_comment_only_change(original_code, updated_code, language)

        if valid and updated_code != original_code:
            return FileResult(
                file=file_path,
                status="changed",
                functions=[function.name for function in functions],
                attempts=attempt,
                updated_code=updated_code,
            )

        retry_context = "\n".join(errors) or "No comment was inserted."

    return FileResult(
        file=file_path,
        status="failed",
        functions=[function.name for function in functions],
        attempts=max_attempts,
        reason=retry_context,
    )


def analyze_pr_file(file_info: dict, current_code: str, comment_generator, max_attempts: int) -> FileResult:
    file_path = file_info["filename"]
    language = language_for_path(file_path)
    if language is None:
        return FileResult(file=file_path, status="skipped", functions=[], reason="Unsupported language.")

    patch = file_info.get("patch")
    if not patch:
        return FileResult(file=file_path, status="skipped", functions=[], reason="No patch available.")

    changed_lines = changed_lines_from_patch(patch)
    functions = [
        function
        for function in extract_changed_functions(current_code, changed_lines, language)
        if not function.has_leading_comment
    ]

    if not functions:
        return FileResult(
            file=file_path,
            status="skipped",
            functions=[],
            reason="No uncommented changed functions found.",
        )

    return generate_validated_file(
        file_path=file_path,
        original_code=current_code,
        functions=functions,
        language=language,
        comment_generator=comment_generator,
        max_attempts=max_attempts,
    )


def run_comment_workflow(github, comment_generator, pr_number: int, max_attempts: int = 3) -> dict:
    pr = github.get_pull_request(pr_number)
    files = github.list_pull_request_files(pr_number)
    results: list[FileResult] = []
    changed_files: dict[str, str] = {}

    for file_info in files:
        file_path = file_info["filename"]
        language = language_for_path(file_path)
        if language is None:
            results.append(FileResult(file=file_path, status="skipped", functions=[], reason="Unsupported language."))
            continue

        current_code = github.get_file_content(file_path, pr["head"]["sha"])
        result = analyze_pr_file(file_info, current_code, comment_generator, max_attempts)
        results.append(result)
        if result.status == "changed":
            changed_files[file_path] = result.updated_code

    if any(result.status == "failed" for result in results):
        github.create_issue_comment(pr_number, build_failure_summary(results))
        return {"status": "failed", "results": results}

    if not changed_files:
        github.create_issue_comment(pr_number, build_noop_summary(results))
        return {"status": "noop", "results": results}

    branch = f"auto/function-comments-pr-{pr_number}"
    github.create_branch_if_missing(branch, pr["head"]["sha"])

    for file_path, content in changed_files.items():
        github.upsert_file(
            branch=branch,
            path=file_path,
            content=content,
            message=f"docs: add generated function comments for PR #{pr_number}",
        )

    generated_pr = github.create_pull_request(
        title=f"docs: add generated function comments for PR #{pr_number}",
        head=branch,
        base=pr["head"]["ref"],
        body=build_generated_pr_body(pr_number, results),
    )
    github.create_issue_comment(pr_number, build_success_summary(results, generated_pr["html_url"]))
    return {"status": "created", "results": results, "generated_pr": generated_pr}


def build_success_summary(results: list[FileResult], pr_url: str) -> str:
    return (
        "## Generated Function Comment Summary\n\n"
        "Automation generated comment-only changes for this PR.\n\n"
        "Validation:\n"
        "- Passed: AST validation where supported.\n"
        "- Passed: comment-only diff validation.\n\n"
        f"Generated PR:\n- {pr_url}\n\n"
        f"{_format_results(results)}"
    )


def build_failure_summary(results: list[FileResult]) -> str:
    return (
        "## Generated Function Comment Summary\n\n"
        "Automation safely stopped. No generated PR was created because validation failed after 3 attempts.\n\n"
        f"{_format_results(results)}"
    )


def build_noop_summary(results: list[FileResult]) -> str:
    return (
        "## Generated Function Comment Summary\n\n"
        "Automation scanned this PR and found no uncommented changed functions to update.\n\n"
        f"{_format_results(results)}"
    )


def build_generated_pr_body(pr_number: int, results: list[FileResult]) -> str:
    return (
        f"Generated function comments for PR #{pr_number}.\n\n"
        "Validation:\n"
        "- AST validation passed where supported.\n"
        "- Comment-only diff validation passed.\n\n"
        f"{_format_results(results)}"
    )


def _format_results(results: list[FileResult]) -> str:
    lines = []
    for result in results:
        functions = f" Functions: {', '.join(result.functions)}." if result.functions else ""
        reason = f" Reason: {result.reason}" if result.reason else ""
        attempts = f" Attempts: {result.attempts}." if result.attempts else ""
        lines.append(f"- `{result.file}`: {result.status}.{functions}{attempts}{reason}")
    return "\n".join(lines)
