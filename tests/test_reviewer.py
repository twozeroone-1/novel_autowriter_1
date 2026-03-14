import unittest
from unittest.mock import ANY, patch

from core.reviewer import Reviewer


class FakeContext:
    project_name = "sample"

    def get_worldview_context(self) -> str:
        return "[WORLD]"

    def get_character_context(self) -> str:
        return "[CHAR]"

    def get_continuity_context(self) -> str:
        return "[CONTINUITY]"

    def get_state_context(self) -> str:
        return "[STATE]"

    def get_plot_outline(self) -> str:
        return "plot outline text"


class TestReviewer(unittest.TestCase):
    def test_review_chapter_includes_continuity_and_state_context(self):
        reviewer = Reviewer(project_name="sample")
        reviewer.ctx = FakeContext()

        with patch("core.reviewer.generate_text", return_value="report") as mocked_generate:
            result = reviewer.review_chapter("draft body", include_plot=True, plot_strength="strict")

        self.assertEqual(result, "report")
        prompt = mocked_generate.call_args.args[0]
        self.assertIn("[WORLD]", prompt)
        self.assertIn("[CHAR]", prompt)
        self.assertIn("[CONTINUITY]", prompt)
        self.assertIn("[STATE]", prompt)
        self.assertIn("plot outline text", prompt)
        self.assertIn("strict", prompt)
        self.assertIn("draft body", prompt)
        self.assertEqual(mocked_generate.call_args.kwargs["project_name"], "sample")
        self.assertEqual(mocked_generate.call_args.kwargs["feature"], "review")

    def test_revise_draft_includes_continuity_and_state_context(self):
        reviewer = Reviewer(project_name="sample")
        reviewer.ctx = FakeContext()

        with patch("core.reviewer.generate_text", return_value="revised") as mocked_generate:
            result = reviewer.revise_draft("draft body", "review report", include_plot=True, plot_strength="strict")

        self.assertEqual(result, "revised")
        prompt = mocked_generate.call_args.args[0]
        self.assertIn("[WORLD]", prompt)
        self.assertIn("[CHAR]", prompt)
        self.assertIn("[CONTINUITY]", prompt)
        self.assertIn("[STATE]", prompt)
        self.assertIn("plot outline text", prompt)
        self.assertIn("strict", prompt)
        self.assertIn("draft body", prompt)
        self.assertIn("review report", prompt)
        self.assertEqual(mocked_generate.call_args.kwargs["project_name"], "sample")
        self.assertEqual(mocked_generate.call_args.kwargs["feature"], "revise")


if __name__ == "__main__":
    unittest.main()
