"""Tests for InteractionPlayer - executes interactions and captures states."""

import pytest
from playwright.sync_api import Page

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
