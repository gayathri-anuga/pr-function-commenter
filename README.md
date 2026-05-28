# PR Function Commenter

A Python GitHub Action script that automatically adds short function comments/docstrings for functions changed in a pull request.

The workflow:

1. A PR is opened or updated.
2. The action scans the PR diff.
3. Changed functions are extracted using language-specific patterns.
4. The OpenAI Responses API generates concise comments.
5. The patch is validated with a Safety Validator:
   - AST equivalence check confirms executable code did not change where supported.
   - Comment-only diff check confirms only comments were added.
6. If validation fails, the action retries up to 3 times.
7. If validation passes, an automation branch and PR are created.
8. The original PR receives an audit summary comment.

## Language Support

The script is designed to work across repos and languages. Current built-in extraction/comment syntax support:

- Python
- JavaScript / TypeScript
- Java / C# / Kotlin
- Go
- Ruby
- PHP
- Rust

Validation levels:

- Python: AST validation plus comment-only diff validation.
- Other supported languages: strict comment-only diff validation.

For production-grade AST validation in every language, add a parser backend such as Tree-sitter later. The code is structured so each language can gain a stronger validator without changing the GitHub workflow.

## GitHub Secrets

Add these repository secrets:

- `OPENAI_API_KEY`
- `GITHUB_TOKEN` is provided automatically by GitHub Actions.

Optional variables:

- `OPENAI_MODEL`, default `gpt-5.1`
- `MAX_COMMENT_ATTEMPTS`, default `3`

## Local Demo

```bash
python -m unittest discover -s test
python examples/demo_run.py
```

## GitHub Action

The included workflow runs on PR open, reopen, and synchronize events.

Generated PRs target the original PR branch, not `main`, so the developer can review the generated comments before merging them into their feature PR.

## Required Permissions

The workflow needs:

- `contents: write` to create the automation branch and commit comment changes.
- `pull-requests: write` to open the generated PR.

## Retry Behavior

If validation fails, the validation error is sent back to the LLM and the script tries again. After 3 failed attempts, it stops safely and posts a failure summary on the original PR.
