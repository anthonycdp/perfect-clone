"""Pydantic models for raw extraction data."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class SelectorStrategy(str, Enum):
    """Strategy for selecting elements."""

    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    HTML_SNIPPET = "html_snippet"


class ExtractionMode(str, Enum):
    """Scope of extraction requested by the user."""

    COMPONENT = "component"
    FULL_PAGE = "full_page"


class InteractionType(str, Enum):
    """Type of user interaction."""

    HOVER = "hover"
    CLICK = "click"
    FOCUS = "focus"
    SCROLL = "scroll"


class AssetType(str, Enum):
    """Type of extracted asset."""

    IMAGE = "image"
    SVG = "svg"
    FONT = "font"
    VIDEO = "video"


class RichMediaType(str, Enum):
    """Type of rich media element captured from the page."""

    VIDEO = "video"
    CANVAS = "canvas"
    WEBGL = "webgl"


class BoundingBox(BaseModel):
    """Bounding box coordinates for an element."""

    x: float
    y: float
    width: float
    height: float


class AnimationData(BaseModel):
    """CSS animation data."""

    name: Optional[str] = None
    duration: str
    delay: str
    timing_function: str
    iteration_count: str
    direction: str
    fill_mode: str
    keyframes: Optional[dict[str, Any]] = None


class TransitionData(BaseModel):
    """CSS transition data."""

    property: str
    duration: str
    timing_function: str
    delay: str


class InteractionState(BaseModel):
    """Recorded interaction state change."""

    type: InteractionType
    selector: str
    before: dict[str, Any]
    after: dict[str, Any]
    duration_ms: float


class Asset(BaseModel):
    """Extracted asset (image, font, etc.)."""

    type: AssetType
    original_url: str
    local_path: str
    file_size_bytes: int
    dimensions: Optional[list[int]] = None


class ExternalLibrary(BaseModel):
    """Detected external JavaScript library."""

    name: str
    version: Optional[str] = None
    source_url: str
    usage_snippets: list[str]
    init_code: Optional[str] = None


class ResponsiveBreakpoint(BaseModel):
    """Responsive design breakpoint data."""

    width: int
    height: int
    source: str  # "media_query" or "user_defined"
    styles_diff: dict[str, Any]
    layout_changes: list[str]


class AnimationRecording(BaseModel):
    """Recorded animation video data."""

    video_path: str
    duration_ms: float
    fps: int
    frames_dir: str
    key_frames: list[int]
