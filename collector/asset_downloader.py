"""AssetDownloader - Downloads images, SVGs, and fonts from a page."""

import os
import re
import urllib.parse
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page

from models.extraction import Asset, AssetType


class AssetDownloader:
    """Downloads and saves assets (images, SVGs, fonts) from web pages."""

    def __init__(self, page: Page, output_dir: str):
        """Initialize AssetDownloader.

        Args:
            page: Playwright Page object to extract assets from.
            output_dir: Directory to save downloaded assets.
        """
        self.page = page
        self.output_dir = output_dir

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def download_all(self, target: Locator) -> list[Asset]:
        """Download all assets (images, SVGs, fonts) within the target.

        Args:
            target: Locator for the target element to scan for assets.

        Returns:
            List of Asset objects representing downloaded assets.
        """
        assets: list[Asset] = []
        seen_urls: set[str] = set()

        # Find and download images
        image_assets = self._download_images(target, seen_urls)
        assets.extend(image_assets)

        # Find and download SVGs (both inline and external)
        svg_assets = self._download_svgs(target, seen_urls)
        assets.extend(svg_assets)

        # Find and download fonts
        font_assets = self._download_fonts(target, seen_urls)
        assets.extend(font_assets)

        return assets

    def _download_images(
        self, target: Locator, seen_urls: set[str]
    ) -> list[Asset]:
        """Download image elements within target."""
        assets: list[Asset] = []

        try:
            images = target.locator("img")
            count = images.count()

            for i in range(count):
                try:
                    img = images.nth(i)
                    src = img.get_attribute("src")

                    if not src or src in seen_urls:
                        continue

                    seen_urls.add(src)

                    asset = self._download_image_asset(img, src)
                    if asset:
                        assets.append(asset)
                except Exception:
                    continue
        except Exception:
            pass

        return assets

    def _download_image_asset(
        self, img: Locator, src: str
    ) -> Asset | None:
        """Download a single image asset."""
        try:
            # Get image dimensions
            dimensions = img.evaluate("""el => {
                return [el.naturalWidth || el.width, el.naturalHeight || el.height];
            }""")

            # Resolve URL
            resolved_url = self._resolve_url(src)

            # Download the image
            local_path, file_size = self._download_file(resolved_url, "images")

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

    def _download_svgs(
        self, target: Locator, seen_urls: set[str]
    ) -> list[Asset]:
        """Download SVG elements within target."""
        assets: list[Asset] = []

        # Handle inline SVGs
        try:
            svgs = target.locator("svg")
            count = svgs.count()

            for i in range(count):
                try:
                    svg = svgs.nth(i)

                    # Get SVG content
                    svg_content = svg.evaluate("el => el.outerHTML")

                    # Generate a unique identifier
                    svg_id = f"inline_svg_{i}"
                    local_path = self._save_svg_content(svg_content, svg_id)

                    if local_path:
                        # Get dimensions
                        dimensions = svg.evaluate("""el => {
                            const bbox = el.getBBox ? el.getBBox() : null;
                            return [el.clientWidth || bbox?.width || 0, el.clientHeight || bbox?.height || 0];
                        }""")

                        file_size = len(svg_content.encode('utf-8'))

                        assets.append(Asset(
                            type=AssetType.SVG,
                            original_url=f"inline:{svg_id}",
                            local_path=local_path,
                            file_size_bytes=file_size,
                            dimensions=dimensions if dimensions[0] > 0 else None,
                        ))
                except Exception:
                    continue
        except Exception:
            pass

        # Handle external SVG files (img with .svg src)
        try:
            svg_images = target.locator('img[src$=".svg"], img[src*=".svg"]')
            count = svg_images.count()

            for i in range(count):
                try:
                    img = svg_images.nth(i)
                    src = img.get_attribute("src")

                    if not src or src in seen_urls:
                        continue

                    seen_urls.add(src)

                    asset = self._download_svg_asset(img, src)
                    if asset:
                        assets.append(asset)
                except Exception:
                    continue
        except Exception:
            pass

        return assets

    def _download_svg_asset(
        self, svg_img: Locator, src: str
    ) -> Asset | None:
        """Download an external SVG file."""
        try:
            # Get dimensions
            dimensions = svg_img.evaluate("""el => {
                return [el.width || el.clientWidth, el.height || el.clientHeight];
            }""")

            # Resolve URL
            resolved_url = self._resolve_url(src)

            # Download the SVG
            local_path, file_size = self._download_file(resolved_url, "svgs")

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

    def _download_fonts(
        self, target: Locator, seen_urls: set[str]
    ) -> list[Asset]:
        """Download font files referenced in styles."""
        assets: list[Asset] = []

        try:
            # Get all font URLs from the page
            font_urls = self.page.evaluate("""() => {
                const fonts = [];
                const sheets = document.styleSheets;

                try {
                    for (const sheet of sheets) {
                        try {
                            for (const rule of sheet.cssRules) {
                                if (rule instanceof CSSFontFaceRule) {
                                    const src = rule.style.getPropertyValue('src');
                                    if (src) {
                                        // Extract URL from src property
                                        const urlMatch = src.match(/url\\(['"]?([^'")]+)['"]?\\)/);
                                        if (urlMatch) {
                                            fonts.push({
                                                family: rule.style.getPropertyValue('font-family'),
                                                url: urlMatch[1]
                                            });
                                        }
                                    }
                                }
                            }
                        } catch (e) {
                            // CORS or other error
                        }
                    }
                } catch (e) {
                    // Error accessing stylesheets
                }

                return fonts;
            }""")

            for font_info in font_urls:
                url = font_info.get("url")
                if not url or url in seen_urls:
                    continue

                seen_urls.add(url)

                try:
                    resolved_url = self._resolve_url(url)
                    local_path, file_size = self._download_file(resolved_url, "fonts")

                    if local_path:
                        assets.append(Asset(
                            type=AssetType.FONT,
                            original_url=url,
                            local_path=local_path,
                            file_size_bytes=file_size,
                        ))
                except Exception:
                    continue
        except Exception:
            pass

        return assets

    def _resolve_url(self, url: str) -> str:
        """Resolve a relative URL to an absolute URL."""
        if url.startswith("data:"):
            return url

        if url.startswith("//"):
            return f"https:{url}"

        if url.startswith("http://") or url.startswith("https://"):
            return url

        # Relative URL - resolve against page URL
        base_url = self.page.url
        return urllib.parse.urljoin(base_url, url)

    def _download_file(
        self, url: str, subfolder: str
    ) -> tuple[str | None, int]:
        """Download a file from URL to the output directory.

        Args:
            url: The URL to download from.
            subfolder: Subfolder within output directory.

        Returns:
            Tuple of (local_path, file_size) or (None, 0) on failure.
        """
        if url.startswith("data:"):
            return self._save_data_url(url, subfolder)

        try:
            # Create subfolder
            output_subdir = os.path.join(self.output_dir, subfolder)
            os.makedirs(output_subdir, exist_ok=True)

            # Generate filename from URL
            filename = self._generate_filename(url)
            local_path = os.path.join(output_subdir, filename)

            # Download using page's context to get cookies, etc.
            response = self.page.context.request.get(url)

            if not response.ok:
                return None, 0

            body = response.body()
            file_size = len(body)

            # Save to file
            with open(local_path, "wb") as f:
                f.write(body)

            return local_path, file_size
        except Exception:
            return None, 0

    def _save_data_url(self, url: str, subfolder: str) -> tuple[str | None, int]:
        """Save a data URL to a file."""
        try:
            # Parse data URL
            match = re.match(r"data:([^;]+);base64,(.+)", url)
            if not match:
                return None, 0

            mime_type = match.group(1)
            data = match.group(2)

            import base64
            body = base64.b64decode(data)
            file_size = len(body)

            # Determine extension
            ext = self._mime_to_extension(mime_type)

            # Create subfolder and save
            output_subdir = os.path.join(self.output_dir, subfolder)
            os.makedirs(output_subdir, exist_ok=True)

            import hashlib
            filename = f"data_{hashlib.md5(url.encode()).hexdigest()[:8]}{ext}"
            local_path = os.path.join(output_subdir, filename)

            with open(local_path, "wb") as f:
                f.write(body)

            return local_path, file_size
        except Exception:
            return None, 0

    def _save_svg_content(self, content: str, identifier: str) -> str | None:
        """Save SVG content to a file."""
        try:
            output_subdir = os.path.join(self.output_dir, "svgs")
            os.makedirs(output_subdir, exist_ok=True)

            import hashlib
            filename = f"{identifier}_{hashlib.md5(content.encode()).hexdigest()[:8]}.svg"
            local_path = os.path.join(output_subdir, filename)

            with open(local_path, "w", encoding="utf-8") as f:
                f.write(content)

            return local_path
        except Exception:
            return None

    def _generate_filename(self, url: str) -> str:
        """Generate a safe filename from a URL."""
        # Parse URL path
        parsed = urllib.parse.urlparse(url)
        path = parsed.path

        # Get the filename from path
        filename = os.path.basename(path)

        if not filename:
            import hashlib
            filename = f"asset_{hashlib.md5(url.encode()).hexdigest()[:8]}"

        # Sanitize filename
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

        return filename

    def _mime_to_extension(self, mime_type: str) -> str:
        """Convert MIME type to file extension."""
        mime_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/gif": ".gif",
            "image/svg+xml": ".svg",
            "image/webp": ".webp",
            "font/woff": ".woff",
            "font/woff2": ".woff2",
            "font/ttf": ".ttf",
            "font/otf": ".otf",
            "application/font-woff": ".woff",
            "application/font-woff2": ".woff2",
            "application/x-font-ttf": ".ttf",
            "application/x-font-otf": ".otf",
        }
        return mime_map.get(mime_type, "")
