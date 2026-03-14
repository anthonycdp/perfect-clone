"""Browser lifecycle management using Playwright."""

from typing import Optional

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from models.errors import NavigationError


class BrowserManager:
    """Manages Playwright browser lifecycle."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def start(self) -> None:
        """Initialize browser and page."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()

    def navigate(self, url: str, timeout: int = 30000) -> None:
        """Navigate to URL and wait for page load."""
        if not self.page:
            self.start()

        try:
            self.page.goto(url, timeout=timeout, wait_until="networkidle")
        except Exception as e:
            raise NavigationError(f"Failed to navigate to {url}: {str(e)}")

    def resize_viewport(self, width: int, height: int) -> None:
        """Resize browser viewport."""
        if self.page:
            self.page.set_viewport_size({"width": width, "height": height})

    def close(self) -> None:
        """Release all browser resources."""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

        self.page = None
        self.browser = None
        self.playwright = None

    def __enter__(self) -> "BrowserManager":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
