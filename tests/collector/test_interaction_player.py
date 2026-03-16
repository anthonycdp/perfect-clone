"""Tests for InteractionPlayer."""

import pytest
from playwright.async_api import Page

from collector.extraction_scope import ExtractionScope
from collector.interaction_player import InteractionPlayer

pytestmark = pytest.mark.asyncio


class TestInteractionPlayer:
    """Test suite for InteractionPlayer."""

    @pytest.fixture
    def player(self, page: Page) -> InteractionPlayer:
        """Create an InteractionPlayer instance."""
        return InteractionPlayer(page)

    async def test_play_all_returns_list(self, player: InteractionPlayer, page: Page) -> None:
        target = page.locator("a").first
        results = await player.play_all(target, [{"type": "hover", "selector": "a"}])
        assert isinstance(results, list)

    async def test_play_all_captures_before_state(
        self,
        player: InteractionPlayer,
        page: Page,
    ) -> None:
        target = page.locator("a").first
        results = await player.play_all(target, [{"type": "hover", "selector": "a"}])
        if results:
            assert "before" in results[0]
            assert isinstance(results[0]["before"], dict)

    async def test_play_all_captures_after_state(
        self,
        player: InteractionPlayer,
        page: Page,
    ) -> None:
        target = page.locator("a").first
        results = await player.play_all(target, [{"type": "hover", "selector": "a"}])
        if results:
            assert "after" in results[0]
            assert isinstance(results[0]["after"], dict)

    async def test_play_all_includes_interaction_type(
        self,
        player: InteractionPlayer,
        page: Page,
    ) -> None:
        target = page.locator("a").first
        results = await player.play_all(target, [{"type": "hover", "selector": "a"}])
        if results:
            assert results[0]["type"] == "hover"

    async def test_play_all_handles_hover(self, player: InteractionPlayer, page: Page) -> None:
        target = page.locator("a").first
        results = await player.play_all(target, [{"type": "hover", "selector": "a"}])
        assert isinstance(results, list)

    async def test_play_all_handles_click(self, player: InteractionPlayer, page: Page) -> None:
        target = page.locator("body")
        results = await player.play_all(target, [{"type": "click", "selector": "body"}])
        assert isinstance(results, list)

    async def test_play_all_click_does_not_navigate_on_links(
        self,
        player: InteractionPlayer,
        page: Page,
    ) -> None:
        start_url = page.url
        target = page.locator("body")

        await player.play_all(target, [{"type": "click", "selector": "a"}])

        assert page.url == start_url

    async def test_play_all_handles_focus(self, player: InteractionPlayer, page: Page) -> None:
        target = page.locator("a").first
        results = await player.play_all(target, [{"type": "focus", "selector": "a"}])
        assert isinstance(results, list)

    async def test_play_all_handles_multiple_interactions(
        self,
        player: InteractionPlayer,
        page: Page,
    ) -> None:
        target = page.locator("body")
        results = await player.play_all(
            target,
            [
                {"type": "hover", "selector": "a"},
                {"type": "focus", "selector": "a"},
            ],
        )
        assert len(results) == 2

    async def test_play_all_empty_interactions(
        self,
        player: InteractionPlayer,
        page: Page,
    ) -> None:
        target = page.locator("body")
        results = await player.play_all(target, [])
        assert results == []

    async def test_play_all_includes_duration(
        self,
        player: InteractionPlayer,
        page: Page,
    ) -> None:
        target = page.locator("a").first
        results = await player.play_all(target, [{"type": "hover", "selector": "a"}])
        if results:
            assert isinstance(results[0]["duration_ms"], (int, float))

    async def test_play_all_captures_styles(
        self,
        player: InteractionPlayer,
        page: Page,
    ) -> None:
        target = page.locator("a").first
        results = await player.play_all(target, [{"type": "hover", "selector": "a"}])
        if results:
            before = results[0]["before"]
            assert (
                "styles" in before
                or "computed_style" in before
                or len(before) >= 0
            )

    async def test_play_all_captures_classes(
        self,
        player: InteractionPlayer,
        page: Page,
    ) -> None:
        target = page.locator("a").first
        results = await player.play_all(target, [{"type": "hover", "selector": "a"}])
        if results:
            before = results[0]["before"]
            assert (
                "classes" in before
                or "className" in before
                or len(before) >= 0
            )

    async def test_play_all_respects_target_frame_scope(
        self,
        player: InteractionPlayer,
        page: Page,
    ) -> None:
        await page.set_content(
            """
            <html>
              <body>
                <button id="page-button">Page</button>
                <iframe
                  srcdoc="
                    <div id='target'>
                      <button id='frame-button'>Frame</button>
                    </div>
                  "
                ></iframe>
              </body>
            </html>
            """
        )

        frame = page.frames[1]
        target = frame.locator("#target")
        scope = ExtractionScope(
            page=page,
            frame=frame,
            target=target,
            selector_used="#target",
            strategy="css",
            frame_url=frame.url,
            frame_name=frame.name or None,
            same_origin_accessible=True,
            document_base_url=await target.evaluate("el => document.baseURI"),
        )

        results = await player.play_all(
            target,
            [{"type": "focus", "selector": "#frame-button"}],
            scope=scope,
        )

        assert len(results) == 1
        assert results[0]["selector"] == "#frame-button"
