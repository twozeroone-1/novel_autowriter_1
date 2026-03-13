from copy import deepcopy
from datetime import datetime

from core.app_paths import DATA_PROJECTS_DIR
from core.automation_scheduler import is_schedule_due
from core.publishing_store import PublishingStore


DEFAULT_PUBLISHING_RUNTIME_STATE = {
    "status": "idle",
    "current_job_id": None,
    "last_run_at": None,
    "last_error": "",
}


class PublishingRuntime:
    def __init__(self, store: PublishingStore, executor):
        self.store = store
        self.executor = executor

    def tick(self, now: datetime, *, force: bool = False) -> None:
        config = self.store.load_config()
        if not force and not config.get("enabled", False):
            return

        runtime = self._load_runtime()
        if runtime["status"] in {"paused", "running"}:
            return

        if not force and not is_schedule_due(config.get("schedule", {}), now=now, last_run_at=runtime.get("last_run_at")):
            return

        queue = self.store.load_queue()
        job = next((item for item in queue if item.get("status", "pending") in {"pending", "partial_failed"}), None)
        if job is None:
            return

        job["status"] = "running"
        job["attempt_count"] = int(job.get("attempt_count", 0)) + 1
        runtime["status"] = "running"
        runtime["current_job_id"] = job.get("id")
        runtime["last_error"] = ""
        self.store.save_queue(queue)
        self.store.save_runtime(runtime)

        result = self.executor.publish_job(job=deepcopy(job), config=deepcopy(config))
        platform_results = result.get("platform_results", {})
        platform_config_updates = result.get("platform_config_updates", {})
        self._apply_platform_results(job, platform_results)
        self._apply_platform_config_updates(config, platform_config_updates)

        overall_status = _summarize_job_status(job)
        needs_user_action = any(
            payload.get("error_type") == "requires_user_action"
            for payload in platform_results.values()
            if isinstance(payload, dict)
        )
        last_error = next(
            (
                str(payload.get("error_text", "")).strip()
                for payload in platform_results.values()
                if isinstance(payload, dict) and str(payload.get("error_text", "")).strip()
            ),
            "",
        )

        job["status"] = overall_status
        job["last_error"] = last_error
        runtime["status"] = "paused" if needs_user_action else "idle"
        runtime["current_job_id"] = None
        runtime["last_run_at"] = now.isoformat()
        runtime["last_error"] = last_error
        self.store.save_config(config)
        self.store.save_queue(queue)
        self.store.save_runtime(runtime)
        self.store.append_history(
            {
                "timestamp": now.isoformat(),
                "job_id": job.get("id"),
                "chapter_title": job.get("chapter_title", ""),
                "success": overall_status == "done",
                "platform_results": platform_results,
            }
        )

    def _load_runtime(self) -> dict:
        runtime = deepcopy(DEFAULT_PUBLISHING_RUNTIME_STATE)
        runtime.update(self.store.load_runtime())
        return runtime

    def _apply_platform_results(self, job: dict, platform_results: dict) -> None:
        targets = job.setdefault("targets", {})
        for platform_name, payload in platform_results.items():
            target = targets.setdefault(platform_name, {})
            if not isinstance(payload, dict):
                continue
            target["status"] = payload.get("status", target.get("status", "pending"))
            if payload.get("work_id"):
                target["work_id"] = payload["work_id"]
            if payload.get("episode_id"):
                target["episode_id"] = payload["episode_id"]

    def _apply_platform_config_updates(self, config: dict, platform_config_updates: dict) -> None:
        platforms = config.setdefault("platforms", {})
        for platform_name, updates in platform_config_updates.items():
            platform_config = platforms.setdefault(platform_name, {})
            if not isinstance(updates, dict):
                continue
            platform_config.update(updates)


def _summarize_job_status(job: dict) -> str:
    selected_statuses = [
        payload.get("status", "pending")
        for payload in job.get("targets", {}).values()
        if isinstance(payload, dict) and payload.get("selected")
    ]
    if not selected_statuses:
        return "failed"
    if all(status == "done" for status in selected_statuses):
        return "done"
    if any(status == "done" for status in selected_statuses):
        return "partial_failed"
    return "failed"


def run_publishing_pass(*, now: datetime, executor_factory) -> None:
    if not DATA_PROJECTS_DIR.exists():
        return

    for path in DATA_PROJECTS_DIR.iterdir():
        if not path.is_dir():
            continue
        store = PublishingStore(project_name=path.name)
        if not store.load_config().get("enabled", False):
            continue
        runtime = PublishingRuntime(store=store, executor=executor_factory(path.name))
        runtime.tick(now=now)
