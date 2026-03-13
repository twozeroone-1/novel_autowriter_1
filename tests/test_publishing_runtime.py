import importlib
import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from core.publishing_store import PublishingStore


class FakePublishingExecutor:
    def __init__(self, result: dict | None = None):
        self.result = result or {
            "platform_results": {
                "munpia": {"status": "done", "success": True},
            }
        }
        self.call_count = 0

    def publish_job(self, *, job: dict, config: dict) -> dict:
        self.call_count += 1
        return self.result


class TestPublishingRuntime(unittest.TestCase):
    def _load_runtime_cls(self):
        spec = importlib.util.find_spec("core.publishing_runtime")
        self.assertIsNotNone(spec, "core.publishing_runtime should exist")
        module = importlib.import_module("core.publishing_runtime")
        runtime_cls = getattr(module, "PublishingRuntime", None)
        self.assertIsNotNone(runtime_cls, "PublishingRuntime should exist")
        return runtime_cls

    def test_tick_skips_when_publishing_is_disabled(self):
        runtime_cls = self._load_runtime_cls()
        now = datetime(2026, 3, 12, 21, 0, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch("core.publishing_store.DATA_PROJECTS_DIR", projects_dir):
                store = PublishingStore(project_name="sample")
                store.save_config({"enabled": False, "schedule": {"type": "daily", "time": "21:00"}})
                executor = FakePublishingExecutor()
                runtime = runtime_cls(store=store, executor=executor)

                runtime.tick(now=now)

        self.assertEqual(executor.call_count, 0)

    def test_tick_runs_first_pending_job_when_schedule_is_due(self):
        runtime_cls = self._load_runtime_cls()
        now = datetime(2026, 3, 12, 21, 0, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch("core.publishing_store.DATA_PROJECTS_DIR", projects_dir):
                store = PublishingStore(project_name="sample")
                store.save_config({"enabled": True, "schedule": {"type": "daily", "time": "21:00"}})
                store.save_queue(
                    [
                        {
                            "id": "pub1",
                            "chapter_title": "Episode 12",
                            "status": "pending",
                            "attempt_count": 0,
                            "targets": {
                                "munpia": {"selected": True, "status": "pending"},
                            },
                        }
                    ]
                )
                executor = FakePublishingExecutor()
                runtime = runtime_cls(store=store, executor=executor)

                runtime.tick(now=now)

                queue = store.load_queue()
                state = store.load_runtime()
                history = store.load_recent_history(limit=10)

        self.assertEqual(executor.call_count, 1)
        self.assertEqual(queue[0]["status"], "done")
        self.assertEqual(queue[0]["attempt_count"], 1)
        self.assertEqual(queue[0]["targets"]["munpia"]["status"], "done")
        self.assertEqual(state["status"], "idle")
        self.assertEqual(state["last_run_at"], now.isoformat())
        self.assertEqual(len(history), 1)
        self.assertTrue(history[0]["success"])

    def test_tick_force_runs_pending_job_even_when_disabled_and_not_due(self):
        runtime_cls = self._load_runtime_cls()
        now = datetime(2026, 3, 12, 13, 0, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch("core.publishing_store.DATA_PROJECTS_DIR", projects_dir):
                store = PublishingStore(project_name="sample")
                store.save_config({"enabled": False, "schedule": {"type": "daily", "time": "21:00"}})
                store.save_queue(
                    [
                        {
                            "id": "pub1",
                            "chapter_title": "Episode 12",
                            "status": "pending",
                            "attempt_count": 0,
                            "targets": {
                                "munpia": {"selected": True, "status": "pending"},
                            },
                        }
                    ]
                )
                executor = FakePublishingExecutor()
                runtime = runtime_cls(store=store, executor=executor)

                runtime.tick(now=now, force=True)

                queue = store.load_queue()
                state = store.load_runtime()

        self.assertEqual(executor.call_count, 1)
        self.assertEqual(queue[0]["status"], "done")
        self.assertEqual(state["status"], "idle")
        self.assertEqual(state["last_run_at"], now.isoformat())

    def test_tick_marks_partial_failed_when_only_one_platform_succeeds(self):
        runtime_cls = self._load_runtime_cls()
        now = datetime(2026, 3, 12, 21, 0, tzinfo=timezone.utc)
        executor = FakePublishingExecutor(
            result={
                "platform_results": {
                    "munpia": {"status": "done", "success": True},
                    "novelpia": {
                        "status": "failed",
                        "success": False,
                        "error_type": "retryable",
                        "error_text": "editor missing",
                    },
                }
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch("core.publishing_store.DATA_PROJECTS_DIR", projects_dir):
                store = PublishingStore(project_name="sample")
                store.save_config({"enabled": True, "schedule": {"type": "daily", "time": "21:00"}})
                store.save_queue(
                    [
                        {
                            "id": "pub1",
                            "chapter_title": "Episode 12",
                            "status": "pending",
                            "attempt_count": 0,
                            "targets": {
                                "munpia": {"selected": True, "status": "pending"},
                                "novelpia": {"selected": True, "status": "pending"},
                            },
                        }
                    ]
                )
                runtime = runtime_cls(store=store, executor=executor)

                runtime.tick(now=now)

                queue = store.load_queue()
                state = store.load_runtime()
                history = store.load_recent_history(limit=10)

        self.assertEqual(queue[0]["status"], "partial_failed")
        self.assertEqual(queue[0]["targets"]["munpia"]["status"], "done")
        self.assertEqual(queue[0]["targets"]["novelpia"]["status"], "failed")
        self.assertEqual(state["status"], "idle")
        self.assertFalse(history[0]["success"])
        self.assertEqual(history[0]["platform_results"]["novelpia"]["error_type"], "retryable")

    def test_tick_pauses_runtime_on_requires_user_action_error(self):
        runtime_cls = self._load_runtime_cls()
        now = datetime(2026, 3, 12, 21, 0, tzinfo=timezone.utc)
        executor = FakePublishingExecutor(
            result={
                "platform_results": {
                    "munpia": {
                        "status": "failed",
                        "success": False,
                        "error_type": "requires_user_action",
                        "error_text": "captcha required",
                    },
                }
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch("core.publishing_store.DATA_PROJECTS_DIR", projects_dir):
                store = PublishingStore(project_name="sample")
                store.save_config({"enabled": True, "schedule": {"type": "daily", "time": "21:00"}})
                store.save_queue(
                    [
                        {
                            "id": "pub1",
                            "chapter_title": "Episode 12",
                            "status": "pending",
                            "attempt_count": 0,
                            "targets": {
                                "munpia": {"selected": True, "status": "pending"},
                            },
                        }
                    ]
                )
                runtime = runtime_cls(store=store, executor=executor)

                runtime.tick(now=now)

                queue = store.load_queue()
                state = store.load_runtime()

        self.assertEqual(queue[0]["status"], "failed")
        self.assertEqual(state["status"], "paused")
        self.assertEqual(state["last_error"], "captcha required")

    def test_tick_applies_platform_config_updates_from_executor(self):
        runtime_cls = self._load_runtime_cls()
        now = datetime(2026, 3, 12, 21, 0, tzinfo=timezone.utc)
        executor = FakePublishingExecutor(
            result={
                "platform_results": {
                    "munpia": {"status": "done", "success": True, "work_id": "created-work"},
                },
                "platform_config_updates": {
                    "munpia": {"work_id": "created-work"},
                },
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch("core.publishing_store.DATA_PROJECTS_DIR", projects_dir):
                store = PublishingStore(project_name="sample")
                store.save_config(
                    {
                        "enabled": True,
                        "schedule": {"type": "daily", "time": "21:00"},
                        "platforms": {
                            "munpia": {"enabled": True, "work_id": ""},
                        },
                    }
                )
                store.save_queue(
                    [
                        {
                            "id": "pub1",
                            "chapter_title": "Episode 12",
                            "status": "pending",
                            "attempt_count": 0,
                            "targets": {
                                "munpia": {"selected": True, "status": "pending"},
                            },
                        }
                    ]
                )
                runtime = runtime_cls(store=store, executor=executor)

                runtime.tick(now=now)

                config = store.load_config()

        self.assertEqual(config["platforms"]["munpia"]["work_id"], "created-work")

    def test_run_publishing_pass_only_executes_enabled_projects(self):
        module = importlib.import_module("core.publishing_runtime")
        run_publishing_pass = getattr(module, "run_publishing_pass", None)
        self.assertIsNotNone(run_publishing_pass, "run_publishing_pass should exist")
        now = datetime(2026, 3, 12, 21, 0, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as tmpdir:
            projects_dir = Path(tmpdir) / "projects"
            with patch("core.publishing_store.DATA_PROJECTS_DIR", projects_dir), patch.object(
                module, "DATA_PROJECTS_DIR", projects_dir
            ):
                enabled_store = PublishingStore(project_name="enabled_project")
                enabled_store.save_config({"enabled": True, "schedule": {"type": "daily", "time": "21:00"}})
                enabled_store.save_queue(
                    [
                        {
                            "id": "pub1",
                            "chapter_title": "Episode 12",
                            "status": "pending",
                            "attempt_count": 0,
                            "targets": {
                                "munpia": {"selected": True, "status": "pending"},
                            },
                        }
                    ]
                )

                disabled_store = PublishingStore(project_name="disabled_project")
                disabled_store.save_config({"enabled": False, "schedule": {"type": "daily", "time": "21:00"}})

                executors: dict[str, FakePublishingExecutor] = {}

                def executor_factory(project_name: str):
                    executors.setdefault(project_name, FakePublishingExecutor())
                    return executors[project_name]

                run_publishing_pass(now=now, executor_factory=executor_factory)

                enabled_queue = enabled_store.load_queue()

        self.assertEqual(enabled_queue[0]["status"], "done")
        self.assertEqual(executors["enabled_project"].call_count, 1)
        self.assertNotIn("disabled_project", executors)


if __name__ == "__main__":
    unittest.main()
