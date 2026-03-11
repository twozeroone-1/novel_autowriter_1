import json
import os
from typing import Any, Optional

from core.llm_backend import (
    ApiBackendError,
    CliAuthError,
    CliInvocationError,
    CliUnavailableError,
    LlmRequest,
    _should_retry_on_error,
    generate_via_backend_mode,
)


class LLMError(RuntimeError):
    """Raised when the configured LLM backend cannot produce usable text."""


def _extract_first_json_value(raw_text: str, expected_type: type | None = None) -> Optional[Any]:
    decoder = json.JSONDecoder()
    starts = [idx for idx, ch in enumerate(raw_text) if ch in "[{"]
    for start in starts:
        fragment = raw_text[start:]
        try:
            value, _ = decoder.raw_decode(fragment)
        except json.JSONDecodeError:
            continue

        if expected_type is not None and not isinstance(value, expected_type):
            continue
        return value

    return None


def _extract_last_json_object(raw_text: str) -> Optional[dict]:
    decoder = json.JSONDecoder()
    starts = [idx for idx, ch in enumerate(raw_text) if ch == "{"]
    fallback: Optional[dict] = None
    for start in starts:
        fragment = raw_text[start:]
        try:
            obj, _ = decoder.raw_decode(fragment)
        except Exception:
            continue

        if isinstance(obj, dict):
            if "response" in obj:
                return obj
            fallback = obj

    return fallback


def generate_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.7,
) -> str:
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    backend_mode = os.getenv("GEMINI_BACKEND", "auto")
    request = LlmRequest(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=temperature,
        model_name=model_name,
    )

    try:
        result = generate_via_backend_mode(backend_mode, request)
    except (ApiBackendError, CliUnavailableError, CliAuthError, CliInvocationError) as exc:
        raise LLMError(str(exc)) from exc

    return result.text
