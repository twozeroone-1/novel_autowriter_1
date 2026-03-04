import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict


class AutomationState:
    def __init__(self, project_dir: Path):
        self.path = project_dir / "automation_state.json"
        if not self.path.exists():
            self._save(self._default_state())

    def _default_state(self) -> Dict[str, Any]:
        return {
            "locked": False,
            "lock_owner": "",
            "lock_acquired_at": 0,
            "last_status": "IDLE",
            "last_error": "",
            "last_success_at": 0,
            "last_run_started_at": 0,
            "next_run_at": 0,
            "cycle_count": 0,
        }

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {**self._default_state(), **data}
            return self._default_state()
        except Exception:
            return self._default_state()

    def _save(self, state: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix="auto_state_", suffix=".json", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def read(self) -> Dict[str, Any]:
        return self._load()

    def acquire_lock(self, owner: str, stale_after_sec: int = 7200) -> bool:
        state = self._load()
        now = int(time.time())
        if state.get("locked"):
            lock_age = now - int(state.get("lock_acquired_at", 0))
            same_owner = state.get("lock_owner") == owner
            if not same_owner and lock_age < stale_after_sec:
                return False
        state["locked"] = True
        state["lock_owner"] = owner
        state["lock_acquired_at"] = now
        self._save(state)
        return True

    def refresh_lock(self, owner: str) -> bool:
        state = self._load()
        if not state.get("locked"):
            return False
        if state.get("lock_owner") != owner:
            return False
        state["lock_acquired_at"] = int(time.time())
        self._save(state)
        return True

    def release_lock(self, owner: str = "", force: bool = False) -> bool:
        state = self._load()
        if state.get("locked"):
            if force or state.get("lock_owner") == owner or not owner:
                state["locked"] = False
                state["lock_owner"] = ""
                state["lock_acquired_at"] = 0
                self._save(state)
                return True
            return False
        return True

    def checkpoint(
        self,
        *,
        status: str,
        error: str = "",
        next_run_at: int = 0,
        run_started: bool = False,
        run_succeeded: bool = False,
    ) -> None:
        state = self._load()
        now = int(time.time())
        state["last_status"] = status
        state["last_error"] = error
        state["next_run_at"] = int(next_run_at or 0)
        if run_started:
            state["last_run_started_at"] = now
        if run_succeeded:
            state["last_success_at"] = now
            state["cycle_count"] = int(state.get("cycle_count", 0)) + 1
        self._save(state)
