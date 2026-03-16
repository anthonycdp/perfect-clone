"""LibraryDetector - Detects external JavaScript libraries."""

import re
from typing import Any

from playwright.async_api import Page

from collector.extraction_scope import ExtractionScope
from models.extraction import ExternalLibrary


class LibraryDetector:
    """Detects external JavaScript libraries used on a page.

    Analyzes script URLs, window globals, and inline scripts to identify
    known animation and UI libraries.
    """

    KNOWN_LIBRARIES = {
        "GSAP": ["gsap", "TweenMax", "TweenLite", "TimelineMax", "TimelineLite"],
        "Lottie": ["lottie", "bodymovin"],
        "Three.js": ["THREE"],
        "Swiper": ["Swiper"],
        "AOS": ["AOS"],
        "ScrollTrigger": ["ScrollTrigger"],
        "Framer Motion": ["Motion", "framerMotion"],
        "Anime.js": ["anime"],
        "Velocity.js": ["Velocity"],
        "Particles.js": ["particlesJS"],
        "Typed.js": ["Typed"],
        "CountUp.js": ["CountUp"],
        "Glide": ["Glide"],
        "Splide": ["Splide"],
        "Embla": ["Embla"],
    }

    # CDN URL patterns for version extraction
    VERSION_PATTERNS = [
        r"/(\d+\.\d+\.\d+(?:-[a-zA-Z0-9.]+)?)/",  # /3.12.2/ or /3.12.2-beta/
        r"@(\d+\.\d+\.\d+)/",  # @8.4.5/
        r"(\d+\.\d+\.\d+)\.min\.js",  # 3.12.2.min.js
    ]

    def __init__(self, page: Page):
        """Initialize LibraryDetector.

        Args:
            page: Playwright Page object to analyze.
        """
        self.page = page
        self.last_limitations: list[str] = []

    async def detect(self, scope: ExtractionScope | None = None) -> list[ExternalLibrary]:
        """Detect all external libraries on page.

        Returns:
            List of detected ExternalLibrary objects.
        """
        self.last_limitations = []
        detected: dict[str, ExternalLibrary] = {}
        for context_name, context in self._get_detection_contexts(scope):
            page_data = await self._gather_page_data(context, context_name)
            self._merge_page_data(detected, page_data)

        return list(detected.values())

    def _get_detection_contexts(
        self,
        scope: ExtractionScope | None,
    ) -> list[tuple[str, Any]]:
        """Return the contexts that should contribute library signals."""
        if scope is None:
            return [("page", self.page)]

        contexts: list[tuple[str, Any]] = [("frame", scope.frame)]
        if scope.frame != self.page.main_frame:
            contexts.append(("page", self.page))
        return contexts

    def _merge_page_data(
        self,
        detected: dict[str, ExternalLibrary],
        page_data: dict[str, Any],
    ) -> None:
        """Merge one document worth of library signals into the shared output."""

        # Check script URLs
        for script in page_data.get("scripts", []):
            src = script.get("src", "")
            if src:
                lib_name = self._identify_library_from_url(src)
                if lib_name:
                    version = self._extract_version(src)
                    if lib_name not in detected:
                        detected[lib_name] = ExternalLibrary(
                            name=lib_name,
                            version=version,
                            source_url=src,
                            usage_snippets=[],
                        )

        # Check window globals
        globals_found = page_data.get("globals", {})
        for lib_name, global_names in self.KNOWN_LIBRARIES.items():
            for global_name in global_names:
                if globals_found.get(global_name):
                    if lib_name not in detected:
                        detected[lib_name] = ExternalLibrary(
                            name=lib_name,
                            version=None,
                            source_url="",
                            usage_snippets=[],
                        )
                    break

        # Extract usage snippets from inline scripts
        inline_scripts = page_data.get("inline_scripts", [])
        for lib_name in detected:
            snippets = self._extract_usage_snippets(
                lib_name, inline_scripts, globals_found
            )
            merged_snippets = detected[lib_name].usage_snippets + snippets
            deduped_snippets: list[str] = []
            for snippet in merged_snippets:
                if snippet and snippet not in deduped_snippets:
                    deduped_snippets.append(snippet)
            detected[lib_name].usage_snippets = deduped_snippets[:5]

    async def _gather_page_data(self, context: Any, context_name: str) -> dict[str, Any]:
        """Gather script and global data from the page.

        Returns:
            Dictionary with scripts, globals, and inline_scripts.
        """
        try:
            return await context.evaluate("""() => {
                const data = {
                    scripts: [],
                    globals: {},
                    inline_scripts: []
                };

                // Collect script sources
                document.querySelectorAll('script[src]').forEach(script => {
                    data.scripts.push({ src: script.src });
                });

                // Collect inline scripts
                document.querySelectorAll('script:not([src])').forEach(script => {
                    if (script.textContent && script.textContent.trim()) {
                        data.inline_scripts.push(script.textContent);
                    }
                });

                // Check for known globals
                const globalsToCheck = [
                    'gsap', 'TweenMax', 'TweenLite', 'TimelineMax', 'TimelineLite',
                    'lottie', 'bodymovin', 'THREE', 'Swiper', 'AOS', 'ScrollTrigger',
                    'Motion', 'framerMotion', 'anime', 'Velocity', 'particlesJS',
                    'Typed', 'CountUp', 'Glide', 'Splide', 'Embla'
                ];

                globalsToCheck.forEach(name => {
                    data.globals[name] = typeof window[name] !== 'undefined';
                });

                return data;
            }""")
        except Exception:
            self.last_limitations.append(
                f"Could not inspect external libraries in the {context_name} document."
            )
            return {"scripts": [], "globals": {}, "inline_scripts": []}

    def _identify_library_from_url(self, url: str) -> str | None:
        """Identify library name from a script URL.

        Args:
            url: Script source URL.

        Returns:
            Library name if identified, None otherwise.
        """
        url_lower = url.lower()

        # Map URL patterns to library names
        url_patterns = {
            "gsap": "GSAP",
            "tweenmax": "GSAP",
            "tweenlite": "GSAP",
            "scrolltrigger": "ScrollTrigger",
            "lottie": "Lottie",
            "bodymovin": "Lottie",
            "three": "Three.js",
            "swiper": "Swiper",
            "aos": "AOS",
            "framer-motion": "Framer Motion",
            "anime": "Anime.js",
            "velocity": "Velocity.js",
            "particles": "Particles.js",
            "typed": "Typed.js",
            "countup": "CountUp.js",
            "glide": "Glide",
            "splide": "Splide",
            "embla": "Embla",
        }

        for pattern, lib_name in url_patterns.items():
            if pattern in url_lower:
                return lib_name

        return None

    def _extract_version(self, url: str) -> str | None:
        """Extract version number from a CDN URL.

        Args:
            url: Script source URL.

        Returns:
            Version string if found, None otherwise.
        """
        for pattern in self.VERSION_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _extract_usage_snippets(
        self,
        lib_name: str,
        inline_scripts: list[str],
        globals_found: dict[str, bool],
    ) -> list[str]:
        """Extract usage snippets for a library from inline scripts.

        Args:
            lib_name: Name of the library.
            inline_scripts: List of inline script contents.
            globals_found: Dictionary of found globals.

        Returns:
            List of usage snippet strings.
        """
        snippets: list[str] = []
        global_names = self.KNOWN_LIBRARIES.get(lib_name, [])

        for script in inline_scripts:
            for global_name in global_names:
                # Find lines that use this global
                lines = script.split("\n")
                for line in lines:
                    if global_name in line and len(line.strip()) > 0:
                        # Clean up the line
                        snippet = line.strip()
                        # Limit snippet length
                        if len(snippet) > 200:
                            snippet = snippet[:200] + "..."
                        if snippet not in snippets:
                            snippets.append(snippet)
                        if len(snippets) >= 5:  # Limit to 5 snippets
                            return snippets

        return snippets
