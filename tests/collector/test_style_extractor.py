"""Tests for StyleExtractor frame-aware behavior."""

import pytest
from playwright.async_api import Page

from collector.extraction_scope import ExtractionScope
from collector.style_extractor import StyleExtractor

pytestmark = pytest.mark.asyncio


async def test_extract_reads_keyframes_from_target_frame(page: Page) -> None:
    """Style extraction should inspect the target frame stylesheets when present."""
    await page.set_content(
        """
        <html>
          <body>
            <iframe
              srcdoc="
                <style>
                  @keyframes pulse {
                    0% { opacity: 0; }
                    100% { opacity: 1; }
                  }

                  #target {
                    animation: pulse 1s ease-in-out infinite;
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
        document_base_url=await target.evaluate("el => document.baseURI"),
    )

    result = await StyleExtractor(page).extract(target, scope=scope)

    assert "pulse" in result["keyframes"]
    assert result["limitations"] == []
