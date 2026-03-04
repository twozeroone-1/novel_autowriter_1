import os
from typing import Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(override=True)

def generate_text(prompt: str, system_instruction: Optional[str] = None) -> str:
    """Gemini 모델을 호출하여 프롬프트에 대한 텍스트 응답을 생성합니다."""
    
    config = types.GenerateContentConfig(
        temperature=0.7,
    )
    
    if system_instruction:
        config.system_instruction = system_instruction
        
    api_key_env = os.getenv("GOOGLE_API_KEY", "")
    if not api_key_env.strip():
        return "오류: GOOGLE_API_KEY가 설정되지 않았습니다. 설정 탭에서 API 키를 입력해주세요."
        
    # 복수 키 지원: 쉼표로 구분된 키들을 리스트로 분리
    api_keys = [k.strip() for k in api_key_env.split(",") if k.strip()]
    
    if not api_keys:
        return "오류: 유효한 GOOGLE_API_KEY를 찾을 수 없습니다."

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
            # 성공하면 즉시 텍스트 반환
            return response.text
            
        except Exception as e:
            # 실패하면 콘솔에 로그를 남기고 다음 키로 넘어감
            print(f"[Fallback] API Key {idx + 1}/{len(api_keys)} failed: {e}")
            last_error = e
            continue
            
    # 모든 키가 실패했을 때
    print(f"Error calling Gemini API: All provided keys failed. Last error: {last_error}")
    return f"초안 생성 중 오류가 발생했습니다 (모든 API 키 연결 시도 실패): {str(last_error)}"
