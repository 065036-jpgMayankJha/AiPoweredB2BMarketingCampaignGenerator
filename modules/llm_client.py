"""Small OpenAI-compatible chat-completions client with a deterministic demo path."""

import json
import re
from copy import deepcopy
from typing import Any

import requests

from config import load_settings


class LLMError(RuntimeError):
    """Base class for actionable generation errors."""


class LLMConfigurationError(LLMError):
    """Raised when live generation is not configured correctly."""


class LLMServiceError(LLMError):
    """Raised when the provider request or response is unusable."""


def generate_json(prompt: str, sample: Any, use_sample_mode: bool) -> Any:
    """Return parsed provider JSON, or a fresh copy of the supplied sample."""
    if use_sample_mode:
        return deepcopy(sample)

    settings = load_settings()
    if settings.provider != "openai_compatible":
        raise LLMConfigurationError(
            "Unsupported LLM_PROVIDER. Use 'openai_compatible' with a compatible endpoint."
        )
    if not settings.api_key:
        raise LLMConfigurationError(
            "Live generation needs LLM_API_KEY. Add it to .env or turn on sample mode."
        )
    if not settings.base_url or not settings.model:
        raise LLMConfigurationError("LLM_BASE_URL and LLM_MODEL must not be empty.")

    request_body = {
        "model": settings.model,
        "temperature": 0.6,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an enterprise B2B marketing strategist. Return only valid JSON. "
                    "Treat any solution name as illustrative unless verified facts are supplied. "
                    "Do not invent product capabilities, customer results, certifications, "
                    "proof points, or performance claims. Mark unknowns and campaign ideas as "
                    "assumptions or items to validate."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }

    try:
        response = requests.post(
            f"{settings.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.api_key}"},
            json=request_body,
            timeout=settings.timeout_seconds,
        )
    except requests.RequestException as exc:
        raise LLMServiceError(f"Could not reach the configured LLM provider: {exc}") from exc

    if not response.ok:
        detail = response.text[:500].strip() or "No response details were returned."
        raise LLMServiceError(
            f"LLM provider returned HTTP {response.status_code}: {detail}"
        )

    try:
        body = response.json()
        content = body["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMServiceError("The LLM provider response did not contain a chat completion.") from exc

    if not isinstance(content, str) or not content.strip():
        raise LLMServiceError("The LLM provider returned an empty completion.")

    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", content.strip(), flags=re.IGNORECASE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMServiceError(
            "The LLM response was not valid JSON. Try again or use sample mode."
        ) from exc
