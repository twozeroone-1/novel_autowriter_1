from copy import deepcopy
from datetime import datetime
from typing import Any

from core.automation_scheduler import is_schedule_due
from core.automation_store import AutomationStore


DEFAULT_RUNTIME_STATE = {
    "status": "idle",
    "current_job_id": None,
    "last_run_at": None,
    "last_error": "",
}


class AutomationRuntime:
    def __init__(self, store: AutomationStore, automator: Any):
        self.store = store
        self.automator = automator

    def tick(self, now: datetime) -> None:
        config = self.store.load_config()
        if not config.get("enabled", False):
            return

        runtime = self._load_runtime()
        if runtime["status"] in {"paused", "running"}:
            return

        if not is_schedule_due(config.get("schedule", {}), now=now, last_run_at=runtime.get("last_run_at")):
            return

        queue = self.store.load_queue()
        job = next((item for item in queue if item.get("status", "pending") == "pending"), None)
        if job is None:
            return

        runtime["status"] = "running"
        runtime["current_job_id"] = job.get("id")
        runtime["last_error"] = ""
        self.store.save_runtime(runtime)

        max_attempts = int(config.get("retry_policy", {}).get("max_attempts", 2))
        last_error = ""
        for _ in range(max_attempts):
            job["attempt_count"] = int(job.get("attempt_count", 0)) + 1
            try:
                result = self.automator.run_single_cycle(
                    chapter_title=job.get("title", ""),
                    instruction=job.get("instruction", ""),
                    target_length=int(job.get("target_length", 5000)),
                )
                job["status"] = "done"
                runtime["status"] = "idle"
                runtime["current_job_id"] = None
                runtime["last_run_at"] = now.isoformat()
                runtime["last_error"] = ""
                self.store.save_queue(queue)
                self.store.save_runtime(runtime)
                self.store.append_history(
                    {
                        "timestamp": now.isoformat(),
                        "job_id": job.get("id"),
                        "title": job.get("title", ""),
                        "success": True,
                        "saved_path": result.get("saved_path", ""),
                    }
                )
                return
            except Exception as exc:
                last_error = str(exc)

        job["status"] = "failed"
        runtime["status"] = "paused"
        runtime["current_job_id"] = None
        runtime["last_error"] = last_error
        self.store.save_queue(queue)
        self.store.save_runtime(runtime)
        self.store.append_history(
            {
                "timestamp": now.isoformat(),
                "job_id": job.get("id"),
                "title": job.get("title", ""),
                "success": False,
                "error_text": last_error,
            }
        )

    def _load_runtime(self) -> dict:
        runtime = deepcopy(DEFAULT_RUNTIME_STATE)
        runtime.update(self.store.load_runtime())
        return runtime
