"""Data models for Component Extractor."""

from models.errors import (
    ExtractionError,
    NavigationError,
    TargetNotFoundError,
    APIError,
    BrowserCrashError,
)
from models.extraction import (
    ExtractionMode,
    SelectorStrategy,
    InteractionType,
    AssetType,
    BoundingBox,
    AnimationData,
    TransitionData,
    InteractionState,
    Asset,
    ExternalLibrary,
    ResponsiveBreakpoint,
    AnimationRecording,
)
from models.normalized import (
    BaseNormalizedOutput,
    PageInfo,
    TargetInfo,
    DOMTree,
    StyleSummary,
    ScrollProbeStateChange,
    ScrollProbeSummary,
    AnimationSummary,
    InteractionSummary,
    ResponsiveBehavior,
    PageSectionSummary,
    PageCaptureInfo,
    NormalizedOutput,
    FullPageNormalizedOutput,
)
from models.synthesis import (
    ComponentDescription,
    ComponentTree,
    InteractionBehavior,
    ResponsiveRule,
    Dependency,
    SynthesisOutput,
)

__all__ = [
    # Errors
    "ExtractionError",
    "NavigationError",
    "TargetNotFoundError",
    "APIError",
    "BrowserCrashError",
    # Enums
    "ExtractionMode",
    "SelectorStrategy",
    "InteractionType",
    "AssetType",
    # Extraction Models
    "BoundingBox",
    "AnimationData",
    "TransitionData",
    "InteractionState",
    "Asset",
    "ExternalLibrary",
    "ResponsiveBreakpoint",
    "AnimationRecording",
    # Normalized Models
    "BaseNormalizedOutput",
    "PageInfo",
    "TargetInfo",
    "DOMTree",
    "StyleSummary",
    "ScrollProbeStateChange",
    "ScrollProbeSummary",
    "AnimationSummary",
    "InteractionSummary",
    "ResponsiveBehavior",
    "PageSectionSummary",
    "PageCaptureInfo",
    "NormalizedOutput",
    "FullPageNormalizedOutput",
    # Synthesis Models
    "ComponentDescription",
    "ComponentTree",
    "InteractionBehavior",
    "ResponsiveRule",
    "Dependency",
    "SynthesisOutput",
]
