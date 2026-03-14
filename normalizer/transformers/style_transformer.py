"""Transform raw styles into categorized StyleSummary."""

from models.normalized import StyleSummary


class StyleTransformer:
    """Categorize computed styles."""

    LAYOUT_PROPS = {
        "display",
        "position",
        "flex-direction",
        "flex-wrap",
        "justify-content",
        "align-items",
        "align-content",
        "grid-template-columns",
        "grid-template-rows",
        "gap",
        "row-gap",
        "column-gap",
        "float",
        "clear",
        "z-index",
        "order",
    }

    SPACING_PROPS = {
        "margin",
        "margin-top",
        "margin-right",
        "margin-bottom",
        "margin-left",
        "padding",
        "padding-top",
        "padding-right",
        "padding-bottom",
        "padding-left",
        "width",
        "height",
        "min-width",
        "max-width",
        "min-height",
        "max-height",
    }

    TYPOGRAPHY_PROPS = {
        "font-family",
        "font-size",
        "font-weight",
        "font-style",
        "line-height",
        "letter-spacing",
        "text-align",
        "text-decoration",
        "text-transform",
        "white-space",
        "word-spacing",
        "word-break",
    }

    COLOR_PROPS = {
        "color",
        "background-color",
        "border-color",
        "outline-color",
        "text-shadow",
        "box-shadow",
    }

    EFFECTS_PROPS = {
        "opacity",
        "transform",
        "filter",
        "backdrop-filter",
        "mix-blend-mode",
        "border-radius",
        "border-width",
        "border-style",
        "outline",
        "overflow",
        "overflow-x",
        "overflow-y",
        "visibility",
    }

    def transform(self, raw_styles: dict) -> StyleSummary:
        """Categorize raw styles into groups."""
        return StyleSummary(
            layout=self._extract_category(raw_styles, self.LAYOUT_PROPS),
            spacing=self._extract_category(raw_styles, self.SPACING_PROPS),
            typography=self._extract_category(raw_styles, self.TYPOGRAPHY_PROPS),
            colors=self._extract_category(raw_styles, self.COLOR_PROPS),
            effects=self._extract_category(raw_styles, self.EFFECTS_PROPS),
        )

    def _extract_category(self, styles: dict, props: set) -> dict:
        """Extract matching properties from styles."""
        return {prop: styles[prop] for prop in props if prop in styles}
