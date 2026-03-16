"""Tests for ScrollProbeCollector."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from playwright.async_api import Page

from collector.extraction_scope import ExtractionScope
from collector.scroll_probe_collector import ScrollProbeCollector
from models.extraction import ExtractionMode

pytestmark = pytest.mark.asyncio


async def test_collect_component_scroll_probe_with_overlay_canvas(
    page: Page,
    tmp_path: Path,
) -> None:
    """Component probe should capture scroll-driven changes plus overlay media."""
    await page.set_viewport_size({"width": 1280, "height": 720})
    await page.set_content(
        """
        <html>
          <body style="height: 2600px; margin: 0;">
            <section
              id="target"
              style="margin-top: 900px; height: 700px; position: relative; background: #f3f3f3;"
            >
              <img
                class="probe-img webgl-img opacity-0"
                src="https://example.com/image.webp"
                alt="Probe"
                style="display:block; width: 100%; height: 100%; object-fit: cover; opacity: 0;"
              />
            </section>
            <canvas
              id="overlay"
              width="1280"
              height="720"
              style="position: fixed; inset: 0; width: 100vw; height: 100vh; pointer-events: none;"
            ></canvas>
            <script>
              const overlay = document.querySelector('#overlay');
              const ctx = overlay.getContext('2d');
              const target = document.querySelector('#target');
              const probeImg = document.querySelector('.probe-img');

              function render() {
                const rect = target.getBoundingClientRect();
                const progress = Math.max(0, Math.min(1, (window.innerHeight - rect.top) / (window.innerHeight + rect.height)));
                probeImg.style.transform = `translateY(${Math.round(progress * 32)}px)`;
                probeImg.style.opacity = String(progress.toFixed(2));
                ctx.clearRect(0, 0, overlay.width, overlay.height);
                ctx.fillStyle = `rgba(30, 60, 120, ${Math.max(progress, 0.1)})`;
                ctx.fillRect(0, 0, overlay.width, overlay.height);
              }

              window.addEventListener('scroll', render, { passive: true });
              render();
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
    overlay_media = [
        SimpleNamespace(document_level=True, selector="#overlay", linked_selectors=[".probe-img"])
    ]

    summary = await ScrollProbeCollector(page, str(tmp_path)).collect(
        page.locator("#target"),
        mode=ExtractionMode.COMPONENT,
        scope=scope,
        rich_media=overlay_media,
    )

    assert summary is not None
    assert summary["context"] == "page"
    assert summary["triggered"] is True
    assert summary["step_count"] >= 2
    assert "__target__" in summary["tracked_selectors"]
    assert "#overlay" in summary["overlay_selectors"]
    assert Path(summary["frames_dir"]).exists()
    assert summary["key_frames"]
    assert summary["observations"]
    assert any(change["selector"] == ".probe-img" for change in summary["state_changes"])
    if summary["video_path"] is not None:
        assert Path(summary["video_path"]).exists()


async def test_collect_full_page_scroll_probe(
    page: Page,
    tmp_path: Path,
) -> None:
    """Full-page probe should walk the document and emit frames."""
    await page.set_viewport_size({"width": 1280, "height": 720})
    await page.set_content(
        """
        <html>
          <body style="height: 3200px; margin: 0;">
            <section style="height: 900px; background: #111;"></section>
            <section id="target" style="height: 900px; background: #333;">
              <div class="reveal-block" style="margin-top: 120px; width: 200px; height: 200px; background: #fff;"></div>
            </section>
            <section style="height: 900px; background: #555;"></section>
            <script>
              const block = document.querySelector('.reveal-block');
              function render() {
                const progress = Math.max(0, Math.min(1, window.scrollY / 900));
                block.style.transform = `translateY(${Math.round(progress * 40)}px)`;
                block.style.opacity = String((0.4 + progress * 0.6).toFixed(2));
              }
              window.addEventListener('scroll', render, { passive: true });
              render();
            </script>
          </body>
        </html>
        """
    )

    summary = await ScrollProbeCollector(page, str(tmp_path)).collect(
        page.locator("body"),
        mode=ExtractionMode.FULL_PAGE,
        scope=None,
        rich_media=[],
    )

    assert summary is not None
    assert summary["context"] == "page"
    assert summary["step_count"] >= 2
    assert Path(summary["frames_dir"]).exists()
    assert summary["tracked_selectors"]
