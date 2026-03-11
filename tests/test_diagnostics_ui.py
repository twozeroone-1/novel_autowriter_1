import unittest

from ui import diagnostics as diagnostics_ui


class TestDiagnosticsUi(unittest.TestCase):
    def test_format_sidebar_summary_uses_compact_metadata_only(self):
        summary = diagnostics_ui.format_sidebar_summary(
            {"run_count": 3, "failure_count": 1, "latest_backend": "cli"}
        )

        self.assertIn("3 runs", summary)
        self.assertIn("1 failed", summary)
        self.assertIn("cli", summary)

    def test_filter_runs_by_success_backend_and_model(self):
        runs = [
            {
                "success": False,
                "requested_backend": "auto",
                "actual_backend": "api",
                "model": "gemini-2.5-flash",
            },
            {
                "success": True,
                "requested_backend": "api",
                "actual_backend": "api",
                "model": "gemini-2.5-pro",
            },
        ]

        filtered = diagnostics_ui.filter_runs(
            runs,
            success_filter="failed",
            requested_backend="auto",
            actual_backend="api",
            model_name="gemini-2.5-flash",
        )

        self.assertEqual(len(filtered), 1)

    def test_build_detail_rows_preserves_newest_first_metadata(self):
        rows = diagnostics_ui.build_detail_rows(
            [
                {
                    "timestamp": "2026-03-11T12:00:00+00:00",
                    "feature": "review",
                    "success": False,
                    "requested_backend": "auto",
                    "actual_backend": "api",
                    "model": "gemini-2.5-flash",
                    "duration_ms": 2100,
                    "prompt_text": "prompt",
                    "response_text": "",
                    "stderr_text": "",
                    "error_text": "api failed",
                    "fallback_note": "cli failed -> api",
                }
            ]
        )

        self.assertEqual(rows[0]["feature"], "review")
        self.assertEqual(rows[0]["status"], "failed")
        self.assertEqual(rows[0]["error_text"], "api failed")

    def test_get_diagnostics_warning_text_mentions_sensitive_content(self):
        warning_text = diagnostics_ui.get_diagnostics_warning_text()

        self.assertIn("sensitive", warning_text.lower())
        self.assertIn("prompt", warning_text.lower())


if __name__ == "__main__":
    unittest.main()
