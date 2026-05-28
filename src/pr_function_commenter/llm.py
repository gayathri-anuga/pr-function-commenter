from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .extractor import FunctionBlock


class OpenAICommentGenerator:
    def __init__(self, api_key: str, model: str = "gpt-5.1") -> None:
        self.api_key = api_key
        self.model = model

    def generate(
        self,
        file_path: str,
        language: str,
        functions: list[FunctionBlock],
        retry_context: str = "",
    ) -> dict[str, str]:
        payload = {
            "model": self.model,
            "reasoning": {"effort": "none"},
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "function_comments",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "comments": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "functionName": {"type": "string"},
                                        "comment": {"type": "string"},
                                    },
                                    "required": ["functionName", "comment"],
                                },
                            }
                        },
                        "required": ["comments"],
                    },
                }
            },
            "input": [
                {
                    "role": "developer",
                    "content": (
                        "Generate concise comments for changed functions. "
                        "Describe the function's purpose, not every implementation step. "
                        "Return JSON only. Do not include code fences."
                    ),
                },
                {
                    "role": "user",
                    "content": _build_prompt(file_path, language, functions, retry_context),
                },
            ],
        }

        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise RuntimeError(error.read().decode("utf-8")) from error

        text = body.get("output_text") or _extract_output_text(body)
        parsed = json.loads(text)
        return {item["functionName"]: item["comment"] for item in parsed["comments"]}


class StaticCommentGenerator:
    """Local test generator used when OPENAI_API_KEY is not available."""

    def generate(
        self,
        file_path: str,
        language: str,
        functions: list[FunctionBlock],
        retry_context: str = "",
    ) -> dict[str, str]:
        return {
            function.name: f"Explains the purpose of {function.name}."
            for function in functions
        }


def build_comment_generator() -> OpenAICommentGenerator | StaticCommentGenerator:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return StaticCommentGenerator()
    return OpenAICommentGenerator(api_key=api_key, model=os.environ.get("OPENAI_MODEL", "gpt-5.1"))


def _build_prompt(
    file_path: str,
    language: str,
    functions: list[FunctionBlock],
    retry_context: str,
) -> str:
    retry = f"\nPrevious validation failure:\n{retry_context}\n" if retry_context else ""
    blocks = []
    for function in functions:
        blocks.append(
            f"Function: {function.name}\n"
            f"Lines: {function.start_line}-{function.end_line}\n"
            f"Code:\n```{language}\n{function.code}\n```"
        )
    return f"File: {file_path}\nLanguage: {language}{retry}\n\n" + "\n\n".join(blocks)


def _extract_output_text(body: dict) -> str:
    for item in body.get("output", []):
        for content in item.get("content", []):
            if "text" in content:
                return content["text"]
    raise RuntimeError("OpenAI response did not contain output text.")
