"""Shared fixtures for collector tests."""

import sys
from pathlib import Path

# Ensure project root is at the FRONT of sys.path
# This is critical because pytest adds 'tests' directory to path,
# which can cause test subdirectories to shadow source packages
project_root = str(Path(__file__).resolve().parent.parent.parent)
while project_root in sys.path:
    sys.path.remove(project_root)
sys.path.insert(0, project_root)

import pytest
from playwright.sync_api import Page

from collector.browser import BrowserManager


def pytest_configure(config):
    """Disable asyncio and anyio plugins for collector tests.

    Playwright sync API cannot run inside an asyncio event loop,
    so we need to disable these plugins for browser tests.
    """
    config.pluginmanager.set_blocked("asyncio")
    config.pluginmanager.set_blocked("anyio")


@pytest.fixture(scope="session")
def browser():
    """Create and cleanup browser for tests.

    Uses session scope to avoid event loop conflicts between tests.
    Playwright sync API creates an event loop that persists across tests,
    so we reuse the same browser instance throughout the session.
    """
    manager = BrowserManager(headless=True)
    manager.start()
    yield manager
    manager.close()


@pytest.fixture
def page(browser: BrowserManager) -> Page:
    """Create a new page for each test.

    Creates a fresh page (tab) for each test to ensure isolation
    while reusing the same browser instance.
    """
    # Create a new page for this test
    new_page = browser.browser.new_page()
    # Navigate to example.com for tests
    new_page.goto("https://example.com", wait_until="networkidle")
    yield new_page
    new_page.close()
