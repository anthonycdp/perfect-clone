"""Tests for TargetFinder element location strategies."""

import pytest
from playwright.sync_api import Page

from collector.target_finder import TargetFinder
from models.errors import TargetNotFoundError
from models.extraction import SelectorStrategy


class TestTargetFinder:
    """Test suite for TargetFinder."""

    @pytest.fixture
    def finder(self, page: Page) -> TargetFinder:
        """Create a TargetFinder instance."""
        return TargetFinder(page)

    def test_find_by_css_finds_h1_element(self, finder: TargetFinder) -> None:
        """find_by_css should find h1 element on example.com."""
        scope = finder._find_by_css("h1")
        assert scope is not None
        assert scope.target.count() == 1
        assert scope.frame_url == finder.page.url

    def test_find_by_xpath_finds_element(self, finder: TargetFinder) -> None:
        """find_by_xpath should find element using XPath."""
        scope = finder._find_by_xpath("//h1")
        assert scope is not None
        assert scope.target.count() == 1

    def test_find_by_xpath_searches_srcdoc_iframes(self, page: Page) -> None:
        """XPath lookup should search child frames when the main page has no match."""
        page.set_content(
            """
            <html>
              <body>
                <iframe srcdoc='<section id="workflow"><h2>Workflow</h2></section>'></iframe>
              </body>
            </html>
            """
        )

        finder = TargetFinder(page)
        scope = finder._find_by_xpath('//*[@id="workflow"]')

        assert scope is not None
        assert scope.target.text_content() == "Workflow"
        assert scope.frame_url == "about:srcdoc"
        assert scope.same_origin_accessible is True

    def test_find_by_text_finds_element(self, finder: TargetFinder) -> None:
        """find_by_text should find element containing text."""
        # example.com has "Example Domain" as h1 text
        scope = finder._find_by_text("Example Domain")
        assert scope is not None
        assert scope.target.count() == 1

    def test_find_by_css_finds_element_inside_open_shadow_root(
        self,
        page: Page,
    ) -> None:
        """CSS selectors should pierce open shadow DOM and keep shadow metadata."""
        page.set_content(
            """
            <html>
              <body>
                <x-cta id="card"></x-cta>
                <script>
                  const host = document.querySelector('#card');
                  const root = host.attachShadow({ mode: 'open' });
                  root.innerHTML = '<button id="shadow-button">Shadow CTA</button>';
                </script>
              </body>
            </html>
            """
        )

        finder = TargetFinder(page)
        scope = finder._find_by_css("#shadow-button")

        assert scope.target.text_content() == "Shadow CTA"
        assert scope.within_shadow_dom is True

    def test_find_by_text_finds_element_inside_open_shadow_root(
        self,
        page: Page,
    ) -> None:
        """Text selectors should pierce open shadow DOM."""
        page.set_content(
            """
            <html>
              <body>
                <x-cta></x-cta>
                <script>
                  const host = document.querySelector('x-cta');
                  const root = host.attachShadow({ mode: 'open' });
                  root.innerHTML = '<button>Shadow Action</button>';
                </script>
              </body>
            </html>
            """
        )

        finder = TargetFinder(page)
        scope = finder._find_by_text("Shadow Action")

        assert scope.target.text_content() == "Shadow Action"
        assert scope.within_shadow_dom is True

    def test_find_by_css_invalid_selector_raises_error(
        self, finder: TargetFinder
    ) -> None:
        """find_by_css with invalid selector should raise TargetNotFoundError."""
        with pytest.raises(TargetNotFoundError) as exc_info:
            finder._find_by_css(".nonexistent-class-xyz123")

        assert "not found" in str(exc_info.value).lower()

    def test_target_not_found_error_includes_suggestions(
        self, finder: TargetFinder
    ) -> None:
        """TargetNotFoundError should include suggestions when possible."""
        with pytest.raises(TargetNotFoundError) as exc_info:
            finder._find_by_css(".nonexistent-xyz")

        error = exc_info.value
        assert isinstance(error.suggestions, list)

    def test_find_with_css_strategy(self, finder: TargetFinder) -> None:
        """find() method should work with CSS strategy."""
        scope = finder.find(SelectorStrategy.CSS, "h1")
        assert scope is not None
        assert scope.selector_used == "h1"

    def test_find_with_xpath_strategy(self, finder: TargetFinder) -> None:
        """find() method should work with XPath strategy."""
        scope = finder.find(SelectorStrategy.XPATH, "//h1")
        assert scope is not None
        assert scope.strategy == "xpath"

    def test_find_with_text_strategy(self, finder: TargetFinder) -> None:
        """find() method should work with text strategy."""
        scope = finder.find(SelectorStrategy.TEXT, "Example Domain")
        assert scope is not None
        assert scope.strategy == "text"

    def test_find_with_html_snippet_strategy(self, finder: TargetFinder) -> None:
        """find() method should work with HTML snippet strategy."""
        scope = finder.find(SelectorStrategy.HTML_SNIPPET, "<h1>")
        assert scope is not None
        assert scope.strategy == "html_snippet"

    def test_find_by_html_snippet_with_class(self, finder: TargetFinder) -> None:
        """_find_by_html_snippet should parse and use class from HTML."""
        # example.com has a <p> tag
        scope = finder._find_by_html_snippet("<p>")
        assert scope is not None
        assert scope.target.count() == 1

    def test_find_by_xpath_invalid_raises_error(self, finder: TargetFinder) -> None:
        """_find_by_xpath with invalid XPath should raise TargetNotFoundError."""
        with pytest.raises(TargetNotFoundError) as exc_info:
            finder._find_by_xpath("//nonexistent[tag='xyz']")

        assert "not found" in str(exc_info.value).lower()

    def test_find_by_xpath_shadow_target_raises_guided_error(
        self,
        page: Page,
    ) -> None:
        """XPath should explain that it cannot pierce open shadow roots."""
        page.set_content(
            """
            <html>
              <body>
                <x-cta></x-cta>
                <script>
                  const host = document.querySelector('x-cta');
                  const root = host.attachShadow({ mode: 'open' });
                  root.innerHTML = '<button id="shadow-button">Shadow CTA</button>';
                </script>
              </body>
            </html>
            """
        )

        finder = TargetFinder(page)
        with pytest.raises(TargetNotFoundError) as exc_info:
            finder._find_by_xpath('//*[@id="shadow-button"]')

        assert "xpath does not pierce shadow roots" in str(exc_info.value).lower()

    def test_find_by_text_invalid_raises_error(self, finder: TargetFinder) -> None:
        """_find_by_text with nonexistent text should raise TargetNotFoundError."""
        with pytest.raises(TargetNotFoundError) as exc_info:
            finder._find_by_text("NonexistentText12345")

        assert "not found" in str(exc_info.value).lower()

    def test_find_with_unknown_strategy_raises_value_error(
        self, finder: TargetFinder
    ) -> None:
        """find() with unknown strategy should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            finder.find("unknown_strategy", "query")  # type: ignore

        assert "Unknown strategy" in str(exc_info.value)

    def test_find_by_html_snippet_invalid_html_raises_error(
        self, finder: TargetFinder
    ) -> None:
        """_find_by_html_snippet with invalid HTML should raise TargetNotFoundError."""
        with pytest.raises(TargetNotFoundError) as exc_info:
            finder._find_by_html_snippet("not valid html <")

        assert "Invalid HTML snippet" in str(exc_info.value)

    def test_find_by_html_snippet_nonexistent_raises_error(
        self, finder: TargetFinder
    ) -> None:
        """_find_by_html_snippet with nonexistent element should raise TargetNotFoundError."""
        with pytest.raises(TargetNotFoundError) as exc_info:
            finder._find_by_html_snippet("<nonexistent-tag-xyz>")

        assert "not found" in str(exc_info.value).lower()
