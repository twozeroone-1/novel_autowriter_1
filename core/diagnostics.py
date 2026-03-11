import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.app_paths import DATA_PROJECTS_DIR


def get_diagnostics_dir(project_name: str) -> Path:
    return DATA_PROJECTS_DIR / project_name / "diagnostics" / "llm_runs"


def append_llm_run(project_name: str, record: dict) -> None:
    target_dir = get_diagnostics_dir(project_name)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{record['timestamp'][:10]}.jsonl"
    with target_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _parse_timestamp(raw_value: str) -> datetime:
    parsed = datetime.fromisoformat(raw_value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def load_recent_llm_runs(project_name: str, *, now: datetime | None = None) -> list[dict]:
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time - timedelta(hours=24)
    target_dir = get_diagnostics_dir(project_name)
    if not target_dir.exists():
        return []

    records: list[dict] = []
    for log_path in sorted(target_dir.glob("*.jsonl")):
        with log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if _parse_timestamp(record["timestamp"]) < cutoff:
                    continue
                records.append(record)

    records.sort(key=lambda item: item["timestamp"], reverse=True)
    return records


def build_recent_summary(records: list[dict]) -> dict:
    return {
        "run_count": len(records),
        "failure_count": sum(1 for record in records if not record.get("success")),
        "latest_backend": records[0].get("actual_backend") if records else None,
    }
