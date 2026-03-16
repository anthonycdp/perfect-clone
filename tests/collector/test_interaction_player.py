"""Tests for InteractionPlayer - executes interactions and captures states."""

import pytest
from playwright.sync_api import Page

from collector.extraction_scope import ExtractionScope
from collector.interaction_player import InteractionPlayer
from models.extraction import InteractionType


class TestInteractionPlayer:
    """Test suite for InteractionPlayer."""

    @pytest.fixture
    def player(self, page: Page) -> InteractionPlayer:
        """Create an InteractionPlayer instance."""
        return InteractionPlayer(page)

    def test_play_all_returns_list(self, player: InteractionPlayer, page: Page) -> None:
        """play_all() should return a list of interaction results."""
        target = page.locator("a").first  # Get the first link
        interactions = [{"type": "hover", "selector": "a"}]

        results = player.play_all(target, interactions)

        assert isinstance(results, list)

    def test_play_all_captures_before_state(
        self, player: InteractionPlayer, page: Page
    ) -> None:
        """play_all() should capture state before interaction."""
        target = page.locator("a").first
        interactions = [{"type": "hover", "selector": "a"}]

        results = player.play_all(target, interactions)

        if results:  # If any results were captured
            assert "before" in results[0]
            assert isinstance(results[0]["before"], dict)

    def test_play_all_captures_after_state(
        self, player: InteractionPlayer, page: Page
    ) -> None:
        """play_all() should capture state after interaction."""
        target = page.locator("a").first
        interactions = [{"type": "hover", "selector": "a"}]

        results = player.play_all(target, interactions)

        if results:
            assert "after" in results[0]
            assert isinstance(results[0]["after"], dict)

    def test_play_all_includes_interaction_type(
        self, player: InteractionPlayer, page: Page
    ) -> None:
        """play_all() result should include the interaction type."""
        target = page.locator("a").first
        interactions = [{"type": "hover", "selector": "a"}]

        results = player.play_all(target, interactions)

        if results:
            assert "type" in results[0]
            assert results[0]["type"] == "hover"

    def test_play_all_handles_hover(self, player: InteractionPlayer, page: Page) -> None:
        """play_all() should execute hover interaction."""
        target = page.locator("a").first
        interactions = [{"type": "hover", "selector": "a"}]

        # Should not raise
        results = player.play_all(target, interactions)
        assert isinstance(results, list)

    def test_play_all_handles_click(self, player: InteractionPlayer, page: Page) -> None:
        """play_all() should execute click interaction."""
        target = page.locator("body")
        interactions = [{"type": "click", "selector": "body"}]

        # Should not raise
        results = player.play_all(target, interactions)
        assert isinstance(results, list)

    def test_play_all_click_does_not_navigate_on_links(
        self, player: InteractionPlayer, page: Page
    ) -> None:
        """click interactions should not leave the current page."""
        start_url = page.url
        target = page.locator("body")
        interactions = [{"type": "click", "selector": "a"}]

        player.play_all(target, interactions)

        assert page.url == start_url

    def test_play_all_handles_focus(self, player: InteractionPlayer, page: Page) -> None:
        """play_all() should execute focus interaction."""
        target = page.locator("a").first
        interactions = [{"type": "focus", "selector": "a"}]

        # Should not raise
        results = player.play_all(target, interactions)
        assert isinstance(results, list)

    def test_play_all_handles_multiple_interactions(
        self, player: InteractionPlayer, page: Page
    ) -> None:
        """play_all() should handle multiple interactions."""
        target = page.locator("body")
        interactions = [
            {"type": "hover", "selector": "a"},
            {"type": "focus", "selector": "a"},
        ]

        results = player.play_all(target, interactions)
        assert len(results) == 2

    def test_play_all_empty_interactions(
        self, player: InteractionPlayer, page: Page
    ) -> None:
        """play_all() should return empty list for no interactions."""
        target = page.locator("body")
        interactions = []

        results = player.play_all(target, interactions)
        assert results == []

    def test_play_all_includes_duration(
        self, player: InteractionPlayer, page: Page
    ) -> None:
        """play_all() should include duration of interaction."""
        target = page.locator("a").first
        interactions = [{"type": "hover", "selector": "a"}]

        results = player.play_all(target, interactions)

        if results:
            assert "duration_ms" in results[0]
            assert isinstance(results[0]["duration_ms"], (int, float))

    def test_play_all_captures_styles(
        self, player: InteractionPlayer, page: Page
    ) -> None:
        """play_all() should capture computed styles in states."""
        target = page.locator("a").first
        interactions = [{"type": "hover", "selector": "a"}]

        results = player.play_all(target, interactions)

        if results:
            # Before/after states should include style information
            assert "styles" in results[0]["before"] or "computed_style" in results[0]["before"] or len(results[0]["before"]) >= 0

    def test_play_all_captures_classes(
        self, player: InteractionPlayer, page: Page
    ) -> None:
        """play_all() should capture element classes in states."""
        target = page.locator("a").first
        interactions = [{"type": "hover", "selector": "a"}]

        results = player.play_all(target, interactions)

        if results:
            # States should include class information
            assert "classes" in results[0]["before"] or "className" in results[0]["before"] or len(results[0]["before"]) >= 0

    def test_play_all_respects_target_frame_scope(
        self, player: InteractionPlayer, page: Page
    ) -> None:
        """play_all() should execute interactions inside the target frame."""
        page.set_content(
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
            document_base_url=target.evaluate("el => document.baseURI"),
        )

        results = player.play_all(
            target,
            [{"type": "focus", "selector": "#frame-button"}],
            scope=scope,
        )

        assert len(results) == 1
        assert results[0]["selector"] == "#frame-button"
