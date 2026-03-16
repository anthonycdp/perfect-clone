"""Tests for runtime media collection."""

from pathlib import Path

import pytest
from playwright.async_api import Page

from collector.extraction_scope import ExtractionScope
from collector.rich_media_collector import RichMediaCollector
from models.extraction import RichMediaType

pytestmark = pytest.mark.asyncio


class TestRichMediaCollector:
    """Test suite for RichMediaCollector."""

    async def test_collect_video_metadata_and_snapshot(
        self,
        page: Page,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        await page.set_content(
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
        async def fake_capture(_element, _media_type, _index):
            return str(tmp_path / "video.png")
        monkeypatch.setattr(
            collector,
            "_capture_element_screenshot",
            fake_capture,
        )

        captures = await collector.collect(page.locator("body"))

        assert len(captures) == 1
        assert captures[0].type == RichMediaType.VIDEO
        assert captures[0].selector == "#demo-video"
        assert captures[0].poster_url == "https://example.com/media/poster.png"
        assert captures[0].source_urls == ["https://example.com/media/demo.mp4"]
        assert captures[0].playback_flags["autoplay"] is True
        assert captures[0].snapshot_path == str(tmp_path / "video.png")

    async def test_collect_canvas_exports_png_snapshot(
        self,
        page: Page,
        tmp_path: Path,
    ) -> None:
        await page.set_content(
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

        captures = await RichMediaCollector(page, str(tmp_path)).collect(page.locator("body"))

        assert len(captures) == 1
        assert captures[0].type == RichMediaType.CANVAS
        assert captures[0].snapshot_path is not None
        assert Path(captures[0].snapshot_path).exists()
        assert captures[0].limitations == []

    async def test_collect_canvas_falls_back_to_element_screenshot(
        self,
        page: Page,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        await page.set_content(
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
        async def fake_capture(_element, _media_type, _index):
            return fallback_path
        monkeypatch.setattr(
            collector,
            "_capture_element_screenshot",
            fake_capture,
        )

        captures = await collector.collect(page.locator("body"))

        assert len(captures) == 1
        assert captures[0].snapshot_path == fallback_path
        assert any("fallback" in limitation.lower() for limitation in captures[0].limitations)
        assert collector.last_limitations

    async def test_collect_webgl_canvas_marks_webgl_type(
        self,
        page: Page,
        tmp_path: Path,
    ) -> None:
        await page.set_content(
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

        captures = await RichMediaCollector(page, str(tmp_path)).collect(page.locator("body"))

        assert len(captures) == 1
        assert captures[0].type == RichMediaType.WEBGL

    async def test_collect_document_overlay_canvas_linked_to_target_runtime(
        self,
        page: Page,
        tmp_path: Path,
    ) -> None:
        await page.set_content(
            """
            <html>
              <body>
                <section id="target">
                  <div class="webgl-measure">
                    <img class="webgl-img opacity-0" src="/image.webp" alt="Hero image" />
                  </div>
                </section>
                <canvas
                  id="overlay"
                  width="120"
                  height="120"
                  style="position: fixed; inset: 0; width: 100vw; height: 100vh; pointer-events: none;"
                ></canvas>
                <script>
                  HTMLCanvasElement.prototype.getContext = function(kind) {
                    if (kind === 'webgl' || kind === 'webgl2' || kind === 'experimental-webgl') {
                      return {};
                    }
                    return null;
                  };

                  const measures = document.querySelectorAll('.webgl-measure');
                  const images = document.querySelectorAll('.webgl-img');
                  const renderer = new THREE.WebGLRenderer({ canvas: document.querySelector('#overlay') });
                  function render() {
                    const scrollY = window.scrollY;
                    const columnsCount = 4;
                    images.forEach(mesh => {
                      mesh.position = mesh.position || {};
                      mesh.position.y = scrollY * 0.2;
                    });
                    requestAnimationFrame(render);
                  }
                </script>
              </body>
            </html>
            """
        )

        scope = ExtractionScope(
            page=page,
            frame=page.main_frame,
            target=page.locator("#target"),
            selector_used="#target",
            strategy="css",
            frame_url=page.url,
            frame_name=None,
            same_origin_accessible=True,
            document_base_url=page.url,
            within_shadow_dom=False,
        )

        collector = RichMediaCollector(page, str(tmp_path), scope=scope)
        captures = await collector.collect(page.locator("#target"))

        assert len(captures) == 1
        assert captures[0].type == RichMediaType.WEBGL
        assert captures[0].document_level is True
        assert captures[0].linked_selectors == [".webgl-measure", ".webgl-img"]
        assert captures[0].effect_summary is not None
        assert "scroll velocity" in captures[0].effect_summary
