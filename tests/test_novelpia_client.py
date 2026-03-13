import unittest

from core.platform_clients.base import EpisodeUploadRequest, PlatformError, PlatformWorkMetadata


class FakeBrowserSession:
    def __init__(
        self,
        *,
        click_url: str = "",
        click_urls: list[str] | None = None,
        fail_on_fill: str = "",
        present_selectors: set[str] | None = None,
    ):
        self.actions: list[tuple[str, str, str]] = []
        self.current_url = ""
        self.click_urls = list(click_urls or ([click_url] if click_url else []))
        self.fail_on_fill = fail_on_fill
        self.present_selectors = set(present_selectors or set())

    def goto(self, url: str) -> None:
        self.current_url = url
        self.actions.append(("goto", url, ""))

    def fill(self, selector: str, value: str) -> None:
        if self.fail_on_fill:
            raise RuntimeError(self.fail_on_fill)
        self.actions.append(("fill", selector, value))

    def click(self, selector: str) -> None:
        self.actions.append(("click", selector, ""))
        if self.click_urls:
            self.current_url = self.click_urls.pop(0)

    def select_option(self, selector: str, value: str) -> None:
        self.actions.append(("select_option", selector, value))

    def click_if_present(self, selector: str, timeout_ms: int = 0) -> bool:
        self.actions.append(("click_if_present", selector, str(timeout_ms)))
        if selector not in self.present_selectors:
            return False
        self.click(selector)
        return True

    def wait_for_url_change(self, previous_url: str, timeout_ms: int = 0) -> bool:
        self.actions.append(("wait_for_url_change", previous_url, str(timeout_ms)))
        if self.current_url == previous_url and self.click_urls:
            self.current_url = self.click_urls.pop(0)
        return self.current_url != previous_url

    def close(self) -> None:
        self.actions.append(("close", "", ""))


class TestNovelpiaClient(unittest.TestCase):
    def test_novelpia_client_requires_credentials_before_login(self):
        from core.platform_clients.novelpia import NovelpiaClient

        client = NovelpiaClient(username="", password="", browser_session=FakeBrowserSession())

        with self.assertRaises(PlatformError) as context:
            client.login()

        self.assertEqual(context.exception.error_type, "requires_user_action")

    def test_login_uses_main_site_email_form_on_writer_entry(self):
        from core.platform_clients.novelpia import NovelpiaClient

        browser = FakeBrowserSession()
        client = NovelpiaClient(
            username="writer-id",
            password="secret",
            browser_session=browser,
            platform_config={
                "create_work_url": "https://novelpia.com/publishing/new",
            },
        )

        client.login()

        self.assertEqual(
            browser.actions[:4],
            [
                ("goto", "https://novelpia.com/publishing/new", ""),
                ("fill", "input[name='email']", "writer-id"),
                ("fill", "input[name='wd']", "secret"),
                ("click", "button[type='submit']", ""),
            ],
        )

    def test_novelpia_client_classifies_additional_auth_as_user_action(self):
        from core.platform_clients.novelpia import NovelpiaClient

        client = NovelpiaClient(
            username="writer-id",
            password="secret",
            browser_session=FakeBrowserSession(fail_on_fill="additional auth required"),
            platform_config={
                "upload_url_template": "https://cp.novelpia.com/work/{work_id}/episode/new",
            },
        )

        with self.assertRaises(PlatformError) as context:
            client.upload_episode(
                EpisodeUploadRequest(
                    work_id="work-1",
                    episode_title="Episode 12",
                    content="body",
                )
            )

        self.assertEqual(context.exception.error_type, "requires_user_action")

    def test_ensure_work_returns_existing_work_id_when_present(self):
        from core.platform_clients.novelpia import NovelpiaClient

        browser = FakeBrowserSession()
        client = NovelpiaClient(
            username="writer-id",
            password="secret",
            browser_session=browser,
        )

        result = client.ensure_work(
            PlatformWorkMetadata(title="Project title"),
            work_id="work-1",
        )

        self.assertTrue(result.success)
        self.assertEqual(result.work_id, "work-1")
        self.assertEqual(browser.actions, [])

    def test_upload_episode_returns_success_payload(self):
        from core.platform_clients.novelpia import NovelpiaClient

        browser = FakeBrowserSession(click_url="https://novelpia.com/mynovel/all/416704")
        client = NovelpiaClient(
            username="writer-id",
            password="secret",
            browser_session=browser,
            platform_config={
                "upload_url_template": "https://novelpia.com/mynovel/all/write/{work_id}",
            },
        )

        result = client.upload_episode(
            EpisodeUploadRequest(
                work_id="work-1",
                episode_title="Episode 12",
                content="body",
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.episode_id, "416704")

    def test_upload_episode_uses_real_writer_form_selectors(self):
        from core.platform_clients.novelpia import NovelpiaClient

        browser = FakeBrowserSession(click_url="https://novelpia.com/mynovel/all/416704")
        client = NovelpiaClient(
            username="writer-id",
            password="secret",
            browser_session=browser,
            platform_config={
                "upload_url_template": "https://novelpia.com/mynovel/all/write/{work_id}",
            },
        )

        client.upload_episode(
            EpisodeUploadRequest(
                work_id="416704",
                episode_title="Episode 12",
                content="body",
            )
        )

        self.assertEqual(
            browser.actions[:7],
            [
                ("goto", "https://novelpia.com/mynovel/all/write/416704", ""),
                ("fill", "#content_subject", "Episode 12"),
                ("fill", ".note-editable", "body"),
                ("select_option", "#content_cate", "24"),
                ("click_if_present", ".event-plus-close:visible", "2000"),
                ("click_if_present", "p.later-close:visible", "1000"),
                ("click", ".btn.btn-block.btn-primary.s_inv", ""),
            ],
        )

    def test_upload_episode_sets_private_category_when_requested(self):
        from core.platform_clients.novelpia import NovelpiaClient

        browser = FakeBrowserSession(click_url="https://novelpia.com/mynovel/all/416704")
        client = NovelpiaClient(
            username="writer-id",
            password="secret",
            browser_session=browser,
            platform_config={
                "upload_url_template": "https://novelpia.com/mynovel/all/write/{work_id}",
            },
        )

        client.upload_episode(
            EpisodeUploadRequest(
                work_id="416704",
                episode_title="Episode 12",
                content="body",
                visibility="private",
            )
        )

        self.assertIn(
            ("select_option", "#content_cate", "5"),
            browser.actions,
        )

    def test_upload_episode_dismisses_event_overlay_when_present(self):
        from core.platform_clients.novelpia import NovelpiaClient

        browser = FakeBrowserSession(
            click_url="https://novelpia.com/mynovel/all/416704",
            present_selectors={".event-plus-close:visible"},
        )
        client = NovelpiaClient(
            username="writer-id",
            password="secret",
            browser_session=browser,
            platform_config={
                "upload_url_template": "https://novelpia.com/mynovel/all/write/{work_id}",
            },
        )

        client.upload_episode(
            EpisodeUploadRequest(
                work_id="416704",
                episode_title="Episode 12",
                content="body",
            )
        )

        self.assertIn(
            ("click_if_present", ".event-plus-close:visible", "2000"),
            browser.actions,
        )

    def test_upload_episode_waits_for_viewer_redirect_before_returning_episode_id(self):
        from core.platform_clients.novelpia import NovelpiaClient

        browser = FakeBrowserSession(
            click_urls=[
                "https://novelpia.com/mynovel/all/write_proc",
                "https://novelpia.com/viewer/5471585",
            ]
        )
        client = NovelpiaClient(
            username="writer-id",
            password="secret",
            browser_session=browser,
            platform_config={
                "upload_url_template": "https://novelpia.com/mynovel/all/write/{work_id}",
            },
        )

        result = client.upload_episode(
            EpisodeUploadRequest(
                work_id="416704",
                episode_title="Episode 12",
                content="body",
            )
        )

        self.assertEqual(result.episode_id, "5471585")
        self.assertIn(
            ("wait_for_url_change", "https://novelpia.com/mynovel/all/write/416704", "10000"),
            browser.actions,
        )
        self.assertIn(
            ("wait_for_url_change", "https://novelpia.com/mynovel/all/write_proc", "10000"),
            browser.actions,
        )


if __name__ == "__main__":
    unittest.main()
