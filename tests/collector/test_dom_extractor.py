"""Tests for DOMExtractor shadow DOM serialization."""

import pytest
from playwright.async_api import Page

from collector.dom_extractor import DOMExtractor

pytestmark = pytest.mark.asyncio


async def test_extract_includes_open_shadow_root(page: Page) -> None:
    """DOM extraction should serialize open shadow subtrees under the host element."""
    await page.set_content(
        """
        <html>
          <body>
            <div id="target">
              <x-card id="host"></x-card>
            </div>
            <script>
              const host = document.querySelector('#host');
              const root = host.attachShadow({ mode: 'open' });
              root.innerHTML = `
                <section class="shadow-shell">
                  <button id="shadow-cta">Open Shadow CTA</button>
                </section>
              `;
            </script>
          </body>
        </html>
        """
    )

    result = await DOMExtractor(page).extract(page.locator("#target"))
    host_node = result["dom_tree"]["children"][0]
    shadow_root = host_node["shadow_root"]

    assert shadow_root is not None
    assert shadow_root["tag"] == "#shadow-root"
    assert shadow_root["children"][0]["tag"] == "section"
    assert shadow_root["children"][0]["children"][0]["attributes"]["id"] == "shadow-cta"
