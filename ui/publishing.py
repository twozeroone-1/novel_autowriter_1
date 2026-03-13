PLATFORM_LABELS = {
    "munpia": "문피아",
    "novelpia": "노벨피아",
}


def format_publishing_schedule_summary(config: dict) -> str:
    if not config.get("enabled", False):
        return "비활성"

    schedule = config.get("schedule", {})
    schedule_type = schedule.get("type", "daily")
    if schedule_type == "daily":
        return f"매일 {schedule.get('time', '21:00')}"
    if schedule_type == "weekly":
        return f"매주 {schedule.get('time', '21:00')}"
    if schedule_type == "interval":
        return f"{int(schedule.get('hours', 24))}시간마다 반복"
    return "설정 없음"


def format_publishing_runtime_status(runtime: dict) -> str:
    status = runtime.get("status", "idle")
    if status == "running":
        return "실행 중"
    if status == "paused":
        error = str(runtime.get("last_error", "")).strip()
        return f"일시중지: {error}" if error else "일시중지"
    return "대기 중"


def build_publishing_queue_rows(queue: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for index, job in enumerate(queue, start=1):
        rows.append(
            {
                "순서": index,
                "회차": job.get("chapter_title", ""),
                "상태": job.get("status", "pending"),
                "대상": _format_selected_targets(job.get("targets", {})),
                "시도": int(job.get("attempt_count", 0)),
            }
        )
    return rows


def build_publishing_history_summary(history: list[dict]) -> dict[str, int]:
    total = len(history)
    success = sum(1 for record in history if record.get("success"))
    return {
        "total": total,
        "success": success,
        "failure": total - success,
    }


def render_publishing_tab(app) -> None:
    raise NotImplementedError("Publishing tab UI is not implemented yet.")


def _format_selected_targets(targets: dict) -> str:
    labels = [
        PLATFORM_LABELS[platform_name]
        for platform_name, payload in targets.items()
        if platform_name in PLATFORM_LABELS and payload.get("selected")
    ]
    return ", ".join(labels) if labels else "-"
