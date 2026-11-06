"""Parsing and validation helpers for model-generated JSON."""

import json
import re
from typing import Any

from modules.structured_outputs import validate_structured_output


class JSONResponseError(ValueError):
    """Raised when a model response cannot be parsed or validated as JSON."""


def strip_markdown_fences(response: str) -> str:
    """Remove a single surrounding Markdown code fence, if present."""
    match = re.fullmatch(
        r"\s*```(?:json)?\s*(.*?)\s*```\s*",
        response,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else response.strip()


def parse_json_response(response: str, schema_name: str | None = None) -> Any:
    """Parse JSON text and optionally validate it against a known output schema."""
    if not isinstance(response, str) or not response.strip():
        raise JSONResponseError("The LLM returned an empty response.")

    cleaned = strip_markdown_fences(response)
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise JSONResponseError(
            f"The LLM response was not valid JSON: {exc.msg} (line {exc.lineno}, "
            f"column {exc.colno})."
        ) from exc

    if schema_name:
        try:
            validate_structured_output(result, schema_name)
        except ValueError as exc:
            raise JSONResponseError(str(exc)) from exc
    return result
