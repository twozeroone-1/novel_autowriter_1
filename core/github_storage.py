from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from core.storage import ProjectStorage


class GitHubProjectStorage(ProjectStorage):
    def __init__(
        self,
        *,
        repo: str,
        token: str,
        base_prefix: str = "projects",
        request: Callable | None = None,
    ):
        self.repo = repo.strip()
        self.token = token.strip()
        self.base_prefix = base_prefix.strip().strip("/\\")
        self.request = request or self._default_request

    def project_root(self, project_name: str) -> None:
        return None

    def _project_path(self, project_name: str, relative_path: str) -> str:
        clean_relative = relative_path.strip().strip("/\\")
        if self.base_prefix:
            return f"{self.base_prefix}/{project_name}/{clean_relative}"
        return f"{project_name}/{clean_relative}"

    def _build_url(self, path: str) -> str:
        encoded_path = quote(path, safe="/")
        return f"https://api.github.com/repos/{self.repo}/contents/{encoded_path}"

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "novel-autowriter",
        }

    def _default_request(self, method: str, url: str, *, headers: dict, body: dict | None = None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(url, headers=headers, method=method, data=data)
        try:
            with urlopen(request) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return type("Response", (), {"status_code": response.status, "payload": payload})()
        except HTTPError as exc:
            payload = {}
            try:
                payload = json.loads(exc.read().decode("utf-8"))
            except Exception:
                payload = {}
            return type("Response", (), {"status_code": exc.code, "payload": payload})()

    def _read_metadata(self, project_name: str, relative_path: str) -> dict:
        response = self.request(
            "GET",
            self._build_url(self._project_path(project_name, relative_path)),
            headers=self._headers(),
            body=None,
        )
        if response.status_code == 404:
            raise FileNotFoundError(relative_path)
        if response.status_code >= 400:
            raise RuntimeError(f"GitHub read failed with status {response.status_code}")
        return dict(response.payload)

    def read_text(self, project_name: str, relative_path: str) -> str:
        payload = self._read_metadata(project_name, relative_path)
        encoded = str(payload.get("content", ""))
        if str(payload.get("encoding", "")).lower() != "base64":
            raise RuntimeError("Unsupported GitHub content encoding")
        normalized = encoded.replace("\n", "")
        return base64.b64decode(normalized).decode("utf-8")

    def write_text(self, project_name: str, relative_path: str, content: str) -> None:
        sha = None
        try:
            sha = self._read_metadata(project_name, relative_path).get("sha")
        except FileNotFoundError:
            sha = None

        body = {
            "message": f"Update {self._project_path(project_name, relative_path)}",
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        }
        if sha:
            body["sha"] = str(sha)

        response = self.request(
            "PUT",
            self._build_url(self._project_path(project_name, relative_path)),
            headers=self._headers(),
            body=body,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"GitHub write failed with status {response.status_code}")

    def exists(self, project_name: str, relative_path: str) -> bool:
        try:
            self._read_metadata(project_name, relative_path)
        except FileNotFoundError:
            return False
        return True

    def list_paths(self, project_name: str, prefix: str) -> list[str]:
        relative_prefix = prefix.strip().strip("/\\")
        response = self.request(
            "GET",
            self._build_url(self._project_path(project_name, relative_prefix)),
            headers=self._headers(),
            body=None,
        )
        if response.status_code == 404:
            return []
        if response.status_code >= 400:
            raise RuntimeError(f"GitHub list failed with status {response.status_code}")

        payload = response.payload
        if isinstance(payload, dict):
            item_type = str(payload.get("type", "")).lower()
            if item_type == "file":
                return [relative_prefix] if relative_prefix else []
            return []

        results: list[str] = []
        for item in payload:
            item_type = str(item.get("type", "")).lower()
            item_path = str(item.get("path", ""))
            project_prefix = self._project_path(project_name, "")
            if not item_path.startswith(project_prefix):
                continue
            relative_path = item_path[len(project_prefix) :].lstrip("/")
            if item_type == "file":
                results.append(relative_path)
        return sorted(results)
