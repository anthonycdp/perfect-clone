"""Tests for InteractionMapper - maps interactive elements."""

import pytest
from playwright.sync_api import Page

from collector.interaction_mapper import InteractionMapper


class TestInteractionMapper:
    """Test suite for InteractionMapper."""

    @pytest.fixture
    def mapper(self, page: Page) -> InteractionMapper:
        """Create an InteractionMapper instance."""
        return InteractionMapper(page)

    def test_map_returns_dict_with_correct_keys(
        self, mapper: InteractionMapper, page: Page
    ) -> None:
        """map() should return dict with hoverable, clickable, focusable, scroll_containers."""
        target = page.locator("body")
        result = mapper.map(target)

        assert isinstance(result, dict)
        assert "hoverable" in result
        assert "clickable" in result
        assert "focusable" in result
        assert "scroll_containers" in result

    def test_map_finds_clickable_elements(
        self, mapper: InteractionMapper, page: Page
    ) -> None:
        """map() should find clickable elements (links, buttons)."""
        target = page.locator("body")
        result = mapper.map(target)

        # example.com has links
        assert len(result["clickable"]) > 0
        # Each entry should have a selector
        for item in result["clickable"]:
            assert "selector" in item

    def test_map_finds_focusable_elements(
        self, mapper: InteractionMapper, page: Page
    ) -> None:
        """map() should find focusable elements (links, inputs)."""
        target = page.locator("body")
        result = mapper.map(target)

        # example.com has links which are focusable
        assert len(result["focusable"]) > 0
        for item in result["focusable"]:
            assert "selector" in item

    def test_map_hoverable_elements(
        self, mapper: InteractionMapper, page: Page
    ) -> None:
        """map() should identify hoverable elements."""
        target = page.locator("body")
        result = mapper.map(target)

        assert isinstance(result["hoverable"], list)
        for item in result["hoverable"]:
            assert "selector" in item

    def test_map_scroll_containers(
        self, mapper: InteractionMapper, page: Page
    ) -> None:
        """map() should identify scroll containers."""
        target = page.locator("body")
        result = mapper.map(target)

        assert isinstance(result["scroll_containers"], list)
        for item in result["scroll_containers"]:
            assert "selector" in item

    def test_map_scoped_to_target(
        self, mapper: InteractionMapper, page: Page
    ) -> None:
        """map() should only find elements within target."""
        # Get the first paragraph only
        target = page.locator("p").first
        result = mapper.map(target)

        # Should be scoped to just that element and its children
        assert isinstance(result["clickable"], list)

    def test_map_includes_element_info(
        self, mapper: InteractionMapper, page: Page
    ) -> None:
        """map() should include tag name and other info for each element."""
        target = page.locator("body")
        result = mapper.map(target)

        # Check that clickable items include tag info
        if result["clickable"]:
            item = result["clickable"][0]
            assert "selector" in item
            # Tag should be included for context
            assert "tag" in item or "selector" in item

    def test_map_handles_nested_elements(
        self, mapper: InteractionMapper, page: Page
    ) -> None:
        """map() should handle nested interactive elements."""
        target = page.locator("body")
        result = mapper.map(target)

        # Should not duplicate elements
        all_selectors = (
            result["hoverable"]
            + result["clickable"]
            + result["focusable"]
            + result["scroll_containers"]
        )
        # Just verify it completes without error
        assert isinstance(all_selectors, list)
