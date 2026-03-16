"""Build normalized output from extraction data."""

from models.extraction import BoundingBox, Asset, ExternalLibrary, ExtractionMode
from models.normalized import (
    AnimationSummary,
    FullPageNormalizedOutput,
    InteractionSummary,
    RichMediaCapture,
    NormalizedOutput,
    PageInfo,
    PageCaptureInfo,
    PageSectionSummary,
    ScrollProbeStateChange,
    ScrollProbeSummary,
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

    def build(self, extraction_data: dict) -> NormalizedOutput | FullPageNormalizedOutput:
        """Build normalized output from raw extraction data."""
        mode = ExtractionMode(extraction_data.get("mode", ExtractionMode.COMPONENT))
        page_data = extraction_data.get("page", {})
        dom_data = extraction_data.get("dom_tree", {})
        styles_data = extraction_data.get("styles", {})
        assets_data = extraction_data.get("assets", [])
        interactions_data = extraction_data.get("interactions", {})
        animations_data = extraction_data.get("animations", {})
        responsive_data = extraction_data.get("responsive", {})
        libraries_data = extraction_data.get("libraries", [])
        rich_media_data = extraction_data.get("rich_media", [])
        collection_limitations = extraction_data.get("collection_limitations", [])

        # Build page info
        page_info = PageInfo(
            url=page_data.get("url", ""),
            title=page_data.get("title", ""),
            viewport=page_data.get("viewport", {}),
            loaded_scripts=page_data.get("loaded_scripts", []),
            loaded_stylesheets=page_data.get("loaded_stylesheets", []),
        )

        # Transform DOM
        dom_tree = self.dom_transformer.transform(dom_data)

        # Transform styles
        style_summary = self.style_transformer.transform(styles_data)

        interaction_summary = self._build_interaction_summary(interactions_data)
        animation_summary = self._build_animation_summary(animations_data)

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
        rich_media = self._build_rich_media_captures(rich_media_data)

        common_fields = {
            "page": page_info,
            "dom": dom_tree,
            "styles": style_summary,
            "assets": assets,
            "interactions": interaction_summary,
            "animations": animation_summary,
            "responsive_behavior": responsive_behavior,
            "external_libraries": libraries,
            "rich_media": rich_media,
            "collection_limitations": collection_limitations,
        }

        if mode == ExtractionMode.FULL_PAGE:
            return self._build_full_page_output(
                extraction_data.get("page_capture", {}),
                common_fields,
            )

        return self._build_component_output(
            extraction_data.get("target", {}),
            common_fields,
        )

    def _build_component_output(
        self,
        target_data: dict,
        common_fields: dict,
    ) -> NormalizedOutput:
        """Build normalized output for a single component target."""
        box_data = target_data.get("bounding_box", {})
        target_info = TargetInfo(
            selector_used=target_data.get("selector_used", ""),
            strategy=target_data.get("strategy", "css"),
            html=target_data.get("html", ""),
            bounding_box=self._build_bounding_box(box_data),
            depth_in_dom=target_data.get("depth", 0),
            screenshot_path=target_data.get("screenshot_path"),
            frame_url=target_data.get("frame_url"),
            frame_name=target_data.get("frame_name"),
            same_origin_accessible=target_data.get("same_origin_accessible", True),
            within_shadow_dom=target_data.get("within_shadow_dom", False),
            frame_limitations=target_data.get("frame_limitations", []),
        )

        return NormalizedOutput(
            **common_fields,
            target=target_info,
        )

    def _build_full_page_output(
        self,
        page_capture_data: dict,
        common_fields: dict,
    ) -> FullPageNormalizedOutput:
        """Build normalized output for a full-page extraction."""
        sections = [
            PageSectionSummary(
                section_id=section.get("section_id", ""),
                name=section.get("name", ""),
                selector=section.get("selector", ""),
                tag=section.get("tag", "section"),
                text_excerpt=section.get("text_excerpt", ""),
                bounding_box=self._build_bounding_box(
                    section.get("bounding_box", {})
                ),
                html=section.get("html", ""),
                screenshot_path=section.get("screenshot_path"),
                interactions=self._build_interaction_summary(section.get("interactions"))
                if section.get("interactions")
                else None,
                animations=self._build_animation_summary(section.get("animations"))
                if section.get("animations")
                else None,
                rich_media=self._build_rich_media_captures(
                    section.get("rich_media", [])
                ),
                collection_limitations=section.get("collection_limitations", []),
            )
            for section in page_capture_data.get("sections", [])
        ]

        page_capture = PageCaptureInfo(
            html=page_capture_data.get("html", ""),
            screenshot_path=page_capture_data.get("screenshot_path"),
            bounding_box=self._build_bounding_box(
                page_capture_data.get("bounding_box", {})
            ),
            scroll_completed=page_capture_data.get("scroll_completed", False),
            sections=sections,
        )

        return FullPageNormalizedOutput(
            **common_fields,
            page_capture=page_capture,
        )

    def _build_bounding_box(self, box_data: dict) -> BoundingBox:
        """Normalize raw bounding box dictionaries into a model."""
        return BoundingBox(
            x=box_data.get("x", 0),
            y=box_data.get("y", 0),
            width=box_data.get("width", 0),
            height=box_data.get("height", 0),
        )

    def _build_interaction_summary(
        self,
        interactions_data: dict | None,
    ) -> InteractionSummary:
        """Build an interaction summary from raw collector output."""
        interactions_data = interactions_data or {}
        return InteractionSummary(
            hoverable_elements=[
                el.get("selector", "") if isinstance(el, dict) else el
                for el in interactions_data.get("hoverable", [])
            ],
            clickable_elements=[
                el.get("selector", "") if isinstance(el, dict) else el
                for el in interactions_data.get("clickable", [])
            ],
            focusable_elements=[
                el.get("selector", "") if isinstance(el, dict) else el
                for el in interactions_data.get("focusable", [])
            ],
            scroll_containers=[
                el.get("selector", "") if isinstance(el, dict) else el
                for el in interactions_data.get("scroll_containers", [])
            ],
            observed_states={
                state.get("selector", f"state_{index}"): state
                for index, state in enumerate(
                    interactions_data.get("observed_states", [])
                )
                if isinstance(state, dict)
            },
        )

    def _build_animation_summary(
        self,
        animations_data: dict | None,
    ) -> AnimationSummary:
        """Build a normalized animation summary from raw collector output."""
        animations_data = animations_data or {}
        return self.animation_transformer.transform(
            animations_data.get("animations", []),
            animations_data.get("transitions", []),
            animations_data.get("keyframes", {}),
            animations_data.get("observed_scroll_effects", []),
            animations_data.get("recording"),
            self._build_scroll_probe_summary(animations_data.get("scroll_probe")),
        )

    def _build_rich_media_captures(
        self,
        rich_media_data: list[dict] | None,
    ) -> list[RichMediaCapture]:
        """Build normalized rich-media captures from raw collector output."""
        return [
            RichMediaCapture(
                **{
                    **entry,
                    "bounding_box": self._build_bounding_box(
                        entry.get("bounding_box", {})
                    ),
                }
            )
            for entry in rich_media_data or []
        ]

    def _build_scroll_probe_summary(
        self,
        scroll_probe_data: dict | None,
    ) -> ScrollProbeSummary | None:
        """Build a normalized scroll probe summary when probe data exists."""
        if not scroll_probe_data:
            return None
        if hasattr(scroll_probe_data, "model_dump"):
            scroll_probe_data = scroll_probe_data.model_dump(mode="json")

        state_changes = [
            ScrollProbeStateChange(
                selector=entry.get("selector", ""),
                property_changes=entry.get("property_changes", {}),
                first_changed_step=entry.get("first_changed_step", 0),
                peak_changed_step=entry.get("peak_changed_step", 0),
                notes=entry.get("notes", []),
            )
            for entry in scroll_probe_data.get("state_changes", [])
        ]

        return ScrollProbeSummary(
            context=scroll_probe_data.get("context", "page"),
            triggered=scroll_probe_data.get("triggered", False),
            range_start=scroll_probe_data.get("range_start", 0),
            range_end=scroll_probe_data.get("range_end", 0),
            step_count=scroll_probe_data.get("step_count", 0),
            fps=scroll_probe_data.get("fps", 0),
            frames_dir=scroll_probe_data.get("frames_dir"),
            video_path=scroll_probe_data.get("video_path"),
            key_frames=scroll_probe_data.get("key_frames", []),
            tracked_selectors=scroll_probe_data.get("tracked_selectors", []),
            overlay_selectors=scroll_probe_data.get("overlay_selectors", []),
            observations=scroll_probe_data.get("observations", []),
            state_changes=state_changes,
            limitations=scroll_probe_data.get("limitations", []),
        )
