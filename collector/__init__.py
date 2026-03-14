"""Collector module for browser automation and element extraction."""

from collector.animation_recorder import AnimationRecorder
from collector.asset_downloader import AssetDownloader
from collector.browser import BrowserManager
from collector.interaction_mapper import InteractionMapper
from collector.interaction_player import InteractionPlayer
from collector.library_detector import LibraryDetector
from collector.responsive_collector import ResponsiveCollector
from collector.target_finder import TargetFinder

__all__ = [
    "AnimationRecorder",
    "AssetDownloader",
    "BrowserManager",
    "InteractionMapper",
    "InteractionPlayer",
    "LibraryDetector",
    "ResponsiveCollector",
    "TargetFinder",
]
