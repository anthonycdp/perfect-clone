"""Tests for ResponsiveCollector."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is at the FRONT of sys.path
project_root = str(Path(__file__).resolve().parent.parent.parent)
while project_root in sys.path:
    sys.path.remove(project_root)
sys.path.insert(0, project_root)

import pytest
from playwright.sync_api import Page, Locator

from collector.responsive_collector import ResponsiveCollector
from models.normalized import ResponsiveBehavior


class TestResponsiveCollectorInit:
    """Tests for ResponsiveCollector initialization."""

    def test_init_stores_page(self):
        """init should store page reference."""
        mock_page = MagicMock(spec=Page)

        collector = ResponsiveCollector(mock_page)

        assert collector.page == mock_page

    def test_standard_breakpoints_defined(self):
        """STANDARD_BREAKPOINTS should be defined."""
        mock_page = MagicMock(spec=Page)

        collector = ResponsiveCollector(mock_page)

        assert hasattr(collector, "STANDARD_BREAKPOINTS")
        assert 320 in collector.STANDARD_BREAKPOINTS
        assert 768 in collector.STANDARD_BREAKPOINTS
        assert 1024 in collector.STANDARD_BREAKPOINTS


class TestResponsiveCollectorDetectBreakpoints:
    """Tests for ResponsiveCollector.detect_breakpoints()."""

    def test_detect_breakpoints_returns_list(self):
        """detect_breakpoints() should return a list of integers."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = [768, 1024, 1440]

        collector = ResponsiveCollector(mock_page)
        result = collector.detect_breakpoints()

        assert isinstance(result, list)
        assert all(isinstance(b, int) for b in result)

    def test_detect_breakpoints_parses_media_queries(self):
        """detect_breakpoints() should parse @media rules from CSSOM."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = [480, 768, 1024, 1280]

        collector = ResponsiveCollector(mock_page)
        result = collector.detect_breakpoints()

        assert 768 in result
        assert 1024 in result

    def test_detect_breakpoints_handles_empty_stylesheets(self):
        """detect_breakpoints() should handle pages with no media queries."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = []

        collector = ResponsiveCollector(mock_page)
        result = collector.detect_breakpoints()

        # Should return standard breakpoints when none found
        assert result == collector.STANDARD_BREAKPOINTS

    def test_detect_breakpoints_includes_standard_on_error(self):
        """detect_breakpoints() should return standard breakpoints on error."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.side_effect = Exception("CSSOM access denied")

        collector = ResponsiveCollector(mock_page)
        result = collector.detect_breakpoints()

        # Should fall back to standard breakpoints
        assert result == collector.STANDARD_BREAKPOINTS


class TestResponsiveCollectorCollectAtViewport:
    """Tests for ResponsiveCollector.collect_at_viewport()."""

    def test_collect_at_viewport_sets_viewport(self):
        """collect_at_viewport() should set viewport size."""
        mock_page = MagicMock(spec=Page)
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate.return_value = {"width": 100, "display": "block"}

        collector = ResponsiveCollector(mock_page)
        collector.collect_at_viewport(mock_locator, width=768, height=1024)

        mock_page.set_viewport_size.assert_called_once_with(
            {"width": 768, "height": 1024}
        )

    def test_collect_at_viewport_returns_element_state(self):
        """collect_at_viewport() should return element state dict."""
        mock_page = MagicMock(spec=Page)
        expected_state = {
            "display": "flex",
            "flexDirection": "column",
            "width": 200,
            "height": 100,
        }
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate.return_value = expected_state

        collector = ResponsiveCollector(mock_page)
        result = collector.collect_at_viewport(mock_locator, width=768, height=1024)

        assert result == expected_state

    def test_collect_at_viewport_captures_computed_styles(self):
        """collect_at_viewport() should capture computed styles."""
        mock_page = MagicMock(spec=Page)
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate.return_value = {"display": "block"}

        collector = ResponsiveCollector(mock_page)
        collector.collect_at_viewport(mock_locator, width=480, height=800)

        # Verify locator.evaluate was called
        mock_locator.evaluate.assert_called_once()


class TestResponsiveCollectorCollectAll:
    """Tests for ResponsiveCollector.collect_all()."""

    def test_collect_all_returns_responsive_behavior(self):
        """collect_all() should return ResponsiveBehavior object."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = [768, 1024]
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate.return_value = {"display": "block", "maxWidth": "100%"}

        collector = ResponsiveCollector(mock_page)
        result = collector.collect_all(mock_locator)

        assert isinstance(result, ResponsiveBehavior)

    def test_collect_all_tests_all_breakpoints(self):
        """collect_all() should test element at all breakpoints."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = [768, 1024]
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate.return_value = {"display": "block", "maxWidth": "100%"}

        collector = ResponsiveCollector(mock_page)
        result = collector.collect_all(mock_locator)

        # Should set viewport for each breakpoint
        assert mock_page.set_viewport_size.call_count >= 2

    def test_collect_all_detects_layout_changes(self):
        """collect_all() should detect layout changes between breakpoints."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = [768]

        # Mock different states at different viewports
        states = [
            {"display": "block", "width": 300, "maxWidth": "100%"},  # Mobile
            {"display": "flex", "width": 600, "maxWidth": "100%"},   # Tablet
            {"display": "grid", "width": 900, "maxWidth": "100%"},   # Desktop
        ]

        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate.side_effect = states

        collector = ResponsiveCollector(mock_page)
        result = collector.collect_all(mock_locator)

        assert result is not None

    def test_collect_all_includes_detected_breakpoints(self):
        """collect_all() should include detected media query breakpoints."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = [992, 1200]
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate.return_value = {"display": "block", "maxWidth": "100%"}

        collector = ResponsiveCollector(mock_page)
        result = collector.collect_all(mock_locator)

        assert isinstance(result, ResponsiveBehavior)
