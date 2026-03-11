from copy import deepcopy
from pathlib import Path

from core.app_paths import DATA_PROJECTS_DIR
from core.file_utils import atomic_write_json


DEFAULT_AUTOMATION_CONFIG = {
    "enabled": False,
    "schedule": {
        "type": "daily",
        "time": "21:00",
        "days": [],
        "hours": 24,
    },
    "retry_policy": {
        "max_attempts": 2,
    },
    "poll_interval_seconds": 30,
}


class AutomationStore:
    def __init__(self, project_name: str):
        self.project_name = project_name

    @property
    def automation_dir(self) -> Path:
        return DATA_PROJECTS_DIR / self.project_name / "automation"

    @property
    def config_path(self) -> Path:
        return self.automation_dir / "config.json"

    def load_config(self) -> dict:
        if not self.config_path.exists():
            return deepcopy(DEFAULT_AUTOMATION_CONFIG)
        return deepcopy(DEFAULT_AUTOMATION_CONFIG) | self._read_json(self.config_path)

    def save_config(self, config: dict) -> None:
        atomic_write_json(self.config_path, config)

    def _read_json(self, path: Path) -> dict:
        return __import__("json").loads(path.read_text(encoding="utf-8"))
