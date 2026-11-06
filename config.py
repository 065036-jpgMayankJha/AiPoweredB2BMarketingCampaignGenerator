"""Environment-backed configuration for the marketing content application."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    provider: str
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int


def load_settings() -> Settings:
    """Load and validate settings without requiring a key for sample mode."""
    try:
        timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    except ValueError as exc:
        raise ValueError("LLM_TIMEOUT_SECONDS must be a whole number.") from exc

    if timeout_seconds < 1:
        raise ValueError("LLM_TIMEOUT_SECONDS must be greater than zero.")

    return Settings(
        provider=os.getenv("LLM_PROVIDER", "openai_compatible").strip().lower(),
        api_key=os.getenv("LLM_API_KEY", "").strip(),
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/"),
        model=os.getenv("LLM_MODEL", "gpt-4o-mini").strip(),
        timeout_seconds=timeout_seconds,
    )
