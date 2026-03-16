"""Pipeline orchestrator for component and full-page extraction."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable

from playwright.async_api import Locator
from PIL import Image

from collector import (
    AnimationRecorder,
    AssetDownloader,
    BrowserManager,
    InteractionMapper,
    InteractionPlayer,
    LibraryDetector,
    RichMediaCollector,
    ResponsiveCollector,
    ScrollProbeCollector,
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

    FULL_PAGE_SECTION_LIMIT = 14
    FULL_PAGE_SECTION_INTERACTION_LIMIT = 6

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
        scope = await TargetFinder(self.browser.page).find(
            SelectorStrategy(strategy),
            query,
        )
        target = scope.target
        element_screenshot_path = await self._capture_target_screenshot(target)

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 2, mode)
        dom_data = await DOMExtractor(self.browser.page).extract(target)

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 3, mode)
        style_data = await StyleExtractor(self.browser.page).extract(target, scope=scope)
        style_limitations = list(style_data.pop("limitations", []))

        shared_data = await self._collect_shared_target_data(
            target=target,
            mode=mode,
            scope=scope,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
        )
        animation_recording = shared_data.pop("animation_recording")
        runtime_scroll_effects = shared_data.pop("runtime_scroll_effects", [])
        scroll_probe = shared_data.pop("scroll_probe", None)
        frame_limitations = self._merge_limitations(
            scope.frame_limitations,
            style_limitations,
            shared_data.pop("frame_limitations", []),
        )
        collection_limitations = self._merge_limitations(
            style_limitations,
            shared_data.pop("collection_limitations", []),
        )
        screenshot_path, visual_reference = self._resolve_component_visual_reference(
            element_screenshot_path=element_screenshot_path,
            scroll_probe=scroll_probe,
            runtime_scroll_effects=runtime_scroll_effects,
            rich_media=shared_data.get("rich_media", []),
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
                "element_screenshot_path": element_screenshot_path,
                "visual_reference": visual_reference,
                "frame_url": scope.frame_url,
                "frame_name": scope.frame_name,
                "same_origin_accessible": scope.same_origin_accessible,
                "within_shadow_dom": scope.within_shadow_dom,
                "frame_limitations": frame_limitations,
            },
            "dom_tree": dom_data["dom_tree"],
            "styles": style_data["computed_styles"],
            "animations": self._build_animation_payload(
                style_data,
                animation_recording,
                runtime_scroll_effects,
                scroll_probe,
            ),
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
        page_root, full_page_scope = await self._resolve_full_page_root()

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 1, mode)
        scroll_completed = await self._load_lazy_content(scope=full_page_scope)
        document_screenshot_path = await self._capture_full_page_screenshot(
            page_root,
            full_page_scope,
        )
        page_sections = await self._extract_page_sections(scope=full_page_scope)

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 2, mode)
        dom_data = await DOMExtractor(self.browser.page).extract(page_root)
        dom_data["bounding_box"] = await self._extract_document_bounding_box(
            full_page_scope,
        )

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 3, mode)
        style_data = await StyleExtractor(self.browser.page).extract(
            page_root,
            scope=full_page_scope,
        )
        style_limitations = list(style_data.pop("limitations", []))

        shared_data = await self._collect_shared_target_data(
            target=page_root,
            mode=mode,
            scope=full_page_scope,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
        )
        animation_recording = shared_data.pop("animation_recording")
        runtime_scroll_effects = shared_data.pop("runtime_scroll_effects", [])
        scroll_probe = shared_data.pop("scroll_probe", None)
        section_captures, section_limitations = await self._collect_full_page_sections(
            page_sections,
            full_page_scope,
            cancel_check,
        )
        page_screenshot_path = self._resolve_full_page_visual_reference(
            document_screenshot_path,
            section_captures,
        )

        return {
            "mode": mode.value,
            "page": await self._build_page_metadata(
                initial_viewport,
                scope=full_page_scope,
            ),
            "page_capture": {
                "html": dom_data["html"],
                "screenshot_path": page_screenshot_path,
                "bounding_box": dom_data["bounding_box"],
                "scroll_completed": scroll_completed,
                "sections": section_captures,
            },
            "dom_tree": dom_data["dom_tree"],
            "styles": style_data["computed_styles"],
            "animations": self._build_animation_payload(
                style_data,
                animation_recording,
                runtime_scroll_effects,
                scroll_probe,
            ),
            "collection_limitations": self._merge_limitations(
                style_limitations,
                shared_data.pop("collection_limitations", []),
                section_limitations,
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
        active_scope = scope

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 4, mode)
        interactions = await InteractionMapper(self.browser.page).map(target)

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 5, mode)
        max_interactions = 10 if mode == ExtractionMode.FULL_PAGE else None
        interaction_list = self._build_interaction_list(
            interactions,
            max_per_category=max_interactions,
        )
        observed_states = await InteractionPlayer(self.browser.page).play_all(
            target,
            interaction_list,
            scope=active_scope,
        )

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 6, mode)
        animation_data = await AnimationRecorder(self.browser.page, self.output_dir).record(
            target
        )

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 7, mode)
        asset_downloader = AssetDownloader(
            self.browser.page,
            self.output_dir,
            scope=active_scope,
        )
        assets = await asset_downloader.download_all(target)
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
            scope=active_scope,
        )
        rich_media = await rich_media_collector.collect(target)
        collection_limitations = self._merge_limitations(
            collection_limitations,
            rich_media_collector.last_limitations,
        )

        scroll_probe_collector = ScrollProbeCollector(self.browser.page, self.output_dir)
        scroll_probe = await scroll_probe_collector.collect(
            target,
            mode=mode,
            scope=active_scope,
            rich_media=rich_media,
        )
        collection_limitations = self._merge_limitations(
            collection_limitations,
            scroll_probe_collector.last_limitations,
        )

        self._check_cancelled(cancel_check)
        self._report_progress(progress_callback, 8, mode)
        library_detector = LibraryDetector(self.browser.page)
        libraries = await library_detector.detect(scope=active_scope)
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
        responsive_data = await ResponsiveCollector(self.browser.page).collect_all(
            target,
            scope=active_scope,
        )

        runtime_scroll_effects = self._collect_runtime_scroll_effects(
            rich_media,
            scroll_probe,
        )

        return {
            "assets": [asset.model_dump() for asset in assets],
            "interactions": {
                **interactions,
                "observed_states": observed_states,
            },
            "animation_recording": animation_data.model_dump() if animation_data else None,
            "scroll_probe": scroll_probe,
            "runtime_scroll_effects": runtime_scroll_effects,
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

    async def _build_page_metadata(
        self,
        viewport: dict[str, int],
        scope: ExtractionScope | None = None,
    ) -> dict:
        """Build metadata shared by every extraction mode."""
        title = await self.browser.page.title()
        if scope is not None:
            try:
                title = await scope.frame.evaluate("() => document.title || ''") or title
            except Exception:
                pass

        return {
            "url": scope.frame_url if scope is not None else self.browser.page.url,
            "title": title,
            "viewport": viewport,
            "loaded_scripts": await self._get_loaded_scripts(scope=scope),
            "loaded_stylesheets": await self._get_loaded_stylesheets(scope=scope),
        }

    async def _get_loaded_scripts(
        self,
        scope: ExtractionScope | None = None,
    ) -> list[str]:
        """Get the list of loaded script URLs."""
        context = scope.frame if scope is not None else self.browser.page
        return await context.evaluate(
            """() => Array.from(document.querySelectorAll('script[src]')).map(s => s.src)"""
        )

    async def _get_loaded_stylesheets(
        self,
        scope: ExtractionScope | None = None,
    ) -> list[str]:
        """Get the list of loaded stylesheet URLs."""
        context = scope.frame if scope is not None else self.browser.page
        return await context.evaluate(
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
        return await self._capture_locator_screenshot(
            target,
            self._build_screenshot_path("target"),
            clip_to_visible=True,
        )

    def _resolve_component_visual_reference(
        self,
        element_screenshot_path: str | None,
        scroll_probe: dict | None,
        runtime_scroll_effects: list[str],
        rich_media: list[dict],
    ) -> tuple[str | None, dict[str, str | bool | None]]:
        """Choose the primary screenshot for runtime-heavy components."""
        default_reference = self._build_visual_reference_payload(
            promoted=False,
            source="element_screenshot",
            source_path=element_screenshot_path,
            reason=None,
        )
        if not element_screenshot_path:
            return None, default_reference

        if not self._should_promote_component_visual_reference(
            scroll_probe,
            runtime_scroll_effects,
            rich_media,
        ):
            return element_screenshot_path, default_reference

        promoted_source = self._select_scroll_probe_frame_path(scroll_probe)
        if promoted_source is None:
            return element_screenshot_path, default_reference

        promoted_path = self._promote_visual_reference(promoted_source)
        if promoted_path is None:
            return element_screenshot_path, default_reference

        return str(promoted_path.resolve()), self._build_visual_reference_payload(
            promoted=True,
            source="scroll_probe_frame",
            source_path=str(promoted_source.resolve()),
            reason=(
                "Promoted a scroll-probe frame because the component depends on "
                "runtime scroll or document-level media for its final look."
            ),
        )

    def _should_promote_component_visual_reference(
        self,
        scroll_probe: dict | None,
        runtime_scroll_effects: list[str],
        rich_media: list[dict],
    ) -> bool:
        """Return True when runtime evidence should override the raw element shot."""
        if not scroll_probe or not scroll_probe.get("triggered"):
            return False

        has_runtime_scroll_effects = bool(runtime_scroll_effects)
        has_document_level_media = any(
            media.get("document_level") for media in rich_media
        )
        has_runtime_canvas = any(
            media.get("type") in {"webgl", "canvas"} for media in rich_media
        )
        return (
            has_runtime_scroll_effects
            or has_document_level_media
            or has_runtime_canvas
        )

    def _select_scroll_probe_frame_path(self, scroll_probe: dict | None) -> Path | None:
        """Return the best available scroll-probe frame for visual reference promotion."""
        if not scroll_probe:
            return None

        frames_dir = scroll_probe.get("frames_dir")
        if not frames_dir:
            return None

        key_frames = scroll_probe.get("key_frames") or []
        frame_indexes: list[int] = []
        for candidate in [*key_frames, 0]:
            if isinstance(candidate, int) and candidate not in frame_indexes:
                frame_indexes.append(candidate)

        probe_frames_dir = Path(frames_dir)
        for index in frame_indexes:
            frame_path = probe_frames_dir / f"frame_{index:04d}.png"
            if frame_path.exists():
                return frame_path

        return None

    def _promote_visual_reference(self, source_path: Path) -> Path | None:
        """Copy a scroll-probe frame to a stable screenshot path."""
        destination = Path(self.output_dir) / "screenshots" / "visual_reference.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copyfile(source_path, destination)
        except Exception:
            return None
        return destination

    def _build_visual_reference_payload(
        self,
        promoted: bool,
        source: str,
        source_path: str | None,
        reason: str | None,
    ) -> dict[str, str | bool | None]:
        """Build a serializable description of the chosen visual reference."""
        return {
            "promoted": promoted,
            "source": source,
            "source_path": source_path,
            "reason": reason,
        }

    def _resolve_full_page_visual_reference(
        self,
        document_screenshot_path: str | None,
        section_captures: list[dict],
    ) -> str | None:
        """Choose the best primary screenshot for a full-page extraction."""
        section_screenshot_paths = [
            Path(path)
            for section in section_captures
            if (path := section.get("screenshot_path"))
        ]
        if not section_screenshot_paths:
            return document_screenshot_path

        if document_screenshot_path and not self._should_promote_full_page_visual_reference(
            Path(document_screenshot_path),
        ):
            return document_screenshot_path

        stitched_path = self._build_full_page_visual_reference(section_screenshot_paths)
        if stitched_path is None:
            return document_screenshot_path
        return str(stitched_path.resolve())

    def _should_promote_full_page_visual_reference(self, screenshot_path: Path) -> bool:
        """Return True when the raw full-page screenshot is visually sparse."""
        if not screenshot_path.exists():
            return True

        try:
            with Image.open(screenshot_path) as image:
                sample = image.convert("RGB")
                sample.thumbnail((96, 512))
                sample_width, sample_height = sample.size
                pixels = [
                    sample.getpixel((x, y))
                    for y in range(sample_height)
                    for x in range(sample_width)
                ]
        except Exception:
            return False

        if not pixels:
            return False

        sparse_pixels = 0
        for red, green, blue in pixels:
            max_delta = max(abs(red - green), abs(green - blue), abs(red - blue))
            if red >= 245 and green >= 245 and blue >= 245 and max_delta <= 8:
                sparse_pixels += 1

        return (sparse_pixels / len(pixels)) >= 0.55

    def _build_full_page_visual_reference(
        self,
        section_screenshot_paths: list[Path],
    ) -> Path | None:
        """Build a stitched landing overview from section screenshots."""
        valid_paths = [path for path in section_screenshot_paths if path.exists()]
        if not valid_paths:
            return None

        destination = Path(self.output_dir) / "screenshots" / "page_visual_reference.png"
        destination.parent.mkdir(parents=True, exist_ok=True)

        prepared_images: list[tuple[Image.Image, tuple[int, int]]] = []
        target_width = 0
        for path in valid_paths:
            try:
                image = Image.open(path).convert("RGB")
            except Exception:
                continue
            target_width = max(target_width, image.width)
            prepared_images.append((image, (image.width, image.height)))

        if not prepared_images or target_width <= 0:
            for image, _ in prepared_images:
                image.close()
            return None

        resized_images: list[Image.Image] = []
        total_height = 0
        try:
            for image, (width, height) in prepared_images:
                if width == target_width:
                    resized = image.copy()
                else:
                    scaled_height = max(1, round(height * (target_width / width)))
                    resized = image.resize((target_width, scaled_height), Image.Resampling.LANCZOS)
                resized_images.append(resized)
                total_height += resized.height

            canvas = Image.new("RGB", (target_width, total_height))
            current_y = 0
            for image in resized_images:
                canvas.paste(image, (0, current_y))
                current_y += image.height
            canvas.save(destination, format="PNG")
            canvas.close()
            return destination
        except Exception:
            return None
        finally:
            for image, _ in prepared_images:
                image.close()
            for image in resized_images:
                image.close()

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

    async def _capture_full_page_screenshot(
        self,
        page_root: Locator,
        scope: ExtractionScope,
    ) -> str | None:
        """Capture the primary screenshot for the active full-page document."""
        if scope.frame == self.browser.page.main_frame:
            return await self._capture_page_screenshot()

        return await self._capture_locator_screenshot(
            page_root,
            self._build_screenshot_path("page"),
        )

    async def _capture_locator_screenshot(
        self,
        target: Locator,
        destination: Path,
        clip_to_visible: bool = False,
    ) -> str | None:
        """Capture a screenshot for an arbitrary locator."""
        destination.parent.mkdir(parents=True, exist_ok=True)

        if clip_to_visible:
            visible_clip = await self._build_visible_locator_clip(target)
            if visible_clip is not None:
                try:
                    await self.browser.page.screenshot(
                        path=str(destination),
                        clip=visible_clip,
                        animations="disabled",
                    )
                    return str(destination.resolve())
                except Exception:
                    pass

        try:
            await target.screenshot(path=str(destination), animations="disabled")
        except Exception:
            return None

        return str(destination.resolve())

    async def _build_visible_locator_clip(
        self,
        target: Locator,
    ) -> dict[str, float] | None:
        """Return the intersection between the locator box and the current viewport."""
        try:
            await target.scroll_into_view_if_needed()
            box = await target.bounding_box()
        except Exception:
            return None

        if box is None:
            return None

        viewport = self.browser.page.viewport_size
        if viewport is None:
            return None

        right_edge = box["x"] + box["width"]
        bottom_edge = box["y"] + box["height"]
        overflows_viewport = (
            box["x"] < 0
            or box["y"] < 0
            or right_edge > viewport["width"]
            or bottom_edge > viewport["height"]
        )
        if not overflows_viewport:
            return None

        left = max(0.0, box["x"])
        top = max(0.0, box["y"])
        right = min(float(viewport["width"]), right_edge)
        bottom = min(float(viewport["height"]), bottom_edge)
        width = right - left
        height = bottom - top

        if width < 1 or height < 1:
            return None

        return {
            "x": left,
            "y": top,
            "width": width,
            "height": height,
        }

    async def _resolve_full_page_root(self) -> tuple[Locator, ExtractionScope]:
        """Choose the document that should be treated as the full-page extraction root."""
        iframe_metadata = await self._inspect_dominant_iframe()
        if iframe_metadata:
            iframe_locator = self.browser.page.locator("iframe").nth(
                iframe_metadata["index"]
            )
            iframe_handle = await iframe_locator.element_handle()
            iframe = await iframe_handle.content_frame() if iframe_handle else None
            if iframe is not None:
                page_root = iframe.locator("body").first
                document_base_url = await self._resolve_document_base_url(iframe)
                return page_root, ExtractionScope(
                    page=self.browser.page,
                    frame=iframe,
                    target=page_root,
                    selector_used=iframe_metadata["selector"],
                    strategy=SelectorStrategy.CSS.value,
                    frame_url=iframe.url or iframe_metadata.get("src") or self.browser.page.url,
                    frame_name=iframe.name or None,
                    same_origin_accessible=True,
                    document_base_url=document_base_url,
                    within_shadow_dom=False,
                )

        page_root = self.browser.page.locator("body").first
        return page_root, self._build_page_scope(page_root, "body")

    async def _inspect_dominant_iframe(self) -> dict | None:
        """Return the dominant iframe metadata when the page is a preview shell."""
        return await self.browser.page.evaluate(
            """() => {
                const viewportWidth = Math.max(window.innerWidth, document.documentElement.clientWidth);
                const viewportHeight = Math.max(window.innerHeight, document.documentElement.clientHeight);
                const sectionCandidates = Array.from(
                    document.querySelectorAll('header, nav, main, footer, section, [role="region"], body > div, main > div')
                ).filter(element => {
                    const rect = element.getBoundingClientRect();
                    const style = getComputedStyle(element);
                    return (
                        rect.width >= viewportWidth * 0.35 &&
                        rect.height >= 120 &&
                        style.display !== 'none' &&
                        style.visibility !== 'hidden'
                    );
                });

                const iframeEntries = Array.from(document.querySelectorAll('iframe'))
                    .map((element, index) => {
                        const rect = element.getBoundingClientRect();
                        const area = Math.max(rect.width, 0) * Math.max(rect.height, 0);
                        return {
                            index,
                            selector: element.id ? `#${element.id}` : `iframe:nth-of-type(${index + 1})`,
                            src: element.getAttribute('src') || '',
                            width: rect.width,
                            height: rect.height,
                            area,
                        };
                    })
                    .filter(entry =>
                        entry.width >= viewportWidth * 0.6 &&
                        entry.height >= viewportHeight * 0.6 &&
                        entry.area >= viewportWidth * viewportHeight * 0.45
                    )
                    .sort((left, right) => right.area - left.area);

                if (iframeEntries.length === 0) {
                    return null;
                }

                const shouldUseIframe =
                    sectionCandidates.length <= 3 ||
                    document.body.children.length <= 2;

                return shouldUseIframe ? iframeEntries[0] : null;
            }"""
        )

    async def _resolve_document_base_url(self, context) -> str:
        """Resolve the current document base URL for a page or frame context."""
        try:
            return await context.evaluate("() => document.baseURI || location.href")
        except Exception:
            return self.browser.page.url

    async def _extract_document_bounding_box(
        self,
        scope: ExtractionScope,
    ) -> dict[str, float]:
        """Measure the active document dimensions for the full-page scope."""
        try:
            return await scope.frame.evaluate(
                """() => {
                    const root = document.documentElement;
                    const body = document.body;
                    const width = Math.max(
                        root.scrollWidth,
                        root.clientWidth,
                        body ? body.scrollWidth : 0,
                        body ? body.clientWidth : 0
                    );
                    const height = Math.max(
                        root.scrollHeight,
                        root.clientHeight,
                        body ? body.scrollHeight : 0,
                        body ? body.clientHeight : 0
                    );
                    return { x: 0, y: 0, width, height };
                }"""
            )
        except Exception:
            return {"x": 0, "y": 0, "width": 0, "height": 0}

    async def _collect_full_page_sections(
        self,
        page_sections: list[dict],
        full_page_scope: ExtractionScope,
        cancel_check: Callable[[], bool],
    ) -> tuple[list[dict], list[str]]:
        """Collect section-level runtime evidence for a full-page extraction."""
        section_captures: list[dict] = []
        collection_limitations: list[str] = []

        for index, section in enumerate(page_sections):
            self._check_cancelled(cancel_check)
            capture = await self._collect_full_page_section(
                section,
                index,
                full_page_scope,
            )
            section_captures.append(capture)

            if capture.get("collection_limitations"):
                collection_limitations.append(
                    f"Section `{capture.get('section_id') or capture.get('selector') or index}` had collection limitations; inspect the section entry for details."
                )

        return section_captures, self._merge_limitations(collection_limitations)

    async def _collect_full_page_section(
        self,
        section: dict,
        index: int,
        full_page_scope: ExtractionScope,
    ) -> dict:
        """Collect screenshot, interactions, rich media, and probe data for one page section."""
        section_id = section.get("section_id") or f"section-{index + 1:02d}"
        section_output_dir = Path(self.output_dir) / "sections" / section_id
        probe_selector = section.get("probe_selector") or section.get("selector") or "section"
        target = full_page_scope.frame.locator(probe_selector).first
        section_scope = self._build_page_scope(
            target,
            probe_selector,
            base_scope=full_page_scope,
        )
        collection_limitations: list[str] = []

        await self._position_section_for_capture(section, section_scope)

        screenshot_path = await self._capture_locator_screenshot(
            target,
            section_output_dir / "screenshot.png",
        )
        if screenshot_path is None:
            collection_limitations.append(
                f"Could not capture a stable screenshot for section `{section_id}`."
            )

        html = await self._capture_outer_html(target)
        if not html:
            collection_limitations.append(
                f"Could not serialize the HTML for section `{section_id}`."
            )

        try:
            style_data = await StyleExtractor(self.browser.page).extract(
                target,
                scope=section_scope,
            )
        except Exception:
            style_data = {
                "computed_styles": {},
                "animations": [],
                "transitions": [],
                "keyframes": {},
            }
            collection_limitations.append(
                f"Could not inspect computed styles for section `{section_id}`."
            )
        else:
            collection_limitations = self._merge_limitations(
                collection_limitations,
                style_data.pop("limitations", []),
            )

        try:
            interactions = await InteractionMapper(self.browser.page).map(target)
        except Exception:
            interactions = {
                "hoverable": [],
                "clickable": [],
                "focusable": [],
                "scroll_containers": [],
            }
            observed_states: list[dict] = []
            collection_limitations.append(
                f"Could not map interactions for section `{section_id}`."
            )
        else:
            interaction_list = self._build_interaction_list(
                interactions,
                max_per_category=self.FULL_PAGE_SECTION_INTERACTION_LIMIT,
            )
            observed_states = await InteractionPlayer(self.browser.page).play_all(
                target,
                interaction_list,
                scope=section_scope,
            )

        rich_media_collector = RichMediaCollector(
            self.browser.page,
            str(section_output_dir),
            scope=section_scope,
        )
        rich_media = await rich_media_collector.collect(target)
        collection_limitations = self._merge_limitations(
            collection_limitations,
            rich_media_collector.last_limitations,
        )

        scroll_probe_collector = ScrollProbeCollector(
            self.browser.page,
            str(section_output_dir),
        )
        scroll_probe = await scroll_probe_collector.collect(
            target,
            mode=ExtractionMode.COMPONENT,
            scope=section_scope,
            rich_media=rich_media,
        )
        collection_limitations = self._merge_limitations(
            collection_limitations,
            scroll_probe_collector.last_limitations,
        )

        runtime_scroll_effects = self._collect_runtime_scroll_effects(
            rich_media,
            scroll_probe,
        )

        return {
            "section_id": section_id,
            "name": section.get("name", f"Section {index + 1}"),
            "selector": section.get("selector", probe_selector),
            "tag": section.get("tag", "section"),
            "text_excerpt": section.get("text_excerpt", ""),
            "bounding_box": section.get("bounding_box", {}),
            "html": html,
            "screenshot_path": screenshot_path,
            "interactions": {
                **interactions,
                "observed_states": observed_states,
            },
            "animations": self._build_animation_payload(
                style_data,
                None,
                runtime_scroll_effects,
                scroll_probe,
            ),
            "rich_media": [
                media_capture.model_dump(mode="json") for media_capture in rich_media
            ],
            "collection_limitations": collection_limitations,
        }

    async def _position_section_for_capture(
        self,
        section: dict,
        scope: ExtractionScope,
    ) -> None:
        """Bring a section near the viewport center before collecting section-scoped data."""
        target_y = max(float(section.get("bounding_box", {}).get("y", 0)) - 120, 0)
        await scope.frame.evaluate(
            "(y) => window.scrollTo({ top: y, behavior: 'auto' })",
            target_y,
        )
        await self.browser.page.wait_for_timeout(120)

    async def _capture_outer_html(self, target: Locator) -> str:
        """Return the rendered outer HTML for a locator when possible."""
        try:
            return await target.evaluate("(element) => element.outerHTML || ''")
        except Exception:
            return ""

    def _build_page_scope(
        self,
        target: Locator,
        selector_used: str,
        base_scope: ExtractionScope | None = None,
    ) -> ExtractionScope:
        """Create a same-document extraction scope for a main-frame page section."""
        if base_scope is not None:
            return ExtractionScope(
                page=self.browser.page,
                frame=base_scope.frame,
                target=target,
                selector_used=selector_used,
                strategy=SelectorStrategy.CSS.value,
                frame_url=base_scope.frame_url,
                frame_name=base_scope.frame_name,
                same_origin_accessible=base_scope.same_origin_accessible,
                document_base_url=base_scope.document_base_url,
                within_shadow_dom=False,
            )

        return ExtractionScope(
            page=self.browser.page,
            frame=self.browser.page.main_frame,
            target=target,
            selector_used=selector_used,
            strategy=SelectorStrategy.CSS.value,
            frame_url=self.browser.page.url,
            frame_name=None,
            same_origin_accessible=True,
            document_base_url=self.browser.page.url,
            within_shadow_dom=False,
        )

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
        scope: ExtractionScope | None = None,
    ) -> bool:
        """Scroll through the page to trigger lazy-loaded content."""
        previous_height = 0
        stable_iterations = 0
        viewport_height = self._get_current_viewport().get("height", 900)
        scroll_context = scope.frame if scope is not None else self.browser.page.main_frame

        for _ in range(max_scroll_steps):
            current_height = await scroll_context.evaluate(
                """() => Math.max(
                    document.documentElement.scrollHeight,
                    document.body ? document.body.scrollHeight : 0
                )"""
            )

            target_y = max(current_height - viewport_height, 0)
            await scroll_context.evaluate(
                "(y) => window.scrollTo({ top: y, behavior: 'auto' })",
                target_y,
            )
            await self.browser.page.wait_for_timeout(pause_ms)

            try:
                await self.browser.page.wait_for_load_state("networkidle", timeout=1500)
            except Exception:
                pass

            new_height = await scroll_context.evaluate(
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

            await scroll_context.evaluate(
                "(stepHeight) => window.scrollBy(0, stepHeight)",
                int(viewport_height * 0.85),
            )
            await self.browser.page.wait_for_timeout(pause_ms)

        await scroll_context.evaluate("() => window.scrollTo({ top: 0, behavior: 'auto' })")
        await self.browser.page.wait_for_timeout(150)
        return stable_iterations >= 1

    async def _extract_page_sections(
        self,
        scope: ExtractionScope | None = None,
    ) -> list[dict]:
        """Detect the major sections of the landing page."""
        context = scope.frame if scope is not None else self.browser.page
        return await context.evaluate(
            """(limit) => {
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

                function slugify(value) {
                    return (value || '')
                        .toLowerCase()
                        .replace(/[^a-z0-9]+/g, '-')
                        .replace(/^-+|-+$/g, '')
                        .slice(0, 48);
                }

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

                for (const [candidateIndex, element] of candidates.entries()) {
                    const rect = element.getBoundingClientRect();
                    const style = window.getComputedStyle(element);
                    const visible = rect.width >= viewportWidth * 0.35 && rect.height >= 120;
                    const isLargeFixedOverlay =
                        style.position === 'fixed' &&
                        rect.width >= viewportWidth * 0.6 &&
                        rect.height >= window.innerHeight * 0.6;
                    const nestedSemanticSections = element.querySelectorAll(
                        'section, footer, header, nav, [role="region"]'
                    ).length;
                    const isWrapperContainer =
                        !['header', 'nav', 'main', 'footer', 'section'].includes(element.tagName.toLowerCase()) &&
                        nestedSemanticSections >= 3 &&
                        rect.height >= window.innerHeight * 1.2;

                    if (
                        !visible ||
                        style.display === 'none' ||
                        style.visibility === 'hidden' ||
                        isLargeFixedOverlay ||
                        isWrapperContainer
                    ) {
                        continue;
                    }

                    const textSource = element.querySelector('h1, h2, h3, p') || element;
                    const textExcerpt = (textSource.textContent || '')
                        .replace(/\\s+/g, ' ')
                        .trim()
                        .slice(0, 160);

                    const inferredName = inferName(element, results.length);
                    const slug = slugify(inferredName) || `${element.tagName.toLowerCase()}-${candidateIndex + 1}`;
                    const sectionId = `section-${String(candidateIndex + 1).padStart(2, '0')}-${slug}`;
                    element.setAttribute('data-component-extractor-section-id', sectionId);

                    results.push({
                        section_id: sectionId,
                        name: inferredName,
                        selector: selectorFor(element),
                        probe_selector: `[data-component-extractor-section-id="${sectionId}"]`,
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

                return filtered.slice(0, limit);
            }""",
            self.FULL_PAGE_SECTION_LIMIT,
        )

    def _get_current_viewport(self) -> dict[str, int]:
        """Return the current viewport size with a safe default."""
        return self.browser.page.viewport_size or {"width": 1280, "height": 720}

    def _build_animation_payload(
        self,
        style_data: dict,
        animation_recording: dict | None,
        runtime_scroll_effects: list[str] | None = None,
        scroll_probe: dict | None = None,
    ) -> dict:
        """Combine CSS motion data with the recorded animation artifact."""
        return {
            "animations": style_data["animations"],
            "transitions": style_data["transitions"],
            "keyframes": style_data["keyframes"],
            "observed_scroll_effects": runtime_scroll_effects or [],
            "recording": animation_recording,
            "scroll_probe": scroll_probe,
        }

    def _collect_runtime_scroll_effects(
        self,
        rich_media: list,
        scroll_probe: dict | None = None,
    ) -> list[str]:
        """Extract unique scroll-linked effect summaries from captured rich media."""
        effects: list[str] = []
        for media_capture in rich_media:
            effect_summary = getattr(media_capture, "effect_summary", None)
            if not effect_summary:
                continue
            if "scroll" not in effect_summary.lower():
                continue
            if effect_summary not in effects:
                effects.append(effect_summary)

        for observation in (scroll_probe or {}).get("observations", []):
            if observation and observation not in effects:
                effects.append(observation)
        return effects

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
