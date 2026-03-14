"""Pipeline orchestrator for component extraction."""

import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from playwright.sync_api import Locator

from collector import (
    BrowserManager,
    TargetFinder,
    AnimationRecorder,
    LibraryDetector,
    ResponsiveCollector,
    InteractionMapper,
    InteractionPlayer,
    AssetDownloader,
)
from collector.dom_extractor import DOMExtractor
from collector.style_extractor import StyleExtractor
from normalizer import ContextBuilder
from synthesizer import OpenAISynthesizer
from models.errors import ExtractionError
from models.extraction import SelectorStrategy
from models.synthesis import SynthesisOutput


class ExtractionOrchestrator:
    """Coordinate the complete extraction pipeline."""

    PROGRESS_STEPS = [
        (0, "Connecting to browser"),
        (1, "Locating component"),
        (2, "Extracting DOM"),
        (3, "Extracting styles"),
        (4, "Mapping interactions"),
        (5, "Executing interactions"),
        (6, "Recording animations"),
        (7, "Downloading assets"),
        (8, "Detecting libraries"),
        (9, "Analyzing responsiveness"),
        (10, "Normalizing data"),
        (11, "Generating prompt with AI"),
    ]

    def __init__(self, api_key: str, output_dir: str = "output"):
        self.api_key = api_key
        self.output_dir = output_dir
        self.browser = BrowserManager()
        self.synthesizer = OpenAISynthesizer(api_key)
        self._cancelled = False

    def extract(
        self,
        url: str,
        strategy: str,
        query: str,
        progress_callback: Callable[[int, str], None] | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> SynthesisOutput:
        """Execute complete extraction pipeline."""
        cancel_check = cancel_check or (lambda: False)

        try:
            # Start browser
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 0)
            self.browser.start()
            self.browser.navigate(url)

            # Find target
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 1)
            strategy_enum = SelectorStrategy(strategy)
            finder = TargetFinder(self.browser.page)
            target = finder.find(strategy_enum, query)

            # Extract DOM
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 2)
            dom_extractor = DOMExtractor(self.browser.page)
            dom_data = dom_extractor.extract(target)

            # Extract styles
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 3)
            style_extractor = StyleExtractor(self.browser.page)
            style_data = style_extractor.extract(target)

            # Map interactions
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 4)
            interaction_mapper = InteractionMapper(self.browser.page)
            interactions = interaction_mapper.map(target)

            # Play interactions
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 5)
            interaction_player = InteractionPlayer(self.browser.page)
            observed_states = interaction_player.play_all(target, interactions)

            # Record animations
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 6)
            animation_recorder = AnimationRecorder(self.browser.page, self.output_dir)
            animation_data = animation_recorder.record(target)

            # Download assets
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 7)
            asset_downloader = AssetDownloader(self.browser.page, self.output_dir)
            assets = asset_downloader.download_all(target)

            # Detect libraries
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 8)
            library_detector = LibraryDetector(self.browser.page)
            libraries = library_detector.detect()

            # Collect responsive data
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 9)
            responsive_collector = ResponsiveCollector(self.browser.page)
            responsive_data = responsive_collector.collect_all(target)

            # Normalize data
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 10)
            context_builder = ContextBuilder()
            extraction_data = {
                "page": {
                    "url": self.browser.page.url,
                    "title": self.browser.page.title(),
                    "viewport": self.browser.page.viewport_size,
                    "loaded_scripts": self._get_loaded_scripts(),
                    "loaded_stylesheets": self._get_loaded_stylesheets(),
                },
                "target": {
                    "selector_used": query,
                    "strategy": strategy,
                    "html": dom_data["html"],
                    "bounding_box": dom_data["bounding_box"],
                    "depth": dom_data["depth"],
                },
                "dom_tree": dom_data["dom_tree"],
                "styles": style_data["computed_styles"],
                "assets": [a.model_dump() for a in assets],
                "interactions": {
                    **interactions,
                    "observed_states": observed_states,
                },
                "animations": {
                    "animations": style_data["animations"],
                    "transitions": style_data["transitions"],
                    "keyframes": style_data["keyframes"],
                    "recording": animation_data.model_dump() if animation_data else None,
                },
                "responsive": responsive_data.model_dump(),
                "libraries": [lib.model_dump() for lib in libraries],
            }

            normalized = context_builder.build(extraction_data)

            # Save normalized JSON
            self._save_normalized(normalized)

            # Synthesize with AI
            self._check_cancelled(cancel_check)
            self._report_progress(progress_callback, 11)
            synthesis = self.synthesizer.synthesize(normalized)

            return synthesis

        finally:
            self.browser.close()

    def cancel(self):
        """Cancel the extraction."""
        self._cancelled = True

    def _check_cancelled(self, cancel_check: Callable[[], bool]):
        """Check if extraction should be cancelled."""
        if self._cancelled or cancel_check():
            raise ExtractionError("Cancelled by user")

    def _report_progress(
        self, callback: Callable[[int, str], None] | None, step: int
    ):
        """Report progress if callback provided."""
        if callback:
            _, message = self.PROGRESS_STEPS[step]
            callback(step, message)

    def _get_loaded_scripts(self) -> list[str]:
        """Get list of loaded script URLs."""
        return self.browser.page.evaluate("""() => {
            return Array.from(document.querySelectorAll('script[src]'))
                .map(s => s.src);
        }""")

    def _get_loaded_stylesheets(self) -> list[str]:
        """Get list of loaded stylesheet URLs."""
        return self.browser.page.evaluate("""() => {
            return Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
                .map(l => l.href);
        }""")

    def _save_normalized(self, normalized):
        """Save normalized data to JSON file."""
        extractions_dir = Path(self.output_dir) / "extractions"
        extractions_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"extraction_{timestamp}.json"
        filepath = extractions_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(normalized.model_dump(), f, indent=2, ensure_ascii=False)
