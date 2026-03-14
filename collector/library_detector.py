"""LibraryDetector - Detects external JavaScript libraries."""

import re
from typing import Any

from playwright.sync_api import Page

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

    def detect(self) -> list[ExternalLibrary]:
        """Detect all external libraries on page.

        Returns:
            List of detected ExternalLibrary objects.
        """
        # Gather data from the page
        page_data = self._gather_page_data()

        detected: dict[str, ExternalLibrary] = {}

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
            detected[lib_name].usage_snippets = snippets

        return list(detected.values())

    def _gather_page_data(self) -> dict[str, Any]:
        """Gather script and global data from the page.

        Returns:
            Dictionary with scripts, globals, and inline_scripts.
        """
        try:
            return self.page.evaluate("""() => {
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
