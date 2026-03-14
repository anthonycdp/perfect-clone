"""ResponsiveCollector - Collects responsive breakpoint behavior."""

import re
from typing import Any

from playwright.sync_api import Locator, Page

from models.extraction import ResponsiveBreakpoint
from models.normalized import ResponsiveBehavior


class ResponsiveCollector:
    """Collects responsive design behavior at various viewport sizes.

    Detects CSS media query breakpoints and captures component state
    at different viewport widths.
    """

    STANDARD_BREAKPOINTS = [320, 480, 768, 1024, 1280, 1440]

    def __init__(self, page: Page):
        """Initialize ResponsiveCollector.

        Args:
            page: Playwright Page object to analyze.
        """
        self.page = page

    def detect_breakpoints(self) -> list[int]:
        """Extract breakpoints from CSS media queries via CSSOM.

        Returns:
            List of breakpoint widths in pixels.
        """
        try:
            breakpoints = self.page.evaluate("""() => {
                const breakpoints = new Set();
                const sheets = document.styleSheets;

                try {
                    for (const sheet of sheets) {
                        try {
                            for (const rule of sheet.cssRules) {
                                if (rule instanceof CSSMediaRule) {
                                    const mediaText = rule.media.mediaText;
                                    // Extract min-width values
                                    const minMatch = mediaText.match(/min-width:\\s*(\\d+)px/i);
                                    if (minMatch) {
                                        breakpoints.add(parseInt(minMatch[1], 10));
                                    }
                                    // Extract max-width values
                                    const maxMatch = mediaText.match(/max-width:\\s*(\\d+)px/i);
                                    if (maxMatch) {
                                        // Convert max-width to breakpoint
                                        breakpoints.add(parseInt(maxMatch[1], 10));
                                    }
                                }
                            }
                        } catch (e) {
                            // CORS or other error accessing stylesheet
                        }
                    }
                } catch (e) {
                    // Error accessing stylesheets
                }

                return Array.from(breakpoints).sort((a, b) => a - b);
            }""")

            if breakpoints:
                return breakpoints

            # Return standard breakpoints if none found
            return list(self.STANDARD_BREAKPOINTS)
        except Exception:
            # Return standard breakpoints on error
            return list(self.STANDARD_BREAKPOINTS)

    def collect_at_viewport(
        self, target: Locator, width: int, height: int
    ) -> dict[str, Any]:
        """Capture component state at specific viewport.

        Args:
            target: Locator for the target element.
            width: Viewport width in pixels.
            height: Viewport height in pixels.

        Returns:
            Dictionary of computed styles and layout properties.
        """
        # Set viewport size
        self.page.set_viewport_size({"width": width, "height": height})

        # Capture element state
        return target.evaluate("""el => {
            const styles = window.getComputedStyle(el);
            const rect = el.getBoundingClientRect();

            return {
                // Layout
                display: styles.display,
                position: styles.position,
                flexDirection: styles.flexDirection,
                flexWrap: styles.flexWrap,
                justifyContent: styles.justifyContent,
                alignItems: styles.alignItems,
                gridTemplateColumns: styles.gridTemplateColumns,
                gridTemplateRows: styles.gridTemplateRows,

                // Dimensions
                width: rect.width,
                height: rect.height,
                minWidth: styles.minWidth,
                maxWidth: styles.maxWidth,

                // Spacing
                padding: styles.padding,
                margin: styles.margin,
                gap: styles.gap,

                // Typography
                fontSize: styles.fontSize,
                lineHeight: styles.lineHeight,
                textAlign: styles.textAlign,

                // Visibility
                visibility: styles.visibility,
                opacity: styles.opacity,
                overflow: styles.overflow,

                // Transform
                transform: styles.transform,
            };
        }""")

    def collect_all(self, target: Locator) -> ResponsiveBehavior:
        """Collect responsive behavior at all breakpoints.

        Args:
            target: Locator for the target element.

        Returns:
            ResponsiveBehavior object with breakpoint data.
        """
        # Detect media query breakpoints
        detected_breakpoints = self.detect_breakpoints()

        # Combine with standard breakpoints, deduplicated and sorted
        all_breakpoints = sorted(
            set(detected_breakpoints) | set(self.STANDARD_BREAKPOINTS)
        )

        # Collect state at each breakpoint
        breakpoint_data: list[ResponsiveBreakpoint] = []
        prev_state: dict[str, Any] | None = None
        grid_changes: list[dict[str, Any]] = []
        has_mobile_menu = False
        is_fluid = True

        for width in all_breakpoints:
            # Use 4:3 aspect ratio for height
            height = int(width * 0.75)

            try:
                state = self.collect_at_viewport(target, width, height)

                # Calculate style diff from previous breakpoint
                styles_diff = {}
                layout_changes = []

                if prev_state is not None:
                    styles_diff = self._compute_style_diff(prev_state, state)
                    layout_changes = self._detect_layout_changes(prev_state, state)

                    # Track grid changes
                    if "gridTemplateColumns" in styles_diff:
                        grid_changes.append({
                            "breakpoint": width,
                            "from": prev_state.get("gridTemplateColumns"),
                            "to": state.get("gridTemplateColumns"),
                        })

                    # Check for mobile menu indicators
                    if width <= 768:
                        if state.get("display") != prev_state.get("display"):
                            has_mobile_menu = True

                # Check if element is fluid (uses % or responsive units)
                if state.get("maxWidth") not in ["none", "100%"]:
                    is_fluid = False

                breakpoint_data.append(
                    ResponsiveBreakpoint(
                        width=width,
                        height=height,
                        source="media_query" if width in detected_breakpoints else "user_defined",
                        styles_diff=styles_diff,
                        layout_changes=layout_changes,
                    )
                )

                prev_state = state
            except Exception:
                continue

        return ResponsiveBehavior(
            breakpoints=breakpoint_data,
            is_fluid=is_fluid,
            has_mobile_menu=has_mobile_menu,
            grid_changes=grid_changes,
        )

    def _compute_style_diff(
        self, prev: dict[str, Any], curr: dict[str, Any]
    ) -> dict[str, Any]:
        """Compute the difference between two style states.

        Args:
            prev: Previous style state.
            curr: Current style state.

        Returns:
            Dictionary of changed properties with (old, new) values.
        """
        diff = {}

        for key in curr:
            if key in prev and prev[key] != curr[key]:
                diff[key] = {"from": prev[key], "to": curr[key]}

        return diff

    def _detect_layout_changes(
        self, prev: dict[str, Any], curr: dict[str, Any]
    ) -> list[str]:
        """Detect significant layout changes between states.

        Args:
            prev: Previous style state.
            curr: Current style state.

        Returns:
            List of description strings for layout changes.
        """
        changes = []

        # Display change
        if prev.get("display") != curr.get("display"):
            changes.append(
                f"display: {prev.get('display')} -> {curr.get('display')}"
            )

        # Flex direction change
        if prev.get("flexDirection") != curr.get("flexDirection"):
            changes.append(
                f"flex-direction: {prev.get('flexDirection')} -> {curr.get('flexDirection')}"
            )

        # Position change
        if prev.get("position") != curr.get("position"):
            changes.append(
                f"position: {prev.get('position')} -> {curr.get('position')}"
            )

        # Grid changes
        if prev.get("gridTemplateColumns") != curr.get("gridTemplateColumns"):
            changes.append("grid-columns changed")

        # Visibility change
        if prev.get("visibility") != curr.get("visibility"):
            changes.append(
                f"visibility: {prev.get('visibility')} -> {curr.get('visibility')}"
            )

        return changes
