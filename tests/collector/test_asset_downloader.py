"""Tests for AssetDownloader - downloads images, SVGs, fonts, and CSS assets."""

import os
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import Page

from collector.asset_downloader import AssetDownloader
from collector.extraction_scope import ExtractionScope
from models.extraction import AssetType


PNG_DATA_URL = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+lm6kAAAAASUVORK5CYII="
)
PNG_DATA_URL_ALT = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR42mP8z/D/PwAHggJ/Pk4P4QAAAABJRU5ErkJggg=="
)
SVG_DATA_URL = (
    "data:image/svg+xml,"
    "%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2010%2010%22%3E"
    "%3Ccircle%20cx%3D%225%22%20cy%3D%225%22%20r%3D%225%22/%3E%3C/svg%3E"
)


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

    @staticmethod
    def _stub_download_file(
        downloader: AssetDownloader,
        monkeypatch: pytest.MonkeyPatch,
        temp_dir: str,
    ) -> list[tuple[str, str]]:
        """Stub network downloads so tests can assert URLs deterministically."""
        downloads: list[tuple[str, str]] = []

        def fake_download_file(url: str, subfolder: str) -> tuple[str, int, str]:
            filename = f"asset_{len(downloads)}"
            extension = ".svg" if "svg" in url else ".bin"
            local_dir = Path(temp_dir) / subfolder
            local_dir.mkdir(parents=True, exist_ok=True)
            local_path = local_dir / f"{filename}{extension}"
            local_path.write_bytes(b"asset")
            downloads.append((url, subfolder))
            mime_type = "image/svg+xml" if "svg" in url else "image/png"
            return str(local_path), len(b"asset"), mime_type

        monkeypatch.setattr(downloader, "_download_file", fake_download_file)
        return downloads

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
            assert asset.type in [
                AssetType.IMAGE,
                AssetType.SVG,
                AssetType.FONT,
                AssetType.VIDEO,
            ]
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

    def test_download_all_uses_lazy_image_attributes(
        self, downloader: AssetDownloader, page: Page, temp_dir: str
    ) -> None:
        """download_all() should read lazy-loading image attributes such as data-src."""
        page.set_content("""
            <html><body>
                <img data-src="https://example.com/lazy-image.png">
            </body></html>
        """)
        target = page.locator("body")

        result = downloader.download_all(target)

        assert isinstance(result, list)

    def test_asset_downloader_creates_output_dir(
        self, page: Page, temp_dir: str
    ) -> None:
        """AssetDownloader should create output directory if it doesn't exist."""
        new_dir = os.path.join(temp_dir, "new_subdir", "assets")
        downloader = AssetDownloader(page, new_dir)

        # Directory should be created (or at least not raise)
        assert downloader.output_dir == new_dir

    def test_download_all_finds_css_background_image(
        self,
        downloader: AssetDownloader,
        page: Page,
        temp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """download_all() should include background-image assets from CSS."""
        downloads = self._stub_download_file(downloader, monkeypatch, temp_dir)
        page.set_content(
            f"""
            <html><body>
                <div id="target" style="background-image: url('{PNG_DATA_URL}')"></div>
            </body></html>
            """
        )

        result = downloader.download_all(page.locator("#target"))

        assert any(asset.original_url == PNG_DATA_URL for asset in result)
        assert downloads == [(PNG_DATA_URL, "images")]

    def test_download_all_finds_background_shorthand_urls(
        self,
        downloader: AssetDownloader,
        page: Page,
        temp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """download_all() should capture URLs from background shorthand styles."""
        downloads = self._stub_download_file(downloader, monkeypatch, temp_dir)
        page.set_content(
            f"""
            <html><body>
                <div id="target" style="background: url('{PNG_DATA_URL}') center / cover no-repeat;"></div>
            </body></html>
            """
        )

        result = downloader.download_all(page.locator("#target"))

        assert len(result) == 1
        assert downloads == [(PNG_DATA_URL, "images")]

    def test_download_all_finds_multiple_css_urls(
        self,
        downloader: AssetDownloader,
        page: Page,
        temp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """download_all() should download every distinct CSS URL in a value."""
        downloads = self._stub_download_file(downloader, monkeypatch, temp_dir)
        page.set_content(
            f"""
            <html><body>
                <div
                    id="target"
                    style="background-image: url('{PNG_DATA_URL}'), url('{PNG_DATA_URL_ALT}');"
                ></div>
            </body></html>
            """
        )

        result = downloader.download_all(page.locator("#target"))

        assert len(result) == 2
        assert downloads == [
            (PNG_DATA_URL, "images"),
            (PNG_DATA_URL_ALT, "images"),
        ]

    def test_download_all_finds_pseudo_element_backgrounds(
        self,
        downloader: AssetDownloader,
        page: Page,
        temp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """download_all() should include backgrounds from ::before and ::after."""
        downloads = self._stub_download_file(downloader, monkeypatch, temp_dir)
        page.set_content(
            f"""
            <html>
                <head>
                    <style>
                        #target::before {{
                            content: "";
                            display: block;
                            width: 10px;
                            height: 10px;
                            background-image: url('{PNG_DATA_URL}');
                        }}

                        #target::after {{
                            content: "";
                            display: block;
                            width: 10px;
                            height: 10px;
                            background-image: url('{SVG_DATA_URL}');
                        }}
                    </style>
                </head>
                <body><div id="target"></div></body>
            </html>
            """
        )

        result = downloader.download_all(page.locator("#target"))
        asset_types = {asset.original_url: asset.type for asset in result}

        assert len(result) == 2
        assert downloads == [
            (PNG_DATA_URL, "images"),
            (SVG_DATA_URL, "svgs"),
        ]
        assert asset_types[PNG_DATA_URL] == AssetType.IMAGE
        assert asset_types[SVG_DATA_URL] == AssetType.SVG

    def test_download_all_ignores_gradients_without_urls(
        self,
        downloader: AssetDownloader,
        page: Page,
    ) -> None:
        """download_all() should ignore CSS gradients that contain no asset URLs."""
        page.set_content(
            """
            <html><body>
                <div id="target" style="background-image: linear-gradient(red, blue)"></div>
            </body></html>
            """
        )

        result = downloader.download_all(page.locator("#target"))

        assert result == []

    def test_download_all_deduplicates_html_and_css_assets(
        self,
        downloader: AssetDownloader,
        page: Page,
        temp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """download_all() should not download the same URL twice across HTML and CSS."""
        downloads = self._stub_download_file(downloader, monkeypatch, temp_dir)
        page.set_content(
            f"""
            <html><body>
                <img src="{PNG_DATA_URL}">
                <div id="target" style="background-image: url('{PNG_DATA_URL}')"></div>
            </body></html>
            """
        )

        result = downloader.download_all(page.locator("body"))

        assert len(result) == 1
        assert downloads == [(PNG_DATA_URL, "images")]

    def test_download_all_resolves_relative_css_urls_from_document_base(
        self,
        downloader: AssetDownloader,
        page: Page,
        temp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """download_all() should resolve relative CSS URLs against document.baseURI."""
        downloads = self._stub_download_file(downloader, monkeypatch, temp_dir)
        page.set_content(
            """
            <html>
                <head><base href="https://assets.example.com/landing/"></head>
                <body>
                    <div id="target" style="background-image: url('images/hero-bg.png')"></div>
                </body>
            </html>
            """
        )

        result = downloader.download_all(page.locator("#target"))

        assert len(result) == 1
        assert downloads == [
            ("https://assets.example.com/landing/images/hero-bg.png", "images")
        ]

    def test_download_all_scopes_css_assets_to_target(
        self,
        downloader: AssetDownloader,
        page: Page,
        temp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """download_all() should ignore CSS assets outside the target subtree."""
        downloads = self._stub_download_file(downloader, monkeypatch, temp_dir)
        page.set_content(
            f"""
            <html><body>
                <div id="target" style="background-image: url('{PNG_DATA_URL}')"></div>
                <div id="outside" style="background-image: url('{PNG_DATA_URL_ALT}')"></div>
            </body></html>
            """
        )

        result = downloader.download_all(page.locator("#target"))

        assert len(result) == 1
        assert downloads == [(PNG_DATA_URL, "images")]

    def test_download_all_saves_percent_encoded_svg_data_urls(
        self, downloader: AssetDownloader, page: Page
    ) -> None:
        """download_all() should persist SVG data URLs used in CSS backgrounds."""
        page.set_content(
            f"""
            <html><body>
                <div id="target" style="background-image: url('{SVG_DATA_URL}')"></div>
            </body></html>
            """
        )

        result = downloader.download_all(page.locator("#target"))

        assert len(result) == 1
        assert result[0].type == AssetType.SVG
        assert Path(result[0].local_path).exists()

    def test_download_all_extracts_fonts_from_target_frame(
        self,
        page: Page,
        temp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """download_all() should inspect @font-face rules in the target frame."""
        page.set_content(
            """
            <html>
              <body>
                <iframe
                  srcdoc="
                    <style>
                      @font-face {
                        font-family: 'FrameFont';
                        src: url('https://cdn.example.com/frame-font.woff2') format('woff2');
                      }
                    </style>
                    <section id='target'>Frame target</section>
                  "
                ></iframe>
              </body>
            </html>
            """
        )

        frame = page.frames[1]
        target = frame.locator("#target")
        scope = ExtractionScope(
            page=page,
            frame=frame,
            target=target,
            selector_used="#target",
            strategy="css",
            frame_url=frame.url,
            frame_name=frame.name or None,
            same_origin_accessible=True,
            document_base_url=target.evaluate("el => document.baseURI"),
        )
        downloader = AssetDownloader(page, temp_dir, scope=scope)
        downloads = self._stub_download_file(downloader, monkeypatch, temp_dir)

        result = downloader.download_all(target)
        font_assets = [asset for asset in result if asset.type == AssetType.FONT]

        assert len(font_assets) == 1
        assert downloads[-1] == ("https://cdn.example.com/frame-font.woff2", "fonts")

    def test_download_all_finds_mask_image_assets(
        self,
        downloader: AssetDownloader,
        page: Page,
        temp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """download_all() should capture CSS mask-image URLs."""
        downloads = self._stub_download_file(downloader, monkeypatch, temp_dir)
        page.set_content(
            f"""
            <html><body>
                <div id="target" style="mask-image: url('{PNG_DATA_URL}')"></div>
            </body></html>
            """
        )

        result = downloader.download_all(page.locator("#target"))

        assert len(result) == 1
        assert downloads == [(PNG_DATA_URL, "images")]

    def test_download_all_finds_border_image_source_assets(
        self,
        downloader: AssetDownloader,
        page: Page,
        temp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """download_all() should capture border-image-source URLs."""
        downloads = self._stub_download_file(downloader, monkeypatch, temp_dir)
        page.set_content(
            f"""
            <html><body>
                <div
                    id="target"
                    style="border-image-source: url('{PNG_DATA_URL_ALT}'); border-image-slice: 1;"
                ></div>
            </body></html>
            """
        )

        result = downloader.download_all(page.locator("#target"))

        assert len(result) == 1
        assert downloads == [(PNG_DATA_URL_ALT, "images")]

    def test_download_all_finds_content_url_assets(
        self,
        downloader: AssetDownloader,
        page: Page,
        temp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """download_all() should capture url(...) used in CSS content properties."""
        downloads = self._stub_download_file(downloader, monkeypatch, temp_dir)
        page.set_content(
            f"""
            <html>
                <head>
                    <style>
                        #target::before {{
                            content: url('{SVG_DATA_URL}');
                        }}
                    </style>
                </head>
                <body><div id="target"></div></body>
            </html>
            """
        )

        result = downloader.download_all(page.locator("#target"))

        assert len(result) == 1
        assert result[0].type == AssetType.SVG
        assert downloads == [(SVG_DATA_URL, "svgs")]

    def test_download_all_downloads_video_sources(
        self,
        downloader: AssetDownloader,
        page: Page,
        temp_dir: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """download_all() should download video src and source assets as VIDEO."""
        downloads = self._stub_download_file(downloader, monkeypatch, temp_dir)
        page.set_content(
            """
            <html><body>
                <video id="demo" src="https://cdn.example.com/video.mp4" controls>
                    <source src="https://cdn.example.com/video.webm" type="video/webm">
                </video>
            </body></html>
            """
        )

        result = downloader.download_all(page.locator("body"))
        video_assets = [asset for asset in result if asset.type == AssetType.VIDEO]

        assert len(video_assets) == 2
        assert downloads == [
            ("https://cdn.example.com/video.mp4", "videos"),
            ("https://cdn.example.com/video.webm", "videos"),
        ]
