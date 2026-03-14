"""Data models for Component Extractor."""

from models.errors import (
    ExtractionError,
    NavigationError,
    TargetNotFoundError,
    APIError,
    BrowserCrashError,
)
from models.extraction import (
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
    PageInfo,
    TargetInfo,
    DOMTree,
    StyleSummary,
    AnimationSummary,
    InteractionSummary,
    ResponsiveBehavior,
    NormalizedOutput,
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
    "PageInfo",
    "TargetInfo",
    "DOMTree",
    "StyleSummary",
    "AnimationSummary",
    "InteractionSummary",
    "ResponsiveBehavior",
    "NormalizedOutput",
    # Synthesis Models
    "ComponentDescription",
    "ComponentTree",
    "InteractionBehavior",
    "ResponsiveRule",
    "Dependency",
    "SynthesisOutput",
]
