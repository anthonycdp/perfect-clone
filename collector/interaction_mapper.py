"""InteractionMapper - Maps interactive elements within a target."""

from typing import Any

from playwright.async_api import Locator, Page


class InteractionMapper:
    """Maps interactive elements (hoverable, clickable, focusable, scrollable)."""

    def __init__(self, page: Page):
        """Initialize InteractionMapper with a Playwright page.

        Args:
            page: Playwright Page object to analyze.
        """
        self.page = page

    async def map(self, target: Locator) -> dict[str, list[dict[str, Any]]]:
        """Map all interactive elements within the target.

        Args:
            target: Locator for the target element to analyze.

        Returns:
            Dictionary with keys:
                - hoverable: List of elements that respond to hover
                - clickable: List of elements that can be clicked
                - focusable: List of elements that can receive focus
                - scroll_containers: List of scrollable containers
        """
        result: dict[str, list[dict[str, Any]]] = {
            "hoverable": [],
            "clickable": [],
            "focusable": [],
            "scroll_containers": [],
        }

        # Get the selector for the target if possible
        target_selector = await self._get_target_selector(target)

        # Find clickable elements (links, buttons, elements with onclick)
        result["clickable"] = await self._find_clickable(target, target_selector)

        # Find focusable elements (links, inputs, buttons, elements with tabindex)
        result["focusable"] = await self._find_focusable(target, target_selector)

        # Find hoverable elements (elements with :hover styles)
        result["hoverable"] = await self._find_hoverable(target, target_selector)

        # Find scroll containers
        result["scroll_containers"] = await self._find_scroll_containers(target, target_selector)

        return result

    async def _get_target_selector(self, target: Locator) -> str:
        """Try to get a CSS selector for the target element."""
        try:
            # Try to evaluate and get a unique selector
            selector = await target.evaluate("""el => {
                if (el.id) return '#' + el.id;
                if (el.className && typeof el.className === 'string') {
                    return el.tagName.toLowerCase() + '.' + el.className.split(' ').join('.');
                }
                return el.tagName.toLowerCase();
            }""")
            return selector
        except Exception:
            return "body"

    async def _find_clickable(
        self, target: Locator, target_selector: str
    ) -> list[dict[str, Any]]:
        """Find clickable elements within target."""
        clickable_selectors = [
            "a",
            "button",
            "[role='button']",
            "[onclick]",
            "input[type='submit']",
            "input[type='button']",
            "input[type='image']",
            "[role='link']",
        ]

        elements: list[dict[str, Any]] = []

        for selector in clickable_selectors:
            try:
                locator = target.locator(selector)
                count = await locator.count()

                for i in range(count):
                    try:
                        el = locator.nth(i)
                        element_info = await self._get_element_info(el)
                        if element_info and not self._is_duplicate(elements, element_info["selector"]):
                            elements.append(element_info)
                    except Exception:
                        continue
            except Exception:
                continue

        return elements

    async def _find_focusable(
        self, target: Locator, target_selector: str
    ) -> list[dict[str, Any]]:
        """Find focusable elements within target."""
        focusable_selectors = [
            "a[href]",
            "button",
            "input",
            "select",
            "textarea",
            "[tabindex]",
            "[contenteditable='true']",
        ]

        elements: list[dict[str, Any]] = []

        for selector in focusable_selectors:
            try:
                locator = target.locator(selector)
                count = await locator.count()

                for i in range(count):
                    try:
                        el = locator.nth(i)
                        # Check if element is actually focusable (not disabled, not hidden)
                        is_focusable = await el.evaluate("""el => {
                            return !el.disabled &&
                                   el.tabIndex >= 0 &&
                                   el.offsetParent !== null;
                        }""")
                        if is_focusable:
                            element_info = await self._get_element_info(el)
                            if element_info and not self._is_duplicate(elements, element_info["selector"]):
                                elements.append(element_info)
                    except Exception:
                        continue
            except Exception:
                continue

        return elements

    async def _find_hoverable(
        self, target: Locator, target_selector: str
    ) -> list[dict[str, Any]]:
        """Find elements that respond to hover."""
        elements: list[dict[str, Any]] = []

        try:
            # Get all elements and check if they have :hover styles
            all_elements = target.locator("*")
            count = await all_elements.count()

            for i in range(count):
                try:
                    el = all_elements.nth(i)
                    has_hover = await el.evaluate("""el => {
                        const className = typeof el.className === 'string' ? el.className : '';
                        if (
                            className.includes('hover:') ||
                            className.includes('group-hover:') ||
                            className.includes(':hover')
                        ) {
                            return true;
                        }

                        const inlineCursor = el.style?.cursor || '';
                        if (inlineCursor === 'pointer') {
                            return true;
                        }

                        const computedCursor = window.getComputedStyle(el).cursor;
                        if (computedCursor === 'pointer') {
                            return true;
                        }

                        // Check if element has any :hover styles defined
                        const sheets = document.styleSheets;
                        let hasHover = false;

                        try {
                            for (const sheet of sheets) {
                                try {
                                    for (const rule of sheet.cssRules) {
                                        if (rule.selectorText && rule.selectorText.includes(':hover')) {
                                            // Check if this element matches the :hover selector base
                                            const baseSelector = rule.selectorText.replace(':hover', '').trim();
                                            if (baseSelector) {
                                                try {
                                                    if (el.matches(baseSelector)) {
                                                        hasHover = true;
                                                        break;
                                                    }
                                                } catch (e) {
                                                    // Invalid selector, skip
                                                }
                                            }
                                        }
                                    }
                                } catch (e) {
                                    // CORS or other error accessing stylesheet
                                }
                                if (hasHover) break;
                            }
                        } catch (e) {
                            // Error accessing stylesheets
                        }

                        return hasHover;
                    }""")

                    if has_hover:
                        element_info = await self._get_element_info(el)
                        if element_info and not self._is_duplicate(elements, element_info["selector"]):
                            elements.append(element_info)
                except Exception:
                    continue
        except Exception:
            pass

        return elements

    async def _find_scroll_containers(
        self, target: Locator, target_selector: str
    ) -> list[dict[str, Any]]:
        """Find scrollable containers within target."""
        elements: list[dict[str, Any]] = []

        try:
            all_elements = target.locator("*")
            count = await all_elements.count()

            for i in range(count):
                try:
                    el = all_elements.nth(i)
                    is_scrollable = await el.evaluate("""el => {
                        const style = window.getComputedStyle(el);
                        const overflow = style.overflow + style.overflowY + style.overflowX;
                        return (overflow.includes('auto') || overflow.includes('scroll')) &&
                               (el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth);
                    }""")

                    if is_scrollable:
                        element_info = await self._get_element_info(el)
                        if element_info and not self._is_duplicate(elements, element_info["selector"]):
                            elements.append(element_info)
                except Exception:
                    continue
        except Exception:
            pass

        return elements

    async def _get_element_info(self, element: Locator) -> dict[str, Any] | None:
        """Get information about an element."""
        try:
            info = await element.evaluate("""el => {
                // Generate a unique selector
                let selector = '';

                if (el.id) {
                    selector = '#' + el.id;
                } else {
                    // Build selector from tag and classes
                    selector = el.tagName.toLowerCase();

                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/).filter(c => c);
                        if (classes.length > 0) {
                            selector += '.' + classes.slice(0, 2).join('.');
                        }
                    }

                    // Add nth-child if needed for uniqueness
                    const parent = el.parentElement;
                    if (parent) {
                        const siblings = Array.from(parent.children).filter(
                            c => c.tagName === el.tagName
                        );
                        if (siblings.length > 1) {
                            const index = siblings.indexOf(el) + 1;
                            selector += `:nth-child(${index})`;
                        }
                    }
                }

                return {
                    selector: selector,
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent?.trim().slice(0, 50) || ''
                };
            }""")
            return info
        except Exception:
            return None

    def _is_duplicate(
        self, elements: list[dict[str, Any]], selector: str
    ) -> bool:
        """Check if element with selector already exists in list."""
        return any(el.get("selector") == selector for el in elements)
