"""OpenAI-compatible chat-completions client with a deterministic demo path."""

from copy import deepcopy
from typing import Any

import requests

from config import load_settings
from modules.json_utils import JSONResponseError, parse_json_response
from modules.structured_outputs import LIST_OUTPUT_SCHEMAS, validate_structured_output


class LLMError(RuntimeError):
    """Base class for actionable generation errors."""


class LLMConfigurationError(LLMError):
    """Raised when live generation is not configured correctly."""


class LLMServiceError(LLMError):
    """Raised when the provider request or response is unusable."""


def generate_json(
    prompt: str,
    sample: Any,
    use_sample_mode: bool,
    schema_name: str | None = None,
) -> Any:
    """Return validated provider JSON, or a validated fresh copy of the sample."""
    if use_sample_mode:
        sample_copy = deepcopy(sample)
        if schema_name:
            try:
                validate_structured_output(sample_copy, schema_name)
            except ValueError as exc:
                raise LLMServiceError(f"The configured sample output is invalid: {exc}") from exc
        return sample_copy

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

    repair_prompt = prompt
    object_json_mode = schema_name not in LIST_OUTPUT_SCHEMAS
    for attempt in range(2):
        content = _request_completion(
            repair_prompt,
            settings.base_url,
            settings.model,
            settings.api_key,
            settings.timeout_seconds,
            object_json_mode,
            temperature=0.6 if attempt == 0 else 0.2,
        )
        try:
            return parse_json_response(content, schema_name)
        except JSONResponseError as exc:
            if attempt == 1:
                raise LLMServiceError(
                    "The LLM response remained invalid after one JSON repair attempt: "
                    f"{exc}"
                ) from exc
            repair_prompt = (
                f"{prompt}\n\nJSON REPAIR REQUEST\n"
                f"The previous response failed parsing or validation: {exc}\n"
                "Return a corrected response that matches the required schema exactly. "
                "Do not omit required fields, use null, or add explanatory text outside JSON. "
                "Do not invent facts; use an explicit assumption or validation note when evidence "
                "is unavailable."
            )
    raise LLMServiceError("The LLM response could not be validated.")


def _request_completion(
    prompt: str,
    base_url: str,
    model: str,
    api_key: str,
    timeout_seconds: int,
    object_json_mode: bool,
    temperature: float,
) -> str:
    request_body: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
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
    if object_json_mode:
        request_body["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=request_body,
            timeout=timeout_seconds,
        )
    except requests.RequestException as exc:
        raise LLMServiceError(f"Could not reach the configured LLM provider: {exc}") from exc

    if not response.ok:
        detail = response.text[:500].strip() or "No response details were returned."
        raise LLMServiceError(f"LLM provider returned HTTP {response.status_code}: {detail}")

    try:
        body = response.json()
        content = body["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMServiceError(
            "The LLM provider response did not contain a chat completion."
        ) from exc

    if not isinstance(content, str) or not content.strip():
        raise LLMServiceError("The LLM provider returned an empty completion.")
    return content
