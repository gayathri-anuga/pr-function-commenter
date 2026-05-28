from __future__ import annotations

import json
import os
import sys

from .github_api import GitHubClient
from .llm import build_comment_generator
from .workflow import run_comment_workflow


def main() -> int:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    owner, _, repo = repository.partition("/")
    pr_number = int(os.environ.get("PR_NUMBER") or os.environ.get("GITHUB_REF_NAME", "0").split("/")[0])
    token = os.environ.get("GITHUB_TOKEN")

    missing = []
    if not owner or not repo:
        missing.append("GITHUB_REPOSITORY")
    if not pr_number:
        missing.append("PR_NUMBER")
    if not token:
        missing.append("GITHUB_TOKEN")

    if missing:
        raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")

    github = GitHubClient(token=token, owner=owner, repo=repo)
    result = run_comment_workflow(
        github=github,
        comment_generator=build_comment_generator(),
        pr_number=pr_number,
        max_attempts=int(os.environ.get("MAX_COMMENT_ATTEMPTS", "3")),
    )
    print(json.dumps({"status": result["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
