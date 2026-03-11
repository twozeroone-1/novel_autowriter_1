import json
import os
import inspect
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Optional

from core.diagnostics import append_llm_run
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


FEATURE_NAME_BY_CALLER = {
    "create_chapter": "chapter_generate",
    "summarize_chapter": "chapter_summary",
    "compress_history_summary": "history_compress",
    "elaborate_worldview": "worldview_expand",
    "compress_worldview": "worldview_compress",
    "structure_style_guide": "style_structure",
    "structure_continuity": "continuity_structure",
    "summarize_state": "state_summary",
    "generate_tone": "tone_suggest",
    "generate_characters": "character_extract",
    "review_chapter": "review",
    "revise_draft": "revise",
    "suggest_ideas": "idea",
    "build_macro_plot": "plot",
}


def _append_diagnostics_record(project_name: str | None, record: dict) -> None:
    if not project_name:
        return
    try:
        append_llm_run(project_name, record)
    except Exception:
        pass


def _infer_logging_context(
    project_name: str | None,
    feature: str,
) -> tuple[str | None, str]:
    inferred_project_name = project_name
    inferred_feature = feature

    frame = inspect.currentframe()
    try:
        caller = frame.f_back.f_back if frame and frame.f_back else None
        if caller is None:
            return inferred_project_name, inferred_feature

        if inferred_feature == "generic":
            inferred_feature = FEATURE_NAME_BY_CALLER.get(caller.f_code.co_name, inferred_feature)

        if inferred_project_name is not None:
            return inferred_project_name, inferred_feature

        owner = caller.f_locals.get("self")
        if owner is None:
            return None, inferred_feature

        ctx = getattr(owner, "ctx", None)
        if ctx is not None:
            inferred_project_name = getattr(ctx, "project_name", None)
        if inferred_project_name is None:
            inferred_project_name = getattr(owner, "project_name", None)
        return inferred_project_name, inferred_feature
    finally:
        del frame


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
    *,
    project_name: str | None = None,
    feature: str = "generic",
) -> str:
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    backend_mode = os.getenv("GEMINI_BACKEND", "auto")
    project_name, feature = _infer_logging_context(project_name, feature)
    request = LlmRequest(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=temperature,
        model_name=model_name,
    )
    started_at = perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        result = generate_via_backend_mode(backend_mode, request)
    except (ApiBackendError, CliUnavailableError, CliAuthError, CliInvocationError) as exc:
        _append_diagnostics_record(
            project_name,
            {
                "timestamp": timestamp,
                "project": project_name,
                "feature": feature,
                "requested_backend": backend_mode,
                "actual_backend": None,
                "fallback_note": "",
                "model": model_name,
                "success": False,
                "duration_ms": int((perf_counter() - started_at) * 1000),
                "prompt_text": prompt,
                "response_text": "",
                "stderr_text": "",
                "error_text": str(exc),
            },
        )
        raise LLMError(str(exc)) from exc

    _append_diagnostics_record(
        project_name,
        {
            "timestamp": timestamp,
            "project": project_name,
            "feature": feature,
            "requested_backend": backend_mode,
            "actual_backend": result.backend_used,
            "fallback_note": "\n".join(result.diagnostics),
            "model": model_name,
            "success": True,
            "duration_ms": int((perf_counter() - started_at) * 1000),
            "prompt_text": prompt,
            "response_text": result.text,
            "stderr_text": result.stderr_text,
            "error_text": "",
        },
    )

    return result.text
