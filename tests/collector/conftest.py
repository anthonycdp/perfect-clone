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


@pytest.fixture
def browser():
    """Create and cleanup browser for tests."""
    manager = BrowserManager(headless=True)
    manager.start()
    yield manager
    manager.close()


@pytest.fixture
def page(browser: BrowserManager) -> Page:
    """Create a page navigated to example.com for testing."""
    browser.navigate("https://example.com", timeout=15000)
    return browser.page
