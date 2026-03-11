import unittest
from unittest.mock import patch

from core.reviewer import Reviewer


class FakeContext:
    def get_worldview_context(self) -> str:
        return "[WORLD]"

    def get_character_context(self) -> str:
        return "[CHAR]"

    def get_continuity_context(self) -> str:
        return "[CONTINUITY]"

    def get_state_context(self) -> str:
        return "[STATE]"


class TestReviewer(unittest.TestCase):
    def test_review_chapter_includes_continuity_and_state_context(self):
        reviewer = Reviewer(project_name="sample")
        reviewer.ctx = FakeContext()

        with patch("core.reviewer.generate_text", return_value="report") as mocked_generate:
            result = reviewer.review_chapter("draft body")

        self.assertEqual(result, "report")
        prompt = mocked_generate.call_args.args[0]
        self.assertIn("[WORLD]", prompt)
        self.assertIn("[CHAR]", prompt)
        self.assertIn("[CONTINUITY]", prompt)
        self.assertIn("[STATE]", prompt)
        self.assertIn("draft body", prompt)

    def test_revise_draft_includes_continuity_and_state_context(self):
        reviewer = Reviewer(project_name="sample")
        reviewer.ctx = FakeContext()

        with patch("core.reviewer.generate_text", return_value="revised") as mocked_generate:
            result = reviewer.revise_draft("draft body", "review report")

        self.assertEqual(result, "revised")
        prompt = mocked_generate.call_args.args[0]
        self.assertIn("[WORLD]", prompt)
        self.assertIn("[CHAR]", prompt)
        self.assertIn("[CONTINUITY]", prompt)
        self.assertIn("[STATE]", prompt)
        self.assertIn("draft body", prompt)
        self.assertIn("review report", prompt)


if __name__ == "__main__":
    unittest.main()
