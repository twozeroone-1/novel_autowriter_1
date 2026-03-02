import os
from datetime import datetime
from pathlib import Path
from core.llm import generate_text
from core.context import ContextManager

class Generator:
    def __init__(self, project_name: str = "default_project"):
        # ContextManager에 project_name 주입
        self.ctx = ContextManager(project_name=project_name)
        # ContextManager가 생성한 동적 경로를 참조
        self.chapters_dir = self.ctx.data_dir / "chapters"
        self.chapters_dir.mkdir(parents=True, exist_ok=True)
        
    def create_chapter(self, instruction: str, length_goal: int = 5000) -> str:
        """컨텍스트를 모아 LLM에 전달하고 생성된 원고 텍스트를 반환합니다."""
        prompt = self.ctx.build_generation_prompt(instruction, length_goal)
        print(f">> [{self.ctx.project_name}] 작품 생성 요청 중...")
        system_instruction = f"너는 사용자가 제시한 목표 분량(공백 포함 약 {length_goal}자 내외)을 엄격하게 지키으면서 기승전결이 있는 전개를 작성하는 프로 웹소설 작가야."
        result = generate_text(prompt, system_instruction=system_instruction)
        return result
        
    def save_chapter(self, title: str, content: str) -> str:
        """생성된 회차를 마크다운 파일로 저장합니다."""
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        if not safe_title:
            safe_title = "연재_" + datetime.now().strftime("%Y%m%d%H%M%S")
            
        filename = f"{safe_title}.md"
        # 동적 디렉토리에 저장
        filepath = self.chapters_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(content)
            
        return str(filepath)
        
    def summarize_chapter(self, chapter_content: str) -> str:
        """작성된 회차의 핵심 내용을 짧게 요약합니다."""
        prompt = f"""당신은 웹소설 편집자입니다. 방금 작성된 다음 원고를 읽고, 이후 스토리 전개에 참고할 수 있도록 주요 사건과 인물의 감정선/변화를 3~4줄로 핵심만 요약해 주세요.

[원고 내용]
{chapter_content}

요약:"""
        print(">> 회차 요약 생성 중...")
        result = generate_text(prompt, system_instruction="너는 줄거리 파악과 요약에 능통한 편집자야.")
        return result.strip()

    def elaborate_worldview(self, draft_content: str) -> str:
        """사용자가 입력한 세계관 초안을 바탕으로 AI가 구체적인 세계관을 생성합니다."""
        prompt = f"""당신은 탑티어 웹소설 세계관 기획자입니다.
작가가 구상한 다음 '세계관 초안'을 바탕으로, 독자들이 흥미를 느낄 만한 구체적이고 매력적인 세계관 설정(배경, 마법/기연/시스템 체계, 주요 세력이나 갈등 요소 등)으로 디테일을 더해주세요.

[세계관 초안]
{draft_content}

너무 장황하지 않게 3~4문단 정도로 핵심 설정 위주로 정리해 주세요."""
        print(">> 세계관 구체화 중...")
        result = generate_text(prompt, system_instruction="너는 상상력이 풍부하고 체계적인 세계관 기획자야.")
        return result.strip()

    def generate_tone(self, worldview: str) -> str:
        """세계관을 바탕으로 어울리는 소설 문체 및 분위기를 제안합니다."""
        prompt = f"""당신은 탑티어 웹소설 기획자입니다.
다음 구축된 세계관을 바탕으로 이 소설에 가장 잘 어울릴법한 '문체 및 분위기 지침(Tone & Manner)'을 2~3문장으로 작성해 주세요. 
(예시: 건조하고 속도감 있는 문체. 주인공의 냉소적인 독백을 중심으로 사건이 전개됨.)

[세계관]
{worldview}"""
        print(">> 문체 및 분위기 제안 중...")
        result = generate_text(prompt, system_instruction="너는 작품에 색깔을 입히는 웹소설 기획자야.")
        return result.strip()
        
    def generate_characters(self, worldview: str) -> str:
        """세계관을 바탕으로 어울리는 주요 등장인물들의 JSON 배열을 추출 및 생성합니다."""
        prompt = f"""당신은 탑티어 웹소설 기획자입니다.
다음 세계관 텍스트를 읽고, 텍스트 내에 실제로 언급되거나 암시된 모든 주요 등장인물을 추출 및 기획해 주세요. (인원수 제한 없음)
주의: 반드시 텍스트에 존재하는 인물만 추출해야 하며, 절대 새로운 인물을 창작하거나 지어내지 마세요.
반드시 아래의 JSON 배열 포맷으로만 출력해야 합니다. 추가 설명이나 마크다운 백틱(```) 없이 순수 JSON 텍스트 배열만 반환하세요.

포맷 예시:
[
  {{
    "id": "char_001",
    "name": "등장인물 이름",
    "role": "주인공/조력자 등",
    "description": "성격 요약 (1문장)",
    "traits": ["강함", "과묵함"]
  }}
]

[세계관]
{worldview}"""
        print(">> 캐릭터 설정 생성 중...")
        result = generate_text(prompt, system_instruction="너는 매력적인 캐릭터를 짜는 웹소설 기획자야. JSON 형식으로만 답해.")
        
        cleaned = result.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
            
        return cleaned.strip()
