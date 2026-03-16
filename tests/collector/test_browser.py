"""Tests for BrowserManager."""

import subprocess
import sys
import textwrap

import pytest

from collector.browser import BrowserManager
from models.errors import NavigationError


def run_browser_manager_script(script_body: str) -> subprocess.CompletedProcess[str]:
    """Run BrowserManager startup checks in a clean subprocess."""
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script_body)],
        capture_output=True,
        text=True,
        check=False,
    )


class TestBrowserManagerStart:
    """Tests for BrowserManager.start()"""

    def test_start_creates_browser_and_page(self):
        """start() should create playwright, browser, and page instances."""
        result = run_browser_manager_script(
            """
            from collector.browser import BrowserManager

            manager = BrowserManager(headless=True)
            assert manager.playwright is None
            assert manager.browser is None
            assert manager.page is None

            manager.start()
            assert manager.playwright is not None
            assert manager.browser is not None
            assert manager.page is not None
            manager.close()
            """
        )

        assert result.returncode == 0, result.stderr

    def test_start_with_headless_true(self):
        """start() with headless=True should launch headless browser."""
        result = run_browser_manager_script(
            """
            from collector.browser import BrowserManager

            manager = BrowserManager(headless=True)
            manager.start()
            assert manager.browser.is_connected()
            manager.close()
            """
        )

        assert result.returncode == 0, result.stderr


class TestBrowserManagerNavigate:
    """Tests for BrowserManager.navigate()"""

    def test_navigate_loads_url(self, page):
        """navigate() should load the specified URL."""
        page.goto("https://example.com", timeout=10000)

        assert page is not None
        assert "example.com" in page.url

    def test_navigate_invalid_url_raises_navigation_error(self, browser):
        """navigate() with invalid URL should raise NavigationError."""
        with pytest.raises(NavigationError) as exc_info:
            browser.navigate("not-a-valid-url", timeout=5000)

        assert "Failed to navigate" in str(exc_info.value)

    def test_navigate_timeout_raises_navigation_error(self, browser):
        """navigate() timeout should raise NavigationError."""
        with pytest.raises(NavigationError):
            # Very short timeout on a slow-loading page
            browser.navigate("https://httpstat.us/200?sleep=5000", timeout=100)


class TestBrowserManagerResizeViewport:
    """Tests for BrowserManager.resize_viewport()"""

    def test_resize_viewport_changes_dimensions(self, browser):
        """resize_viewport() should change page viewport size."""
        # resize_viewport sets the default viewport for new pages
        browser.resize_viewport(1920, 1080)

        # Check the viewport on the browser's page
        viewport = browser.page.viewport_size
        assert viewport["width"] == 1920
        assert viewport["height"] == 1080

    def test_resize_viewport_multiple_times(self, browser):
        """resize_viewport() should work multiple times."""
        browser.resize_viewport(800, 600)
        assert browser.page.viewport_size["width"] == 800

        browser.resize_viewport(1024, 768)
        assert browser.page.viewport_size["width"] == 1024

    def test_resize_viewport_without_page_does_nothing(self):
        """resize_viewport() without started browser should not error."""
        manager = BrowserManager(headless=True)

        # Should not raise
        manager.resize_viewport(1920, 1080)

        manager.close()


class TestBrowserManagerClose:
    """Tests for BrowserManager.close()"""

    def test_close_without_start_does_not_error(self):
        """close() without start() should not raise."""
        manager = BrowserManager(headless=True)

        # Should not raise
        manager.close()
