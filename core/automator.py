import os
import streamlit as st
from typing import Dict, Any
from core.generator import Generator
from core.reviewer import Reviewer

class Automator:
    def __init__(self, project_name: str = "default_project"):
        self.project_name = project_name
        self.generator = Generator(project_name=project_name)
        self.reviewer = Reviewer(project_name=project_name)

    def run_single_cycle(self, chapter_title: str, instruction: str, target_length: int = 5000) -> Dict[str, Any]:
        """
        초안 생성 -> 자동 검수 -> 자동 수정 -> 저장 -> 요약 갱신까지 한 번에 순차적으로 실행합니다.
        Streamlit UI(st.spinner 등)과 결합하여 현재 진행 상태를 화면에 표시할 수 있습니다.
        """
        result = {}

        # 1. 초안 생성
        with st.spinner(f"작가가 원고 초안을 집필 중입니다 (목표: {target_length}자 내외)... ☕"):
            draft = self.generator.create_chapter(instruction, target_length)
            result['draft'] = draft

        with st.spinner("생성된 초안을 마크다운 파일로 저장 중입니다... 💾"):
            draft_path = self.generator.save_markdown_document(
                filename_title=chapter_title + "_초안",
                content=draft,
                heading_title=chapter_title + " (초안)",
            )
            result['draft_path'] = draft_path

        # 2. 자동 검수
        with st.spinner("편집자가 원고를 꼼꼼히 검수하고 리포트를 작성 중입니다... 👓"):
            review_report = self.reviewer.review_chapter(draft)
            result['review_report'] = review_report

        with st.spinner("검수 리포트를 마크다운 파일로 저장 중입니다... 💾"):
            review_report_path = self.generator.save_markdown_document(
                filename_title=chapter_title + "_검수리포트",
                content=review_report,
            )
            result['review_report_path'] = review_report_path

        # 3. 자동 수정
        with st.spinner("작가가 피드백을 반영하여 원고를 완벽하게 고쳐 쓰는 중입니다... ✍️"):
            revised_draft = self.reviewer.revise_draft(draft, review_report)
            result['revised_draft'] = revised_draft

        # 4. 파일 저장
        with st.spinner("최종 수정본을 마크다운 파일로 저장 중입니다... 💾"):
            saved_path = self.generator.save_chapter(chapter_title, revised_draft)
            result['saved_path'] = saved_path

        # 5. 컨텍스트 요약 갱신
        with st.spinner("다음 회차를 위해 방금 저장한 내용을 컨텍스트에 요약하여 반영 중입니다 (필요시 자동 압축 🔄)..."):
            try:
                new_summary = self.generator.summarize_chapter(revised_draft)
                self.generator.ctx.update_summary(new_summary, generator_instance=self.generator)
                result['new_summary'] = new_summary
            except Exception as exc:
                result['summary_error'] = str(exc)
            
        return result
