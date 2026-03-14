"""TargetFinder - Find elements using various strategies."""

import re

from playwright.sync_api import Locator, Page

from models.errors import TargetNotFoundError
from models.extraction import SelectorStrategy


class TargetFinder:
    """Find elements using various strategies."""

    def __init__(self, page: Page):
        """Initialize TargetFinder with a Playwright page.

        Args:
            page: Playwright Page object to search within.
        """
        self.page = page

    def find(self, strategy: SelectorStrategy, query: str) -> Locator:
        """Find element using specified strategy.

        Args:
            strategy: The selector strategy to use.
            query: The query string (selector, xpath, text, or HTML snippet).

        Returns:
            Locator for the found element.

        Raises:
            TargetNotFoundError: If no element is found.
            ValueError: If the strategy is unknown.
        """
        if strategy == SelectorStrategy.CSS:
            return self._find_by_css(query)
        elif strategy == SelectorStrategy.XPATH:
            return self._find_by_xpath(query)
        elif strategy == SelectorStrategy.TEXT:
            return self._find_by_text(query)
        elif strategy == SelectorStrategy.HTML_SNIPPET:
            return self._find_by_html_snippet(query)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _find_by_css(self, selector: str) -> Locator:
        """Find element by CSS selector.

        Args:
            selector: CSS selector string.

        Returns:
            Locator for the first matching element.

        Raises:
            TargetNotFoundError: If no element matches the selector.
        """
        locator = self.page.locator(selector)

        if locator.count() == 0:
            suggestions = self._get_similar_selectors(selector)
            raise TargetNotFoundError(
                f"CSS selector '{selector}' not found", suggestions=suggestions
            )

        return locator.first

    def _find_by_xpath(self, xpath: str) -> Locator:
        """Find element by XPath.

        Args:
            xpath: XPath expression.

        Returns:
            Locator for the first matching element.

        Raises:
            TargetNotFoundError: If no element matches the XPath.
        """
        locator = self.page.locator(f"xpath={xpath}")

        if locator.count() == 0:
            raise TargetNotFoundError(f"XPath '{xpath}' not found")

        return locator.first

    def _find_by_text(self, text: str) -> Locator:
        """Find element containing text.

        Args:
            text: Text to search for.

        Returns:
            Locator for the first matching element.

        Raises:
            TargetNotFoundError: If no element contains the text.
        """
        locator = self.page.locator(f"text={text}")

        if locator.count() == 0:
            raise TargetNotFoundError(f"Text '{text}' not found")

        return locator.first

    def _find_by_html_snippet(self, html: str) -> Locator:
        """Find element matching HTML snippet.

        Parses the HTML snippet to extract tag name and optional classes,
        then constructs a CSS selector to find matching elements.

        Args:
            html: HTML snippet string.

        Returns:
            Locator for the first matching element.

        Raises:
            TargetNotFoundError: If the HTML is invalid or no element matches.
        """
        tag_match = re.match(r"<(\w+)", html.strip())
        if not tag_match:
            raise TargetNotFoundError(f"Invalid HTML snippet: {html}")

        tag = tag_match.group(1)

        class_match = re.search(r'class=["\']([^"\']+)["\']', html)
        if class_match:
            classes = class_match.group(1).split()
            selector = f"{tag}.{'.'.join(classes)}"
        else:
            selector = tag

        locator = self.page.locator(selector)

        if locator.count() == 0:
            raise TargetNotFoundError(f"HTML snippet not found: {html}")

        return locator.first

    def _get_similar_selectors(self, selector: str) -> list[str]:
        """Find similar selectors that do exist.

        Provides suggestions when a selector is not found to help users
        find the correct selector.

        Args:
            selector: The original selector that was not found.

        Returns:
            List of up to 5 similar selector suggestions.
        """
        suggestions: list[str] = []

        # Extract tag and try it
        if "." in selector:
            tag = selector.split(".")[0]
            if tag:
                try:
                    if self.page.locator(tag).count() > 0:
                        suggestions.append(tag)
                except Exception:
                    pass

        # Find similar classes
        try:
            classes = self.page.evaluate("""() => {
                const elements = document.querySelectorAll('*');
                const classes = new Set();
                elements.forEach(el => {
                    el.classList.forEach(cls => classes.add(cls));
                });
                return Array.from(classes).slice(0, 20);
            }""")

            selector_class = selector.split(".")[-1] if "." in selector else ""
            for cls in classes:
                if selector_class and (
                    cls.startswith(selector_class[:3])
                    or selector_class[:3] in cls
                ):
                    suggestions.append(f".{cls}")
        except Exception:
            pass

        return suggestions[:5]
