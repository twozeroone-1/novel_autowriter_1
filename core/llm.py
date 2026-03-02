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
        
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return f"초안 생성 중 오류가 발생했습니다: {str(e)}"
