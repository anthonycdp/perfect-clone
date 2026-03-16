"""Tests for ExtractionOrchestrator."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from PIL import Image

import orchestrator as orchestrator_module
from collector.extraction_scope import ExtractionScope
from models.extraction import BoundingBox
from models.normalized import (
    AnimationSummary,
    DOMTree,
    FullPageNormalizedOutput,
    InteractionSummary,
    NormalizedOutput,
    PageCaptureInfo,
    PageInfo,
    ResponsiveBehavior,
    StyleSummary,
    TargetInfo,
)
from models.synthesis import (
    ComponentDescription,
    ComponentTree,
    Dependency,
    ResponsiveRule,
    SynthesisOutput,
)

pytestmark = pytest.mark.asyncio


def build_synthesis_output() -> SynthesisOutput:
    """Create a valid synthesis output."""
    return SynthesisOutput(
        description=ComponentDescription(
            technical="Technical",
            visual="Visual",
            purpose="Purpose",
        ),
        component_tree=ComponentTree(name="LandingPage", role="page", children=[]),
        interactions=[],
        responsive_rules=[ResponsiveRule(breakpoint="768px", changes=["stack"])],
        dependencies=[Dependency(name="None", reason="No dependency")],
        recreation_prompt="Build the landing page",
    )


def build_full_page_output() -> FullPageNormalizedOutput:
    """Create a minimal full-page normalized output."""
    return FullPageNormalizedOutput(
        page=PageInfo(
            url="https://example.com",
            title="Landing",
            viewport={"width": 1440, "height": 900},
            loaded_scripts=[],
            loaded_stylesheets=[],
        ),
        page_capture=PageCaptureInfo(
            html="<body><section>Hero</section></body>",
            screenshot_path="/tmp/page.png",
            bounding_box=BoundingBox(x=0, y=0, width=1440, height=3200),
            scroll_completed=True,
            sections=[],
        ),
        dom=DOMTree(
            tag="body",
            attributes={},
            children=[],
            text_content="",
            computed_styles={},
        ),
        styles=StyleSummary(layout={}, spacing={}, typography={}, colors={}, effects={}),
        animations=AnimationSummary(
            css_animations=[],
            css_transitions=[],
            scroll_effects=[],
            recording=None,
        ),
        interactions=InteractionSummary(
            hoverable_elements=[],
            clickable_elements=[],
            focusable_elements=[],
            scroll_containers=[],
            observed_states={},
        ),
        responsive_behavior=ResponsiveBehavior(
            breakpoints=[],
            is_fluid=True,
            has_mobile_menu=False,
            grid_changes=[],
        ),
        assets=[],
        external_libraries=[],
    )


class FakeSynthesizer:
    """Test double for the OpenAI synthesizer."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.calls = []

    def synthesize(self, normalized_data):
        self.calls.append(normalized_data)
        return build_synthesis_output()


async def test_extract_full_page_skips_target_lookup(monkeypatch):
    """Full-page mode should not use TargetFinder and should return synthesis output."""
    monkeypatch.setattr(orchestrator_module, "OpenAISynthesizer", FakeSynthesizer)

    page = Mock()
    page.url = "https://example.com"
    page.title = AsyncMock(return_value="Landing")
    page.viewport_size = {"width": 1440, "height": 900}
    page.evaluate = AsyncMock(
        side_effect=[
            ["https://cdn.example.com/app.js"],
            ["https://cdn.example.com/app.css"],
        ]
    )
    body_locator = Mock()
    body_locator.first = body_locator
    page.locator.return_value = body_locator
    page.wait_for_timeout = AsyncMock()
    page.wait_for_load_state = AsyncMock()

    browser = Mock()
    browser.page = page
    browser.start = AsyncMock()
    browser.navigate = AsyncMock()
    browser.close = AsyncMock()

    orchestrator = orchestrator_module.ExtractionOrchestrator(api_key="test-key")
    orchestrator.browser = browser
    orchestrator._load_lazy_content = AsyncMock(return_value=True)
    full_page_scope = ExtractionScope(
        page=page,
        frame=Mock(),
        target=body_locator,
        selector_used="body",
        strategy="css",
        frame_url="https://example.com",
        frame_name=None,
        same_origin_accessible=True,
        document_base_url="https://example.com",
        within_shadow_dom=False,
    )
    orchestrator._resolve_full_page_root = AsyncMock(
        return_value=(body_locator, full_page_scope)
    )
    orchestrator._capture_full_page_screenshot = AsyncMock(return_value="/tmp/page.png")
    orchestrator._extract_document_bounding_box = AsyncMock(
        return_value={"x": 0, "y": 0, "width": 1440, "height": 3200}
    )
    orchestrator._build_page_metadata = AsyncMock(
        return_value={
            "url": "https://example.com",
            "title": "Landing",
            "viewport": {"width": 1440, "height": 900},
            "loaded_scripts": ["https://cdn.example.com/app.js"],
            "loaded_stylesheets": ["https://cdn.example.com/app.css"],
        }
    )
    orchestrator._extract_page_sections = AsyncMock(return_value=[])
    orchestrator._save_normalized = Mock()

    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("TargetFinder should not be used in full_page mode")

    monkeypatch.setattr(orchestrator_module.TargetFinder, "find", fail_if_called)

    class FakeDOMExtractor:
        def __init__(self, _page):
            pass

        async def extract(self, _target):
            return {
                "html": "<body><section>Hero</section></body>",
                "dom_tree": {
                    "tag": "body",
                    "attributes": {},
                    "children": [],
                    "text_content": "",
                    "computed_styles": {},
                },
                "bounding_box": {"x": 0, "y": 0, "width": 1440, "height": 3200},
                "depth": 0,
            }

    class FakeStyleExtractor:
        def __init__(self, _page):
            pass

        async def extract(self, _target, scope=None):
            return {
                "computed_styles": {"display": "block"},
                "animations": [],
                "transitions": [],
                "keyframes": {},
            }

    class FakeInteractionMapper:
        def __init__(self, _page):
            pass

        async def map(self, _target):
            return {
                "hoverable": [],
                "clickable": [],
                "focusable": [],
                "scroll_containers": [],
            }

    class FakeInteractionPlayer:
        def __init__(self, _page):
            pass

        async def play_all(self, _target, _interactions, scope=None):
            return []

    class FakeAnimationRecorder:
        def __init__(self, _page, _output_dir):
            pass

        async def record(self, _target):
            return None

    class FakeAssetDownloader:
        def __init__(self, _page, _output_dir, scope=None):
            self.last_limitations = []

        async def download_all(self, _target):
            return []

    class FakeRichMediaCollector:
        def __init__(self, _page, _output_dir, scope=None):
            self.last_limitations = []

        async def collect(self, _target):
            return []

    class FakeScrollProbeCollector:
        def __init__(self, _page, _output_dir):
            self.last_limitations = []

        async def collect(self, _target, mode, scope=None, rich_media=None):
            return {
                "context": "page",
                "triggered": False,
                "range_start": 0,
                "range_end": 0,
                "step_count": 0,
                "fps": 12,
                "frames_dir": None,
                "video_path": None,
                "key_frames": [],
                "tracked_selectors": ["__target__"],
                "overlay_selectors": [],
                "observations": [],
                "state_changes": [],
                "limitations": [],
            }

    class FakeLibraryDetector:
        def __init__(self, _page):
            self.last_limitations = []

        async def detect(self, scope=None):
            return []

    class FakeResponsiveCollector:
        def __init__(self, _page):
            pass

        async def collect_all(self, _target, scope=None):
            return SimpleNamespace(
                model_dump=lambda: {
                    "breakpoints": [],
                    "is_fluid": True,
                    "has_mobile_menu": False,
                    "grid_changes": [],
                }
            )

    class FakeContextBuilder:
        def build(self, extraction_data):
            assert extraction_data["mode"] == "full_page"
            assert extraction_data["page_capture"]["screenshot_path"] == "/tmp/page.png"
            return build_full_page_output()

    monkeypatch.setattr(orchestrator_module, "DOMExtractor", FakeDOMExtractor)
    monkeypatch.setattr(orchestrator_module, "StyleExtractor", FakeStyleExtractor)
    monkeypatch.setattr(orchestrator_module, "InteractionMapper", FakeInteractionMapper)
    monkeypatch.setattr(orchestrator_module, "InteractionPlayer", FakeInteractionPlayer)
    monkeypatch.setattr(orchestrator_module, "AnimationRecorder", FakeAnimationRecorder)
    monkeypatch.setattr(orchestrator_module, "AssetDownloader", FakeAssetDownloader)
    monkeypatch.setattr(orchestrator_module, "RichMediaCollector", FakeRichMediaCollector)
    monkeypatch.setattr(orchestrator_module, "ScrollProbeCollector", FakeScrollProbeCollector)
    monkeypatch.setattr(orchestrator_module, "LibraryDetector", FakeLibraryDetector)
    monkeypatch.setattr(orchestrator_module, "ResponsiveCollector", FakeResponsiveCollector)
    monkeypatch.setattr(orchestrator_module, "ContextBuilder", FakeContextBuilder)

    result = await orchestrator.extract("https://example.com", extraction_mode="full_page")

    assert result.recreation_prompt == "Build the landing page"
    assert orchestrator.last_normalized_output.mode.value == "full_page"
    browser.start.assert_awaited_once()
    browser.navigate.assert_awaited_once_with("https://example.com")
    browser.close.assert_awaited_once()


async def test_capture_target_screenshot_clips_oversized_elements(tmp_path):
    """Oversized targets should use a viewport-clipped page screenshot."""
    orchestrator = orchestrator_module.ExtractionOrchestrator(
        api_key="test-key",
        output_dir=str(tmp_path),
    )
    page = Mock()
    page.viewport_size = {"width": 1280, "height": 900}
    page.screenshot = AsyncMock()
    orchestrator.browser = Mock(page=page)

    target = Mock()
    target.scroll_into_view_if_needed = AsyncMock()
    target.bounding_box = AsyncMock(
        return_value={"x": 0, "y": 0, "width": 1280, "height": 3150}
    )
    target.screenshot = AsyncMock()

    screenshot_path = await orchestrator._capture_target_screenshot(target)

    assert screenshot_path is not None
    page.screenshot.assert_awaited_once()
    assert page.screenshot.await_args.kwargs["clip"] == {
        "x": 0.0,
        "y": 0.0,
        "width": 1280.0,
        "height": 900.0,
    }
    target.screenshot.assert_not_awaited()


async def test_capture_target_screenshot_keeps_locator_capture_for_normal_size_elements(
    tmp_path,
):
    """Normal-sized targets should still use locator.screenshot()."""
    orchestrator = orchestrator_module.ExtractionOrchestrator(
        api_key="test-key",
        output_dir=str(tmp_path),
    )
    page = Mock()
    page.viewport_size = {"width": 1280, "height": 900}
    page.screenshot = AsyncMock()
    orchestrator.browser = Mock(page=page)

    target = Mock()
    target.scroll_into_view_if_needed = AsyncMock()
    target.bounding_box = AsyncMock(
        return_value={"x": 100, "y": 80, "width": 420, "height": 240}
    )
    target.screenshot = AsyncMock()

    screenshot_path = await orchestrator._capture_target_screenshot(target)

    assert screenshot_path is not None
    page.screenshot.assert_not_awaited()
    target.screenshot.assert_awaited_once()


async def test_resolve_component_visual_reference_promotes_scroll_probe_frame(tmp_path):
    """Runtime-heavy components should promote a scroll-probe frame to primary screenshot."""
    orchestrator = orchestrator_module.ExtractionOrchestrator(
        api_key="test-key",
        output_dir=str(tmp_path),
    )
    element_screenshot = tmp_path / "screenshots" / "target.png"
    probe_frames = tmp_path / "animations" / "scroll_probe" / "frames"
    promoted_source = probe_frames / "frame_0003.png"
    element_screenshot.parent.mkdir(parents=True, exist_ok=True)
    probe_frames.mkdir(parents=True, exist_ok=True)
    element_screenshot.write_bytes(b"raw")
    promoted_source.write_bytes(b"probe")

    screenshot_path, visual_reference = orchestrator._resolve_component_visual_reference(
        element_screenshot_path=str(element_screenshot),
        scroll_probe={
            "triggered": True,
            "frames_dir": str(probe_frames),
            "key_frames": [3, 7],
        },
        runtime_scroll_effects=["Document-level media changes during scroll."],
        rich_media=[{"type": "webgl", "document_level": True}],
    )

    assert screenshot_path == str(
        (tmp_path / "screenshots" / "visual_reference.png").resolve()
    )
    assert visual_reference["promoted"] is True
    assert visual_reference["source"] == "scroll_probe_frame"
    assert visual_reference["source_path"] == str(promoted_source.resolve())
    assert (tmp_path / "screenshots" / "visual_reference.png").read_bytes() == b"probe"


async def test_resolve_full_page_visual_reference_promotes_section_overview(tmp_path):
    """Whitespace-dominated page screenshots should be replaced by a stitched section overview."""
    orchestrator = orchestrator_module.ExtractionOrchestrator(
        api_key="test-key",
        output_dir=str(tmp_path),
    )
    raw_page = tmp_path / "screenshots" / "page.png"
    section_one = tmp_path / "sections" / "section-01" / "screenshot.png"
    section_two = tmp_path / "sections" / "section-02" / "screenshot.png"
    raw_page.parent.mkdir(parents=True, exist_ok=True)
    section_one.parent.mkdir(parents=True, exist_ok=True)
    section_two.parent.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 3000), "white").save(raw_page)
    Image.new("RGB", (700, 300), "black").save(section_one)
    Image.new("RGB", (700, 500), "navy").save(section_two)

    resolved = orchestrator._resolve_full_page_visual_reference(
        str(raw_page),
        [
            {"screenshot_path": str(section_one)},
            {"screenshot_path": str(section_two)},
        ],
    )

    assert resolved == str(
        (tmp_path / "screenshots" / "page_visual_reference.png").resolve()
    )
    with Image.open(resolved) as stitched:
        assert stitched.width == 700
        assert stitched.height == 800


async def test_resolve_full_page_visual_reference_keeps_informative_capture(tmp_path):
    """Informative page screenshots should remain the primary full-page image."""
    orchestrator = orchestrator_module.ExtractionOrchestrator(
        api_key="test-key",
        output_dir=str(tmp_path),
    )
    raw_page = tmp_path / "screenshots" / "page.png"
    section_one = tmp_path / "sections" / "section-01" / "screenshot.png"
    raw_page.parent.mkdir(parents=True, exist_ok=True)
    section_one.parent.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 1200), "black").save(raw_page)
    Image.new("RGB", (700, 300), "navy").save(section_one)

    resolved = orchestrator._resolve_full_page_visual_reference(
        str(raw_page),
        [{"screenshot_path": str(section_one)}],
    )

    assert resolved == str(raw_page)


async def test_extract_component_passes_frame_scope(monkeypatch):
    """Component mode should propagate frame metadata and scope-aware collectors."""
    monkeypatch.setattr(orchestrator_module, "OpenAISynthesizer", FakeSynthesizer)

    page = Mock()
    page.url = "https://example.com"
    page.title = AsyncMock(return_value="Component")
    page.viewport_size = {"width": 1280, "height": 720}
    page.evaluate = AsyncMock(
        side_effect=[
            ["https://cdn.example.com/app.js"],
            ["https://cdn.example.com/app.css"],
        ]
    )

    browser = Mock()
    browser.page = page
    browser.start = AsyncMock()
    browser.navigate = AsyncMock()
    browser.close = AsyncMock()

    target = Mock()
    frame = Mock()
    frame.url = "https://example.com/embed"
    frame.name = "iframe-hero"
    scope = ExtractionScope(
        page=page,
        frame=frame,
        target=target,
        selector_used='//*[@id="hero"]',
        strategy="xpath",
        frame_url=frame.url,
        frame_name=frame.name,
        same_origin_accessible=True,
        document_base_url="https://example.com/embed",
        within_shadow_dom=True,
    )

    orchestrator = orchestrator_module.ExtractionOrchestrator(api_key="test-key")
    orchestrator.browser = browser
    orchestrator._capture_target_screenshot = AsyncMock(return_value="/tmp/target.png")
    orchestrator._save_normalized = Mock()

    class FakeDOMExtractor:
        def __init__(self, _page):
            pass

        async def extract(self, _target):
            return {
                "html": "<section id='hero'></section>",
                "dom_tree": {
                    "tag": "section",
                    "attributes": {"id": "hero"},
                    "children": [],
                    "text_content": "",
                    "computed_styles": {},
                },
                "bounding_box": {"x": 0, "y": 0, "width": 400, "height": 200},
                "depth": 3,
            }

    class FakeStyleExtractor:
        def __init__(self, _page):
            self.calls = []

        async def extract(self, _target, scope=None):
            self.calls.append(scope)
            return {
                "computed_styles": {"display": "block"},
                "animations": [],
                "transitions": [],
                "keyframes": {},
                "limitations": ["Could not extract keyframes from the target frame stylesheets."],
            }

    class FakeInteractionMapper:
        def __init__(self, _page):
            pass

        async def map(self, _target):
            return {
                "hoverable": [],
                "clickable": [{"selector": "button"}],
                "focusable": [],
                "scroll_containers": [],
            }

    class FakeInteractionPlayer:
        seen_scope = None

        def __init__(self, _page):
            pass

        async def play_all(self, _target, _interactions, scope=None):
            FakeInteractionPlayer.seen_scope = scope
            return []

    class FakeAnimationRecorder:
        def __init__(self, _page, _output_dir):
            pass

        async def record(self, _target):
            return None

    class FakeAssetDownloader:
        seen_scope = None

        def __init__(self, _page, _output_dir, scope=None):
            FakeAssetDownloader.seen_scope = scope
            self.last_limitations = ["Could not extract @font-face rules from the target frame stylesheets."]

        async def download_all(self, _target):
            return []

    class FakeRichMediaCollector:
        seen_scope = None

        def __init__(self, _page, _output_dir, scope=None):
            FakeRichMediaCollector.seen_scope = scope
            self.last_limitations = ["Canvas export fell back to screenshot."]

        async def collect(self, _target):
            return []

    class FakeScrollProbeCollector:
        def __init__(self, _page, _output_dir):
            self.last_limitations = []

        async def collect(self, _target, mode, scope=None, rich_media=None):
            assert mode.value == "component"
            assert scope is not None
            return {
                "context": "frame",
                "triggered": True,
                "range_start": 100,
                "range_end": 500,
                "step_count": 8,
                "fps": 12,
                "frames_dir": "/tmp/scroll_probe/frames",
                "video_path": "/tmp/scroll_probe/recording.webm",
                "key_frames": [0, 3, 7],
                "tracked_selectors": ["__target__", ".webgl-img"],
                "overlay_selectors": ["canvas"],
                "observations": ["Document-level overlay media changes across viewport scroll."],
                "state_changes": [],
                "limitations": [],
            }

    class FakeLibraryDetector:
        seen_scope = None

        def __init__(self, _page):
            self.last_limitations = ["Could not inspect external libraries in the frame document."]

        async def detect(self, scope=None):
            FakeLibraryDetector.seen_scope = scope
            return []

    class FakeResponsiveCollector:
        seen_scope = None

        def __init__(self, _page):
            pass

        async def collect_all(self, _target, scope=None):
            FakeResponsiveCollector.seen_scope = scope
            return SimpleNamespace(
                model_dump=lambda: {
                    "breakpoints": [],
                    "is_fluid": True,
                    "has_mobile_menu": False,
                    "grid_changes": [],
                }
            )

    class FakeContextBuilder:
        def build(self, extraction_data):
            assert extraction_data["target"]["frame_url"] == "https://example.com/embed"
            assert extraction_data["target"]["frame_name"] == "iframe-hero"
            assert extraction_data["target"]["same_origin_accessible"] is True
            assert extraction_data["target"]["within_shadow_dom"] is True
            assert extraction_data["target"]["frame_limitations"] == [
                "Could not extract keyframes from the target frame stylesheets.",
                "Could not extract @font-face rules from the target frame stylesheets.",
                "Could not inspect external libraries in the frame document.",
            ]
            assert extraction_data["collection_limitations"] == [
                "Could not extract keyframes from the target frame stylesheets.",
                "Could not extract @font-face rules from the target frame stylesheets.",
                "Canvas export fell back to screenshot.",
                "Could not inspect external libraries in the frame document.",
            ]
            assert extraction_data["animations"]["observed_scroll_effects"] == [
                "Document-level overlay media changes across viewport scroll."
            ]
            assert extraction_data["animations"]["scroll_probe"]["context"] == "frame"
            return NormalizedOutput(
                page=PageInfo(
                    url="https://example.com",
                    title="Component",
                    viewport={"width": 1280, "height": 720},
                    loaded_scripts=[],
                    loaded_stylesheets=[],
                ),
                target=TargetInfo(
                    selector_used='//*[@id="hero"]',
                    strategy="xpath",
                    html="<section id='hero'></section>",
                    bounding_box=BoundingBox(x=0, y=0, width=400, height=200),
                    depth_in_dom=3,
                    screenshot_path="/tmp/target.png",
                    frame_url="https://example.com/embed",
                    frame_name="iframe-hero",
                    same_origin_accessible=True,
                    within_shadow_dom=True,
                    frame_limitations=extraction_data["target"]["frame_limitations"],
                ),
                dom=DOMTree(
                    tag="section",
                    attributes={"id": "hero"},
                    children=[],
                    text_content="",
                    computed_styles={},
                ),
                styles=StyleSummary(layout={}, spacing={}, typography={}, colors={}, effects={}),
                animations=AnimationSummary(
                    css_animations=[],
                    css_transitions=[],
                    scroll_effects=[],
                    recording=None,
                ),
                interactions=InteractionSummary(
                    hoverable_elements=[],
                    clickable_elements=[],
                    focusable_elements=[],
                    scroll_containers=[],
                    observed_states={},
                ),
                responsive_behavior=ResponsiveBehavior(
                    breakpoints=[],
                    is_fluid=True,
                    has_mobile_menu=False,
                    grid_changes=[],
                ),
                assets=[],
                external_libraries=[],
            )

    monkeypatch.setattr(
        orchestrator_module.TargetFinder,
        "find",
        AsyncMock(return_value=scope),
    )
    monkeypatch.setattr(orchestrator_module, "DOMExtractor", FakeDOMExtractor)
    monkeypatch.setattr(orchestrator_module, "StyleExtractor", FakeStyleExtractor)
    monkeypatch.setattr(orchestrator_module, "InteractionMapper", FakeInteractionMapper)
    monkeypatch.setattr(orchestrator_module, "InteractionPlayer", FakeInteractionPlayer)
    monkeypatch.setattr(orchestrator_module, "AnimationRecorder", FakeAnimationRecorder)
    monkeypatch.setattr(orchestrator_module, "AssetDownloader", FakeAssetDownloader)
    monkeypatch.setattr(orchestrator_module, "RichMediaCollector", FakeRichMediaCollector)
    monkeypatch.setattr(orchestrator_module, "ScrollProbeCollector", FakeScrollProbeCollector)
    monkeypatch.setattr(orchestrator_module, "LibraryDetector", FakeLibraryDetector)
    monkeypatch.setattr(orchestrator_module, "ResponsiveCollector", FakeResponsiveCollector)
    monkeypatch.setattr(orchestrator_module, "ContextBuilder", FakeContextBuilder)

    result = await orchestrator.extract(
        "https://example.com",
        strategy="xpath",
        query='//*[@id="hero"]',
        extraction_mode="component",
    )

    assert result.recreation_prompt == "Build the landing page"
    assert FakeInteractionPlayer.seen_scope is scope
    assert FakeAssetDownloader.seen_scope is scope
    assert FakeRichMediaCollector.seen_scope is scope
    assert FakeLibraryDetector.seen_scope is scope
    assert FakeResponsiveCollector.seen_scope is scope


async def test_collect_full_page_data_includes_section_captures(monkeypatch):
    """Full-page raw extraction should embed enriched section captures and merge their limitations."""
    monkeypatch.setattr(orchestrator_module, "OpenAISynthesizer", FakeSynthesizer)

    body_locator = Mock()
    body_locator.first = body_locator

    page = Mock()
    page.url = "https://example.com"
    page.title = AsyncMock(return_value="Landing")
    page.viewport_size = {"width": 1440, "height": 900}
    page.evaluate = AsyncMock(side_effect=[[], []])
    page.locator.return_value = body_locator

    browser = Mock()
    browser.page = page
    browser.close = AsyncMock()

    orchestrator = orchestrator_module.ExtractionOrchestrator(api_key="test-key")
    orchestrator.browser = browser
    full_page_scope = ExtractionScope(
        page=page,
        frame=Mock(),
        target=body_locator,
        selector_used="body",
        strategy="css",
        frame_url="https://example.com",
        frame_name=None,
        same_origin_accessible=True,
        document_base_url="https://example.com",
        within_shadow_dom=False,
    )
    orchestrator._resolve_full_page_root = AsyncMock(
        return_value=(body_locator, full_page_scope)
    )
    orchestrator._load_lazy_content = AsyncMock(return_value=True)
    orchestrator._capture_full_page_screenshot = AsyncMock(return_value="/tmp/page.png")
    orchestrator._extract_document_bounding_box = AsyncMock(
        return_value={"x": 0, "y": 0, "width": 1440, "height": 3200}
    )
    orchestrator._build_page_metadata = AsyncMock(
        return_value={
            "url": "https://example.com",
            "title": "Landing",
            "viewport": {"width": 1440, "height": 900},
            "loaded_scripts": [],
            "loaded_stylesheets": [],
        }
    )
    orchestrator._extract_page_sections = AsyncMock(
        return_value=[
            {
                "section_id": "section-01-hero",
                "name": "Hero",
                "selector": "section.hero",
                "tag": "section",
                "text_excerpt": "Build faster",
                "bounding_box": {"x": 0, "y": 0, "width": 1440, "height": 640},
                "probe_selector": '[data-component-extractor-section-id="section-01-hero"]',
            }
        ]
    )
    orchestrator._collect_shared_target_data = AsyncMock(
        return_value={
            "assets": [],
            "interactions": {
                "hoverable": [],
                "clickable": [],
                "focusable": [],
                "scroll_containers": [],
                "observed_states": [],
            },
            "animation_recording": None,
            "scroll_probe": None,
            "runtime_scroll_effects": [],
            "responsive": {
                "breakpoints": [],
                "is_fluid": True,
                "has_mobile_menu": False,
                "grid_changes": [],
            },
            "libraries": [],
            "rich_media": [],
            "frame_limitations": [],
            "collection_limitations": ["Landing-level limitation"],
        }
    )
    orchestrator._collect_full_page_sections = AsyncMock(
        return_value=(
            [
                {
                    "section_id": "section-01-hero",
                    "name": "Hero",
                    "selector": "section.hero",
                    "tag": "section",
                    "text_excerpt": "Build faster",
                    "bounding_box": {"x": 0, "y": 0, "width": 1440, "height": 640},
                    "html": "<section class='hero'></section>",
                    "screenshot_path": "/tmp/sections/hero.png",
                    "interactions": {
                        "hoverable": [{"selector": ".hero-card"}],
                        "clickable": [{"selector": ".hero-cta"}],
                        "focusable": [],
                        "scroll_containers": [],
                        "observed_states": [],
                    },
                    "animations": {
                        "animations": [],
                        "transitions": [],
                        "keyframes": {},
                        "observed_scroll_effects": ["Hero media lifts on scroll."],
                        "recording": None,
                        "scroll_probe": None,
                    },
                    "rich_media": [],
                    "collection_limitations": ["Section limitation"],
                }
            ],
            ["Section limitation"],
        )
    )

    class FakeDOMExtractor:
        def __init__(self, _page):
            pass

        async def extract(self, _target):
            return {
                "html": "<body><section>Hero</section></body>",
                "dom_tree": {
                    "tag": "body",
                    "attributes": {},
                    "children": [],
                    "text_content": "",
                    "computed_styles": {},
                },
                "bounding_box": {"x": 0, "y": 0, "width": 1440, "height": 3200},
            }

    class FakeStyleExtractor:
        def __init__(self, _page):
            pass

        async def extract(self, _target, scope=None):
            return {
                "computed_styles": {"display": "block"},
                "animations": [],
                "transitions": [],
                "keyframes": {},
                "limitations": ["Style limitation"],
            }

    monkeypatch.setattr(orchestrator_module, "DOMExtractor", FakeDOMExtractor)
    monkeypatch.setattr(orchestrator_module, "StyleExtractor", FakeStyleExtractor)

    raw = await orchestrator._collect_full_page_data(
        initial_viewport={"width": 1440, "height": 900},
        progress_callback=None,
        cancel_check=lambda: False,
    )

    assert raw["page_capture"]["sections"][0]["section_id"] == "section-01-hero"
    assert raw["page_capture"]["sections"][0]["screenshot_path"] == "/tmp/sections/hero.png"
    assert raw["collection_limitations"] == [
        "Style limitation",
        "Landing-level limitation",
        "Section limitation",
    ]
