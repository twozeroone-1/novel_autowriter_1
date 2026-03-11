from contextlib import nullcontext
from typing import Any, Callable

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
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        progress = step_context or (lambda _message: nullcontext())

        with progress(f"초안을 생성하는 중입니다 (목표: {target_length}자 내외)..."):
            draft = self.generator.create_chapter(instruction, target_length)
            result["draft"] = draft

        with progress("초안을 마크다운 파일로 저장하는 중입니다..."):
            result["draft_path"] = self.generator.save_markdown_document(
                filename_title=chapter_title + "_초안",
                content=draft,
                heading_title=chapter_title + " (초안)",
            )

        with progress("검수 리포트를 생성하는 중입니다..."):
            review_report = self.reviewer.review_chapter(draft)
            result["review_report"] = review_report

        with progress("검수 리포트를 저장하는 중입니다..."):
            result["review_report_path"] = self.generator.save_markdown_document(
                filename_title=chapter_title + "_검수리포트",
                content=review_report,
            )

        with progress("검수 피드백을 반영해 수정본을 만드는 중입니다..."):
            revised_draft = self.reviewer.revise_draft(draft, review_report)
            result["revised_draft"] = revised_draft

        with progress("수정본을 저장하는 중입니다..."):
            result["saved_path"] = self.generator.save_chapter(chapter_title, revised_draft)

        with progress("다음 회차용 STATE/PREVIOUS SUMMARY 제안을 만드는 중입니다..."):
            result.update(self.generator.build_context_suggestions(revised_draft))

        return result

    def apply_context_updates(
        self,
        *,
        state: str | None = None,
        summary_of_previous: str | None = None,
    ) -> dict[str, Any]:
        return self.generator.ctx.apply_context_updates(
            state=state,
            summary_of_previous=summary_of_previous,
        )
