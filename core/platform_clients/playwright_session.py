try:
    from playwright.sync_api import sync_playwright
except ModuleNotFoundError:
    sync_playwright = None


class PlaywrightBrowserSession:
    def __init__(self, *, headless: bool = True):
        if sync_playwright is None:
            raise RuntimeError(
                "Playwright is not installed. Run `python -m pip install playwright` "
                "and `python -m playwright install chromium` first."
            )
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)
        self._page = self._browser.new_page()

    @property
    def current_url(self) -> str:
        return self._page.url

    def goto(self, url: str) -> None:
        self._page.goto(url, wait_until="domcontentloaded")

    def fill(self, selector: str, value: str) -> None:
        self._page.locator(selector).first.fill(value)

    def click(self, selector: str) -> None:
        self._page.locator(selector).first.click()

    def close(self) -> None:
        self._browser.close()
        self._playwright.stop()
