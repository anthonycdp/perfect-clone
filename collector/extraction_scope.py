"""Shared frame-aware extraction context for a located target."""

from dataclasses import dataclass, field
import urllib.parse

from playwright.async_api import Frame, Locator, Page


@dataclass(slots=True)
class ExtractionScope:
    """Bind the target locator to the frame and document metadata it came from."""

    page: Page
    frame: Frame
    target: Locator
    selector_used: str
    strategy: str
    frame_url: str
    frame_name: str | None
    same_origin_accessible: bool
    document_base_url: str
    within_shadow_dom: bool = False
    frame_limitations: list[str] = field(default_factory=list)

    def add_limitation(self, message: str) -> None:
        """Record a frame-specific limitation once."""
        if message and message not in self.frame_limitations:
            self.frame_limitations.append(message)

    def resolve_url(self, url: str) -> str:
        """Resolve a relative URL using the target frame document base."""
        if url.startswith("data:"):
            return url
        if url.startswith("//"):
            return f"https:{url}"
        if url.startswith(("http://", "https://", "blob:")):
            return url

        base_url = self.document_base_url or self.frame_url or self.page.url
        return urllib.parse.urljoin(base_url, url)
