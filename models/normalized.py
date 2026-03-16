"""Pydantic models for normalized extraction data."""

from typing import Any, Optional

from pydantic import BaseModel, Field

from models.extraction import (
    AnimationData,
    AnimationRecording,
    Asset,
    BoundingBox,
    ExtractionMode,
    ExternalLibrary,
    RichMediaType,
    ResponsiveBreakpoint,
    SelectorStrategy,
    TransitionData,
)


class PageInfo(BaseModel):
    """Information about the page being analyzed."""

    url: str
    title: str
    viewport: dict[str, int]
    loaded_scripts: list[str]
    loaded_stylesheets: list[str]


class TargetInfo(BaseModel):
    """Information about the target element being extracted."""

    selector_used: str
    strategy: SelectorStrategy
    html: str
    bounding_box: BoundingBox
    depth_in_dom: int
    screenshot_path: Optional[str] = None
    frame_url: Optional[str] = None
    frame_name: Optional[str] = None
    same_origin_accessible: bool = True
    within_shadow_dom: bool = False
    frame_limitations: list[str] = Field(default_factory=list)


class DOMTree(BaseModel):
    """Recursive DOM tree structure.

    IMPORTANT: After defining this class, call DOMTree.model_rebuild()
    to resolve the forward reference in the children field.
    """

    tag: str
    attributes: dict[str, Any]
    children: list["DOMTree"]
    text_content: str
    computed_styles: dict[str, Any]
    shadow_root: "DOMTree | None" = None


# Rebuild the model to resolve forward references for recursive structure
DOMTree.model_rebuild()


class StyleSummary(BaseModel):
    """Summary of extracted styles organized by category."""

    layout: dict[str, Any]
    spacing: dict[str, Any]
    typography: dict[str, Any]
    colors: dict[str, Any]
    effects: dict[str, Any]


class ScrollProbeStateChange(BaseModel):
    """Observed property changes for one selector during the scroll probe."""

    selector: str
    property_changes: dict[str, Any]
    first_changed_step: int
    peak_changed_step: int
    notes: list[str] = Field(default_factory=list)


class ScrollProbeSummary(BaseModel):
    """Structured output from the runtime scroll probe."""

    context: str
    triggered: bool
    range_start: float
    range_end: float
    step_count: int
    fps: int
    frames_dir: Optional[str] = None
    video_path: Optional[str] = None
    key_frames: list[int] = Field(default_factory=list)
    tracked_selectors: list[str] = Field(default_factory=list)
    overlay_selectors: list[str] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    state_changes: list[ScrollProbeStateChange] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class AnimationSummary(BaseModel):
    """Summary of animations and transitions."""

    css_animations: list[AnimationData]
    css_transitions: list[TransitionData]
    scroll_effects: list[str]
    recording: Optional[AnimationRecording] = None
    scroll_probe: Optional[ScrollProbeSummary] = None


class InteractionSummary(BaseModel):
    """Summary of interactive elements and observed states."""

    hoverable_elements: list[str]
    clickable_elements: list[str]
    focusable_elements: list[str]
    scroll_containers: list[str]
    observed_states: dict[str, Any]


class ResponsiveBehavior(BaseModel):
    """Responsive design behavior analysis."""

    breakpoints: list[ResponsiveBreakpoint]
    is_fluid: bool
    has_mobile_menu: bool
    grid_changes: list[dict[str, Any]]


class RichMediaCapture(BaseModel):
    """Captured runtime media metadata and snapshots."""

    type: RichMediaType
    selector: str
    bounding_box: BoundingBox
    source_urls: list[str] = Field(default_factory=list)
    poster_url: Optional[str] = None
    snapshot_path: Optional[str] = None
    playback_flags: dict[str, bool] = Field(default_factory=dict)
    document_level: bool = False
    linked_selectors: list[str] = Field(default_factory=list)
    effect_summary: Optional[str] = None
    limitations: list[str] = Field(default_factory=list)


class BaseNormalizedOutput(BaseModel):
    """Shared normalized data for every extraction mode."""

    mode: ExtractionMode
    page: PageInfo
    dom: DOMTree
    styles: StyleSummary
    animations: AnimationSummary
    interactions: InteractionSummary
    responsive_behavior: ResponsiveBehavior
    assets: list[Asset]
    external_libraries: list[ExternalLibrary]
    rich_media: list[RichMediaCapture] = Field(default_factory=list)
    collection_limitations: list[str] = Field(default_factory=list)

    def get_primary_screenshot_path(self) -> str | None:
        """Return the primary screenshot path associated with this extraction."""
        return None


class PageSectionSummary(BaseModel):
    """High-level section detected within a full-page extraction."""

    section_id: str = ""
    name: str
    selector: str
    tag: str
    text_excerpt: str
    bounding_box: BoundingBox
    html: str = ""
    screenshot_path: Optional[str] = None
    interactions: InteractionSummary | None = None
    animations: AnimationSummary | None = None
    rich_media: list[RichMediaCapture] = Field(default_factory=list)
    collection_limitations: list[str] = Field(default_factory=list)


class PageCaptureInfo(BaseModel):
    """Full-page specific metadata captured during extraction."""

    html: str
    screenshot_path: Optional[str] = None
    bounding_box: BoundingBox
    scroll_completed: bool
    sections: list[PageSectionSummary]


class NormalizedOutput(BaseNormalizedOutput):
    """Normalized output for single-component extraction."""

    mode: ExtractionMode = ExtractionMode.COMPONENT
    target: TargetInfo

    def get_primary_screenshot_path(self) -> str | None:
        """Return the target screenshot when available."""
        return self.target.screenshot_path


class FullPageNormalizedOutput(BaseNormalizedOutput):
    """Normalized output for full-page extraction."""

    mode: ExtractionMode = ExtractionMode.FULL_PAGE
    page_capture: PageCaptureInfo

    def get_primary_screenshot_path(self) -> str | None:
        """Return the full-page screenshot when available."""
        return self.page_capture.screenshot_path
