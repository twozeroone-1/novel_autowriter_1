import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as handle:
            handle.write(content)
        os.replace(temp_path, path)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=4),
    )


def _quote_env_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def upsert_env_contents(contents: str, key: str, value: str) -> str:
    normalized_lines = contents.splitlines()
    target_prefix = f"{key}="
    serialized_line = f'{key}="{_quote_env_value(value)}"'
    updated_lines: list[str] = []
    found = False

    for line in normalized_lines:
        if line.startswith(target_prefix):
            updated_lines.append(serialized_line)
            found = True
        else:
            updated_lines.append(line)

    if not found:
        updated_lines.append(serialized_line)

    line_ending = "\r\n" if "\r\n" in contents else "\n"
    return line_ending.join(updated_lines) + line_ending


def update_env_file(path: Path, key: str, value: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    atomic_write_text(path, upsert_env_contents(existing, key, value))


def remove_env_key_contents(contents: str, key: str) -> str:
    normalized_lines = contents.splitlines()
    target_prefix = f"{key}="
    updated_lines = [line for line in normalized_lines if not line.startswith(target_prefix)]
    if not updated_lines:
        return ""
    line_ending = "\r\n" if "\r\n" in contents else "\n"
    return line_ending.join(updated_lines) + line_ending


def remove_env_key(path: Path, key: str) -> None:
    if not path.exists():
        return
    existing = path.read_text(encoding="utf-8")
    updated = remove_env_key_contents(existing, key)
    atomic_write_text(path, updated)
