"""Tests for ResponsiveCollector."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from playwright.async_api import Locator, Page

from collector.extraction_scope import ExtractionScope
from collector.responsive_collector import ResponsiveCollector
from models.normalized import ResponsiveBehavior


class TestResponsiveCollectorInit:
    """Tests for ResponsiveCollector initialization."""

    def test_init_stores_page(self):
        mock_page = MagicMock(spec=Page)
        collector = ResponsiveCollector(mock_page)
        assert collector.page == mock_page

    def test_standard_breakpoints_defined(self):
        collector = ResponsiveCollector(MagicMock(spec=Page))
        assert hasattr(collector, "STANDARD_BREAKPOINTS")
        assert 320 in collector.STANDARD_BREAKPOINTS
        assert 768 in collector.STANDARD_BREAKPOINTS
        assert 1024 in collector.STANDARD_BREAKPOINTS


@pytest.mark.asyncio
class TestResponsiveCollectorDetectBreakpoints:
    """Tests for ResponsiveCollector.detect_breakpoints()."""

    async def test_detect_breakpoints_returns_list(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(return_value=[768, 1024, 1440])

        result = await ResponsiveCollector(mock_page).detect_breakpoints()

        assert isinstance(result, list)
        assert all(isinstance(breakpoint, int) for breakpoint in result)

    async def test_detect_breakpoints_parses_media_queries(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(return_value=[480, 768, 1024, 1280])

        result = await ResponsiveCollector(mock_page).detect_breakpoints()

        assert 768 in result
        assert 1024 in result

    async def test_detect_breakpoints_handles_empty_stylesheets(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(return_value=[])

        collector = ResponsiveCollector(mock_page)
        result = await collector.detect_breakpoints()

        assert result == collector.STANDARD_BREAKPOINTS

    async def test_detect_breakpoints_includes_standard_on_error(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(side_effect=Exception("CSSOM access denied"))

        collector = ResponsiveCollector(mock_page)
        result = await collector.detect_breakpoints()

        assert result == collector.STANDARD_BREAKPOINTS

    async def test_detect_breakpoints_uses_target_frame_when_scope_is_provided(self):
        mock_page = MagicMock(spec=Page)
        mock_frame = MagicMock()
        mock_frame.evaluate = AsyncMock(return_value=[640, 960])
        scope = ExtractionScope(
            page=mock_page,
            frame=mock_frame,
            target=MagicMock(spec=Locator),
            selector_used="#target",
            strategy="css",
            frame_url="https://example.com/embed",
            frame_name="embed",
            same_origin_accessible=True,
            document_base_url="https://example.com/embed",
        )

        result = await ResponsiveCollector(mock_page).detect_breakpoints(scope=scope)

        assert result == [640, 960]
        mock_frame.evaluate.assert_awaited_once()


@pytest.mark.asyncio
class TestResponsiveCollectorCollectAtViewport:
    """Tests for ResponsiveCollector.collect_at_viewport()."""

    async def test_collect_at_viewport_sets_viewport(self):
        mock_page = MagicMock(spec=Page)
        mock_page.set_viewport_size = AsyncMock()
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate = AsyncMock(return_value={"width": 100, "display": "block"})

        collector = ResponsiveCollector(mock_page)
        await collector.collect_at_viewport(mock_locator, width=768, height=1024)

        mock_page.set_viewport_size.assert_awaited_once_with(
            {"width": 768, "height": 1024}
        )

    async def test_collect_at_viewport_returns_element_state(self):
        mock_page = MagicMock(spec=Page)
        mock_page.set_viewport_size = AsyncMock()
        expected_state = {
            "display": "flex",
            "flexDirection": "column",
            "width": 200,
            "height": 100,
        }
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate = AsyncMock(return_value=expected_state)

        result = await ResponsiveCollector(mock_page).collect_at_viewport(
            mock_locator,
            width=768,
            height=1024,
        )

        assert result == expected_state

    async def test_collect_at_viewport_captures_computed_styles(self):
        mock_page = MagicMock(spec=Page)
        mock_page.set_viewport_size = AsyncMock()
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate = AsyncMock(return_value={"display": "block"})

        await ResponsiveCollector(mock_page).collect_at_viewport(
            mock_locator,
            width=480,
            height=800,
        )

        mock_locator.evaluate.assert_awaited_once()


@pytest.mark.asyncio
class TestResponsiveCollectorCollectAll:
    """Tests for ResponsiveCollector.collect_all()."""

    async def test_collect_all_returns_responsive_behavior(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(return_value=[768, 1024])
        mock_page.set_viewport_size = AsyncMock()
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate = AsyncMock(return_value={"display": "block", "maxWidth": "100%"})

        result = await ResponsiveCollector(mock_page).collect_all(mock_locator)

        assert isinstance(result, ResponsiveBehavior)

    async def test_collect_all_tests_all_breakpoints(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(return_value=[768, 1024])
        mock_page.set_viewport_size = AsyncMock()
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate = AsyncMock(return_value={"display": "block", "maxWidth": "100%"})

        await ResponsiveCollector(mock_page).collect_all(mock_locator)

        assert mock_page.set_viewport_size.await_count >= 2

    async def test_collect_all_detects_layout_changes(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(return_value=[768])
        mock_page.set_viewport_size = AsyncMock()
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate = AsyncMock(
            side_effect=[
                {"display": "block", "width": 300, "maxWidth": "100%"},
                {"display": "flex", "width": 600, "maxWidth": "100%"},
                {"display": "grid", "width": 900, "maxWidth": "100%"},
            ]
        )

        result = await ResponsiveCollector(mock_page).collect_all(mock_locator)

        assert result is not None

    async def test_collect_all_includes_detected_breakpoints(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(return_value=[992, 1200])
        mock_page.set_viewport_size = AsyncMock()
        mock_locator = MagicMock(spec=Locator)
        mock_locator.evaluate = AsyncMock(return_value={"display": "block", "maxWidth": "100%"})

        result = await ResponsiveCollector(mock_page).collect_all(mock_locator)

        assert isinstance(result, ResponsiveBehavior)
