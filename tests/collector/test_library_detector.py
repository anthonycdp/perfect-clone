"""Tests for LibraryDetector."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is at the FRONT of sys.path
project_root = str(Path(__file__).resolve().parent.parent.parent)
while project_root in sys.path:
    sys.path.remove(project_root)
sys.path.insert(0, project_root)

import pytest
from playwright.sync_api import Page

from collector.library_detector import LibraryDetector
from models.extraction import ExternalLibrary


class TestLibraryDetectorInit:
    """Tests for LibraryDetector initialization."""

    def test_init_stores_page(self):
        """init should store page reference."""
        mock_page = MagicMock(spec=Page)

        detector = LibraryDetector(mock_page)

        assert detector.page == mock_page

    def test_known_libraries_constant_exists(self):
        """KNOWN_LIBRARIES should be defined."""
        mock_page = MagicMock(spec=Page)

        detector = LibraryDetector(mock_page)

        assert hasattr(detector, "KNOWN_LIBRARIES")
        assert isinstance(detector.KNOWN_LIBRARIES, dict)


class TestLibraryDetectorDetect:
    """Tests for LibraryDetector.detect()."""

    def test_detect_returns_list(self):
        """detect() should return a list of ExternalLibrary objects."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = {
            "scripts": [],
            "globals": {},
            "inline_scripts": [],
        }

        detector = LibraryDetector(mock_page)
        result = detector.detect()

        assert isinstance(result, list)

    def test_detect_finds_library_from_script_url(self):
        """detect() should find libraries from script src URLs."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = {
            "scripts": [
                {"src": "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.0/gsap.min.js"},
                {"src": "https://unpkg.com/swiper@8.4.5/swiper-bundle.min.js"},
            ],
            "globals": {},
            "inline_scripts": [],
        }

        detector = LibraryDetector(mock_page)
        result = detector.detect()

        # Should find GSAP and Swiper
        names = [lib.name for lib in result]
        assert "GSAP" in names
        assert "Swiper" in names

    def test_detect_finds_library_from_globals(self):
        """detect() should find libraries from window globals."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = {
            "scripts": [],
            "globals": {
                "gsap": True,
                "THREE": True,
                "lottie": True,
            },
            "inline_scripts": [],
        }

        detector = LibraryDetector(mock_page)
        result = detector.detect()

        names = [lib.name for lib in result]
        assert "GSAP" in names
        assert "Three.js" in names
        assert "Lottie" in names

    def test_detect_extracts_version_from_url(self):
        """detect() should extract version numbers from CDN URLs."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = {
            "scripts": [
                {"src": "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"},
            ],
            "globals": {},
            "inline_scripts": [],
        }

        detector = LibraryDetector(mock_page)
        result = detector.detect()

        gsap = next((lib for lib in result if lib.name == "GSAP"), None)
        assert gsap is not None
        assert gsap.version == "3.12.2"

    def test_detect_extracts_usage_snippets(self):
        """detect() should extract usage snippets from inline scripts."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = {
            "scripts": [],
            "globals": {"gsap": True},
            "inline_scripts": [
                "gsap.to('.box', {duration: 1, x: 100});",
                "gsap.from('.title', {opacity: 0, y: 50});",
            ],
        }

        detector = LibraryDetector(mock_page)
        result = detector.detect()

        gsap = next((lib for lib in result if lib.name == "GSAP"), None)
        assert gsap is not None
        assert len(gsap.usage_snippets) > 0


class TestLibraryDetectorKnownLibraries:
    """Tests for known library detection."""

    def test_detects_gsap(self):
        """detect() should detect GSAP library."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = {
            "scripts": [],
            "globals": {"gsap": True, "TweenMax": True},
            "inline_scripts": [],
        }

        detector = LibraryDetector(mock_page)
        result = detector.detect()

        names = [lib.name for lib in result]
        assert "GSAP" in names

    def test_detects_lottie(self):
        """detect() should detect Lottie library."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = {
            "scripts": [],
            "globals": {"lottie": True, "bodymovin": True},
            "inline_scripts": [],
        }

        detector = LibraryDetector(mock_page)
        result = detector.detect()

        names = [lib.name for lib in result]
        assert "Lottie" in names

    def test_detects_threejs(self):
        """detect() should detect Three.js library."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = {
            "scripts": [],
            "globals": {"THREE": True},
            "inline_scripts": [],
        }

        detector = LibraryDetector(mock_page)
        result = detector.detect()

        names = [lib.name for lib in result]
        assert "Three.js" in names

    def test_detects_aos(self):
        """detect() should detect AOS library."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = {
            "scripts": [],
            "globals": {"AOS": True},
            "inline_scripts": [],
        }

        detector = LibraryDetector(mock_page)
        result = detector.detect()

        names = [lib.name for lib in result]
        assert "AOS" in names

    def test_detects_scrolltrigger(self):
        """detect() should detect ScrollTrigger plugin."""
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate.return_value = {
            "scripts": [],
            "globals": {"ScrollTrigger": True},
            "inline_scripts": [],
        }

        detector = LibraryDetector(mock_page)
        result = detector.detect()

        names = [lib.name for lib in result]
        assert "ScrollTrigger" in names
