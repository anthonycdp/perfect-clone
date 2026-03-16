"""Tests for runtime media collection."""

from pathlib import Path

import pytest
from playwright.sync_api import Page

from collector.rich_media_collector import RichMediaCollector
from models.extraction import RichMediaType


class TestRichMediaCollector:
    """Test suite for RichMediaCollector."""

    def test_collect_video_metadata_and_snapshot(
        self,
        page: Page,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Video capture should keep sources, poster, flags, and a snapshot path."""
        page.set_content(
            """
            <html><body>
                <video
                    id="demo-video"
                    src="/media/demo.mp4"
                    poster="/media/poster.png"
                    autoplay
                    muted
                    controls
                ></video>
            </body></html>
            """
        )

        collector = RichMediaCollector(page, str(tmp_path))
        monkeypatch.setattr(
            collector,
            "_capture_element_screenshot",
            lambda _element, _media_type, _index: str(tmp_path / "video.png"),
        )

        captures = collector.collect(page.locator("body"))

        assert len(captures) == 1
        assert captures[0].type == RichMediaType.VIDEO
        assert captures[0].selector == "#demo-video"
        assert captures[0].poster_url == "https://example.com/media/poster.png"
        assert captures[0].source_urls == ["https://example.com/media/demo.mp4"]
        assert captures[0].playback_flags["autoplay"] is True
        assert captures[0].snapshot_path == str(tmp_path / "video.png")

    def test_collect_canvas_exports_png_snapshot(
        self,
        page: Page,
        tmp_path: Path,
    ) -> None:
        """Canvas capture should prefer direct PNG export when available."""
        page.set_content(
            """
            <html>
              <body>
                <canvas id="chart" width="20" height="20"></canvas>
                <script>
                  const ctx = document.querySelector('#chart').getContext('2d');
                  ctx.fillStyle = '#ff0000';
                  ctx.fillRect(0, 0, 20, 20);
                </script>
              </body>
            </html>
            """
        )

        collector = RichMediaCollector(page, str(tmp_path))
        captures = collector.collect(page.locator("body"))

        assert len(captures) == 1
        assert captures[0].type == RichMediaType.CANVAS
        assert captures[0].snapshot_path is not None
        assert Path(captures[0].snapshot_path).exists()
        assert captures[0].limitations == []

    def test_collect_canvas_falls_back_to_element_screenshot(
        self,
        page: Page,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Canvas capture should fall back to a screenshot when export is blocked."""
        page.set_content(
            """
            <html>
              <body>
                <canvas id="chart" width="20" height="20"></canvas>
                <script>
                  HTMLCanvasElement.prototype.toDataURL = function() {
                    throw new Error('tainted');
                  };
                </script>
              </body>
            </html>
            """
        )

        collector = RichMediaCollector(page, str(tmp_path))
        fallback_path = str(tmp_path / "fallback.png")
        monkeypatch.setattr(
            collector,
            "_capture_element_screenshot",
            lambda _element, _media_type, _index: fallback_path,
        )

        captures = collector.collect(page.locator("body"))

        assert len(captures) == 1
        assert captures[0].snapshot_path == fallback_path
        assert any("fallback" in limitation.lower() for limitation in captures[0].limitations)
        assert collector.last_limitations

    def test_collect_webgl_canvas_marks_webgl_type(
        self,
        page: Page,
        tmp_path: Path,
    ) -> None:
        """Canvas metadata should classify WebGL contexts separately."""
        page.set_content(
            """
            <html>
              <body>
                <canvas id="scene" width="10" height="10"></canvas>
                <script>
                  const originalGetContext = HTMLCanvasElement.prototype.getContext;
                  HTMLCanvasElement.prototype.getContext = function(kind) {
                    if (kind === 'webgl' || kind === 'webgl2' || kind === 'experimental-webgl') {
                      return {};
                    }
                    return originalGetContext ? originalGetContext.call(this, kind) : null;
                  };
                </script>
              </body>
            </html>
            """
        )

        collector = RichMediaCollector(page, str(tmp_path))
        captures = collector.collect(page.locator("body"))

        assert len(captures) == 1
        assert captures[0].type == RichMediaType.WEBGL
