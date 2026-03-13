from urllib.parse import urlparse

from core.platform_clients.base import (
    BasePlatformClient,
    EpisodeUploadRequest,
    PlatformActionResult,
    PlatformError,
    PlatformWorkMetadata,
)
from core.platform_clients.playwright_session import PlaywrightBrowserSession


class NovelpiaClient(BasePlatformClient):
    LOGIN_URL = "https://cp.novelpia.com/auth/login"
    DEFAULT_SELECTORS = {
        "login_username": "#userid",
        "login_password": "#pwd",
        "login_submit": "button[type='submit']",
        "create_title": "input[name='title']",
        "create_description": "textarea[name='description']",
        "create_submit": "button[type='submit']",
        "episode_title": "input[name='title']",
        "episode_body": "textarea[name='content']",
        "episode_submit": "button[type='submit']",
    }

    def __init__(
        self,
        *,
        username: str,
        password: str,
        browser_session=None,
        platform_config: dict | None = None,
        headless: bool = True,
    ):
        self.username = username.strip()
        self.password = password.strip()
        self._browser_session = browser_session
        self.platform_config = platform_config or {}
        self.headless = headless

    def login(self) -> PlatformActionResult:
        self._require_credentials()
        browser = self._get_browser()
        selectors = self._selectors()
        try:
            browser.goto(self.LOGIN_URL)
            browser.fill(selectors["login_username"], self.username)
            browser.fill(selectors["login_password"], self.password)
            browser.click(selectors["login_submit"])
        except Exception as exc:
            raise self._classify_browser_error(exc) from exc
        return PlatformActionResult(status="done", success=True)

    def ensure_work(self, metadata: PlatformWorkMetadata, work_id: str = "") -> PlatformActionResult:
        if work_id:
            return PlatformActionResult(status="done", success=True, work_id=work_id)

        create_work_url = str(self.platform_config.get("create_work_url", "")).strip()
        if not create_work_url:
            raise PlatformError("Novelpia work creation URL is not configured.", error_type="requires_user_action")

        browser = self._get_browser()
        selectors = self._selectors()
        try:
            browser.goto(create_work_url)
            browser.fill(selectors["create_title"], metadata.title)
            browser.fill(selectors["create_description"], metadata.description)
            browser.click(selectors["create_submit"])
        except Exception as exc:
            raise self._classify_browser_error(exc) from exc

        created_work_id = _extract_last_url_segment(browser.current_url)
        return PlatformActionResult(status="done", success=True, work_id=created_work_id)

    def upload_episode(self, request: EpisodeUploadRequest) -> PlatformActionResult:
        if not request.work_id.strip():
            raise PlatformError("Novelpia work ID is required for episode upload.", error_type="permanent")

        upload_url_template = str(self.platform_config.get("upload_url_template", "")).strip()
        if not upload_url_template:
            raise PlatformError("Novelpia upload URL template is not configured.", error_type="requires_user_action")

        browser = self._get_browser()
        selectors = self._selectors()
        try:
            browser.goto(upload_url_template.format(work_id=request.work_id))
            browser.fill(selectors["episode_title"], request.episode_title)
            browser.fill(selectors["episode_body"], request.content)
            browser.click(selectors["episode_submit"])
        except Exception as exc:
            raise self._classify_browser_error(exc) from exc

        return PlatformActionResult(
            status="done",
            success=True,
            work_id=request.work_id,
            episode_id=_extract_last_url_segment(browser.current_url),
        )

    def close(self) -> None:
        if self._browser_session is not None:
            self._browser_session.close()
            self._browser_session = None

    def _require_credentials(self) -> None:
        if not self.username or not self.password:
            raise PlatformError("Novelpia credentials are missing.", error_type="requires_user_action")

    def _get_browser(self):
        if self._browser_session is None:
            self._browser_session = PlaywrightBrowserSession(headless=self.headless)
        return self._browser_session

    def _selectors(self) -> dict:
        return self.DEFAULT_SELECTORS | self.platform_config.get("selectors", {})

    def _classify_browser_error(self, exc: Exception) -> PlatformError:
        message = str(exc).strip() or exc.__class__.__name__
        lowered = message.lower()
        if "captcha" in lowered or "auth" in lowered or "login" in lowered:
            return PlatformError(message, error_type="requires_user_action")
        if "editor" in lowered or "timeout" in lowered or "missing" in lowered:
            return PlatformError(message, error_type="retryable")
        return PlatformError(message, error_type="permanent")


def _extract_last_url_segment(url: str) -> str:
    parsed = urlparse(url)
    path_segments = [segment for segment in parsed.path.split("/") if segment]
    if path_segments:
        return path_segments[-1]
    return ""
