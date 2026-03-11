import json
import os
from typing import Any, Optional
from core.api_key_store import load_secure_api_key_into_environment

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False

try:
    from google import genai
    from google.genai import types
    from google.genai import errors as genai_errors
except ModuleNotFoundError:
    genai = None
    types = None
    genai_errors = None

try:
    import httpx
except ModuleNotFoundError:
    httpx = None

load_dotenv(override=True)

class LLMError(RuntimeError):
    """Raised when the Gemini client cannot produce usable text."""


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


def _should_retry_on_error(exc: Exception) -> bool:
    if genai_errors is not None and isinstance(exc, genai_errors.APIError):
        if isinstance(exc, genai_errors.ServerError):
            return True

        retryable_codes = {408, 429, 500, 502, 503, 504}
        retryable_statuses = {
            "DEADLINE_EXCEEDED",
            "RESOURCE_EXHAUSTED",
            "UNAVAILABLE",
        }
        error_code = getattr(exc, "code", None)
        error_status = str(getattr(exc, "status", "") or "").upper()
        return error_code in retryable_codes or error_status in retryable_statuses

    if httpx is not None and isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
        return True

    message = str(exc).lower()
    retryable_markers = (
        "connection reset",
        "deadline exceeded",
        "quota",
        "rate limit",
        "resource exhausted",
        "service unavailable",
        "temporarily unavailable",
        "timeout",
        "timed out",
        "unavailable",
    )

    fallback_type_names = {
        "DeadlineExceeded",
        "GoogleAPICallError",
        "ResourceExhausted",
        "RetryError",
        "ServiceUnavailable",
        "TooManyRequests",
        "TransportError",
    }
    type_name = exc.__class__.__name__
    module_name = exc.__class__.__module__.lower()
    if type_name not in fallback_type_names and not module_name.startswith(("google.", "httpx", "httpcore")):
        return False

    return any(marker in message for marker in retryable_markers)


def generate_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.7,
) -> str:
    """Gemini 모델을 호출하여 프롬프트에 대한 텍스트 응답을 생성합니다."""
    if genai is None or types is None:
        raise LLMError("google-genai 패키지가 설치되지 않았습니다. `pip install -r requirements.txt` 후 다시 시도해주세요.")
    
    config = types.GenerateContentConfig(
        temperature=temperature,
    )
    
    if system_instruction:
        config.system_instruction = system_instruction

    load_secure_api_key_into_environment()
    api_key_env = os.getenv("GOOGLE_API_KEY", "")
    if not api_key_env.strip():
        raise LLMError("GOOGLE_API_KEY가 설정되지 않았습니다. 설정 탭에서 API 키를 입력해주세요.")
        
    # 복수 키 지원: 쉼표로 구분된 키들을 리스트로 분리
    api_keys = [k.strip() for k in api_key_env.split(",") if k.strip()]
    
    if not api_keys:
        raise LLMError("유효한 GOOGLE_API_KEY를 찾을 수 없습니다.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    last_error = None
    
    for idx, api_key in enumerate(api_keys):
        try:
            client = genai.Client(api_key=api_key)
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            text = getattr(response, "text", None)
            if not text or not text.strip():
                raise LLMError("모델이 비어 있는 응답을 반환했습니다.")

            # 성공하면 즉시 텍스트 반환
            return text
        except MemoryError:
            raise
        except Exception as e:
            if not _should_retry_on_error(e):
                raise LLMError(f"Gemini 호출에 실패했습니다. 사용 중인 모델: {model_name}. 오류: {e}") from e

            print(f"[Fallback] API Key {idx + 1}/{len(api_keys)} failed: {e}")
            last_error = e
            continue
            
    # 모든 키가 실패했을 때
    print(f"Error calling Gemini API: All provided keys failed. Last error: {last_error}")
    raise LLMError(f"Gemini 호출에 실패했습니다. 사용 중인 모델: {model_name}. 마지막 오류: {last_error}")
