"""Extract computed styles and animation data."""

from typing import Any

from playwright.async_api import Page, Locator

from collector.extraction_scope import ExtractionScope


class StyleExtractor:
    """Extract CSS styles and animations from elements."""

    ANIMATION_PROPS = [
        "animation-name", "animation-duration", "animation-delay",
        "animation-timing-function", "animation-iteration-count",
        "animation-direction", "animation-fill-mode"
    ]

    TRANSITION_PROPS = [
        "transition-property", "transition-duration",
        "transition-timing-function", "transition-delay"
    ]

    DEFAULT_VALUES = {
        "align-content": "normal",
        "align-items": "normal",
        "align-self": "auto",
        "animation": "none 0s ease 0s 1 normal none running none",
        "background": "rgba(0, 0, 0, 0) none repeat scroll 0% 0% / auto padding-box border-box",
        "border": "0px none rgb(0, 0, 0)",
        "border-radius": "0px",
        "bottom": "auto",
        "box-shadow": "none",
        "clear": "none",
        "color": "rgb(0, 0, 0)",
        "cursor": "auto",
        "display": "block",
        "float": "none",
        "font": "normal normal 400 16px / normal serif",
        "height": "auto",
        "left": "auto",
        "letter-spacing": "normal",
        "line-height": "normal",
        "margin": "0px",
        "max-height": "none",
        "max-width": "none",
        "min-height": "0px",
        "min-width": "0px",
        "opacity": "1",
        "outline": "rgb(0, 0, 0) none 0px",
        "overflow": "visible",
        "padding": "0px",
        "position": "static",
        "right": "auto",
        "text-align": "start",
        "text-decoration": "none solid rgb(0, 0, 0)",
        "text-indent": "0px",
        "text-transform": "none",
        "top": "auto",
        "transform": "none",
        "transition": "all 0s ease 0s",
        "visibility": "visible",
        "white-space": "normal",
        "width": "auto",
        "word-spacing": "normal",
        "z-index": "auto",
    }

    def __init__(self, page: Page):
        self.page = page
        self.last_limitations: list[str] = []

    async def extract(
        self,
        target: Locator,
        scope: ExtractionScope | None = None,
    ) -> dict:
        """Extract all style data from target element."""
        self.last_limitations = []
        style_data = await target.evaluate(self._style_extraction_script())

        return await self._build_style_payload(style_data, scope=scope)

    async def extract_page(self) -> dict:
        """Extract style signals for the rendered page body."""
        self.last_limitations = []
        style_data = await self.page.evaluate(
            f"""() => {{
                const root = document.body || document.documentElement;
                {self._build_style_helpers()}
                return extractStyles(root);
            }}"""
        )

        return await self._build_style_payload(style_data)

    async def _build_style_payload(
        self,
        style_data: dict,
        scope: ExtractionScope | None = None,
    ) -> dict:
        """Normalize raw style extraction into the shared payload shape."""
        # Filter out default values
        filtered_styles = {
            k: v for k, v in style_data["computed"].items()
            if not self._is_default(k, v)
        }

        context = scope.frame if scope is not None else self.page
        keyframes = await self._extract_keyframes(context, scope=scope)

        return {
            "computed_styles": filtered_styles,
            "animations": style_data["animations"],
            "transitions": style_data["transitions"],
            "keyframes": keyframes,
            "limitations": list(self.last_limitations),
        }

    def _is_default(self, prop: str, value: str) -> bool:
        """Check if value is likely a browser default."""
        if prop in self.DEFAULT_VALUES:
            default = self.DEFAULT_VALUES[prop]
            return value.replace(" ", "") == default.replace(" ", "")
        return False

    async def _extract_keyframes(
        self,
        context: Any,
        scope: ExtractionScope | None = None,
    ) -> dict:
        """Extract all @keyframes rules from the active document stylesheets."""
        try:
            return await context.evaluate("""() => {
                const keyframes = {};

                for (const sheet of document.styleSheets) {
                    try {
                        for (const rule of sheet.cssRules) {
                            if (rule.type === CSSRule.KEYFRAMES_RULE) {
                                const frames = {};
                                for (const frame of rule.cssRules) {
                                    frames[frame.keyText] = {};
                                    for (const style of frame.style) {
                                        frames[frame.keyText][style] = frame.style.getPropertyValue(style);
                                    }
                                }
                                keyframes[rule.name] = frames;
                            }
                        }
                    } catch (e) {
                        // CORS may block access to some stylesheets
                    }
                }

                return keyframes;
            }""")
        except Exception:
            if scope is not None:
                self.last_limitations.append(
                    "Could not extract keyframes from the target frame stylesheets."
                )
            return {}

    def _style_extraction_script(self) -> str:
        """Return the style extraction script for locator evaluation."""
        return f"""el => {{
            {self._build_style_helpers()}
            return extractStyles(el);
        }}"""

    def _build_style_helpers(self) -> str:
        """Return JS helpers that serialize computed styles and motion data."""
        return """
            function extractStyles(element) {
                const styles = window.getComputedStyle(element);
                const computed = {};

                for (let i = 0; i < styles.length; i++) {
                    const prop = styles[i];
                    computed[prop] = styles.getPropertyValue(prop);
                }

                const animations = [];
                const animName = styles.getPropertyValue('animation-name');
                if (animName && animName !== 'none') {
                    animations.push({
                        name: animName,
                        duration: styles.getPropertyValue('animation-duration'),
                        delay: styles.getPropertyValue('animation-delay'),
                        timing_function: styles.getPropertyValue('animation-timing-function'),
                        iteration_count: styles.getPropertyValue('animation-iteration-count'),
                        direction: styles.getPropertyValue('animation-direction'),
                        fill_mode: styles.getPropertyValue('animation-fill-mode'),
                    });
                }

                const transitions = [];
                const transProp = styles.getPropertyValue('transition-property');
                if (transProp && transProp !== 'all') {
                    const props = transProp.split(',').map(s => s.trim());
                    const durations = styles.getPropertyValue('transition-duration').split(',').map(s => s.trim());
                    const timings = styles.getPropertyValue('transition-timing-function').split(',').map(s => s.trim());
                    const delays = styles.getPropertyValue('transition-delay').split(',').map(s => s.trim());

                    props.forEach((prop, i) => {
                        transitions.push({
                            property: prop,
                            duration: durations[i] || '0s',
                            timing_function: timings[i] || 'ease',
                            delay: delays[i] || '0s',
                        });
                    });
                }

                return {
                    computed,
                    animations,
                    transitions,
                };
            }
        """
