import unittest

from core.token_budget import get_field_stats
from ui.app import normalize_project_name
from ui.chapters import build_session_bound_text_area_kwargs, build_workflow_steps
from ui.workspace import ProjectFieldSpec, build_project_field_panels, summarize_text_preview


class TestUiHelpers(unittest.TestCase):
    def setUp(self):
        self.specs = (
            ProjectFieldSpec(
                section_title="1. STORY BIBLE",
                subtitle="World and serialization goal",
                guide_text="700-1500 chars",
                input_label="",
                config_key="worldview",
                textarea_key="ta_worldview",
                height=250,
                actions=(),
            ),
            ProjectFieldSpec(
                section_title="2. STYLE GUIDE",
                subtitle="Voice and prose rules",
                guide_text="200-600 chars",
                input_label="",
                config_key="tone_and_manner",
                textarea_key="ta_tone",
                height=250,
                actions=(),
            ),
            ProjectFieldSpec(
                section_title="3. CONTINUITY",
                subtitle="Fixed canon and relationships",
                guide_text="300-900 chars",
                input_label="",
                config_key="continuity",
                textarea_key="ta_continuity",
                height=250,
                actions=(),
            ),
            ProjectFieldSpec(
                section_title="4. STATE",
                subtitle="Current status and emotions",
                guide_text="150-500 chars",
                input_label="",
                config_key="state",
                textarea_key="ta_state",
                height=250,
                actions=(),
            ),
        )

    def test_normalize_project_name_collapses_spaces(self):
        normalized, error = normalize_project_name("  my   project   name  ")

        self.assertEqual(normalized, "my project name")
        self.assertIsNone(error)

    def test_normalize_project_name_rejects_reserved_name(self):
        normalized, error = normalize_project_name("default_project")

        self.assertIsNone(normalized)
        self.assertIsNotNone(error)

    def test_normalize_project_name_rejects_sample_name(self):
        normalized, error = normalize_project_name("sample")

        self.assertIsNone(normalized)
        self.assertIsNotNone(error)

    def test_normalize_project_name_rejects_path_characters(self):
        normalized, error = normalize_project_name("bad/name")

        self.assertIsNone(normalized)
        self.assertIsNotNone(error)

    def test_build_project_field_panels_marks_first_attention_panel_expanded(self):
        config = {
            "worldview": "",
            "tone_and_manner": "Third-person limited, concise sentences.",
            "continuity": "The school chair never meets the hero directly.",
            "state": "The hero just lost the first duel.",
        }

        panels = build_project_field_panels(self.specs, get_field_stats(config), config)

        self.assertEqual(len(panels), 4)
        self.assertIn("비어 있음", panels[0].expander_label)
        self.assertEqual(panels[0].preview_text, "아직 작성되지 않았습니다.")
        self.assertTrue(panels[0].expanded)
        self.assertFalse(panels[1].expanded)

    def test_build_project_field_panels_truncates_preview_and_keeps_healthy_panels_collapsed(self):
        config = {
            "worldview": (
                "The protagonist enters school with lost memories. "
                "The school is tied to a hidden organization, and each discipline uses a different device. "
                "The story goal is to reveal the power structure of the school and the hero's missing past."
            ),
            "tone_and_manner": "Third-person limited, concise prose, balanced dialogue.",
            "continuity": "The chair and the hero cannot meet directly.",
            "state": "The protagonist won the first field test.",
        }

        panels = build_project_field_panels(self.specs, get_field_stats(config), config)

        self.assertTrue(panels[0].preview_text.endswith("..."))
        self.assertLessEqual(len(panels[0].preview_text), 93)
        self.assertFalse(any(panel.expanded for panel in panels))

    def test_summarize_text_preview_strips_simple_markdown(self):
        preview = summarize_text_preview("# Title\n**Bold** text with `code`", max_chars=50)

        self.assertEqual(preview, "Title Bold text with code")

    def test_build_workflow_steps_marks_done_current_and_upcoming(self):
        steps = build_workflow_steps(
            ("Select draft", "Generate report", "Save revised draft"),
            current_step=1,
        )

        self.assertEqual([step.state for step in steps], ["완료", "현재 단계", "다음 단계"])
        self.assertEqual(
            [step.label for step in steps],
            ["Select draft", "Generate report", "Save revised draft"],
        )

    def test_build_session_bound_text_area_kwargs_uses_value_when_widget_state_missing(self):
        kwargs = build_session_bound_text_area_kwargs("edited_draft", "new draft", {})

        self.assertEqual(kwargs, {"key": "edited_draft", "value": "new draft"})

    def test_build_session_bound_text_area_kwargs_omits_value_when_widget_state_exists(self):
        kwargs = build_session_bound_text_area_kwargs(
            "edited_draft",
            "new draft",
            {"edited_draft": "user edited draft"},
        )

        self.assertEqual(kwargs, {"key": "edited_draft"})


if __name__ == "__main__":
    unittest.main()
