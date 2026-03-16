"""Download images, SVGs, fonts, videos, and CSS URL-based assets."""

import os
import re
import urllib.parse
from typing import Any

from playwright.async_api import Locator, Page

from collector.extraction_scope import ExtractionScope
from models.extraction import Asset, AssetType


class AssetDownloader:
    """Download rendered assets that belong to the target subtree."""

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
        os.makedirs(output_dir, exist_ok=True)

    async def download_all(self, target: Locator) -> list[Asset]:
        """Download all assets (HTML, CSS, SVG, fonts, video) within the target."""
        self.last_limitations = []
        assets: list[Asset] = []
        seen_urls: set[str] = set()

        assets.extend(await self._download_images(target, seen_urls))
        assets.extend(await self._download_svgs(target, seen_urls))
        assets.extend(await self._download_css_background_assets(target, seen_urls))
        assets.extend(await self._download_videos(target, seen_urls))
        assets.extend(await self._download_fonts(seen_urls))

        return assets

    async def _download_images(
        self,
        target: Locator,
        seen_urls: set[str],
    ) -> list[Asset]:
        """Download image elements within target."""
        assets: list[Asset] = []

        try:
            images = target.locator("img")
            for index in range(await images.count()):
                try:
                    image = images.nth(index)
                    src = await self._get_image_source(image)
                    if not src:
                        continue

                    asset_key = self._build_asset_key(src)
                    if asset_key in seen_urls:
                        continue

                    seen_urls.add(asset_key)
                    asset = await self._download_image_asset(image, src)
                    if asset:
                        assets.append(asset)
                except Exception:
                    continue
        except Exception:
            pass

        return assets

    async def _get_image_source(self, img: Locator) -> str | None:
        """Return the best available source for an image element."""
        source_attributes = [
            "src",
            "data-src",
            "data-lazy-src",
            "data-original",
            "data-url",
        ]

        for attribute in source_attributes:
            try:
                value = await img.get_attribute(attribute)
            except Exception:
                value = None

            if value:
                return value

        return None

    async def _download_image_asset(self, img: Locator, src: str) -> Asset | None:
        """Download a single image asset."""
        try:
            dimensions = await img.evaluate(
                """el => [el.naturalWidth || el.width, el.naturalHeight || el.height]"""
            )
            local_path, file_size, _mime_type = await self._download_file(
                self._resolve_url(src),
                "images",
            )
            if not local_path:
                return None

            return Asset(
                type=AssetType.IMAGE,
                original_url=src,
                local_path=local_path,
                file_size_bytes=file_size,
                dimensions=dimensions if dimensions[0] > 0 else None,
            )
        except Exception:
            return None

    async def _download_svgs(
        self,
        target: Locator,
        seen_urls: set[str],
    ) -> list[Asset]:
        """Download inline SVGs and external SVG images within target."""
        assets: list[Asset] = []
        assets.extend(await self._download_inline_svgs(target))
        assets.extend(await self._download_external_svgs(target, seen_urls))
        return assets

    async def _download_inline_svgs(self, target: Locator) -> list[Asset]:
        """Download inline SVG elements within target."""
        assets: list[Asset] = []

        try:
            svgs = target.locator("svg")
            for index in range(await svgs.count()):
                try:
                    svg = svgs.nth(index)
                    svg_content = await svg.evaluate("el => el.outerHTML")
                    local_path = self._save_svg_content(svg_content, f"inline_svg_{index}")
                    if not local_path:
                        continue

                    dimensions = await svg.evaluate(
                        """el => {
                            const bbox = el.getBBox ? el.getBBox() : null;
                            return [
                                el.clientWidth || bbox?.width || 0,
                                el.clientHeight || bbox?.height || 0
                            ];
                        }"""
                    )

                    assets.append(
                        Asset(
                            type=AssetType.SVG,
                            original_url=f"inline:inline_svg_{index}",
                            local_path=local_path,
                            file_size_bytes=len(svg_content.encode("utf-8")),
                            dimensions=dimensions if dimensions[0] > 0 else None,
                        )
                    )
                except Exception:
                    continue
        except Exception:
            pass

        return assets

    async def _download_external_svgs(
        self,
        target: Locator,
        seen_urls: set[str],
    ) -> list[Asset]:
        """Download SVG files referenced by img tags."""
        assets: list[Asset] = []

        try:
            svg_images = target.locator('img[src$=".svg"], img[src*=".svg"]')
            for index in range(await svg_images.count()):
                try:
                    image = svg_images.nth(index)
                    src = await image.get_attribute("src")
                    if not src:
                        continue

                    asset_key = self._build_asset_key(src)
                    if asset_key in seen_urls:
                        continue

                    seen_urls.add(asset_key)
                    asset = await self._download_svg_asset(image, src)
                    if asset:
                        assets.append(asset)
                except Exception:
                    continue
        except Exception:
            pass

        return assets

    async def _download_svg_asset(self, svg_img: Locator, src: str) -> Asset | None:
        """Download an external SVG file."""
        try:
            dimensions = await svg_img.evaluate(
                """el => [el.width || el.clientWidth, el.height || el.clientHeight]"""
            )
            local_path, file_size, _mime_type = await self._download_file(
                self._resolve_url(src),
                "svgs",
            )
            if not local_path:
                return None

            return Asset(
                type=AssetType.SVG,
                original_url=src,
                local_path=local_path,
                file_size_bytes=file_size,
                dimensions=dimensions if dimensions[0] > 0 else None,
            )
        except Exception:
            return None

    async def _download_css_background_assets(
        self,
        target: Locator,
        seen_urls: set[str],
    ) -> list[Asset]:
        """Download background images referenced by computed CSS styles."""
        assets: list[Asset] = []

        try:
            candidates = await self._extract_css_asset_candidates(target)
        except Exception:
            return assets

        for candidate in candidates:
            original_url = candidate.get("original_url")
            resolved_url = candidate.get("resolved_url")
            if not original_url or not resolved_url:
                continue

            asset_key = self._build_asset_key(resolved_url)
            if asset_key in seen_urls:
                continue

            seen_urls.add(asset_key)
            asset = await self._download_css_background_asset(candidate)
            if asset:
                assets.append(asset)

        return assets

    async def _extract_css_asset_candidates(self, target: Locator) -> list[dict]:
        """Extract CSS URL-based asset candidates from the target subtree."""
        return await target.evaluate(
            """root => {
                const candidates = [];
                const seen = new Set();
                const urlPattern = /url\\((['"]?)(.*?)\\1\\)/g;

                function collectUrls(value) {
                    if (!value || value === 'none') {
                        return [];
                    }

                    const urls = [];
                    for (const match of value.matchAll(urlPattern)) {
                        const url = match[2]?.trim();
                        if (url) {
                            urls.push(url);
                        }
                    }
                    return urls;
                }

                function resolveUrl(url) {
                    if (!url) {
                        return null;
                    }
                    if (url.startsWith('data:')) {
                        return url;
                    }
                    if (url.startsWith('blob:')) {
                        return null;
                    }
                    try {
                        return new URL(url, document.baseURI).href;
                    } catch (e) {
                        return url;
                    }
                }

                function classifyAsset(url) {
                    const normalized = url.toLowerCase();
                    if (
                        normalized.startsWith('data:image/svg+xml') ||
                        normalized.includes('.svg')
                    ) {
                        return 'svg';
                    }
                    return 'image';
                }

                function pushCandidate(value, source) {
                    for (const url of collectUrls(value)) {
                        const resolved = resolveUrl(url);
                        if (!resolved || seen.has(resolved)) {
                            continue;
                        }

                        seen.add(resolved);
                        candidates.push({
                            original_url: url,
                            resolved_url: resolved,
                            asset_type: classifyAsset(url),
                            source,
                        });
                    }
                }

                const elements = [root, ...root.querySelectorAll('*')];
                for (const element of elements) {
                    const styles = window.getComputedStyle(element);
                    pushCandidate(styles.backgroundImage, 'background-image');
                    if (styles.backgroundImage === 'none') {
                        pushCandidate(styles.background, 'background');
                    }
                    pushCandidate(styles.maskImage, 'mask-image');
                    pushCandidate(
                        styles.getPropertyValue('-webkit-mask-image'),
                        '-webkit-mask-image'
                    );
                    pushCandidate(styles.borderImageSource, 'border-image-source');
                    pushCandidate(styles.content, 'content');

                    for (const pseudo of ['::before', '::after']) {
                        const pseudoStyles = window.getComputedStyle(element, pseudo);
                        pushCandidate(pseudoStyles.backgroundImage, pseudo);
                        if (pseudoStyles.backgroundImage === 'none') {
                            pushCandidate(pseudoStyles.background, `${pseudo}:background`);
                        }
                        pushCandidate(pseudoStyles.maskImage, `${pseudo}:mask-image`);
                        pushCandidate(
                            pseudoStyles.getPropertyValue('-webkit-mask-image'),
                            `${pseudo}:-webkit-mask-image`
                        );
                        pushCandidate(
                            pseudoStyles.borderImageSource,
                            `${pseudo}:border-image-source`
                        );
                        pushCandidate(pseudoStyles.content, `${pseudo}:content`);
                    }
                }

                return candidates;
            }"""
        )

    async def _download_css_background_asset(self, candidate: dict) -> Asset | None:
        """Download a single CSS background asset."""
        try:
            original_url = candidate["original_url"]
            resolved_url = candidate["resolved_url"]
            asset_type_hint = candidate.get("asset_type", "image")
            subfolder = "svgs" if asset_type_hint == "svg" else "images"

            local_path, file_size, mime_type = await self._download_file(
                resolved_url,
                subfolder,
            )
            if not local_path:
                return None

            asset_type = self._classify_downloaded_asset_type(
                original_url=original_url,
                resolved_url=resolved_url,
                mime_type=mime_type,
                fallback=asset_type_hint,
            )
            return Asset(
                type=asset_type,
                original_url=original_url,
                local_path=local_path,
                file_size_bytes=file_size,
            )
        except Exception:
            return None

    async def _download_fonts(self, seen_urls: set[str]) -> list[Asset]:
        """Download font files referenced in accessible stylesheets."""
        assets: list[Asset] = []
        evaluate_context: Any = self.scope.frame if self.scope is not None else self.page

        try:
            font_urls = await evaluate_context.evaluate(
                """() => {
                    const fonts = [];
                    const sheets = document.styleSheets;

                    try {
                        for (const sheet of sheets) {
                            try {
                                for (const rule of sheet.cssRules) {
                                    if (rule instanceof CSSFontFaceRule) {
                                        const src = rule.style.getPropertyValue('src');
                                        if (!src) {
                                            continue;
                                        }

                                        const match = src.match(/url\\(['"]?([^'")]+)['"]?\\)/);
                                        if (match) {
                                            fonts.push({
                                                family: rule.style.getPropertyValue('font-family'),
                                                url: match[1],
                                            });
                                        }
                                    }
                                }
                            } catch (e) {
                                continue;
                            }
                        }
                    } catch (e) {
                        return fonts;
                    }

                    return fonts;
                }"""
            )

            for font_info in font_urls:
                url = font_info.get("url")
                if not url:
                    continue

                asset_key = self._build_asset_key(url)
                if asset_key in seen_urls:
                    continue

                seen_urls.add(asset_key)
                try:
                    local_path, file_size, _mime_type = await self._download_file(
                        self._resolve_url(url),
                        "fonts",
                    )
                    if local_path:
                        assets.append(
                            Asset(
                                type=AssetType.FONT,
                                original_url=url,
                                local_path=local_path,
                                file_size_bytes=file_size,
                            )
                        )
                except Exception:
                    continue
        except Exception:
            if self.scope is not None:
                self.last_limitations.append(
                    "Could not extract @font-face rules from the target frame stylesheets."
                )
            pass

        return assets

    async def _download_videos(
        self,
        target: Locator,
        seen_urls: set[str],
    ) -> list[Asset]:
        """Download direct video sources referenced by video and source elements."""
        assets: list[Asset] = []

        try:
            videos = target.locator("video")
            for index in range(await videos.count()):
                video = videos.nth(index)
                source_urls = await video.evaluate(
                    """el => {
                        const urls = new Set();
                        if (el.getAttribute('src')) {
                            urls.add(el.getAttribute('src'));
                        }
                        if (el.currentSrc) {
                            urls.add(el.currentSrc);
                        }

                        for (const source of el.querySelectorAll('source[src]')) {
                            urls.add(source.getAttribute('src') || source.src);
                        }

                        return Array.from(urls).filter(Boolean);
                    }"""
                )

                for source_url in source_urls:
                    asset_key = self._build_asset_key(source_url)
                    if asset_key in seen_urls:
                        continue

                    seen_urls.add(asset_key)
                    asset = await self._download_video_asset(video, source_url, index)
                    if asset:
                        assets.append(asset)
        except Exception:
            pass

        return assets

    async def _download_video_asset(
        self,
        video: Locator,
        src: str,
        index: int,
    ) -> Asset | None:
        """Download a single video source."""
        try:
            dimensions = await video.evaluate(
                """el => [el.videoWidth || el.clientWidth || 0, el.videoHeight || el.clientHeight || 0]"""
            )
            local_path, file_size, _mime_type = await self._download_file(
                self._resolve_url(src),
                "videos",
            )
            if not local_path:
                return None

            return Asset(
                type=AssetType.VIDEO,
                original_url=src,
                local_path=local_path,
                file_size_bytes=file_size,
                dimensions=dimensions if dimensions[0] > 0 else None,
            )
        except Exception:
            return None

    def _resolve_url(self, url: str) -> str:
        """Resolve a relative URL to an absolute URL."""
        if self.scope is not None:
            return self.scope.resolve_url(url)

        if url.startswith("data:"):
            return url
        if url.startswith("//"):
            return f"https:{url}"
        if url.startswith(("http://", "https://", "blob:")):
            return url

        return urllib.parse.urljoin(self.page.url, url)

    async def _download_file(
        self,
        url: str,
        subfolder: str,
    ) -> tuple[str | None, int, str | None]:
        """Download a file into the output directory."""
        if url.startswith("data:"):
            return self._save_data_url(url, subfolder)

        try:
            output_subdir = os.path.join(self.output_dir, subfolder)
            os.makedirs(output_subdir, exist_ok=True)

            filename = self._generate_filename(url)
            local_path = os.path.join(output_subdir, filename)

            response = await self.page.context.request.get(url)
            if not response.ok:
                return None, 0, None

            body = await response.body()
            with open(local_path, "wb") as handle:
                handle.write(body)

            return local_path, len(body), response.headers.get("content-type")
        except Exception:
            return None, 0, None

    def _save_data_url(
        self,
        url: str,
        subfolder: str,
    ) -> tuple[str | None, int, str | None]:
        """Save a data URL to a file."""
        try:
            header, _, payload = url.partition(",")
            if not header.startswith("data:") or not payload:
                return None, 0, None

            mime_type = header[5:] or "text/plain"
            is_base64 = False
            if ";base64" in mime_type:
                mime_type = mime_type.replace(";base64", "")
                is_base64 = True

            import base64

            if is_base64:
                body = base64.b64decode(payload)
            else:
                body = urllib.parse.unquote_to_bytes(payload)

            output_subdir = os.path.join(self.output_dir, subfolder)
            os.makedirs(output_subdir, exist_ok=True)

            ext = self._mime_to_extension(mime_type)
            filename = f"data_{self._short_hash(url)}{ext}"
            local_path = os.path.join(output_subdir, filename)

            with open(local_path, "wb") as handle:
                handle.write(body)

            return local_path, len(body), mime_type
        except Exception:
            return None, 0, None

    def _save_svg_content(self, content: str, identifier: str) -> str | None:
        """Save inline SVG content to disk."""
        try:
            output_subdir = os.path.join(self.output_dir, "svgs")
            os.makedirs(output_subdir, exist_ok=True)

            filename = f"{identifier}_{self._short_hash(content)}.svg"
            local_path = os.path.join(output_subdir, filename)

            with open(local_path, "w", encoding="utf-8") as handle:
                handle.write(content)

            return local_path
        except Exception:
            return None

    def _generate_filename(self, url: str) -> str:
        """Generate a safe filename from a URL."""
        parsed = urllib.parse.urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename:
            filename = f"asset_{self._short_hash(url)}"

        return re.sub(r'[<>:"/\\\\|?*]', "_", filename)

    def _mime_to_extension(self, mime_type: str) -> str:
        """Convert MIME type to file extension."""
        mime_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/gif": ".gif",
            "image/svg+xml": ".svg",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
            "video/webm": ".webm",
            "video/ogg": ".ogv",
            "font/woff": ".woff",
            "font/woff2": ".woff2",
            "font/ttf": ".ttf",
            "font/otf": ".otf",
            "application/font-woff": ".woff",
            "application/font-woff2": ".woff2",
            "application/x-font-ttf": ".ttf",
            "application/x-font-otf": ".otf",
            "text/plain": ".txt",
        }
        return mime_map.get(mime_type, "")

    def _build_asset_key(self, url: str) -> str:
        """Build a deduplication key for any asset URL."""
        if url.startswith("data:"):
            return url
        return self._resolve_url(url)

    def _classify_downloaded_asset_type(
        self,
        original_url: str,
        resolved_url: str,
        mime_type: str | None,
        fallback: str,
    ) -> AssetType:
        """Classify a CSS asset as image or SVG."""
        normalized_mime = (mime_type or "").split(";")[0].strip().lower()
        if normalized_mime == "image/svg+xml":
            return AssetType.SVG

        if (
            original_url.startswith("data:image/svg+xml")
            or resolved_url.lower().endswith(".svg")
            or ".svg" in original_url.lower()
        ):
            return AssetType.SVG

        return AssetType.SVG if fallback == "svg" else AssetType.IMAGE

    def _short_hash(self, value: str) -> str:
        """Create a short stable hash for generated filenames."""
        import hashlib

        return hashlib.md5(value.encode()).hexdigest()[:8]
