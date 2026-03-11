from contextlib import nullcontext
from typing import Callable, Dict, Any
from core.generator import Generator
from core.reviewer import Reviewer

class Automator:
    def __init__(
        self,
        project_name: str = "default_project",
        generator: Generator | None = None,
        reviewer: Reviewer | None = None,
    ):
        self.project_name = project_name
        self.generator = generator or Generator(project_name=project_name)
        self.reviewer = reviewer or Reviewer(project_name=project_name)

    def run_single_cycle(
        self,
        chapter_title: str,
        instruction: str,
        target_length: int = 5000,
        step_context: Callable[[str], Any] | None = None,
    ) -> Dict[str, Any]:
        """
        초안 생성 -> 자동 검수 -> 자동 수정 -> 저장 -> 요약 갱신까지 한 번에 순차적으로 실행합니다.
        step_context에는 st.spinner 같은 컨텍스트 매니저 팩토리를 넘길 수 있습니다.
        """
        result = {}
        progress = step_context or (lambda _message: nullcontext())

        # 1. 초안 생성
        with progress(f"작가가 원고 초안을 집필 중입니다 (목표: {target_length}자 내외)... ☕"):
            draft = self.generator.create_chapter(instruction, target_length)
            result['draft'] = draft

        with progress("생성된 초안을 마크다운 파일로 저장 중입니다... 💾"):
            draft_path = self.generator.save_markdown_document(
                filename_title=chapter_title + "_초안",
                content=draft,
                heading_title=chapter_title + " (초안)",
            )
            result['draft_path'] = draft_path

        # 2. 자동 검수
        with progress("편집자가 원고를 꼼꼼히 검수하고 리포트를 작성 중입니다... 👓"):
            review_report = self.reviewer.review_chapter(draft)
            result['review_report'] = review_report

        with progress("검수 리포트를 마크다운 파일로 저장 중입니다... 💾"):
            review_report_path = self.generator.save_markdown_document(
                filename_title=chapter_title + "_검수리포트",
                content=review_report,
            )
            result['review_report_path'] = review_report_path

        # 3. 자동 수정
        with progress("작가가 피드백을 반영하여 원고를 완벽하게 고쳐 쓰는 중입니다... ✍️"):
            revised_draft = self.reviewer.revise_draft(draft, review_report)
            result['revised_draft'] = revised_draft

        # 4. 파일 저장
        with progress("최종 수정본을 마크다운 파일로 저장 중입니다... 💾"):
            saved_path = self.generator.save_chapter(chapter_title, revised_draft)
            result['saved_path'] = saved_path

        # 5. 컨텍스트 요약 갱신
        with progress("다음 회차를 위해 방금 저장한 내용을 컨텍스트에 요약하여 반영 중입니다 (필요시 자동 압축 🔄)..."):
            try:
                new_summary = self.generator.summarize_and_update_context(revised_draft)
                result['new_summary'] = new_summary
            except Exception as exc:
                result['summary_error'] = str(exc)
            
        return result
