import importlib
import importlib.util
import unittest


class TestPublishingUi(unittest.TestCase):
    def _load_module(self):
        spec = importlib.util.find_spec("ui.publishing")
        self.assertIsNotNone(spec, "ui.publishing should exist")
        return importlib.import_module("ui.publishing")

    def test_format_publishing_schedule_summary_for_daily_rule(self):
        module = self._load_module()
        config = {
            "enabled": True,
            "schedule": {
                "type": "daily",
                "time": "21:30",
            },
        }

        summary = module.format_publishing_schedule_summary(config)

        self.assertEqual(summary, "매일 21:30")

    def test_build_publishing_queue_rows_handles_partial_platform_selection(self):
        module = self._load_module()
        rows = module.build_publishing_queue_rows(
            [
                {
                    "chapter_title": "Episode 12",
                    "status": "partial_failed",
                    "attempt_count": 1,
                    "targets": {
                        "munpia": {"selected": True},
                        "novelpia": {"selected": False},
                    },
                }
            ]
        )

        self.assertEqual(rows[0]["순서"], 1)
        self.assertEqual(rows[0]["회차"], "Episode 12")
        self.assertEqual(rows[0]["상태"], "partial_failed")
        self.assertEqual(rows[0]["대상"], "문피아")
        self.assertEqual(rows[0]["시도"], 1)

    def test_format_publishing_runtime_status_reports_paused_error(self):
        module = self._load_module()
        runtime = {
            "status": "paused",
            "last_error": "login failed",
        }

        status = module.format_publishing_runtime_status(runtime)

        self.assertEqual(status, "일시중지: login failed")

    def test_build_publishing_history_summary_counts_total_success_and_failure(self):
        module = self._load_module()

        summary = module.build_publishing_history_summary(
            [
                {"success": True},
                {"success": False},
                {"success": True},
            ]
        )

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["success"], 2)
        self.assertEqual(summary["failure"], 1)


if __name__ == "__main__":
    unittest.main()
