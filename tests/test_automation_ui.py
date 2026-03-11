import importlib
import importlib.util
import unittest


class TestAutomationUi(unittest.TestCase):
    def _load_module(self):
        spec = importlib.util.find_spec("ui.automation")
        self.assertIsNotNone(spec, "ui.automation should exist")
        return importlib.import_module("ui.automation")

    def test_format_schedule_summary_for_weekly_rule(self):
        module = self._load_module()
        config = {
            "enabled": True,
            "schedule": {
                "type": "weekly",
                "time": "07:30",
                "days": ["mon", "wed", "fri"],
            },
        }

        summary = module.format_schedule_summary(config)

        self.assertEqual(summary, "매주 월, 수, 금 07:30")

    def test_format_schedule_summary_for_interval_rule(self):
        module = self._load_module()
        config = {
            "enabled": True,
            "schedule": {
                "type": "interval",
                "hours": 6,
            },
        }

        summary = module.format_schedule_summary(config)

        self.assertEqual(summary, "6시간마다 반복")

    def test_format_runtime_status_reports_paused_error(self):
        module = self._load_module()
        runtime = {
            "status": "paused",
            "last_error": "boom",
        }

        status = module.format_runtime_status(runtime)

        self.assertEqual(status, "일시중지: boom")

    def test_build_queue_rows_adds_order_and_defaults(self):
        module = self._load_module()
        rows = module.build_queue_rows(
            [
                {"title": "Episode 12", "status": "pending", "attempt_count": 0},
                {"title": "Episode 13", "status": "failed", "attempt_count": 2},
            ]
        )

        self.assertEqual(rows[0]["순서"], 1)
        self.assertEqual(rows[0]["제목"], "Episode 12")
        self.assertEqual(rows[1]["상태"], "failed")
        self.assertEqual(rows[1]["시도"], 2)

    def test_build_history_rows_formats_backend_and_result(self):
        module = self._load_module()
        rows = module.build_history_rows(
            [
                {
                    "timestamp": "2026-03-12T21:00:00+09:00",
                    "title": "Episode 12",
                    "success": True,
                    "backend": "cli",
                }
            ]
        )

        self.assertEqual(rows[0]["결과"], "성공")
        self.assertEqual(rows[0]["백엔드"], "cli")
        self.assertEqual(rows[0]["제목"], "Episode 12")

    def test_build_schedule_editor_state_for_interval(self):
        module = self._load_module()

        editor_state = module.build_schedule_editor_state("interval")

        self.assertFalse(editor_state["show_time"])
        self.assertFalse(editor_state["show_days"])
        self.assertTrue(editor_state["show_hours"])


if __name__ == "__main__":
    unittest.main()
