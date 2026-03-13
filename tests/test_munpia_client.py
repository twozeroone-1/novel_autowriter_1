import unittest

from core.platform_clients.base import EpisodeUploadRequest, PlatformError, PlatformWorkMetadata


class FakeBrowserSession:
    def __init__(self, *, click_url: str = "", fail_on_fill: str = ""):
        self.actions: list[tuple[str, str, str]] = []
        self.current_url = ""
        self.click_url = click_url
        self.fail_on_fill = fail_on_fill

    def goto(self, url: str) -> None:
        self.current_url = url
        self.actions.append(("goto", url, ""))

    def fill(self, selector: str, value: str) -> None:
        if self.fail_on_fill:
            raise RuntimeError(self.fail_on_fill)
        self.actions.append(("fill", selector, value))

    def click(self, selector: str) -> None:
        self.actions.append(("click", selector, ""))
        if self.click_url:
            self.current_url = self.click_url

    def close(self) -> None:
        self.actions.append(("close", "", ""))


class TestMunpiaClient(unittest.TestCase):
    def test_munpia_client_requires_credentials_before_login(self):
        from core.platform_clients.munpia import MunpiaClient

        client = MunpiaClient(username="", password="", browser_session=FakeBrowserSession())

        with self.assertRaises(PlatformError) as context:
            client.login()

        self.assertEqual(context.exception.error_type, "requires_user_action")

    def test_login_uses_public_login_form_ids(self):
        from core.platform_clients.munpia import MunpiaClient

        browser = FakeBrowserSession()
        client = MunpiaClient(
            username="writer-id",
            password="secret",
            browser_session=browser,
        )

        client.login()

        self.assertEqual(
            browser.actions[:4],
            [
                ("goto", "https://nssl.munpia.com/login", ""),
                ("fill", "#username", "writer-id"),
                ("fill", "#password", "secret"),
                ("click", "button[type='submit']", ""),
            ],
        )

    def test_munpia_client_maps_missing_editor_field_to_retryable_error(self):
        from core.platform_clients.munpia import MunpiaClient

        client = MunpiaClient(
            username="writer-id",
            password="secret",
            browser_session=FakeBrowserSession(fail_on_fill="editor field missing"),
            platform_config={
                "upload_url_template": "https://munpia.test/work/{work_id}/episode/new",
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

        self.assertEqual(context.exception.error_type, "retryable")

    def test_ensure_work_returns_existing_work_id_when_present(self):
        from core.platform_clients.munpia import MunpiaClient

        browser = FakeBrowserSession()
        client = MunpiaClient(
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

    def test_upload_episode_returns_episode_id_on_success(self):
        from core.platform_clients.munpia import MunpiaClient

        browser = FakeBrowserSession(click_url="https://munpia.test/work/work-1/episode/episode-7")
        client = MunpiaClient(
            username="writer-id",
            password="secret",
            browser_session=browser,
            platform_config={
                "upload_url_template": "https://munpia.test/work/{work_id}/episode/new",
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
        self.assertEqual(result.episode_id, "episode-7")


if __name__ == "__main__":
    unittest.main()
