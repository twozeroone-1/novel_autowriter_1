from pathlib import Path

from core.app_paths import DATA_PROJECTS_DIR


def load_chapter_source(project_name: str, source_path: str | Path) -> dict[str, str | Path]:
    resolved_path = resolve_project_source_path(project_name, source_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Chapter source does not exist: {resolved_path}")

    content = resolved_path.read_text(encoding="utf-8")
    return {
        "path": resolved_path,
        "title": _extract_title(content, resolved_path),
        "content": content,
    }


def resolve_project_source_path(project_name: str, source_path: str | Path) -> Path:
    candidate = Path(source_path)
    if candidate.is_absolute():
        return candidate
    return (DATA_PROJECTS_DIR / project_name / candidate).resolve()


def _extract_title(content: str, resolved_path: Path) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                return heading
    return resolved_path.stem
