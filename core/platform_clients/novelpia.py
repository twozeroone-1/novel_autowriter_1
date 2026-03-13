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
    LOGIN_URL = "https://novelpia.com/mybook/mynovel"
    DEFAULT_SELECTORS = {
        "login_username": "input[name='email']",
        "login_password": "input[name='wd']",
        "login_submit": "button[type='submit']",
        "create_title": "input[name='title']",
        "create_description": "textarea[name='description']",
        "create_submit": "button[type='submit']",
        "dismiss_event_overlay": ".event-plus-close:visible",
        "dismiss_event_overlay_secondary": "p.later-close:visible",
        "episode_category": "#content_cate",
        "episode_title": "#content_subject",
        "episode_body": ".note-editable",
        "episode_submit": ".btn.btn-block.btn-primary.s_inv",
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
            browser.goto(self._login_url())
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
        editor_url = upload_url_template.format(work_id=request.work_id)
        try:
            browser.goto(editor_url)
            browser.fill(selectors["episode_title"], request.episode_title)
            browser.fill(selectors["episode_body"], request.content)
            if hasattr(browser, "select_option"):
                browser.select_option(selectors["episode_category"], _content_category_value(request.visibility))
            if hasattr(browser, "click_if_present"):
                dismissed = browser.click_if_present(selectors["dismiss_event_overlay"], timeout_ms=2000)
                if not dismissed:
                    browser.click_if_present(selectors["dismiss_event_overlay_secondary"], timeout_ms=1000)
            browser.click(selectors["episode_submit"])
            if hasattr(browser, "wait_for_url_change"):
                if not browser.wait_for_url_change(editor_url, timeout_ms=10000):
                    raise PlatformError(
                        "Novelpia episode submission did not leave the editor page.",
                        error_type="retryable",
                    )
                if browser.current_url.endswith("write_proc") and not browser.wait_for_url_change(
                    browser.current_url,
                    timeout_ms=10000,
                ):
                    raise PlatformError(
                        "Novelpia episode submission did not reach the viewer page.",
                        error_type="retryable",
                    )
            elif browser.current_url == editor_url:
                raise PlatformError(
                    "Novelpia episode submission did not leave the editor page.",
                    error_type="retryable",
                )
        except Exception as exc:
            if isinstance(exc, PlatformError):
                raise
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

    def _login_url(self) -> str:
        create_work_url = str(self.platform_config.get("create_work_url", "")).strip()
        if create_work_url:
            return create_work_url
        return self.LOGIN_URL

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


def _content_category_value(visibility: str) -> str:
    if str(visibility).strip().lower() == "private":
        return "5"
    return "24"
