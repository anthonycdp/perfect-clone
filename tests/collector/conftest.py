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

import pytest_asyncio
from playwright.async_api import Page

from collector.browser import BrowserManager


@pytest_asyncio.fixture
async def browser():
    """Create and cleanup a shared async browser manager for collector tests."""
    manager = BrowserManager(headless=True)
    await manager.start()
    yield manager
    await manager.close()


@pytest_asyncio.fixture
async def page(browser: BrowserManager) -> Page:
    """Create a fresh async page for each collector test."""
    new_page = await browser.browser.new_page()
    await new_page.goto("https://example.com", wait_until="networkidle")
    yield new_page
    await new_page.close()
