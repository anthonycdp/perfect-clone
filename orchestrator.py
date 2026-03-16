"""Pipeline orchestrator for component and full-page extraction."""

import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from playwright.async_api import Locator

from collector import (
    AnimationRecorder,
    AssetDownloader,
    BrowserManager,
    InteractionMapper,
    InteractionPlayer,
    LibraryDetector,
    RichMediaCollector,
    ResponsiveCollector,
    TargetFinder,
    ExtractionScope,
)
from collector.dom_extractor import DOMExtractor
from collector.style_extractor import StyleExtractor
from models.errors import ExtractionError
from models.extraction import ExtractionMode, SelectorStrategy
from models.normalized import FullPageNormalizedOutput, NormalizedOutput
from models.synthesis import SynthesisOutput
from normalizer import ContextBuilder
from synthesizer import OpenAISynthesizer


class ExtractionOrchestrator:
    """Coordinate the complete extraction pipeline."""

    PROGRESS_STEPS = {
        0: "Connecting to browser",
        1: {
            ExtractionMode.COMPONENT: "Locating component",
            ExtractionMode.FULL_PAGE: "Preparing full-page capture",
        },
        2: {
            ExtractionMode.COMPONENT: "Extracting DOM",
            ExtractionMode.FULL_PAGE: "Extracting page DOM",
        },
        3: "Extracting styles",
        4: "Mapping interactions",
        5: "Executing interactions",
        6: "Recording animations",
        7: "Downloading assets",
        8: "Detecting libraries",
        9: "Analyzing responsiveness",
        10: "Normalizing data",
        11: "Generating prompt with AI",
    }

    def __init__(self, api_key: str, output_dir: str = "output"):
        self.api_key = api_key
        self.output_dir = output_dir
        self.browser = BrowserManager()
        self.synthesizer = OpenAISynthesizer(api_key)
        self._cancelled = False
        self.last_normalized_output: NormalizedOutput | FullPageNormalizedOutput | None = None

    async def extract(
        self,
        url: str,
        strategy: str = "css",
        query: str = "",
        extraction_mode: str = ExtractionMode.COMPONENT.value,
        progress_callback: Callable[[int, str, str], None] | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> SynthesisOutput:
        """Execute the complete extraction pipeline."""
        cancel_check = cancel_check or (lambda: False)
        mode = ExtractionMode(extraction_mode)
        self._cancelled = False

        try:
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 0, mode)
            await self.browser.start()
            await self.browser.navigate(url)

            initial_viewport = self._get_current_viewport()
            raw_extraction = await self._collect_extraction_data(
                mode=mode,
                strategy=strategy,
                query=query,
                initial_viewport=initial_viewport,
                progress_callback=progress_callback,
                cancel_check=cancel_check,
            )

            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 10, mode)
            normalized = ContextBuilder().build(raw_extraction)
            self.last_normalized_output = normalized
            self._save_normalized(normalized)

            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 11, mode)
            return self.synthesizer.synthesize(normalized)
        finally:
            await self.browser.close()

    def cancel(self):
        """Cancel the extraction."""
        self._cancelled = True

    async def _collect_extraction_data(
        self,
        mode: ExtractionMode,
        strategy: str,
        query: str,
        initial_viewport: dict[str, int],
        progress_callback: Callable[[int, str, str], None] | None,
        cancel_check: Callable[[], bool],
    ) -> dict:
        """Collect raw extraction data for the selected mode."""
        if mode == ExtractionMode.FULL_PAGE:
            return await self._collect_full_page_data(
                initial_viewport=initial_viewport,
                progress_callback=progress_callback,
                cancel_check=cancel_check,
            )

        return await self._collect_component_data(
            strategy=strategy,
            query=query,
            initial_viewport=initial_viewport,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
        )

    async def _collect_component_data(
        self,
        strategy: str,
        query: str,
        initial_viewport: dict[str, int],
        progress_callback: Callable[[int, str, str], None] | None,
        cancel_check: Callable[[], bool],
    ) -> dict:
        """Collect raw data for a single target component."""
        mode = ExtractionMode.COMPONENT

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 1, mode)
        scope = TargetFinder(self.browser.page).find(SelectorStrategy(strategy), query)
        target = scope.target
        screenshot_path = await self._capture_target_screenshot(target)

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 2, mode)
        dom_data = DOMExtractor(self.browser.page).extract(target)

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 3, mode)
        style_data = StyleExtractor(self.browser.page).extract(target, scope=scope)
        style_limitations = list(style_data.pop("limitations", []))

        shared_data = await self._collect_shared_target_data(
            target=target,
            mode=mode,
            scope=scope,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
        )
        animation_recording = shared_data.pop("animation_recording")
        frame_limitations = self._merge_limitations(
            scope.frame_limitations,
            style_limitations,
            shared_data.pop("frame_limitations", []),
        )
        collection_limitations = self._merge_limitations(
            style_limitations,
            shared_data.pop("collection_limitations", []),
        )

        return {
            "mode": mode.value,
            "page": await self._build_page_metadata(initial_viewport),
            "target": {
                "selector_used": scope.selector_used,
                "strategy": scope.strategy,
                "html": dom_data["html"],
                "bounding_box": dom_data["bounding_box"],
                "depth": dom_data["depth"],
                "screenshot_path": screenshot_path,
                "frame_url": scope.frame_url,
                "frame_name": scope.frame_name,
                "same_origin_accessible": scope.same_origin_accessible,
                "within_shadow_dom": scope.within_shadow_dom,
                "frame_limitations": frame_limitations,
            },
            "dom_tree": dom_data["dom_tree"],
            "styles": style_data["computed_styles"],
            "animations": self._build_animation_payload(style_data, animation_recording),
            "collection_limitations": collection_limitations,
            **shared_data,
        }

    async def _collect_full_page_data(
        self,
        initial_viewport: dict[str, int],
        progress_callback: Callable[[int, str, str], None] | None,
        cancel_check: Callable[[], bool],
    ) -> dict:
        """Collect raw data for a full landing page."""
        mode = ExtractionMode.FULL_PAGE

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 1, mode)
        scroll_completed = await self._load_lazy_content()
        page_screenshot_path = await self._capture_page_screenshot()
        page_sections = await self._extract_page_sections()
        page_root = self.browser.page.locator("body").first

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 2, mode)
        dom_data = DOMExtractor(self.browser.page).extract_page()

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 3, mode)
        style_data = StyleExtractor(self.browser.page).extract_page()
        style_limitations = list(style_data.pop("limitations", []))

        shared_data = await self._collect_shared_target_data(
            target=page_root,
            mode=mode,
            scope=None,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
        )
        animation_recording = shared_data.pop("animation_recording")

        return {
            "mode": mode.value,
            "page": await self._build_page_metadata(initial_viewport),
            "page_capture": {
                "html": dom_data["html"],
                "screenshot_path": page_screenshot_path,
                "bounding_box": dom_data["bounding_box"],
                "scroll_completed": scroll_completed,
                "sections": page_sections,
            },
            "dom_tree": dom_data["dom_tree"],
            "styles": style_data["computed_styles"],
            "animations": self._build_animation_payload(style_data, animation_recording),
            "collection_limitations": self._merge_limitations(
                style_limitations,
                shared_data.pop("collection_limitations", []),
            ),
            **shared_data,
        }

    async def _collect_shared_target_data(
        self,
        target: Locator,
        mode: ExtractionMode,
        scope: ExtractionScope | None,
        progress_callback: Callable[[int, str, str], None] | None,
        cancel_check: Callable[[], bool],
    ) -> dict:
        """Collect data shared by component and full-page extraction."""
        frame_limitations: list[str] = []
        collection_limitations: list[str] = []

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 4, mode)
        interactions = InteractionMapper(self.browser.page).map(target)

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 5, mode)
        max_interactions = 10 if mode == ExtractionMode.FULL_PAGE else None
        interaction_list = self._build_interaction_list(
            interactions,
            max_per_category=max_interactions,
        )
        observed_states = InteractionPlayer(self.browser.page).play_all(
            target,
            interaction_list,
            scope=scope,
        )

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 6, mode)
        animation_data = AnimationRecorder(self.browser.page, self.output_dir).record(
            target
        )

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 7, mode)
        asset_downloader = AssetDownloader(
            self.browser.page,
            self.output_dir,
            scope=scope if mode == ExtractionMode.COMPONENT else None,
        )
        assets = asset_downloader.download_all(target)
        frame_limitations = self._merge_limitations(
            frame_limitations,
            asset_downloader.last_limitations,
        )
        collection_limitations = self._merge_limitations(
            collection_limitations,
            asset_downloader.last_limitations,
        )

        rich_media_collector = RichMediaCollector(
            self.browser.page,
            self.output_dir,
            scope=scope if mode == ExtractionMode.COMPONENT else None,
        )
        rich_media = rich_media_collector.collect(target)
        collection_limitations = self._merge_limitations(
            collection_limitations,
            rich_media_collector.last_limitations,
        )

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 8, mode)
        library_detector = LibraryDetector(self.browser.page)
        libraries = library_detector.detect(
            scope=scope if mode == ExtractionMode.COMPONENT else None
        )
        frame_limitations = self._merge_limitations(
            frame_limitations,
            library_detector.last_limitations,
        )
        collection_limitations = self._merge_limitations(
            collection_limitations,
            library_detector.last_limitations,
        )

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 9, mode)
        responsive_data = ResponsiveCollector(self.browser.page).collect_all(
            target,
            scope=scope if mode == ExtractionMode.COMPONENT else None,
        )

        return {
            "assets": [asset.model_dump() for asset in assets],
            "interactions": {
                **interactions,
                "observed_states": observed_states,
            },
            "animation_recording": animation_data.model_dump() if animation_data else None,
            "responsive": responsive_data.model_dump(),
            "libraries": [library.model_dump() for library in libraries],
            "rich_media": [
                media_capture.model_dump(mode="json") for media_capture in rich_media
            ],
            "frame_limitations": frame_limitations,
            "collection_limitations": collection_limitations,
        }

    def _check_cancelled(self, cancel_check: Callable[[], bool]):
        """Stop the pipeline when the user cancels the current run."""
        if self._cancelled or cancel_check():
            raise ExtractionError("Cancelled by user")

    def _report_progress(
        self,
        callback: Callable[[int, str, str], None] | None,
        step: int,
        mode: ExtractionMode,
    ):
        """Report progress if a callback was provided."""
        if not callback:
            return

        message = self.PROGRESS_STEPS[step]
        if isinstance(message, dict):
            message = message[mode]
        step_name = message.lower().replace(" ", "_")
        callback(step, step_name, message)

    async def _build_page_metadata(self, viewport: dict[str, int]) -> dict:
        """Build metadata shared by every extraction mode."""
        return {
            "url": self.browser.page.url,
            "title": await self.browser.page.title(),
            "viewport": viewport,
            "loaded_scripts": await self._get_loaded_scripts(),
            "loaded_stylesheets": await self._get_loaded_stylesheets(),
        }

    async def _get_loaded_scripts(self) -> list[str]:
        """Get the list of loaded script URLs."""
        return await self.browser.page.evaluate(
            """() => Array.from(document.querySelectorAll('script[src]')).map(s => s.src)"""
        )

    async def _get_loaded_stylesheets(self) -> list[str]:
        """Get the list of loaded stylesheet URLs."""
        return await self.browser.page.evaluate(
            """() => Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href)"""
        )

    def _build_interaction_list(
        self,
        interactions: dict,
        max_per_category: int | None = None,
    ) -> list[dict]:
        """Build a flat interaction list from categorized elements."""
        category_to_type = {
            "hoverable": "hover",
            "clickable": "click",
            "focusable": "focus",
            "scroll_containers": "scroll",
        }
        interaction_list: list[dict[str, str]] = []

        for category, interaction_type in category_to_type.items():
            elements = interactions.get(category, [])
            if max_per_category is not None:
                elements = elements[:max_per_category]

            for element in elements:
                selector = element.get("selector", "")
                if selector:
                    interaction_list.append(
                        {
                            "type": interaction_type,
                            "selector": selector,
                        }
                    )

        return interaction_list

    async def _capture_target_screenshot(self, target: Locator) -> str | None:
        """Capture a stable screenshot of the target element."""
        screenshot_path = self._build_screenshot_path("target")

        try:
            await target.screenshot(path=str(screenshot_path), animations="disabled")
        except Exception:
            return None

        return str(screenshot_path.resolve())

    async def _capture_page_screenshot(self) -> str | None:
        """Capture a stable screenshot of the full page."""
        screenshot_path = self._build_screenshot_path("page")

        try:
            await self.browser.page.screenshot(
                path=str(screenshot_path),
                full_page=True,
                animations="disabled",
            )
        except Exception:
            return None

        return str(screenshot_path.resolve())

    def _build_screenshot_path(self, prefix: str) -> Path:
        """Build the output path for a screenshot asset."""
        screenshots_dir = Path(self.output_dir) / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return screenshots_dir / f"{prefix}_{timestamp}.png"

    async def _load_lazy_content(
        self,
        max_scroll_steps: int = 12,
        pause_ms: int = 250,
    ) -> bool:
        """Scroll through the page to trigger lazy-loaded content."""
        previous_height = 0
        stable_iterations = 0
        viewport_height = self._get_current_viewport().get("height", 900)

        for _ in range(max_scroll_steps):
            current_height = await self.browser.page.evaluate(
                """() => Math.max(
                    document.documentElement.scrollHeight,
                    document.body ? document.body.scrollHeight : 0
                )"""
            )

            target_y = max(current_height - viewport_height, 0)
            await self.browser.page.evaluate(
                "(y) => window.scrollTo({ top: y, behavior: 'auto' })",
                target_y,
            )
            await self.browser.page.wait_for_timeout(pause_ms)

            try:
                await self.browser.page.wait_for_load_state("networkidle", timeout=1500)
            except Exception:
                pass

            new_height = await self.browser.page.evaluate(
                """() => Math.max(
                    document.documentElement.scrollHeight,
                    document.body ? document.body.scrollHeight : 0
                )"""
            )

            if new_height == previous_height:
                stable_iterations += 1
            else:
                stable_iterations = 0

            previous_height = new_height
            if stable_iterations >= 2:
                break

            await self.browser.page.evaluate(
                "(stepHeight) => window.scrollBy(0, stepHeight)",
                int(viewport_height * 0.85),
            )
            await self.browser.page.wait_for_timeout(pause_ms)

        await self.browser.page.evaluate("() => window.scrollTo({ top: 0, behavior: 'auto' })")
        await self.browser.page.wait_for_timeout(150)
        return stable_iterations >= 1

    async def _extract_page_sections(self) -> list[dict]:
        """Detect the major sections of the landing page."""
        return await self.browser.page.evaluate(
            """() => {
                const viewportWidth = Math.max(window.innerWidth, document.documentElement.clientWidth);
                const keywordMap = [
                    ['hero', 'Hero'],
                    ['feature', 'Features'],
                    ['benefit', 'Benefits'],
                    ['testimonial', 'Testimonials'],
                    ['pricing', 'Pricing'],
                    ['faq', 'FAQ'],
                    ['cta', 'Call To Action'],
                    ['footer', 'Footer'],
                    ['header', 'Header'],
                    ['nav', 'Navigation'],
                ];

                function selectorFor(element) {
                    if (element.id) {
                        return '#' + element.id;
                    }

                    const className = typeof element.className === 'string'
                        ? element.className.trim().split(/\\s+/).filter(Boolean).slice(0, 2)
                        : [];

                    let selector = element.tagName.toLowerCase();
                    if (className.length > 0) {
                        selector += '.' + className.join('.');
                    }
                    return selector;
                }

                function inferName(element, index) {
                    const heading = element.querySelector('h1, h2, h3, h4');
                    if (heading && heading.textContent.trim()) {
                        return heading.textContent.replace(/\\s+/g, ' ').trim().slice(0, 80);
                    }

                    const signals = [
                        element.getAttribute('aria-label') || '',
                        element.id || '',
                        typeof element.className === 'string' ? element.className : '',
                        element.tagName.toLowerCase(),
                    ].join(' ').toLowerCase();

                    for (const [keyword, label] of keywordMap) {
                        if (signals.includes(keyword)) {
                            return label;
                        }
                    }

                    return `Section ${index + 1}`;
                }

                const candidates = Array.from(
                    document.querySelectorAll('header, nav, main, footer, section, [role="region"], body > div, main > div')
                );
                const results = [];

                for (const element of candidates) {
                    const rect = element.getBoundingClientRect();
                    const style = window.getComputedStyle(element);
                    const visible = rect.width >= viewportWidth * 0.35 && rect.height >= 120;
                    if (!visible || style.display === 'none' || style.visibility === 'hidden') {
                        continue;
                    }

                    const textSource = element.querySelector('h1, h2, h3, p') || element;
                    const textExcerpt = (textSource.textContent || '')
                        .replace(/\\s+/g, ' ')
                        .trim()
                        .slice(0, 160);

                    results.push({
                        name: inferName(element, results.length),
                        selector: selectorFor(element),
                        tag: element.tagName.toLowerCase(),
                        text_excerpt: textExcerpt,
                        bounding_box: {
                            x: rect.left + window.scrollX,
                            y: rect.top + window.scrollY,
                            width: rect.width,
                            height: rect.height,
                        },
                    });
                }

                results.sort((left, right) => left.bounding_box.y - right.bounding_box.y);

                const filtered = [];
                for (const section of results) {
                    const duplicate = filtered.some(existing =>
                        Math.abs(existing.bounding_box.y - section.bounding_box.y) < 40 &&
                        Math.abs(existing.bounding_box.height - section.bounding_box.height) < 40 &&
                        existing.selector === section.selector
                    );
                    if (!duplicate) {
                        filtered.push(section);
                    }
                }

                return filtered.slice(0, 12);
            }"""
        )

    def _get_current_viewport(self) -> dict[str, int]:
        """Return the current viewport size with a safe default."""
        return self.browser.page.viewport_size or {"width": 1280, "height": 720}

    def _build_animation_payload(
        self,
        style_data: dict,
        animation_recording: dict | None,
    ) -> dict:
        """Combine CSS motion data with the recorded animation artifact."""
        return {
            "animations": style_data["animations"],
            "transitions": style_data["transitions"],
            "keyframes": style_data["keyframes"],
            "recording": animation_recording,
        }

    def _save_normalized(self, normalized):
        """Save normalized data to a JSON file."""
        extractions_dir = Path(self.output_dir) / "extractions"
        extractions_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = extractions_dir / f"extraction_{timestamp}.json"

        with open(filepath, "w", encoding="utf-8") as handle:
            json.dump(normalized.model_dump(mode="json"), handle, indent=2, ensure_ascii=False)

    def _merge_limitations(self, *groups: list[str]) -> list[str]:
        """Merge limitation lists while preserving the first occurrence order."""
        merged: list[str] = []
        for group in groups:
            for item in group:
                if item and item not in merged:
                    merged.append(item)
        return merged
