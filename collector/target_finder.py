"""TargetFinder - Find elements using various strategies."""

import re
from typing import Callable
import urllib.parse

from playwright.async_api import Frame, Locator, Page

from collector.extraction_scope import ExtractionScope
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

    async def find(self, strategy: SelectorStrategy, query: str) -> ExtractionScope:
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
            return await self._find_by_css(query)
        elif strategy == SelectorStrategy.XPATH:
            return await self._find_by_xpath(query)
        elif strategy == SelectorStrategy.TEXT:
            return await self._find_by_text(query)
        elif strategy == SelectorStrategy.HTML_SNIPPET:
            return await self._find_by_html_snippet(query)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    async def _find_by_css(self, selector: str) -> ExtractionScope:
        """Find element by CSS selector.

        Args:
            selector: CSS selector string.

        Returns:
            Locator for the first matching element.

        Raises:
            TargetNotFoundError: If no element matches the selector.
        """
        frame_locator = await self._find_across_frames(lambda frame: frame.locator(selector))
        if frame_locator is None:
            suggestions = await self._get_similar_selectors(selector)
            raise TargetNotFoundError(
                f"CSS selector '{selector}' not found", suggestions=suggestions
            )
        frame, locator = frame_locator
        return await self._build_scope(frame, locator, SelectorStrategy.CSS, selector)

    async def _find_by_xpath(self, xpath: str) -> ExtractionScope:
        """Find element by XPath.

        Args:
            xpath: XPath expression.

        Returns:
            Locator for the first matching element.

        Raises:
            TargetNotFoundError: If no element matches the XPath.
        """
        frame_locator = await self._find_across_frames(
            lambda frame: frame.locator(f"xpath={xpath}")
        )
        if frame_locator is None:
            if await self._xpath_requires_shadow_dom(xpath):
                raise TargetNotFoundError(
                    f"XPath '{xpath}' not found. XPath does not pierce shadow roots in Playwright. "
                    "Use a CSS or text selector for targets inside open shadow DOM."
                )
            raise TargetNotFoundError(f"XPath '{xpath}' not found")
        frame, locator = frame_locator
        return await self._build_scope(frame, locator, SelectorStrategy.XPATH, xpath)

    async def _find_by_text(self, text: str) -> ExtractionScope:
        """Find element containing text.

        Args:
            text: Text to search for.

        Returns:
            Locator for the first matching element.

        Raises:
            TargetNotFoundError: If no element contains the text.
        """
        frame_locator = await self._find_across_frames(lambda frame: frame.locator(f"text={text}"))
        if frame_locator is None:
            raise TargetNotFoundError(f"Text '{text}' not found")
        frame, locator = frame_locator
        return await self._build_scope(frame, locator, SelectorStrategy.TEXT, text)

    async def _find_by_html_snippet(self, html: str) -> ExtractionScope:
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

        frame_locator = await self._find_across_frames(lambda frame: frame.locator(selector))
        if frame_locator is None:
            raise TargetNotFoundError(f"HTML snippet not found: {html}")
        frame, locator = frame_locator
        return await self._build_scope(frame, locator, SelectorStrategy.HTML_SNIPPET, html)

    async def _find_across_frames(
        self,
        locator_factory: Callable[[Frame], Locator],
    ) -> tuple[Frame, Locator] | None:
        """Search the main document and all child frames for the first match."""
        for frame in self.page.frames:
            try:
                locator = locator_factory(frame)
                if await locator.count() > 0:
                    return frame, locator.first
            except Exception:
                continue
        return None

    async def _build_scope(
        self,
        frame: Frame,
        locator: Locator,
        strategy: SelectorStrategy,
        query: str,
    ) -> ExtractionScope:
        """Build frame-aware metadata for a located target."""
        return ExtractionScope(
            page=self.page,
            frame=frame,
            target=locator,
            selector_used=query,
            strategy=strategy.value,
            frame_url=frame.url,
            frame_name=frame.name or None,
            same_origin_accessible=self._is_same_origin(frame),
            within_shadow_dom=await self._is_within_shadow_dom(locator),
            document_base_url=await self._get_document_base_url(locator, frame),
        )

    async def _get_document_base_url(self, locator: Locator, frame: Frame) -> str:
        """Return the base URL used to resolve relative assets for the target frame."""
        try:
            base_url = await locator.evaluate(
                """el => document.baseURI || window.location.href || ''"""
            )
            if isinstance(base_url, str) and base_url:
                return base_url
        except Exception:
            pass

        return frame.url or self.page.url

    def _is_same_origin(self, frame: Frame) -> bool:
        """Return whether the frame shares the origin of the main page or is srcdoc/about."""
        frame_url = frame.url or ""
        page_url = self.page.url or ""

        if frame_url.startswith("about:") or page_url.startswith("about:"):
            return True

        frame_parts = urllib.parse.urlparse(frame_url)
        page_parts = urllib.parse.urlparse(page_url)
        return (
            frame_parts.scheme == page_parts.scheme
            and frame_parts.netloc == page_parts.netloc
        )

    async def _is_within_shadow_dom(self, locator: Locator) -> bool:
        """Return whether the located element lives inside an open shadow root."""
        try:
            return bool(
                await locator.evaluate(
                    """el => el.getRootNode() instanceof ShadowRoot"""
                )
            )
        except Exception:
            return False

    async def _xpath_requires_shadow_dom(self, xpath: str) -> bool:
        """Best-effort hint that a failed XPath would need shadow traversal."""
        shadow_id = re.search(r"@id=['\"]([^'\"]+)['\"]", xpath)
        if shadow_id and await self._shadow_roots_contain_id(shadow_id.group(1)):
            return True

        text_match = re.search(
            r"(?:text\(\)\s*=\s*|contains\(\s*text\(\)\s*,\s*)['\"]([^'\"]+)['\"]",
            xpath,
        )
        if text_match and await self._shadow_roots_contain_text(text_match.group(1)):
            return True

        tag_match = re.fullmatch(r"//([a-zA-Z][\w-]*)", xpath.strip())
        if tag_match and await self._shadow_roots_contain_selector(tag_match.group(1)):
            return True

        return False

    async def _shadow_roots_contain_id(self, element_id: str) -> bool:
        """Return whether any open shadow root contains a matching element id."""
        return await self._shadow_roots_match(
            """elementId => {
                function containsId(root) {
                    const allElements = root.querySelectorAll ? Array.from(root.querySelectorAll('*')) : [];
                    for (const element of allElements) {
                        if (element.id === elementId) {
                            return true;
                        }
                        if (element.shadowRoot && containsId(element.shadowRoot)) {
                            return true;
                        }
                    }
                    return false;
                }

                return containsId(document);
            }""",
            element_id,
        )

    async def _shadow_roots_contain_text(self, text: str) -> bool:
        """Return whether any open shadow root contains matching visible text."""
        normalized_text = " ".join(text.split())
        return await self._shadow_roots_match(
            """expectedText => {
                function normalize(value) {
                    return (value || '').replace(/\\s+/g, ' ').trim();
                }

                function containsText(root) {
                    const allElements = root.querySelectorAll ? Array.from(root.querySelectorAll('*')) : [];
                    for (const element of allElements) {
                        if (normalize(element.textContent).includes(expectedText)) {
                            return true;
                        }
                        if (element.shadowRoot && containsText(element.shadowRoot)) {
                            return true;
                        }
                    }
                    return false;
                }

                return containsText(document);
            }""",
            normalized_text,
        )

    async def _shadow_roots_contain_selector(self, selector: str) -> bool:
        """Return whether any open shadow root contains a matching CSS selector."""
        return await self._shadow_roots_match(
            """selector => {
                function containsSelector(root) {
                    let matches = false;
                    try {
                        matches = !!root.querySelector(selector);
                    } catch (e) {
                        return false;
                    }

                    if (matches) {
                        return true;
                    }

                    const allElements = root.querySelectorAll ? Array.from(root.querySelectorAll('*')) : [];
                    for (const element of allElements) {
                        if (element.shadowRoot && containsSelector(element.shadowRoot)) {
                            return true;
                        }
                    }
                    return false;
                }

                return containsSelector(document);
            }""",
            selector,
        )

    async def _shadow_roots_match(self, script: str, value: str) -> bool:
        """Evaluate a best-effort shadow-root lookup across all page frames."""
        for frame in self.page.frames:
            try:
                if await frame.evaluate(script, value):
                    return True
            except Exception:
                continue
        return False

    async def _get_similar_selectors(self, selector: str) -> list[str]:
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
                    if await self.page.locator(tag).count() > 0:
                        suggestions.append(tag)
                except Exception:
                    pass

        # Find similar classes
        try:
            classes = await self.page.evaluate("""() => {
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
