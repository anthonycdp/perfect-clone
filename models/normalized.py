"""Pydantic models for normalized extraction data."""

from typing import Any, Optional

from pydantic import BaseModel

from models.extraction import (
    AnimationData,
    AnimationRecording,
    BoundingBox,
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


# Rebuild the model to resolve forward references for recursive structure
DOMTree.model_rebuild()


class StyleSummary(BaseModel):
    """Summary of extracted styles organized by category."""

    layout: dict[str, Any]
    spacing: dict[str, Any]
    typography: dict[str, Any]
    colors: dict[str, Any]
    effects: dict[str, Any]


class AnimationSummary(BaseModel):
    """Summary of animations and transitions."""

    css_animations: list[AnimationData]
    css_transitions: list[TransitionData]
    scroll_effects: list[str]
    recording: Optional[AnimationRecording] = None


class InteractionSummary(BaseModel):
    """Summary of interactive elements and observed states."""

    hoverable_elements: list[str]
    clickable_elements: list[str]
    focusable_elements: list[str]
    scroll_containers: list[str]
    observed_states: list[str]


class ResponsiveBehavior(BaseModel):
    """Responsive design behavior analysis."""

    breakpoints: list[ResponsiveBreakpoint]
    is_fluid: bool
    has_mobile_menu: bool
    grid_changes: list[str]


class NormalizedOutput(BaseModel):
    """Combined normalized output from extraction.

    Combines all normalized models into a single output structure.
    """

    page_info: PageInfo
    target_info: TargetInfo
    dom_tree: DOMTree
    style_summary: StyleSummary
    animation_summary: AnimationSummary
    interaction_summary: InteractionSummary
    responsive_behavior: ResponsiveBehavior
