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
    # Models
    "BoundingBox",
    "AnimationData",
    "TransitionData",
    "InteractionState",
    "Asset",
    "ExternalLibrary",
    "ResponsiveBreakpoint",
    "AnimationRecording",
]
