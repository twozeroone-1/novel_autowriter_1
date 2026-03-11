import importlib
import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from core.automation_store import AutomationStore


class FakeAutomator:
    def __init__(self, *, should_fail: bool = False):
        self.should_fail = should_fail
        self.call_count = 0

    def run_single_cycle(self, chapter_title: str, instruction: str, target_length: int):
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("boom")
        return {
            "saved_path": f"/tmp/{chapter_title}.md",
            "new_summary": "summary",
        }


class TestAutomationRuntime(unittest.TestCase):
    def _load_runtime_cls(self):
        spec = importlib.util.find_spec("core.automation_runtime")
        self.assertIsNotNone(spec, "core.automation_runtime should exist")
        module = importlib.import_module("core.automation_runtime")
        runtime_cls = getattr(module, "AutomationRuntime", None)
        self.assertIsNotNone(runtime_cls, "AutomationRuntime should exist")
        return runtime_cls

    def test_runtime_executes_next_pending_job_and_marks_done(self):
        runtime_cls = self._load_runtime_cls()
        now = datetime(2026, 3, 12, 21, 0, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch("core.automation_store.DATA_PROJECTS_DIR", projects_dir):
                store = AutomationStore(project_name="sample")
                store.save_config({"enabled": True, "schedule": {"type": "daily", "time": "21:00"}})
                store.save_queue(
                    [
                        {
                            "id": "job1",
                            "title": "Episode 12",
                            "instruction": "scene instruction",
                            "target_length": 5000,
                            "status": "pending",
                            "attempt_count": 0,
                        }
                    ]
                )
                runtime = runtime_cls(store=store, automator=FakeAutomator())

                runtime.tick(now=now)

                queue = store.load_queue()
                state = store.load_runtime()
                history = store.load_recent_history(limit=10)

        self.assertEqual(queue[0]["status"], "done")
        self.assertEqual(queue[0]["attempt_count"], 1)
        self.assertEqual(state["status"], "idle")
        self.assertEqual(state["last_run_at"], now.isoformat())
        self.assertEqual(len(history), 1)

    def test_runtime_retries_once_then_pauses_queue_on_second_failure(self):
        runtime_cls = self._load_runtime_cls()
        now = datetime(2026, 3, 12, 21, 0, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch("core.automation_store.DATA_PROJECTS_DIR", projects_dir):
                store = AutomationStore(project_name="sample")
                store.save_config({"enabled": True, "schedule": {"type": "daily", "time": "21:00"}})
                store.save_queue(
                    [
                        {
                            "id": "job1",
                            "title": "Episode 12",
                            "instruction": "scene instruction",
                            "target_length": 5000,
                            "status": "pending",
                            "attempt_count": 0,
                        }
                    ]
                )
                runtime = runtime_cls(store=store, automator=FakeAutomator(should_fail=True))

                runtime.tick(now=now)

                queue = store.load_queue()
                state = store.load_runtime()

        self.assertEqual(queue[0]["status"], "failed")
        self.assertEqual(queue[0]["attempt_count"], 2)
        self.assertEqual(state["status"], "paused")
        self.assertEqual(state["last_error"], "boom")

    def test_runtime_skips_execution_when_paused(self):
        runtime_cls = self._load_runtime_cls()
        now = datetime(2026, 3, 12, 21, 0, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch("core.automation_store.DATA_PROJECTS_DIR", projects_dir):
                store = AutomationStore(project_name="sample")
                store.save_config({"enabled": True, "schedule": {"type": "daily", "time": "21:00"}})
                store.save_runtime({"status": "paused", "last_error": "boom"})
                store.save_queue(
                    [
                        {
                            "id": "job1",
                            "title": "Episode 12",
                            "instruction": "scene instruction",
                            "target_length": 5000,
                            "status": "pending",
                            "attempt_count": 0,
                        }
                    ]
                )
                fake_automator = FakeAutomator()
                runtime = runtime_cls(store=store, automator=fake_automator)

                runtime.tick(now=now)

        self.assertEqual(fake_automator.call_count, 0)


if __name__ == "__main__":
    unittest.main()
