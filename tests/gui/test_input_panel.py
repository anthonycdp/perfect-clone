"""Tests for InputPanel."""

import tkinter as tk
from unittest.mock import Mock

import pytest

from gui.panels.input_panel import InputPanel


def create_root() -> tk.Tk:
    """Create a Tk root or skip when Tk is not installed correctly."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk is not available in this environment: {exc}")
    root.withdraw()
    return root


class TestInputPanel:
    """GUI tests for InputPanel."""

    def test_full_page_mode_disables_selector_controls(self):
        """Full-page mode should disable strategy and query input."""
        root = create_root()

        try:
            panel = InputPanel(root, on_extract_callback=Mock())
            panel.mode_var.set("full_page")

            assert str(panel.selector_text["state"]) == "disabled"
            assert str(panel.extract_btn["text"]) == "Extract Landing Page"
            assert "ignores selector/query" in panel.hint_var.get()
        finally:
            root.destroy()

    def test_component_mode_requires_query(self):
        """Component mode should not invoke the callback without a selector query."""
        root = create_root()

        try:
            callback = Mock()
            panel = InputPanel(root, on_extract_callback=callback)
            panel.url_entry.insert(0, "https://example.com")

            panel._on_extract_click()

            callback.assert_not_called()
        finally:
            root.destroy()

    def test_full_page_mode_invokes_callback_without_query(self):
        """Full-page mode should allow extraction without a selector."""
        root = create_root()

        try:
            callback = Mock()
            panel = InputPanel(root, on_extract_callback=callback)
            panel.url_entry.insert(0, "https://example.com")
            panel.mode_var.set("full_page")

            panel._on_extract_click()

            callback.assert_called_once_with(
                "https://example.com",
                "full_page",
                panel.strategy_var.get(),
                "",
            )
        finally:
            root.destroy()
