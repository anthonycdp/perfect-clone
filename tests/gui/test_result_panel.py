"""Tests for ResultPanel."""

from pathlib import Path

import tkinter as tk
from unittest.mock import patch

import pytest
from PIL import Image

from gui.panels.result_panel import ResultPanel
from models.synthesis import (
    ComponentDescription,
    ComponentTree,
    Dependency,
    ResponsiveRule,
    SynthesisOutput,
)


def create_root() -> tk.Tk:
    """Create a Tk root or skip when Tk is unavailable."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk is not available in this environment: {exc}")
    root.withdraw()
    return root


def build_result() -> SynthesisOutput:
    """Create a valid synthesis result."""
    return SynthesisOutput(
        description=ComponentDescription(
            technical="Technical",
            visual="Visual",
            purpose="Purpose",
        ),
        component_tree=ComponentTree(
            name="HeroSection",
            role="container",
            children=[],
        ),
        interactions=[],
        responsive_rules=[
            ResponsiveRule(
                breakpoint="768px",
                changes=["Stack items vertically"],
            )
        ],
        dependencies=[
            Dependency(
                name="None",
                reason="No dependency",
            )
        ],
        recreation_prompt="Generated prompt",
    )


class TestResultPanel:
    """GUI tests for ResultPanel."""

    def test_display_result_loads_screenshot_preview(self, tmp_path: Path):
        """display_result() should store screenshot path and enable saving."""
        image_path = tmp_path / "preview.png"
        Image.new("RGB", (120, 80), "navy").save(image_path)

        root = create_root()

        try:
            panel = ResultPanel(root)
            panel.display_result(
                build_result(),
                full_json={"ok": True},
                screenshot_path=str(image_path),
                result_kind="Landing Page",
            )

            assert panel.current_screenshot_path == str(image_path)
            assert str(image_path) in panel.screenshot_path_var.get()
            assert str(panel.save_image_btn["state"]) == "normal"
            assert panel.screenshot_preview_image is not None
            assert panel.result_summary_var.get() == "Current result: Landing Page"
        finally:
            root.destroy()

    def test_save_screenshot_copies_file(self, tmp_path: Path):
        """save action should copy the current screenshot to the selected location."""
        source_path = tmp_path / "source.png"
        destination_path = tmp_path / "saved.png"
        Image.new("RGB", (40, 40), "black").save(source_path)

        root = create_root()

        try:
            panel = ResultPanel(root)
            panel.display_screenshot(str(source_path))

            with (
                patch("gui.panels.result_panel.filedialog.asksaveasfilename", return_value=str(destination_path)),
                patch("gui.panels.result_panel.messagebox.showinfo") as mock_showinfo,
            ):
                panel._save_screenshot()

            assert destination_path.exists()
            assert destination_path.read_bytes() == source_path.read_bytes()
            mock_showinfo.assert_called_once()
        finally:
            root.destroy()
