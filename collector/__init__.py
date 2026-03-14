"""Collector module for browser automation and element extraction."""

from collector.asset_downloader import AssetDownloader
from collector.browser import BrowserManager
from collector.interaction_mapper import InteractionMapper
from collector.interaction_player import InteractionPlayer
from collector.target_finder import TargetFinder

__all__ = [
    "AssetDownloader",
    "BrowserManager",
    "InteractionMapper",
    "InteractionPlayer",
    "TargetFinder",
]
