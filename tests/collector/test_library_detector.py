"""Tests for LibraryDetector."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from playwright.async_api import Page

from collector.extraction_scope import ExtractionScope
from collector.library_detector import LibraryDetector


class TestLibraryDetectorInit:
    """Tests for LibraryDetector initialization."""

    def test_init_stores_page(self):
        mock_page = MagicMock(spec=Page)
        detector = LibraryDetector(mock_page)
        assert detector.page == mock_page

    def test_known_libraries_constant_exists(self):
        detector = LibraryDetector(MagicMock(spec=Page))
        assert hasattr(detector, "KNOWN_LIBRARIES")
        assert isinstance(detector.KNOWN_LIBRARIES, dict)


@pytest.mark.asyncio
class TestLibraryDetectorDetect:
    """Tests for LibraryDetector.detect()."""

    async def test_detect_returns_list(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(
            return_value={"scripts": [], "globals": {}, "inline_scripts": []}
        )

        result = await LibraryDetector(mock_page).detect()

        assert isinstance(result, list)

    async def test_detect_finds_library_from_script_url(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(
            return_value={
                "scripts": [
                    {"src": "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.0/gsap.min.js"},
                    {"src": "https://unpkg.com/swiper@8.4.5/swiper-bundle.min.js"},
                ],
                "globals": {},
                "inline_scripts": [],
            }
        )

        names = [lib.name for lib in await LibraryDetector(mock_page).detect()]
        assert "GSAP" in names
        assert "Swiper" in names

    async def test_detect_finds_library_from_globals(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(
            return_value={
                "scripts": [],
                "globals": {"gsap": True, "THREE": True, "lottie": True},
                "inline_scripts": [],
            }
        )

        names = [lib.name for lib in await LibraryDetector(mock_page).detect()]
        assert "GSAP" in names
        assert "Three.js" in names
        assert "Lottie" in names

    async def test_detect_merges_frame_and_page_signals(self):
        mock_page = MagicMock(spec=Page)
        mock_frame = MagicMock()
        mock_page.main_frame = MagicMock()
        mock_page.evaluate = AsyncMock(
            return_value={
                "scripts": [],
                "globals": {"gsap": True},
                "inline_scripts": ["gsap.to('.hero', {x: 100});"],
            }
        )
        mock_frame.evaluate = AsyncMock(
            return_value={
                "scripts": [
                    {"src": "https://unpkg.com/swiper@8.4.5/swiper-bundle.min.js"},
                ],
                "globals": {},
                "inline_scripts": [],
            }
        )
        scope = ExtractionScope(
            page=mock_page,
            frame=mock_frame,
            target=MagicMock(),
            selector_used="#workflow",
            strategy="css",
            frame_url="https://example.com/embed",
            frame_name="frame",
            same_origin_accessible=True,
            document_base_url="https://example.com/embed",
        )

        detector = LibraryDetector(mock_page)
        result = await detector.detect(scope=scope)

        names = [lib.name for lib in result]
        assert "GSAP" in names
        assert "Swiper" in names
        assert detector.last_limitations == []

    async def test_detect_extracts_version_from_url(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(
            return_value={
                "scripts": [
                    {"src": "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"},
                ],
                "globals": {},
                "inline_scripts": [],
            }
        )

        result = await LibraryDetector(mock_page).detect()
        gsap = next((lib for lib in result if lib.name == "GSAP"), None)

        assert gsap is not None
        assert gsap.version == "3.12.2"

    async def test_detect_extracts_usage_snippets(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(
            return_value={
                "scripts": [],
                "globals": {"gsap": True},
                "inline_scripts": [
                    "gsap.to('.box', {duration: 1, x: 100});",
                    "gsap.from('.title', {opacity: 0, y: 50});",
                ],
            }
        )

        result = await LibraryDetector(mock_page).detect()
        gsap = next((lib for lib in result if lib.name == "GSAP"), None)

        assert gsap is not None
        assert len(gsap.usage_snippets) > 0


@pytest.mark.asyncio
class TestLibraryDetectorKnownLibraries:
    """Tests for known library detection."""

    async def test_detects_gsap(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(
            return_value={
                "scripts": [],
                "globals": {"gsap": True, "TweenMax": True},
                "inline_scripts": [],
            }
        )
        names = [lib.name for lib in await LibraryDetector(mock_page).detect()]
        assert "GSAP" in names

    async def test_detects_lottie(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(
            return_value={
                "scripts": [],
                "globals": {"lottie": True, "bodymovin": True},
                "inline_scripts": [],
            }
        )
        names = [lib.name for lib in await LibraryDetector(mock_page).detect()]
        assert "Lottie" in names

    async def test_detects_threejs(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(
            return_value={
                "scripts": [],
                "globals": {"THREE": True},
                "inline_scripts": [],
            }
        )
        names = [lib.name for lib in await LibraryDetector(mock_page).detect()]
        assert "Three.js" in names

    async def test_detects_aos(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(
            return_value={
                "scripts": [],
                "globals": {"AOS": True},
                "inline_scripts": [],
            }
        )
        names = [lib.name for lib in await LibraryDetector(mock_page).detect()]
        assert "AOS" in names

    async def test_detects_scrolltrigger(self):
        mock_page = MagicMock(spec=Page)
        mock_page.evaluate = AsyncMock(
            return_value={
                "scripts": [],
                "globals": {"ScrollTrigger": True},
                "inline_scripts": [],
            }
        )
        names = [lib.name for lib in await LibraryDetector(mock_page).detect()]
        assert "ScrollTrigger" in names
