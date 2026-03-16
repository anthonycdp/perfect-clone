"""Runtime scroll probe for scroll-linked component and page effects."""

from __future__ import annotations

import math
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import Locator, Page

from collector.extraction_scope import ExtractionScope
from models.extraction import ExtractionMode


class ScrollProbeCollector:
    """Capture scroll-driven runtime changes as frames, video, and structured state."""

    COMPONENT_MAX_STEPS = 18
    FULL_PAGE_MAX_STEPS = 28
    COMPONENT_MIN_STEPS = 8
    FULL_PAGE_MIN_STEPS = 10
    FPS = 12
    SETTLE_MS = 140

    def __init__(self, page: Page, output_dir: str):
        self.page = page
        self.output_dir = output_dir
        self.last_limitations: list[str] = []
        self.probe_dir = Path(output_dir) / "animations" / "scroll_probe"

    async def collect(
        self,
        target: Locator,
        mode: ExtractionMode,
        scope: ExtractionScope | None = None,
        rich_media: list[Any] | None = None,
    ) -> dict[str, Any] | None:
        """Capture runtime scroll behavior and summarize the observed changes."""
        self.last_limitations = []
        rich_media = rich_media or []

        probe_range = await self._measure_probe_range(target, mode)
        if probe_range is None:
            return None

        context_label = self._resolve_probe_context(scope)
        scroll_positions = self._build_scroll_positions(mode, probe_range)
        if not scroll_positions:
            return self._empty_summary(context_label, probe_range, rich_media)

        tracked_selectors = await self._discover_tracked_selectors(target, rich_media)
        overlay_selectors = self._collect_overlay_selectors(rich_media)
        recording_dir, frames_dir = self._create_probe_dirs()

        states_by_selector: dict[str, list[dict[str, Any]]] = {
            selector: [] for selector in [*tracked_selectors, *overlay_selectors]
        }

        scroll_context = scope.frame if scope is not None else self.page.main_frame
        for index, scroll_y in enumerate(scroll_positions):
            await scroll_context.evaluate(
                "(position) => window.scrollTo({ top: position, behavior: 'instant' })",
                scroll_y,
            )
            await self.page.wait_for_timeout(self.SETTLE_MS)

            frame_path = frames_dir / f"frame_{index:04d}.png"
            await self._capture_probe_frame(target, mode, frame_path)

            probe_states = await target.evaluate(
                self._capture_probe_states_script(),
                {
                    "trackedSelectors": tracked_selectors,
                    "overlaySelectors": overlay_selectors,
                },
            )
            for state in probe_states:
                selector = state.get("selector")
                if selector in states_by_selector:
                    states_by_selector[selector].append(state)

        key_frames = self._detect_key_frames(frames_dir, len(scroll_positions))
        video_path = self._encode_video(frames_dir, recording_dir, self.FPS)
        observations, state_changes = self._summarize_probe_states(
            states_by_selector,
            rich_media,
            key_frames,
        )

        return {
            "context": context_label,
            "triggered": len(key_frames) > 1 or bool(state_changes),
            "range_start": probe_range["range_start"],
            "range_end": probe_range["range_end"],
            "step_count": len(scroll_positions),
            "fps": self.FPS,
            "frames_dir": str(frames_dir.resolve()),
            "video_path": str(video_path.resolve()) if video_path else None,
            "key_frames": key_frames,
            "tracked_selectors": tracked_selectors,
            "overlay_selectors": overlay_selectors,
            "observations": observations,
            "state_changes": state_changes,
            "limitations": list(self.last_limitations),
        }

    async def _measure_probe_range(
        self,
        target: Locator,
        mode: ExtractionMode,
    ) -> dict[str, float] | None:
        """Measure the scroll range that should be probed."""
        try:
            geometry = await target.evaluate(
                """
                (element, mode) => {
                    const rect = element.getBoundingClientRect();
                    const viewportHeight = window.innerHeight;
                    const docHeight = Math.max(
                        document.documentElement.scrollHeight,
                        document.body ? document.body.scrollHeight : 0
                    );
                    const maxScroll = Math.max(0, docHeight - viewportHeight);
                    const targetTop = rect.top + window.scrollY;
                    const targetBottom = rect.bottom + window.scrollY;

                    if (mode === 'full_page') {
                        return {
                            range_start: 0,
                            range_end: maxScroll,
                            viewport_height: viewportHeight,
                            max_scroll: maxScroll,
                        };
                    }

                    let rangeStart = Math.max(0, targetTop - viewportHeight * 0.95);
                    let rangeEnd = Math.min(maxScroll, targetBottom - viewportHeight * 0.1);
                    if (rangeEnd <= rangeStart) {
                        rangeEnd = Math.min(maxScroll, rangeStart + viewportHeight);
                    }

                    return {
                        range_start: rangeStart,
                        range_end: rangeEnd,
                        viewport_height: viewportHeight,
                        max_scroll: maxScroll,
                    };
                }
                """,
                mode.value,
            )
        except Exception:
            self.last_limitations.append(
                "Could not measure the runtime scroll range for this extraction."
            )
            return None

        return geometry

    def _resolve_probe_context(self, scope: ExtractionScope | None) -> str:
        """Classify the probe context for prompt-friendly output."""
        if scope is None or scope.frame == self.page.main_frame:
            return "page"
        return "frame"

    def _build_scroll_positions(
        self,
        mode: ExtractionMode,
        probe_range: dict[str, float],
    ) -> list[float]:
        """Build the ordered scroll positions used during the probe."""
        range_start = float(probe_range.get("range_start", 0))
        range_end = float(probe_range.get("range_end", 0))
        viewport_height = max(float(probe_range.get("viewport_height", 1)), 1.0)

        if range_end <= range_start:
            return [range_start]

        if mode == ExtractionMode.COMPONENT:
            target_steps = math.ceil((range_end - range_start) / (viewport_height * 0.12))
            step_count = min(
                self.COMPONENT_MAX_STEPS,
                max(self.COMPONENT_MIN_STEPS, target_steps),
            )
        else:
            target_steps = math.ceil((range_end - range_start) / (viewport_height * 0.22))
            step_count = min(
                self.FULL_PAGE_MAX_STEPS,
                max(self.FULL_PAGE_MIN_STEPS, target_steps),
            )

        if step_count <= 1:
            return [range_start, range_end]

        positions = [
            range_start + (range_end - range_start) * index / (step_count - 1)
            for index in range(step_count)
        ]

        deduped: list[float] = []
        for position in positions:
            rounded = round(position, 2)
            if not deduped or rounded != deduped[-1]:
                deduped.append(rounded)
        return deduped

    async def _discover_tracked_selectors(
        self,
        target: Locator,
        rich_media: list[Any],
    ) -> list[str]:
        """Find the most useful target-local selectors to observe during the probe."""
        linked_selectors: list[str] = []
        for media in rich_media:
            for selector in getattr(media, "linked_selectors", []):
                if selector and selector not in linked_selectors:
                    linked_selectors.append(selector)

        try:
            selectors = await target.evaluate(
                """
                (element, payload) => {
                    function buildSelector(node) {
                        if (node === element) {
                            return '__target__';
                        }

                        if (node.id) {
                            return '#' + node.id;
                        }

                        let selector = node.tagName.toLowerCase();
                        if (node.className && typeof node.className === 'string') {
                            const classes = node.className.trim().split(/\\s+/).filter(Boolean);
                            if (classes.length > 0) {
                                selector += '.' + classes.slice(0, 2).join('.');
                            }
                        }

                        const parent = node.parentElement;
                        if (!parent) {
                            return selector;
                        }

                        const siblings = Array.from(parent.children).filter(
                            sibling => sibling.tagName === node.tagName
                        );
                        if (siblings.length > 1) {
                            selector += `:nth-of-type(${siblings.indexOf(node) + 1})`;
                        }

                        return selector;
                    }

                    const selectors = ['__target__'];
                    const candidates = [element, ...element.querySelectorAll('*')];
                    const keywordPattern = /(webgl|parallax|reveal|scroll|animate|motion|mask)/i;

                    for (const node of candidates) {
                        const style = getComputedStyle(node);
                        const className = typeof node.className === 'string' ? node.className : '';
                        const hasKeyword = keywordPattern.test(className);
                        const hasInterestingStyle = (
                            style.opacity !== '1' ||
                            style.transform !== 'none' ||
                            style.filter !== 'none' ||
                            style.clipPath !== 'none' ||
                            style.maskImage !== 'none'
                        );
                        const isMedia = ['IMG', 'VIDEO', 'CANVAS'].includes(node.tagName);
                        if (!hasKeyword && !hasInterestingStyle && !isMedia) {
                            continue;
                        }

                        const selector = buildSelector(node);
                        if (!selectors.includes(selector)) {
                            selectors.push(selector);
                        }
                    }

                    for (const selector of payload.linkedSelectors || []) {
                        try {
                            if (selector && (element.matches(selector) || element.querySelector(selector))) {
                                if (!selectors.includes(selector)) {
                                    selectors.push(selector);
                                }
                            }
                        } catch (error) {
                            // Ignore invalid selectors from heuristic media linkage.
                        }
                    }

                    return selectors.slice(0, 16);
                }
                """,
                {"linkedSelectors": linked_selectors},
            )
        except Exception:
            self.last_limitations.append(
                "Could not determine the selector set for the runtime scroll probe."
            )
            return ["__target__"]

        return selectors or ["__target__"]

    def _collect_overlay_selectors(self, rich_media: list[Any]) -> list[str]:
        """Return document-level rich media selectors that should be observed during probe."""
        overlay_selectors: list[str] = []
        for media in rich_media:
            if not getattr(media, "document_level", False):
                continue
            selector = getattr(media, "selector", "")
            if selector and selector not in overlay_selectors:
                overlay_selectors.append(selector)
        return overlay_selectors

    def _create_probe_dirs(self) -> tuple[Path, Path]:
        """Create one timestamped directory for the current probe run."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recording_dir = self.probe_dir / timestamp
        frames_dir = recording_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        return recording_dir, frames_dir

    async def _capture_probe_frame(
        self,
        target: Locator,
        mode: ExtractionMode,
        frame_path: Path,
    ) -> None:
        """Capture one frame for the current probe step."""
        await self.page.screenshot(path=str(frame_path))

    def _capture_probe_states_script(self) -> str:
        """Return the JS that snapshots tracked elements at one scroll position."""
        return """
            (element, payload) => {
                function serialize(node, selector, stepScope) {
                    if (!node) {
                        return {
                            selector,
                            scope: stepScope,
                            present: false,
                        };
                    }

                    const style = getComputedStyle(node);
                    const rect = node.getBoundingClientRect();
                    return {
                        selector,
                        scope: stepScope,
                        present: true,
                        tag: node.tagName.toLowerCase(),
                        classes: Array.from(node.classList),
                        opacity: style.opacity,
                        transform: style.transform,
                        filter: style.filter,
                        clip_path: style.clipPath,
                        mask_image: style.maskImage,
                        bounding_box: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                        },
                    };
                }

                const states = [];
                for (const selector of payload.trackedSelectors || []) {
                    let node = null;
                    if (selector === '__target__') {
                        node = element;
                    } else {
                        try {
                            node = element.querySelector(selector);
                        } catch (error) {
                            node = null;
                        }
                    }
                    states.push(serialize(node, selector, 'target'));
                }

                for (const selector of payload.overlaySelectors || []) {
                    let node = null;
                    try {
                        node = document.querySelector(selector);
                    } catch (error) {
                        node = null;
                    }
                    states.push(serialize(node, selector, 'document'));
                }

                return states;
            }
        """

    def _summarize_probe_states(
        self,
        states_by_selector: dict[str, list[dict[str, Any]]],
        rich_media: list[Any],
        key_frames: list[int],
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Convert raw per-step states into prompt-ready observations."""
        state_changes: list[dict[str, Any]] = []
        observations: list[str] = []

        for selector, states in states_by_selector.items():
            meaningful_states = [state for state in states if state.get("present")]
            if len(meaningful_states) < 2:
                continue

            property_changes: dict[str, Any] = {}
            changed_steps: list[int] = []
            first_state = meaningful_states[0]
            last_state = meaningful_states[-1]

            opacity_values = self._extract_numeric_series(meaningful_states, "opacity")
            if opacity_values and max(opacity_values) - min(opacity_values) > 0.05:
                property_changes["opacity"] = {
                    "first": first_state.get("opacity"),
                    "last": last_state.get("opacity"),
                    "min": min(opacity_values),
                    "max": max(opacity_values),
                }
                changed_steps.extend(
                    index for index, value in enumerate(opacity_values)
                    if abs(value - opacity_values[0]) > 0.05
                )

            for property_name in ("transform", "filter", "clip_path", "mask_image"):
                first_value = first_state.get(property_name)
                last_value = last_state.get(property_name)
                if first_value != last_value:
                    property_changes[property_name] = {
                        "first": first_value,
                        "last": last_value,
                    }
                    changed_steps.extend(
                        index
                        for index, state in enumerate(meaningful_states)
                        if state.get(property_name) != first_value
                    )

            first_classes = first_state.get("classes", [])
            last_classes = last_state.get("classes", [])
            if first_classes != last_classes:
                property_changes["class_list"] = {
                    "first": first_classes,
                    "last": last_classes,
                }
                changed_steps.extend(
                    index
                    for index, state in enumerate(meaningful_states)
                    if state.get("classes", []) != first_classes
                )

            box_series = [state.get("bounding_box", {}) for state in meaningful_states]
            y_values = [float(box.get("y", 0)) for box in box_series]
            if y_values and max(y_values) - min(y_values) > 24:
                property_changes["bounding_box"] = {
                    "first": box_series[0],
                    "last": box_series[-1],
                    "min_y": min(y_values),
                    "max_y": max(y_values),
                }
                changed_steps.extend(
                    index
                    for index, value in enumerate(y_values)
                    if abs(value - y_values[0]) > 24
                )

            if not property_changes:
                continue

            if set(property_changes.keys()) == {"bounding_box"}:
                continue

            first_changed = min(changed_steps) if changed_steps else 0
            peak_changed = max(changed_steps) if changed_steps else 0
            notes = self._build_selector_notes(selector, property_changes)

            state_changes.append(
                {
                    "selector": selector,
                    "property_changes": property_changes,
                    "first_changed_step": first_changed,
                    "peak_changed_step": peak_changed,
                    "notes": notes,
                }
            )
            observations.append(self._build_selector_observation(selector, property_changes))

        overlay_media = [
            media for media in rich_media if getattr(media, "document_level", False)
        ]
        if overlay_media and len(key_frames) > 1:
            observations.append(
                "Scroll probe confirmed visual changes across document-level overlay media while the observed scope moved through the viewport."
            )

        unique_observations: list[str] = []
        for observation in observations:
            if observation and observation not in unique_observations:
                unique_observations.append(observation)

        return unique_observations, state_changes

    def _extract_numeric_series(
        self,
        states: list[dict[str, Any]],
        property_name: str,
    ) -> list[float]:
        """Convert a property series to floats when possible."""
        values: list[float] = []
        for state in states:
            raw_value = state.get(property_name)
            try:
                values.append(float(raw_value))
            except (TypeError, ValueError):
                return []
        return values

    def _build_selector_notes(
        self,
        selector: str,
        property_changes: dict[str, Any],
    ) -> list[str]:
        """Build structured notes for one selector's change summary."""
        notes: list[str] = []
        if "opacity" in property_changes:
            notes.append("Opacity changed during viewport scroll.")
        if "transform" in property_changes:
            notes.append("Transform changed during viewport scroll.")
        if "bounding_box" in property_changes and selector != "__target__":
            notes.append("Element position shifted relative to the viewport.")
        if "mask_image" in property_changes or "clip_path" in property_changes:
            notes.append("A clipping or masking effect changed across scroll steps.")
        return notes

    def _build_selector_observation(
        self,
        selector: str,
        property_changes: dict[str, Any],
    ) -> str:
        """Convert one selector's changes into a short sentence."""
        changed_props = [prop.replace("_", " ") for prop in property_changes.keys()]
        pretty_selector = "target root" if selector == "__target__" else f"`{selector}`"
        return f"{pretty_selector} changes with scroll in: {', '.join(changed_props)}."

    def _detect_key_frames(self, frames_dir: Path, frame_count: int) -> list[int]:
        """Detect frames with visible changes using OpenCV when available."""
        key_frames = [0]
        if frame_count <= 1:
            return key_frames

        try:
            import cv2
            import numpy as np
        except ImportError:
            return self._detect_key_frames_simple(frames_dir, frame_count)

        threshold = 18
        prev_frame = cv2.imread(str(frames_dir / "frame_0000.png"), cv2.IMREAD_GRAYSCALE)
        if prev_frame is None:
            return key_frames

        for index in range(1, frame_count):
            curr_frame = cv2.imread(
                str(frames_dir / f"frame_{index:04d}.png"),
                cv2.IMREAD_GRAYSCALE,
            )
            if curr_frame is None:
                continue

            if prev_frame.shape != curr_frame.shape:
                curr_frame = cv2.resize(curr_frame, (prev_frame.shape[1], prev_frame.shape[0]))

            diff = cv2.absdiff(prev_frame, curr_frame)
            if float(np.mean(diff)) > threshold:
                key_frames.append(index)

            prev_frame = curr_frame

        return key_frames

    def _detect_key_frames_simple(self, frames_dir: Path, frame_count: int) -> list[int]:
        """Detect key frames using file-size differences when OpenCV is unavailable."""
        key_frames = [0]
        sizes: list[tuple[int, int]] = []
        for index in range(frame_count):
            frame_path = frames_dir / f"frame_{index:04d}.png"
            if frame_path.exists():
                sizes.append((index, frame_path.stat().st_size))

        for index in range(1, len(sizes)):
            previous_size = sizes[index - 1][1]
            current_size = sizes[index][1]
            if previous_size <= 0:
                continue
            if abs(current_size - previous_size) / previous_size > 0.03:
                key_frames.append(sizes[index][0])

        return key_frames

    def _encode_video(
        self,
        frames_dir: Path,
        recording_dir: Path,
        fps: int,
    ) -> Path | None:
        """Encode the captured frames into a WebM file when ffmpeg is available."""
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            self.last_limitations.append(
                "ffmpeg is unavailable; kept scroll probe frames without encoding a WebM video."
            )
            return None

        video_path = recording_dir / "recording.webm"
        command = [
            ffmpeg_path,
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(frames_dir / "frame_%04d.png"),
            "-c:v",
            "libvpx-vp9",
            "-pix_fmt",
            "yuv420p",
            str(video_path),
        ]

        try:
            subprocess.run(
                command,
                capture_output=True,
                check=True,
                text=True,
            )
        except Exception:
            self.last_limitations.append(
                "ffmpeg failed to encode the scroll probe video; kept frames only."
            )
            return None

        return video_path

    def _empty_summary(
        self,
        context_label: str,
        probe_range: dict[str, float],
        rich_media: list[Any],
    ) -> dict[str, Any]:
        """Return a stable summary when no meaningful probe steps are possible."""
        return {
            "context": context_label,
            "triggered": False,
            "range_start": probe_range.get("range_start", 0),
            "range_end": probe_range.get("range_end", 0),
            "step_count": 0,
            "fps": self.FPS,
            "frames_dir": None,
            "video_path": None,
            "key_frames": [],
            "tracked_selectors": ["__target__"],
            "overlay_selectors": self._collect_overlay_selectors(rich_media),
            "observations": [],
            "state_changes": [],
            "limitations": list(self.last_limitations),
        }
