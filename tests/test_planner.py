import unittest
from unittest.mock import patch

from core.planner import Planner


class TestPlanner(unittest.TestCase):
    def test_suggest_ideas_passes_feature_and_project_context_to_generate_text(self):
        planner = Planner(project_name="sample")

        with patch("core.planner.generate_text", return_value="ideas") as mocked_generate:
            result = planner.suggest_ideas("series", "academy, magic", tone="light", count=3)

        self.assertEqual(result, "ideas")
        self.assertEqual(mocked_generate.call_args.kwargs["feature"], "idea")
        self.assertEqual(mocked_generate.call_args.kwargs["project_name"], "sample")

    def test_build_macro_plot_passes_feature_and_project_context_to_generate_text(self):
        planner = Planner(project_name="sample")

        with patch("core.planner.generate_text", return_value="plot") as mocked_generate:
            result = planner.build_macro_plot("series", "title", "phase1", "phase2", "phase3", total_episodes=150)

        self.assertEqual(result, "plot")
        self.assertEqual(mocked_generate.call_args.kwargs["feature"], "plot")
        self.assertEqual(mocked_generate.call_args.kwargs["project_name"], "sample")


if __name__ == "__main__":
    unittest.main()
