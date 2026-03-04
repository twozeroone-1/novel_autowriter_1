import os
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)
load_dotenv(override=True)

class LLMError(Exception):
    """LLM 호출 계층의 공통 예외."""


class LLMConfigError(LLMError):
    """환경 변수/설정 오류."""


class LLMServiceError(LLMError):
    """외부 API 호출 실패."""


def _classify_llm_error(error: Exception) -> tuple[str, str]:
    text = str(error)
    lower = text.lower()

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


def generate_text(prompt: str, system_instruction: Optional[str] = None, max_output_tokens: Optional[int] = None) -> str:
    """Gemini 모델을 호출하여 프롬프트에 대한 텍스트 응답을 생성합니다."""
    
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
        
    # 복수 키 지원: 쉼표로 구분된 키들을 리스트로 분리
    api_keys = [k.strip() for k in api_key_env.split(",") if k.strip()]
    
    if not api_keys:
        raise LLMConfigError("유효한 GOOGLE_API_KEY를 찾을 수 없습니다.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    last_error = None
    last_error_kind = "unknown"
    last_user_message = "LLM API 호출 실패"
    
    for idx, api_key in enumerate(api_keys):
        try:
            # 기본 네트워크 옵션을 사용해 SDK 내부 재시도/연결 전략을 활용
            client = genai.Client(api_key=api_key)
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            if not response.text:
                raise LLMServiceError("모델 응답 본문이 비어 있습니다.")
            # 성공하면 즉시 텍스트 반환
            return response.text
            
        except Exception as e:
            kind, user_message = _classify_llm_error(e)
            # 실패하면 콘솔에 로그를 남기고 다음 키로 넘어감
            print(f"[Fallback] API Key {idx + 1}/{len(api_keys)} failed: {e}")
            last_error = e
            last_error_kind = kind
            last_user_message = user_message
            continue
            
    # 모든 키가 실패했을 때
    print(f"Error calling Gemini API: All provided keys failed. Last error: {last_error}")
    if last_error_kind == "auth":
        raise LLMConfigError(f"{last_user_message} (마지막 오류: {str(last_error)})") from last_error
    raise LLMServiceError(f"{last_user_message} (마지막 오류: {str(last_error)})") from last_error
