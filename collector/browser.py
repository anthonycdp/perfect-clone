"""Browser lifecycle management using Playwright."""

from typing import Optional

from playwright.async_api import Browser, Page, Playwright, async_playwright

from models.errors import NavigationError


class BrowserManager:
    """Manages Playwright browser lifecycle."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def start(self) -> None:
        """Initialize browser and page."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()

    async def navigate(self, url: str, timeout: int = 30000) -> None:
        """Navigate to URL and wait for page load."""
        if not self.page:
            await self.start()

        try:
            await self.page.goto(url, timeout=timeout, wait_until="networkidle")
        except Exception as e:
            raise NavigationError(f"Failed to navigate to {url}: {str(e)}")

    async def resize_viewport(self, width: int, height: int) -> None:
        """Resize browser viewport."""
        if self.page:
            await self.page.set_viewport_size({"width": width, "height": height})

    async def close(self) -> None:
        """Release all browser resources."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        self.page = None
        self.browser = None
        self.playwright = None

    async def __aenter__(self) -> "BrowserManager":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
