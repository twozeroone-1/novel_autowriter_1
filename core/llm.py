import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GEMINI_OAUTH_CREDS_PATH = Path.home() / ".gemini" / "oauth_creds.json"
SUPPORTED_PROVIDERS = {"google_api", "gemini_cli_oauth"}
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)
load_dotenv(override=True)

class LLMError(Exception):
    """LLM 호출 계층의 공통 예외."""


class LLMConfigError(LLMError):
    """환경 변수/설정 오류."""


class LLMServiceError(LLMError):
    """외부 API 호출 실패."""


def get_llm_provider() -> str:
    provider = os.getenv("LLM_PROVIDER", "google_api").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        return "google_api"
    return provider


def get_llm_readiness(provider: Optional[str] = None) -> tuple[bool, str]:
    selected = provider or get_llm_provider()
    if selected == "gemini_cli_oauth":
        if not shutil.which("gemini"):
            return (False, "Gemini CLI를 찾을 수 없습니다. `gemini` 설치 후 다시 시도해 주세요.")
        if not GEMINI_OAUTH_CREDS_PATH.exists():
            return (False, "Gemini CLI OAuth 인증이 필요합니다. 터미널에서 `gemini` 실행 후 로그인해 주세요.")
        return (True, "Gemini CLI OAuth 모드 준비 완료")

    api_key_env = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key_env:
        load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)
        api_key_env = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key_env:
        return (False, "GOOGLE_API_KEY가 설정되지 않았습니다. 사이드바에서 API 키를 설정해 주세요.")
    return (True, "Google API 키 모드 준비 완료")


def _classify_llm_error(error: Exception, provider: str = "google_api") -> tuple[str, str]:
    text = str(error)
    lower = text.lower()

    if provider == "gemini_cli_oauth":
        if isinstance(error, FileNotFoundError):
            return ("cli_missing", "Gemini CLI를 찾을 수 없습니다. 설치 상태를 확인해 주세요.")
        if "login" in lower or "oauth" in lower or "unauthorized" in lower:
            return ("auth", "Gemini CLI OAuth 인증이 필요합니다. 터미널에서 `gemini` 로그인 후 재시도해 주세요.")

    if (
        "network is unreachable" in lower
        or "no route to host" in lower
        or "errno 101" in lower
        or "failed to establish a new connection" in lower
    ):
        return ("network", "네트워크 연결 실패: 인터넷/프록시/방화벽 설정을 확인해 주세요.")
    if "name or service not known" in lower or "temporary failure in name resolution" in lower:
        return ("dns", "DNS 해석 실패: 네트워크 DNS 설정을 확인해 주세요.")
    if "timed out" in lower or "timeout" in lower:
        return ("timeout", "요청 시간 초과: 잠시 후 다시 시도해 주세요.")
    if "503" in lower or "service unavailable" in lower:
        return ("server_busy", "서버 과열(503): 잠시 후 다시 시도해 주세요.")
    if "429" in lower or "resource_exhausted" in lower or "quota" in lower:
        return ("quota", "요청 한도(429) 초과: 다른 API 키 또는 잠시 후 재시도가 필요합니다.")
    if "401" in lower or "403" in lower or "invalid api key" in lower or "permission denied" in lower:
        return ("auth", "인증/권한 오류: API 키 또는 모델 접근 권한을 확인해 주세요.")
    return ("unknown", f"LLM API 호출 실패: {text}")


def _extract_last_json_object(raw_text: str) -> Optional[dict]:
    decoder = json.JSONDecoder()
    starts = [idx for idx, ch in enumerate(raw_text) if ch == "{"]
    fallback: Optional[dict] = None
    for start in starts:
        fragment = raw_text[start:]
        try:
            obj, _ = decoder.raw_decode(fragment)
            if isinstance(obj, dict):
                if "response" in obj:
                    return obj
                fallback = obj
        except Exception:
            continue
    return fallback


def _generate_with_google_api(
    prompt: str,
    system_instruction: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
) -> str:
    config_args = {"temperature": 0.7}
    if max_output_tokens is not None:
        config_args["max_output_tokens"] = max_output_tokens

    config = types.GenerateContentConfig(**config_args)

    if system_instruction:
        config.system_instruction = system_instruction

    api_key_env = os.getenv("GOOGLE_API_KEY", "")
    if not api_key_env.strip():
        # 실행 cwd가 프로젝트 루트가 아닐 때를 대비한 보강 로드
        load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)
        api_key_env = os.getenv("GOOGLE_API_KEY", "")
    if not api_key_env.strip():
        raise LLMConfigError("GOOGLE_API_KEY가 설정되지 않았습니다. 설정 탭에서 API 키를 입력해주세요.")

    api_keys = [k.strip() for k in api_key_env.split(",") if k.strip()]
    if not api_keys:
        raise LLMConfigError("유효한 GOOGLE_API_KEY를 찾을 수 없습니다.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    last_error = None
    last_error_kind = "unknown"
    last_user_message = "LLM API 호출 실패"

    for idx, api_key in enumerate(api_keys):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            if not response.text:
                raise LLMServiceError("모델 응답 본문이 비어 있습니다.")
            return response.text
        except Exception as e:
            kind, user_message = _classify_llm_error(e, provider="google_api")
            print(f"[Fallback] API Key {idx + 1}/{len(api_keys)} failed: {e}")
            last_error = e
            last_error_kind = kind
            last_user_message = user_message
            continue

    print(f"Error calling Gemini API: All provided keys failed. Last error: {last_error}")
    if last_error_kind == "auth":
        raise LLMConfigError(f"{last_user_message} (마지막 오류: {str(last_error)})") from last_error
    raise LLMServiceError(f"{last_user_message} (마지막 오류: {str(last_error)})") from last_error


def _generate_with_gemini_cli(
    prompt: str,
    system_instruction: Optional[str] = None,
    max_output_tokens: Optional[int] = None,
) -> str:
    ready, message = get_llm_readiness("gemini_cli_oauth")
    if not ready:
        raise LLMConfigError(message)

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    final_prompt = prompt
    if system_instruction:
        final_prompt = (
            "[SYSTEM INSTRUCTION]\n"
            f"{system_instruction}\n\n"
            "[USER PROMPT]\n"
            f"{prompt}"
        )
    if max_output_tokens is not None:
        final_prompt += f"\n\n[OUTPUT LIMIT]\n가능하면 {max_output_tokens} 토큰 이내로 답변하세요."

    try:
        proc = subprocess.run(
            ["gemini", "-p", final_prompt, "-m", model_name, "-o", "json", "-y"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    except Exception as e:
        _, user_message = _classify_llm_error(e, provider="gemini_cli_oauth")
        raise LLMServiceError(f"{user_message} (마지막 오류: {str(e)})") from e

    if proc.returncode != 0:
        raw_error = (proc.stderr or proc.stdout or "").strip() or f"exit code {proc.returncode}"
        kind, user_message = _classify_llm_error(Exception(raw_error), provider="gemini_cli_oauth")
        if kind == "auth":
            raise LLMConfigError(f"{user_message} (마지막 오류: {raw_error})")
        raise LLMServiceError(f"{user_message} (마지막 오류: {raw_error})")

    parsed = _extract_last_json_object(proc.stdout or "")
    if not parsed:
        preview = (proc.stdout or "").strip()
        preview = preview[-300:] if preview else "empty output"
        raise LLMServiceError(f"Gemini CLI 응답 파싱 실패: JSON 출력이 없습니다. (출력 일부: {preview})")

    response_text = str(parsed.get("response", "")).strip()
    if not response_text:
        raise LLMServiceError("Gemini CLI 응답 본문이 비어 있습니다.")
    return response_text


def generate_text(prompt: str, system_instruction: Optional[str] = None, max_output_tokens: Optional[int] = None) -> str:
    """Gemini 모델을 호출하여 프롬프트에 대한 텍스트 응답을 생성합니다."""
    provider = get_llm_provider()
    if provider == "gemini_cli_oauth":
        return _generate_with_gemini_cli(
            prompt=prompt,
            system_instruction=system_instruction,
            max_output_tokens=max_output_tokens,
        )
    return _generate_with_google_api(
        prompt=prompt,
        system_instruction=system_instruction,
        max_output_tokens=max_output_tokens,
    )
