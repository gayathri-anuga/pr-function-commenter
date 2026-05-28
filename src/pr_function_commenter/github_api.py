from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request


class GitHubClient:
    def __init__(self, token: str, owner: str, repo: str) -> None:
        self.token = token
        self.owner = owner
        self.repo = repo

    def request(self, path: str, method: str = "GET", payload: dict | None = None) -> dict | list | None:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            f"https://api.github.com{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if response.status == 204:
                    return None
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8")
            raise RuntimeError(f"GitHub {error.code} {path}: {detail}") from error

    def get_pull_request(self, pr_number: int) -> dict:
        return self.request(f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}")  # type: ignore[return-value]

    def list_pull_request_files(self, pr_number: int) -> list[dict]:
        files: list[dict] = []
        page = 1
        while True:
            result = self.request(
                f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}/files?per_page=100&page={page}"
            )
            assert isinstance(result, list)
            files.extend(result)
            if len(result) < 100:
                return files
            page += 1

    def get_file_content(self, path: str, ref: str) -> str:
        encoded_path = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
        result = self.request(
            f"/repos/{self.owner}/{self.repo}/contents/{encoded_path}?ref={urllib.parse.quote(ref, safe='')}"
        )
        assert isinstance(result, dict)
        return base64.b64decode(result["content"]).decode("utf-8")

    def create_branch_if_missing(self, branch: str, sha: str) -> None:
        try:
            self.request(f"/repos/{self.owner}/{self.repo}/git/ref/heads/{urllib.parse.quote(branch, safe='')}")
            return
        except RuntimeError as error:
            if "GitHub 404" not in str(error):
                raise

        self.request(
            f"/repos/{self.owner}/{self.repo}/git/refs",
            method="POST",
            payload={"ref": f"refs/heads/{branch}", "sha": sha},
        )

    def upsert_file(self, branch: str, path: str, content: str, message: str) -> None:
        encoded_path = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
        sha = None
        try:
            current = self.request(
                f"/repos/{self.owner}/{self.repo}/contents/{encoded_path}?ref={urllib.parse.quote(branch, safe='')}"
            )
            assert isinstance(current, dict)
            sha = current["sha"]
        except RuntimeError as error:
            if "GitHub 404" not in str(error):
                raise

        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha

        self.request(
            f"/repos/{self.owner}/{self.repo}/contents/{encoded_path}",
            method="PUT",
            payload=payload,
        )

    def create_pull_request(self, title: str, head: str, base: str, body: str) -> dict:
        return self.request(
            f"/repos/{self.owner}/{self.repo}/pulls",
            method="POST",
            payload={"title": title, "head": head, "base": base, "body": body},
        )  # type: ignore[return-value]

    def create_issue_comment(self, issue_number: int, body: str) -> None:
        self.request(
            f"/repos/{self.owner}/{self.repo}/issues/{issue_number}/comments",
            method="POST",
            payload={"body": body},
        )
