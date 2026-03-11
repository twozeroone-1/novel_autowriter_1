import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from core import diagnostics


def build_record(*, timestamp: datetime, success: bool = True, actual_backend: str = "cli") -> dict:
    return {
        "timestamp": timestamp.isoformat(),
        "project": "sample_project",
        "feature": "chapter_generate",
        "requested_backend": "auto",
        "actual_backend": actual_backend,
        "fallback_note": "",
        "model": "gemini-2.5-flash",
        "success": success,
        "duration_ms": 1234,
        "prompt_text": "prompt",
        "response_text": "response",
        "stderr_text": "",
        "error_text": "",
    }


class TestDiagnosticsStorage(unittest.TestCase):
    def test_append_and_read_recent_runs_newest_first(self):
        now = datetime(2026, 3, 11, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch.object(diagnostics, "DATA_PROJECTS_DIR", projects_dir):
                diagnostics.append_llm_run("sample_project", build_record(timestamp=now - timedelta(minutes=5)))
                diagnostics.append_llm_run("sample_project", build_record(timestamp=now))

                records = diagnostics.load_recent_llm_runs("sample_project", now=now)

        self.assertEqual(len(records), 2)
        self.assertGreater(records[0]["timestamp"], records[1]["timestamp"])

    def test_cleanup_drops_records_older_than_24_hours(self):
        now = datetime(2026, 3, 11, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch.object(diagnostics, "DATA_PROJECTS_DIR", projects_dir):
                diagnostics.append_llm_run("sample_project", build_record(timestamp=now - timedelta(hours=25)))
                diagnostics.append_llm_run("sample_project", build_record(timestamp=now - timedelta(hours=1)))

                records = diagnostics.load_recent_llm_runs("sample_project", now=now)

        self.assertEqual(len(records), 1)

    def test_load_recent_runs_skips_malformed_jsonl_lines(self):
        now = datetime(2026, 3, 11, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch.object(diagnostics, "DATA_PROJECTS_DIR", projects_dir):
                log_dir = diagnostics.get_diagnostics_dir("sample_project")
                log_dir.mkdir(parents=True, exist_ok=True)
                log_path = log_dir / "2026-03-11.jsonl"
                log_path.write_text(
                    '{"timestamp":"2026-03-11T11:30:00+00:00","success":true,"actual_backend":"cli"}\nnot-json\n',
                    encoding="utf-8",
                )

                records = diagnostics.load_recent_llm_runs("sample_project", now=now)

        self.assertEqual(len(records), 1)

    def test_build_recent_summary_counts_failures_and_latest_backend(self):
        records = [
            {"success": True, "actual_backend": "cli"},
            {"success": False, "actual_backend": "api"},
        ]

        summary = diagnostics.build_recent_summary(records)

        self.assertEqual(summary["run_count"], 2)
        self.assertEqual(summary["failure_count"], 1)
        self.assertEqual(summary["latest_backend"], "cli")


if __name__ == "__main__":
    unittest.main()
