import tempfile
import unittest
from pathlib import Path

from core.token_budget import get_field_stats
from ui.app import (
    PROJECT_SETTINGS_SUBSECTION_LABELS,
    PROJECT_STATE_KEYS,
    PROJECT_TAB_LABELS,
    normalize_project_name,
)
from ui.chapters import build_session_bound_text_area_kwargs, build_workflow_steps, select_context_update_value
from ui.workspace import (
    ProjectFieldSpec,
    apply_pending_project_textarea_updates,
    build_project_field_panels,
    resolve_summary_suggestion_source,
    summarize_text_preview,
)


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

    def test_select_context_update_value_prefers_ai_suggestion(self):
        selected = select_context_update_value("new state", "old state")

        self.assertEqual(selected, "new state")

    def test_select_context_update_value_falls_back_to_current_config(self):
        selected = select_context_update_value("", "old state")

        self.assertEqual(selected, "old state")

    def test_resolve_summary_suggestion_source_prefers_pasted_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            latest_path = Path(tmpdir) / "2화.md"
            latest_path.write_text("latest chapter text", encoding="utf-8")

            source_text, source_label = resolve_summary_suggestion_source("pasted text", latest_path)

        self.assertEqual(source_text, "pasted text")
        self.assertEqual(source_label, "붙여넣은 텍스트")

    def test_resolve_summary_suggestion_source_falls_back_to_latest_saved_chapter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            latest_path = Path(tmpdir) / "2화.md"
            latest_path.write_text("latest chapter text", encoding="utf-8")

            source_text, source_label = resolve_summary_suggestion_source("", latest_path)

        self.assertEqual(source_text, "latest chapter text")
        self.assertEqual(source_label, "최근 저장 원고: 2화.md")

    def test_resolve_summary_suggestion_source_returns_empty_when_no_input_exists(self):
        source_text, source_label = resolve_summary_suggestion_source("", None)

        self.assertEqual(source_text, "")
        self.assertEqual(source_label, "")

    def test_project_state_keys_include_workspace_state_source_text(self):
        self.assertIn("workspace_state_source_text", PROJECT_STATE_KEYS)

    def test_project_state_keys_include_project_settings_subsection(self):
        self.assertIn("project_settings_subsection", PROJECT_STATE_KEYS)

    def test_project_state_keys_include_publishing_controls(self):
        self.assertIn("publishing_enabled", PROJECT_STATE_KEYS)
        self.assertIn("publishing_selected_job_id", PROJECT_STATE_KEYS)

    def test_project_state_keys_include_plot_controls_for_review_and_automation(self):
        self.assertIn("review_use_plot", PROJECT_STATE_KEYS)
        self.assertIn("review_plot_strength", PROJECT_STATE_KEYS)
        self.assertIn("auto_use_plot", PROJECT_STATE_KEYS)
        self.assertIn("auto_plot_strength", PROJECT_STATE_KEYS)
        self.assertIn("automation_use_plot", PROJECT_STATE_KEYS)
        self.assertIn("automation_plot_strength", PROJECT_STATE_KEYS)

    def test_project_tab_labels_follow_grouped_order(self):
        self.assertEqual(
            PROJECT_TAB_LABELS,
            (
                "[1] 프로젝트 통합 설정",
                "[2] 회차 생성",
                "[3] 원고 검수",
                "[4] 반자동 연재 모드",
                "[5] 자동화 연재 모드",
                "[6] 외부 플랫폼 업로드",
            ),
        )

    def test_project_settings_subsection_labels_follow_secondary_navigation_order(self):
        self.assertEqual(
            PROJECT_SETTINGS_SUBSECTION_LABELS,
            (
                "기본 설정",
                "아이디어/제목",
                "대형 플롯",
            ),
        )

    def test_apply_pending_project_textarea_updates_applies_and_clears_pending_values(self):
        session_state = {
            "_pending_project_textarea_updates": {
                "ta_state": "new state",
                "ta_tone": "new tone",
            },
            "ta_state": "old state",
        }

        apply_pending_project_textarea_updates(session_state)

        self.assertEqual(session_state["ta_state"], "new state")
        self.assertEqual(session_state["ta_tone"], "new tone")
        self.assertNotIn("_pending_project_textarea_updates", session_state)

    def test_apply_pending_project_textarea_updates_noops_without_pending_values(self):
        session_state = {"ta_state": "old state"}

        apply_pending_project_textarea_updates(session_state)

        self.assertEqual(session_state, {"ta_state": "old state"})


if __name__ == "__main__":
    unittest.main()
