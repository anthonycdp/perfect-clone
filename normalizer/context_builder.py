"""Build normalized output from extraction data."""

from models.extraction import BoundingBox, Asset, ExternalLibrary
from models.normalized import (
    NormalizedOutput,
    PageInfo,
    TargetInfo,
    InteractionSummary,
    ResponsiveBehavior,
)
from normalizer.transformers import DOMTransformer, StyleTransformer, AnimationTransformer


class ContextBuilder:
    """Assemble extraction data into NormalizedOutput."""

    def __init__(self):
        self.dom_transformer = DOMTransformer()
        self.style_transformer = StyleTransformer()
        self.animation_transformer = AnimationTransformer()

    def build(self, extraction_data: dict) -> NormalizedOutput:
        """Build NormalizedOutput from raw extraction data."""
        page_data = extraction_data.get("page", {})
        target_data = extraction_data.get("target", {})
        dom_data = extraction_data.get("dom_tree", {})
        styles_data = extraction_data.get("styles", {})
        assets_data = extraction_data.get("assets", [])
        interactions_data = extraction_data.get("interactions", {})
        animations_data = extraction_data.get("animations", {})
        responsive_data = extraction_data.get("responsive", {})
        libraries_data = extraction_data.get("libraries", [])

        # Build page info
        page_info = PageInfo(
            url=page_data.get("url", ""),
            title=page_data.get("title", ""),
            viewport=page_data.get("viewport", {}),
            loaded_scripts=page_data.get("loaded_scripts", []),
            loaded_stylesheets=page_data.get("loaded_stylesheets", []),
        )

        # Build target info
        box_data = target_data.get("bounding_box", {})
        target_info = TargetInfo(
            selector_used=target_data.get("selector_used", ""),
            strategy=target_data.get("strategy", "css"),
            html=target_data.get("html", ""),
            bounding_box=BoundingBox(
                x=box_data.get("x", 0),
                y=box_data.get("y", 0),
                width=box_data.get("width", 0),
                height=box_data.get("height", 0),
            ),
            depth_in_dom=target_data.get("depth", 0),
        )

        # Transform DOM
        dom_tree = self.dom_transformer.transform(dom_data)

        # Transform styles
        style_summary = self.style_transformer.transform(styles_data)

        # Build interaction summary
        interaction_summary = InteractionSummary(
            hoverable_elements=interactions_data.get("hoverable", []),
            clickable_elements=interactions_data.get("clickable", []),
            focusable_elements=interactions_data.get("focusable", []),
            scroll_containers=interactions_data.get("scroll_containers", []),
            observed_states=interactions_data.get("observed_states", {}),
        )

        # Transform animations
        animation_summary = self.animation_transformer.transform(
            animations_data.get("animations", []),
            animations_data.get("transitions", []),
            animations_data.get("keyframes", {}),
            animations_data.get("recording"),
        )

        # Build responsive behavior
        responsive_behavior = ResponsiveBehavior(
            breakpoints=responsive_data.get("breakpoints", []),
            is_fluid=responsive_data.get("is_fluid", False),
            has_mobile_menu=responsive_data.get("has_mobile_menu", False),
            grid_changes=responsive_data.get("grid_changes", []),
        )

        # Build assets
        assets = [Asset(**a) for a in assets_data]

        # Build libraries
        libraries = [ExternalLibrary(**lib) for lib in libraries_data]

        return NormalizedOutput(
            page=page_info,
            target=target_info,
            dom=dom_tree,
            styles=style_summary,
            assets=assets,
            interactions=interaction_summary,
            animations=animation_summary,
            responsive_behavior=responsive_behavior,
            external_libraries=libraries,
        )
