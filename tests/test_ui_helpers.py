import unittest

from core.token_budget import get_field_stats
from ui.app import normalize_project_name
from ui.workspace import ProjectFieldSpec, build_project_field_panels, summarize_text_preview


class TestUiHelpers(unittest.TestCase):
    def setUp(self):
        self.specs = (
            ProjectFieldSpec(
                section_title="1. STORY BIBLE",
                subtitle="세계관과 연재 목표",
                guide_text="700~1500자",
                input_label="",
                config_key="worldview",
                textarea_key="ta_worldview",
                height=250,
                actions=(),
            ),
            ProjectFieldSpec(
                section_title="2. STYLE GUIDE",
                subtitle="문체와 서술 규칙",
                guide_text="200~600자",
                input_label="",
                config_key="tone_and_manner",
                textarea_key="ta_tone",
                height=250,
                actions=(),
            ),
            ProjectFieldSpec(
                section_title="3. CONTINUITY",
                subtitle="고정 설정과 관계도",
                guide_text="300~900자",
                input_label="",
                config_key="continuity",
                textarea_key="ta_continuity",
                height=250,
                actions=(),
            ),
            ProjectFieldSpec(
                section_title="4. STATE",
                subtitle="현재 상황과 감정선",
                guide_text="150~500자",
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
            "tone_and_manner": "1인칭 현재 시제, 짧은 문장 위주.",
            "continuity": "절대 변하지 않는 설정",
            "state": "주인공은 방금 패배했다.",
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
                "주인공은 기억을 잃은 채 마도 학교에 입학한다. "
                "학교는 탑의 심장과 연결되어 있고, 각 기숙사는 서로 다른 금기를 지닌다. "
                "연재의 목표는 학교 내부 권력 구조와 주인공의 잃어버린 과거를 함께 드러내는 것이다."
            ),
            "tone_and_manner": "1인칭 현재 시제, 짧은 문장, 농담은 절제.",
            "continuity": "탑의 심장은 외부인이 직접 만질 수 없다.",
            "state": "주인공은 첫 결투에서 패배한 직후다.",
        }

        panels = build_project_field_panels(self.specs, get_field_stats(config), config)

        self.assertTrue(panels[0].preview_text.endswith("..."))
        self.assertLessEqual(len(panels[0].preview_text), 93)
        self.assertFalse(any(panel.expanded for panel in panels))

    def test_summarize_text_preview_strips_simple_markdown(self):
        preview = summarize_text_preview("# 제목\n**강조** 문장과 `코드`", max_chars=50)

        self.assertEqual(preview, "제목 강조 문장과 코드")


if __name__ == "__main__":
    unittest.main()
