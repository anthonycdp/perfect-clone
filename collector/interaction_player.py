"""InteractionPlayer - Executes interactions and captures before/after states."""

import time
from typing import Any

from playwright.async_api import Locator, Page

from collector.extraction_scope import ExtractionScope


class InteractionPlayer:
    """Executes interactions on elements and captures state changes."""

    def __init__(self, page: Page):
        """Initialize InteractionPlayer with a Playwright page.

        Args:
            page: Playwright Page object to interact with.
        """
        self.page = page

    async def play_all(
        self,
        target: Locator,
        interactions: list[dict[str, Any]],
        scope: ExtractionScope | None = None,
    ) -> list[dict[str, Any]]:
        """Execute all interactions and capture before/after states.

        Args:
            target: Locator for the target element.
            interactions: List of interactions to execute, each with:
                - type: "hover", "click", "focus", or "scroll"
                - selector: CSS selector for the element to interact with

        Returns:
            List of interaction results, each containing:
                - type: The interaction type
                - selector: The element selector
                - before: State before interaction (styles, classes, etc.)
                - after: State after interaction
                - duration_ms: Time taken for the interaction
        """
        results: list[dict[str, Any]] = []

        for interaction in interactions:
            interaction_type = interaction.get("type", "")
            selector = interaction.get("selector", "")

            if not interaction_type or not selector:
                continue

            result = await self._execute_interaction(
                target,
                interaction_type,
                selector,
                scope=scope,
            )
            if result:
                results.append(result)

        return results

    async def _execute_interaction(
        self,
        target: Locator,
        interaction_type: str,
        selector: str,
        scope: ExtractionScope | None = None,
    ) -> dict[str, Any] | None:
        """Execute a single interaction and capture states.

        Args:
            target: The target locator.
            interaction_type: Type of interaction (hover, click, focus, scroll).
            selector: CSS selector for the element.

        Returns:
            Dictionary with before/after states and duration, or None on failure.
        """
        try:
            element = await self._find_interaction_element(target, selector, scope=scope)
            if element is None:
                return None

            # Capture before state
            before_state = await self._capture_state(element)

            # Execute the interaction
            start_time = time.time()

            if interaction_type == "hover":
                await element.hover(force=True)
            elif interaction_type == "click":
                await element.evaluate("""el => {
                    const cancelDefault = event => event.preventDefault();
                    el.addEventListener('click', cancelDefault, { capture: true, once: true });
                    el.dispatchEvent(
                        new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window,
                        })
                    );
                }""")
            elif interaction_type == "focus":
                await element.focus()
            elif interaction_type == "scroll":
                await element.evaluate("el => el.scrollTop = el.scrollHeight")
            else:
                return None

            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # Small delay to let any animations start
            time.sleep(0.05)

            # Capture after state
            after_state = await self._capture_state(element)

            return {
                "type": interaction_type,
                "selector": selector,
                "before": before_state,
                "after": after_state,
                "duration_ms": round(duration_ms, 2),
            }
        except Exception:
            return None

    async def _find_interaction_element(
        self,
        target: Locator,
        selector: str,
        scope: ExtractionScope | None = None,
    ) -> Locator | None:
        """Resolve an interaction selector within the correct document scope."""
        element = target.locator(selector)
        if await element.count() > 0:
            return element.first

        if scope is not None:
            frame_element = scope.frame.locator(selector)
            if await frame_element.count() > 0:
                return frame_element.first
            return None

        page_element = self.page.locator(selector)
        if await page_element.count() > 0:
            return page_element.first
        return None

    async def _capture_state(self, element: Locator) -> dict[str, Any]:
        """Capture the current state of an element.

        Args:
            element: Locator for the element.

        Returns:
            Dictionary containing element state information.
        """
        try:
            state = await element.evaluate("""el => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();

                // Capture relevant computed styles
                const computedStyle = {
                    backgroundColor: style.backgroundColor,
                    color: style.color,
                    opacity: style.opacity,
                    transform: style.transform,
                    boxShadow: style.boxShadow,
                    border: style.border,
                    borderRadius: style.borderRadius,
                    visibility: style.visibility,
                    display: style.display,
                };

                return {
                    tag: el.tagName.toLowerCase(),
                    classes: Array.from(el.classList),
                    computedStyle: computedStyle,
                    boundingBox: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                    },
                    attributes: {
                        id: el.id || null,
                        disabled: el.disabled,
                        ariaExpanded: el.getAttribute('aria-expanded'),
                        ariaPressed: el.getAttribute('aria-pressed'),
                    }
                };
            }""")
            return state
        except Exception:
            return {}
