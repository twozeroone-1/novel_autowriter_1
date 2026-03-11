import unittest

from core.automator import Automator


class FakeGenerator:
    def __init__(self):
        self.calls = []

    def create_chapter(self, instruction: str, target_length: int) -> str:
        self.calls.append(("create_chapter", instruction, target_length))
        return "draft text"

    def save_markdown_document(self, filename_title: str, content: str, heading_title: str | None = None) -> str:
        self.calls.append(("save_markdown_document", filename_title, content, heading_title))
        return f"/tmp/{filename_title}.md"

    def save_chapter(self, title: str, content: str) -> str:
        self.calls.append(("save_chapter", title, content))
        return f"/tmp/{title}.md"

    def summarize_and_update_context(self, chapter_content: str) -> str:
        self.calls.append(("summarize_and_update_context", chapter_content))
        return "summary text"


class FakeReviewer:
    def __init__(self):
        self.calls = []

    def review_chapter(self, draft: str) -> str:
        self.calls.append(("review_chapter", draft))
        return "review report"

    def revise_draft(self, draft: str, report: str) -> str:
        self.calls.append(("revise_draft", draft, report))
        return "revised draft"


class RecordingStepContext:
    def __init__(self, messages: list[str], message: str):
        self.messages = messages
        self.message = message

    def __enter__(self):
        self.messages.append(self.message)
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestAutomator(unittest.TestCase):
    def test_run_single_cycle_uses_injected_services_and_reports_progress(self):
        generator = FakeGenerator()
        reviewer = FakeReviewer()
        automator = Automator(project_name="sample", generator=generator, reviewer=reviewer)
        messages: list[str] = []

        result = automator.run_single_cycle(
            chapter_title="1화",
            instruction="scene instruction",
            target_length=3000,
            step_context=lambda message: RecordingStepContext(messages, message),
        )

        self.assertEqual(result["draft"], "draft text")
        self.assertEqual(result["review_report"], "review report")
        self.assertEqual(result["revised_draft"], "revised draft")
        self.assertEqual(result["new_summary"], "summary text")
        self.assertEqual(len(messages), 7)
        self.assertEqual(generator.calls[0], ("create_chapter", "scene instruction", 3000))
        self.assertEqual(reviewer.calls[0], ("review_chapter", "draft text"))
        self.assertEqual(reviewer.calls[1], ("revise_draft", "draft text", "review report"))

    def test_run_single_cycle_captures_summary_error(self):
        generator = FakeGenerator()
        reviewer = FakeReviewer()
        automator = Automator(project_name="sample", generator=generator, reviewer=reviewer)

        def fail_summary(_: str) -> str:
            raise RuntimeError("summary failed")

        generator.summarize_and_update_context = fail_summary  # type: ignore[method-assign]

        result = automator.run_single_cycle(
            chapter_title="1화",
            instruction="scene instruction",
            target_length=1000,
        )

        self.assertEqual(result["draft"], "draft text")
        self.assertEqual(result["saved_path"], "/tmp/1화.md")
        self.assertEqual(result["summary_error"], "summary failed")


if __name__ == "__main__":
    unittest.main()
