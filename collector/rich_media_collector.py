"""Collect runtime media metadata and snapshots for video, canvas, and WebGL."""

import base64
from datetime import datetime
from pathlib import Path
import urllib.parse

from playwright.async_api import Locator, Page

from collector.extraction_scope import ExtractionScope
from models.extraction import BoundingBox, RichMediaType
from models.normalized import RichMediaCapture


class RichMediaCollector:
    """Capture rich media artifacts that do not fit plain DOM or asset scans."""

    def __init__(
        self,
        page: Page,
        output_dir: str,
        scope: ExtractionScope | None = None,
    ):
        self.page = page
        self.output_dir = output_dir
        self.scope = scope
        self.last_limitations: list[str] = []
        self.media_dir = Path(output_dir) / "rich_media"
        self.media_dir.mkdir(parents=True, exist_ok=True)

    async def collect(self, target: Locator) -> list[RichMediaCapture]:
        """Collect video, canvas, and WebGL metadata plus best-effort snapshots."""
        self.last_limitations = []
        captures: list[RichMediaCapture] = []
        captures.extend(await self._collect_videos(target))
        captures.extend(await self._collect_canvases(target))
        captures.extend(await self._collect_document_overlay_canvases(target))
        return captures

    async def _collect_videos(self, target: Locator) -> list[RichMediaCapture]:
        """Collect metadata and snapshots for video elements in the subtree."""
        captures: list[RichMediaCapture] = []

        try:
            videos = target.locator("video")
            for index in range(await videos.count()):
                video = videos.nth(index)
                metadata = await video.evaluate(self._video_metadata_script())
                if not metadata:
                    continue

                captures.append(
                    RichMediaCapture(
                        type=RichMediaType.VIDEO,
                        selector=metadata.get("selector", f"video:nth-of-type({index + 1})"),
                        bounding_box=self._build_bounding_box(
                            metadata.get("bounding_box", {})
                        ),
                        source_urls=self._resolve_source_urls(
                            metadata.get("source_urls", [])
                        ),
                        poster_url=self._resolve_url(metadata["poster_url"])
                        if metadata.get("poster_url")
                        else None,
                        snapshot_path=await self._capture_element_screenshot(
                            video,
                            "video",
                            index,
                        ),
                        playback_flags=metadata.get("playback_flags", {}),
                        limitations=[],
                    )
                )
        except Exception:
            self._add_limitation(
                "Could not inspect video elements within the extraction scope."
            )

        return captures

    async def _collect_canvases(self, target: Locator) -> list[RichMediaCapture]:
        """Collect metadata and snapshots for canvas and WebGL elements."""
        captures: list[RichMediaCapture] = []

        try:
            canvases = target.locator("canvas")
            for index in range(await canvases.count()):
                canvas = canvases.nth(index)
                metadata = await canvas.evaluate(self._canvas_metadata_script())
                if not metadata:
                    continue

                limitations = list(metadata.get("limitations", []))
                data_url = metadata.get("snapshot_data_url")
                snapshot_path = None

                if data_url:
                    snapshot_path = self._save_data_url(
                        data_url,
                        f"{metadata.get('type', 'canvas')}_{index}",
                    )
                else:
                    if limitations:
                        self._add_limitation(limitations[0])
                    snapshot_path = await self._capture_element_screenshot(
                        canvas,
                        metadata.get("type", "canvas"),
                        index,
                    )
                    if snapshot_path and limitations:
                        limitations.append(
                            "Used element screenshot fallback instead of direct canvas export."
                        )

                captures.append(
                    RichMediaCapture(
                        type=RichMediaType(metadata.get("type", "canvas")),
                        selector=metadata.get(
                            "selector",
                            f"canvas:nth-of-type({index + 1})",
                        ),
                        bounding_box=self._build_bounding_box(
                            metadata.get("bounding_box", {})
                        ),
                        source_urls=[],
                        poster_url=None,
                        snapshot_path=snapshot_path,
                        playback_flags={},
                        limitations=self._dedupe_limitations(limitations),
                    )
                )
        except Exception:
            self._add_limitation(
                "Could not inspect canvas or WebGL elements within the extraction scope."
            )

        return captures

    async def _collect_document_overlay_canvases(
        self,
        target: Locator,
    ) -> list[RichMediaCapture]:
        """Collect document-level overlay canvases that visually affect the target."""
        if self.scope is None:
            return []

        try:
            metadata_entries = await target.evaluate(self._document_overlay_media_script())
        except Exception:
            self._add_limitation(
                "Could not inspect document-level overlay canvas elements related to the component."
            )
            return []

        captures: list[RichMediaCapture] = []
        for index, metadata in enumerate(metadata_entries):
            limitations = list(metadata.get("limitations", []))
            snapshot_path = None
            data_url = metadata.get("snapshot_data_url")

            if data_url:
                snapshot_path = self._save_data_url(
                    data_url,
                    f"document_{metadata.get('type', 'canvas')}_{index}",
                )

            if snapshot_path is None:
                if limitations:
                    self._add_limitation(limitations[0])
                snapshot_path = await self._capture_document_canvas_screenshot(
                    metadata.get("document_index", index),
                    metadata.get("type", "canvas"),
                    index,
                )
                if snapshot_path and limitations:
                    limitations.append(
                        "Used element screenshot fallback instead of direct canvas export."
                    )

            linked_selectors = metadata.get("linked_selectors", [])
            captures.append(
                RichMediaCapture(
                    type=RichMediaType(metadata.get("type", "canvas")),
                    selector=metadata.get(
                        "selector",
                        f"canvas.document-overlay:nth-of-type({index + 1})",
                    ),
                    bounding_box=self._build_bounding_box(
                        metadata.get("bounding_box", {})
                    ),
                    source_urls=[],
                    poster_url=None,
                    snapshot_path=snapshot_path,
                    playback_flags={},
                    document_level=True,
                    linked_selectors=linked_selectors,
                    effect_summary=self._build_effect_summary(metadata),
                    limitations=self._dedupe_limitations(limitations),
                )
            )

        return captures

    async def _capture_element_screenshot(
        self,
        element: Locator,
        media_type: str,
        index: int,
    ) -> str | None:
        """Capture a stable screenshot for a runtime media element."""
        path = self.media_dir / self._build_filename(media_type, index, "png")

        try:
            await element.screenshot(path=str(path), animations="disabled")
        except Exception:
            return None

        return str(path.resolve())

    async def _capture_document_canvas_screenshot(
        self,
        document_index: int,
        media_type: str,
        index: int,
    ) -> str | None:
        """Capture a screenshot for a document-level canvas overlay."""
        context = self.scope.frame if self.scope is not None else self.page
        canvas = context.locator("canvas").nth(document_index)
        return await self._capture_element_screenshot(canvas, media_type, index)

    def _save_data_url(self, data_url: str, stem: str) -> str | None:
        """Persist a data URL snapshot to the rich media output directory."""
        try:
            header, _, payload = data_url.partition(",")
            if not header.startswith("data:") or not payload:
                return None

            mime_type = header[5:]
            is_base64 = False
            if ";base64" in mime_type:
                mime_type = mime_type.replace(";base64", "")
                is_base64 = True

            body = (
                base64.b64decode(payload)
                if is_base64
                else urllib.parse.unquote_to_bytes(payload)
            )

            extension = ".png" if mime_type == "image/png" else ""
            path = self.media_dir / f"{stem}_{self._timestamp()}{extension}"
            path.write_bytes(body)
            return str(path.resolve())
        except Exception:
            return None

    def _build_bounding_box(self, raw_box: dict) -> BoundingBox:
        """Normalize raw media bounds into the shared model."""
        return BoundingBox(
            x=raw_box.get("x", 0),
            y=raw_box.get("y", 0),
            width=raw_box.get("width", 0),
            height=raw_box.get("height", 0),
        )

    def _build_effect_summary(self, metadata: dict) -> str | None:
        """Convert runtime media heuristics into a short, prompt-friendly summary."""
        linked_selectors = metadata.get("linked_selectors", [])
        selector_summary = (
            f" linked to {', '.join(f'`{selector}`' for selector in linked_selectors)}"
            if linked_selectors
            else ""
        )

        if metadata.get("uses_webgl_runtime"):
            summary = f"Document-level WebGL canvas{selector_summary}"
            if metadata.get("hides_source_images"):
                summary += " replaces hidden source images from the DOM"
            if metadata.get("uses_column_split_runtime"):
                summary += " by rendering them as split columns"
            if metadata.get("uses_scroll_runtime"):
                summary += " and offsets those columns based on viewport scroll velocity"
            return summary

        if metadata.get("uses_scroll_runtime") and linked_selectors:
            return (
                "Document-level canvas overlay appears scroll-linked and references "
                f"{', '.join(f'`{selector}`' for selector in linked_selectors)}."
            )

        return None

    def _resolve_url(self, url: str) -> str:
        """Resolve a relative media URL within the active extraction scope."""
        if self.scope is not None:
            return self.scope.resolve_url(url)

        if url.startswith("data:"):
            return url
        if url.startswith("//"):
            return f"https:{url}"
        if url.startswith(("http://", "https://", "blob:")):
            return url
        return urllib.parse.urljoin(self.page.url, url)

    def _resolve_source_urls(self, urls: list[str]) -> list[str]:
        """Resolve and deduplicate ordered source URLs for a media element."""
        resolved_urls: list[str] = []
        for url in urls:
            if not url:
                continue
            resolved = self._resolve_url(url)
            if resolved not in resolved_urls:
                resolved_urls.append(resolved)
        return resolved_urls

    def _add_limitation(self, message: str) -> None:
        """Record a collection limitation once."""
        if message and message not in self.last_limitations:
            self.last_limitations.append(message)

    def _dedupe_limitations(self, limitations: list[str]) -> list[str]:
        """Remove duplicate media limitation messages while preserving order."""
        merged: list[str] = []
        for limitation in limitations:
            if limitation and limitation not in merged:
                merged.append(limitation)
        return merged

    def _build_filename(self, media_type: str, index: int, extension: str) -> str:
        """Build a deterministic filename for a captured media artifact."""
        return f"{media_type}_{index}_{self._timestamp()}.{extension}"

    def _timestamp(self) -> str:
        """Return a compact timestamp for artifact filenames."""
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _video_metadata_script(self) -> str:
        """Return the JS used to serialize a video element."""
        return """
            el => {
                function buildSelector(element) {
                    if (element.id) {
                        return '#' + element.id;
                    }

                    let selector = element.tagName.toLowerCase();
                    if (element.className && typeof element.className === 'string') {
                        const classes = element.className.trim().split(/\\s+/).filter(Boolean);
                        if (classes.length > 0) {
                            selector += '.' + classes.slice(0, 2).join('.');
                        }
                    }

                    return selector;
                }

                const rect = el.getBoundingClientRect();
                const sourceUrls = new Set();

                if (el.currentSrc) {
                    sourceUrls.add(el.currentSrc);
                }
                if (el.src) {
                    sourceUrls.add(el.getAttribute('src') || el.src);
                }

                for (const source of el.querySelectorAll('source[src]')) {
                    sourceUrls.add(source.getAttribute('src') || source.src);
                }

                return {
                    selector: buildSelector(el),
                    bounding_box: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                    },
                    source_urls: Array.from(sourceUrls),
                    poster_url: el.getAttribute('poster') || '',
                    playback_flags: {
                        autoplay: !!el.autoplay,
                        muted: !!el.muted,
                        loop: !!el.loop,
                        controls: !!el.controls,
                        playsinline: !!el.playsInline,
                    },
                };
            }
        """

    def _canvas_metadata_script(self) -> str:
        """Return the JS used to serialize a canvas or WebGL element."""
        return """
            el => {
                function buildSelector(element) {
                    if (element.id) {
                        return '#' + element.id;
                    }

                    let selector = element.tagName.toLowerCase();
                    if (element.className && typeof element.className === 'string') {
                        const classes = element.className.trim().split(/\\s+/).filter(Boolean);
                        if (classes.length > 0) {
                            selector += '.' + classes.slice(0, 2).join('.');
                        }
                    }

                    return selector;
                }

                const rect = el.getBoundingClientRect();
                const limitations = [];
                let snapshotDataUrl = null;
                let isWebgl = false;

                try {
                    isWebgl = !!(
                        el.getContext('webgl2') ||
                        el.getContext('webgl') ||
                        el.getContext('experimental-webgl')
                    );
                } catch (error) {
                    isWebgl = false;
                }

                try {
                    snapshotDataUrl = el.toDataURL('image/png');
                } catch (error) {
                    limitations.push(
                        'Could not export canvas pixels directly; the canvas may be tainted or GPU-backed.'
                    );
                }

                return {
                    type: isWebgl ? 'webgl' : 'canvas',
                    selector: buildSelector(el),
                    bounding_box: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                    },
                    snapshot_data_url: snapshotDataUrl,
                    limitations,
                };
            }
        """

    def _document_overlay_media_script(self) -> str:
        """Return the JS used to discover overlay canvases outside the target subtree."""
        return """
            target => {
                function buildSelector(element) {
                    if (element.id) {
                        return '#' + element.id;
                    }

                    let selector = element.tagName.toLowerCase();
                    if (element.className && typeof element.className === 'string') {
                        const classes = element.className.trim().split(/\\s+/).filter(Boolean);
                        if (classes.length > 0) {
                            selector += '.' + classes.slice(0, 2).join('.');
                        }
                    }

                    const parent = element.parentElement;
                    if (!parent) {
                        return selector;
                    }

                    const siblings = Array.from(parent.children).filter(
                        sibling => sibling.tagName === element.tagName
                    );
                    if (siblings.length > 1) {
                        selector += `:nth-of-type(${siblings.indexOf(element) + 1})`;
                    }
                    return selector;
                }

                function intersects(a, b) {
                    return !(
                        a.right <= b.left ||
                        a.left >= b.right ||
                        a.bottom <= b.top ||
                        a.top >= b.bottom
                    );
                }

                function canvasType(canvas) {
                    try {
                        if (
                            canvas.getContext('webgl2') ||
                            canvas.getContext('webgl') ||
                            canvas.getContext('experimental-webgl')
                        ) {
                            return 'webgl';
                        }
                    } catch (error) {
                        return 'canvas';
                    }
                    return 'canvas';
                }

                const targetRect = target.getBoundingClientRect();
                const targetClasses = new Set();
                [target, ...target.querySelectorAll('[class]')].forEach(node => {
                    if (!node.className || typeof node.className !== 'string') {
                        return;
                    }
                    node.className
                        .trim()
                        .split(/\\s+/)
                        .filter(Boolean)
                        .forEach(className => targetClasses.add(`.${className}`));
                });

                const inlineScriptText = Array.from(document.scripts)
                    .map(script => script.textContent || '')
                    .join('\\n');

                const referencedSelectors = Array.from(targetClasses).filter(
                    selector => inlineScriptText.includes(selector)
                );
                const preferredSelectors = referencedSelectors.filter(selector =>
                    /(webgl|parallax|reveal|scroll|canvas|mask|gl)/i.test(selector)
                );
                const linkedSelectors = (
                    preferredSelectors.length > 0 ? preferredSelectors : referencedSelectors
                ).slice(0, 8);

                const usesWebglRuntime = (
                    inlineScriptText.includes('THREE.') ||
                    inlineScriptText.includes('WebGLRenderer')
                );
                const usesScrollRuntime = (
                    inlineScriptText.includes('window.scrollY') ||
                    inlineScriptText.includes('ScrollTrigger')
                );
                const usesColumnSplitRuntime = (
                    inlineScriptText.includes('columnsCount') &&
                    inlineScriptText.includes('mesh.position.y')
                );
                const hidesSourceImages = !!target.querySelector(
                    'img.opacity-0, video.opacity-0, .webgl-img.opacity-0'
                );
                const targetHasWebglMarkers = !!target.querySelector('.webgl-measure, .webgl-img');

                return Array.from(document.querySelectorAll('canvas'))
                    .map((canvas, documentIndex) => {
                        const rect = canvas.getBoundingClientRect();
                        const style = getComputedStyle(canvas);
                        const visible = rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                        const insideTarget = target.contains(canvas);
                        const overlayLike = (
                            ['fixed', 'absolute', 'sticky'].includes(style.position) ||
                            style.pointerEvents === 'none'
                        );
                        const overlapsTarget = intersects(rect, {
                            left: targetRect.left,
                            top: targetRect.top,
                            right: targetRect.right,
                            bottom: targetRect.bottom,
                        });
                        const coversViewport = (
                            rect.width >= window.innerWidth * 0.6 &&
                            rect.height >= window.innerHeight * 0.6
                        );

                        const limitations = [];
                        let snapshotDataUrl = null;
                        try {
                            snapshotDataUrl = canvas.toDataURL('image/png');
                        } catch (error) {
                            limitations.push(
                                'Could not export canvas pixels directly; the canvas may be tainted or GPU-backed.'
                            );
                        }

                        return {
                            selector: buildSelector(canvas),
                            document_index: documentIndex,
                            type: canvasType(canvas),
                            bounding_box: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                            },
                            linked_selectors: linkedSelectors,
                            uses_webgl_runtime: usesWebglRuntime,
                            uses_scroll_runtime: usesScrollRuntime,
                            uses_column_split_runtime: usesColumnSplitRuntime,
                            hides_source_images: hidesSourceImages,
                            snapshot_data_url: snapshotDataUrl,
                            limitations,
                            visible,
                            inside_target: insideTarget,
                            overlay_like: overlayLike,
                            overlaps_target: overlapsTarget,
                            covers_viewport: coversViewport,
                            is_candidate: (
                                visible &&
                                !insideTarget &&
                                overlayLike &&
                                (overlapsTarget || coversViewport) &&
                                (linkedSelectors.length > 0 || targetHasWebglMarkers) &&
                                (usesWebglRuntime || usesScrollRuntime)
                            ),
                        };
                    })
                    .filter(entry => entry.is_candidate);
            }
        """
