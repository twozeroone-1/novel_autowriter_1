import os
from core.llm import generate_text
from core.context import ContextManager

class Reviewer:
    def __init__(self, project_name: str = "default_project"):
        self.ctx = ContextManager(project_name=project_name)
        
    def review_chapter(self, draft_content: str) -> str:
        """초안 원고가 기존 설정에 맞는지, 오류나 어색한 부분이 없는지 검토합니다."""
        
        world_ctx = self.ctx.get_worldview_context()
        char_ctx = self.ctx.get_character_context()
        
        prompt = f"""당신은 탑티어 웹소설 편집자(PD)이자 교정교열 전문가입니다.
다음은 작가가 방금 넘긴 소설 원고 초안과 이 소설의 기본 세계관/캐릭터 설정입니다.

{world_ctx}

{char_ctx}

[원고 초안]
{draft_content}

[검수 요청사항]
위의 초안을 읽고 다음 세 가지 기준에 따라 냉철하게 검토해 주세요.
1. **설정 충돌**: 캐릭터의 특징, 말투, 세계관 규칙(마법, 기술, 배경 등)에 어긋나는 부분이 없는가?
2. **문맥 및 흐름**: 이전 사건과 자연스럽게 이어지는가? 갑작스러운 전개나 개연성 없는 묘사가 없는가? (건조하지만 흡입력 있는 문체에 어긋나지 않는지 포함)
3. **오탈자 및 문장 구조**: 어색한 문장 구조, 반복되는 단어/표현, 오탈자가 없는가?

검토 결과를 리포트 형식으로 작성하고, 수정이 필요한 부분들에 대한 구체적인 개선안을 제시하세요.
"""
        print(">> 검수 리포트 작성 중...")
        result = generate_text(prompt, system_instruction="너는 예리한 통찰력과 경험을 가진 웹소설 담당 편집자야.")
        return result

    def revise_draft(self, draft_content: str, review_report: str) -> str:
        """검수 리포트를 바탕으로 초안을 수정하여 수정본을 생성합니다."""
        
        world_ctx = self.ctx.get_worldview_context()
        char_ctx = self.ctx.get_character_context()
        
        prompt = f"""당신은 탑티어 웹소설 작가입니다. 편집자의 검수 리포트를 반영하여 원고 초안을 훌륭하게 수정해 주세요.

{world_ctx}

{char_ctx}

[원고 초안]
{draft_content}

[편집자 검수 리포트]
{review_report}

위의 검수 리포트에서 지적된 문제점(설정 충돌, 문맥, 오탈자 등)을 모두 고려하여 초안을 자연스럽게 수정하세요. 제목은 생략하고 수정된 본문만 출력하세요.
"""
        print(">> 수정본 작성 중...")
        result = generate_text(prompt, system_instruction="너는 편집자의 피드백을 수용하여 원고를 완벽하게 고쳐 쓰는 탑티어 웹소설 작가야.")
        return result
