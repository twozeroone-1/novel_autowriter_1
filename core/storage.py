from __future__ import annotations

from pathlib import Path

from core.file_utils import atomic_write_text


class ProjectStorage:
    def project_root(self, project_name: str) -> Path | None:
        raise NotImplementedError

    def read_text(self, project_name: str, relative_path: str) -> str:
        raise NotImplementedError

    def write_text(self, project_name: str, relative_path: str, content: str) -> None:
        raise NotImplementedError

    def exists(self, project_name: str, relative_path: str) -> bool:
        raise NotImplementedError

    def list_paths(self, project_name: str, prefix: str) -> list[str]:
        raise NotImplementedError


class LocalProjectStorage(ProjectStorage):
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)

    def project_root(self, project_name: str) -> Path:
        return self.base_dir / project_name

    def _resolve(self, project_name: str, relative_path: str) -> Path:
        return self.project_root(project_name) / Path(relative_path)

    def read_text(self, project_name: str, relative_path: str) -> str:
        return self._resolve(project_name, relative_path).read_text(encoding="utf-8")

    def write_text(self, project_name: str, relative_path: str, content: str) -> None:
        atomic_write_text(self._resolve(project_name, relative_path), content)

    def exists(self, project_name: str, relative_path: str) -> bool:
        return self._resolve(project_name, relative_path).exists()

    def list_paths(self, project_name: str, prefix: str) -> list[str]:
        root = self.project_root(project_name)
        if not root.exists():
            return []

        normalized_prefix = prefix.strip().strip("/\\")
        search_root = root / normalized_prefix if normalized_prefix else root
        if not search_root.exists():
            return []

        return sorted(
            path.relative_to(root).as_posix()
            for path in search_root.rglob("*")
            if path.is_file()
        )


class InMemoryProjectStorage(ProjectStorage):
    def __init__(self):
        self._projects: dict[str, dict[str, str]] = {}

    def project_root(self, project_name: str) -> None:
        return None

    def _get_project(self, project_name: str) -> dict[str, str]:
        return self._projects.setdefault(project_name, {})

    def read_text(self, project_name: str, relative_path: str) -> str:
        return self._get_project(project_name)[relative_path]

    def write_text(self, project_name: str, relative_path: str, content: str) -> None:
        self._get_project(project_name)[relative_path] = content

    def exists(self, project_name: str, relative_path: str) -> bool:
        return relative_path in self._get_project(project_name)

    def list_paths(self, project_name: str, prefix: str) -> list[str]:
        normalized_prefix = prefix.strip().strip("/\\")
        prefix_with_sep = f"{normalized_prefix}/" if normalized_prefix else ""
        return sorted(
            path
            for path in self._get_project(project_name).keys()
            if not normalized_prefix or path == normalized_prefix or path.startswith(prefix_with_sep)
        )


def build_project_storage(base_dir: Path) -> ProjectStorage:
    from core.github_storage import GitHubProjectStorage
    from core.runtime import get_cloud_storage_repo, get_cloud_storage_token, is_cloud_runtime, validate_cloud_storage_settings

    if is_cloud_runtime():
        validate_cloud_storage_settings()
        return GitHubProjectStorage(
            repo=get_cloud_storage_repo(),
            token=get_cloud_storage_token(),
        )
    return LocalProjectStorage(base_dir)
