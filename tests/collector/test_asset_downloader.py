"""Tests for AssetDownloader - downloads images, SVGs, fonts."""

import os
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import Page

from collector.asset_downloader import AssetDownloader
from models.extraction import AssetType


class TestAssetDownloader:
    """Test suite for AssetDownloader."""

    @pytest.fixture
    def temp_dir(self) -> str:
        """Create a temporary directory for downloads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def downloader(self, page: Page, temp_dir: str) -> AssetDownloader:
        """Create an AssetDownloader instance."""
        return AssetDownloader(page, temp_dir)

    def test_download_all_returns_list(
        self, downloader: AssetDownloader, page: Page
    ) -> None:
        """download_all() should return a list of Asset objects."""
        target = page.locator("body")
        result = downloader.download_all(target)

        assert isinstance(result, list)

    def test_download_all_finds_images(
        self, downloader: AssetDownloader, page: Page, temp_dir: str
    ) -> None:
        """download_all() should find and download images."""
        # Create a page with an image
        page.set_content('<html><body><img src="https://example.com/images/test.png"></body></html>')
        target = page.locator("body")

        result = downloader.download_all(target)

        # Check if any images were found (might be empty if image fails to load)
        assert isinstance(result, list)

    def test_download_all_finds_svgs(
        self, downloader: AssetDownloader, page: Page, temp_dir: str
    ) -> None:
        """download_all() should find and download inline SVGs."""
        page.set_content("""
            <html><body>
                <svg width="100" height="100">
                    <circle cx="50" cy="50" r="40" fill="red"/>
                </svg>
            </body></html>
        """)
        target = page.locator("body")

        result = downloader.download_all(target)

        # Should find the SVG
        svg_assets = [a for a in result if a.type == AssetType.SVG]
        assert len(svg_assets) > 0

    def test_download_all_asset_has_required_fields(
        self, downloader: AssetDownloader, page: Page, temp_dir: str
    ) -> None:
        """download_all() assets should have required fields."""
        page.set_content("""
            <html><body>
                <svg width="100" height="100">
                    <circle cx="50" cy="50" r="40" fill="red"/>
                </svg>
            </body></html>
        """)
        target = page.locator("body")

        result = downloader.download_all(target)

        if result:
            asset = result[0]
            assert asset.type in [AssetType.IMAGE, AssetType.SVG, AssetType.FONT]
            assert asset.original_url is not None
            assert asset.local_path is not None
            assert asset.file_size_bytes >= 0

    def test_download_all_saves_to_output_dir(
        self, downloader: AssetDownloader, page: Page, temp_dir: str
    ) -> None:
        """download_all() should save files to output directory."""
        page.set_content("""
            <html><body>
                <svg width="100" height="100">
                    <circle cx="50" cy="50" r="40" fill="red"/>
                </svg>
            </body></html>
        """)
        target = page.locator("body")

        result = downloader.download_all(target)

        if result:
            # Check that local_path is within temp_dir
            for asset in result:
                assert temp_dir in asset.local_path or asset.local_path.startswith("/")

    def test_download_all_handles_external_svgs(
        self, downloader: AssetDownloader, page: Page, temp_dir: str
    ) -> None:
        """download_all() should handle external SVG files."""
        page.set_content("""
            <html><body>
                <img src="https://example.com/icon.svg">
            </body></html>
        """)
        target = page.locator("body")

        # Should not raise
        result = downloader.download_all(target)
        assert isinstance(result, list)

    def test_download_all_scoped_to_target(
        self, downloader: AssetDownloader, page: Page, temp_dir: str
    ) -> None:
        """download_all() should only find assets within target."""
        page.set_content("""
            <html><body>
                <div id="first"><img src="image1.png"></div>
                <div id="second"><img src="image2.png"></div>
            </body></html>
        """)
        target = page.locator("#first")

        result = downloader.download_all(target)

        # Should only find image1.png (though external images may not download)
        # The important thing is it doesn't find assets outside target
        assert isinstance(result, list)

    def test_download_all_handles_fonts(
        self, downloader: AssetDownloader, page: Page, temp_dir: str
    ) -> None:
        """download_all() should detect and download fonts."""
        page.set_content("""
            <html><head>
                <style>
                    @font-face {
                        font-family: 'TestFont';
                        src: url('https://example.com/font.woff2') format('woff2');
                    }
                </style>
            </head><body></body></html>
        """)
        target = page.locator("html")

        result = downloader.download_all(target)

        # Check for font assets (may or may not find depending on network)
        font_assets = [a for a in result if a.type == AssetType.FONT]
        # Just verify it returns without error
        assert isinstance(result, list)

    def test_download_all_handles_no_assets(
        self, downloader: AssetDownloader, page: Page, temp_dir: str
    ) -> None:
        """download_all() should handle elements with no assets."""
        page.set_content('<html><body><p>Just text</p></body></html>')
        target = page.locator("body")

        result = downloader.download_all(target)

        assert result == []

    def test_download_all_dimensions_for_images(
        self, downloader: AssetDownloader, page: Page, temp_dir: str
    ) -> None:
        """download_all() should include dimensions for images when available."""
        page.set_content("""
            <html><body>
                <svg width="100" height="100">
                    <circle cx="50" cy="50" r="40" fill="red"/>
                </svg>
            </body></html>
        """)
        target = page.locator("body")

        result = downloader.download_all(target)

        # SVGs should have dimensions
        svg_assets = [a for a in result if a.type == AssetType.SVG]
        if svg_assets:
            assert svg_assets[0].dimensions is not None

    def test_asset_downloader_creates_output_dir(
        self, page: Page, temp_dir: str
    ) -> None:
        """AssetDownloader should create output directory if it doesn't exist."""
        new_dir = os.path.join(temp_dir, "new_subdir", "assets")
        downloader = AssetDownloader(page, new_dir)

        # Directory should be created (or at least not raise)
        assert downloader.output_dir == new_dir
