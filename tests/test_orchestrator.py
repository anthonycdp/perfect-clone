"""Tests for ExtractionOrchestrator."""

from types import SimpleNamespace
from unittest.mock import Mock

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


def build_synthesis_output() -> SynthesisOutput:
    """Create a valid synthesis output."""
    return SynthesisOutput(
        description=ComponentDescription(
            technical="Technical",
            visual="Visual",
            purpose="Purpose",
        ),
        component_tree=ComponentTree(
            name="LandingPage",
            role="page",
            children=[],
        ),
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
        styles=StyleSummary(
            layout={},
            spacing={},
            typography={},
            colors={},
            effects={},
        ),
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


def test_extract_full_page_skips_target_lookup(monkeypatch):
    """Full-page mode should not use TargetFinder and should return synthesis output."""
    monkeypatch.setattr(orchestrator_module, "OpenAISynthesizer", FakeSynthesizer)

    page = Mock()
    page.url = "https://example.com"
    page.title.return_value = "Landing"
    page.viewport_size = {"width": 1440, "height": 900}
    page.evaluate.side_effect = [
        ["https://cdn.example.com/app.js"],
        ["https://cdn.example.com/app.css"],
    ]
    page.locator.return_value = Mock(first=Mock())
    page.wait_for_timeout.return_value = None
    page.wait_for_load_state.return_value = None

    browser = Mock()
    browser.page = page

    orchestrator = orchestrator_module.ExtractionOrchestrator(api_key="test-key")
    orchestrator.browser = browser
    orchestrator._load_lazy_content = Mock(return_value=True)
    orchestrator._capture_page_screenshot = Mock(return_value="/tmp/page.png")
    orchestrator._extract_page_sections = Mock(return_value=[])
    orchestrator._save_normalized = Mock()

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("TargetFinder should not be used in full_page mode")

    monkeypatch.setattr(orchestrator_module.TargetFinder, "find", fail_if_called)

    class FakeDOMExtractor:
        def __init__(self, _page):
            pass

        def extract_page(self):
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

        def extract_page(self):
            return {
                "computed_styles": {"display": "block"},
                "animations": [],
                "transitions": [],
                "keyframes": {},
            }

    class FakeInteractionMapper:
        def __init__(self, _page):
            pass

        def map(self, _target):
            return {
                "hoverable": [],
                "clickable": [],
                "focusable": [],
                "scroll_containers": [],
            }

    class FakeInteractionPlayer:
        def __init__(self, _page):
            pass

        def play_all(self, _target, _interactions, scope=None):
            return []

    class FakeAnimationRecorder:
        def __init__(self, _page, _output_dir):
            pass

        def record(self, _target):
            return None

    class FakeAssetDownloader:
        def __init__(self, _page, _output_dir, scope=None):
            self.last_limitations = []

        def download_all(self, _target):
            return []

    class FakeRichMediaCollector:
        def __init__(self, _page, _output_dir, scope=None):
            self.last_limitations = []

        def collect(self, _target):
            return []

    class FakeLibraryDetector:
        def __init__(self, _page):
            self.last_limitations = []

        def detect(self, scope=None):
            return []

    class FakeResponsiveCollector:
        def __init__(self, _page):
            pass

        def collect_all(self, _target, scope=None):
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
    monkeypatch.setattr(orchestrator_module, "LibraryDetector", FakeLibraryDetector)
    monkeypatch.setattr(orchestrator_module, "ResponsiveCollector", FakeResponsiveCollector)
    monkeypatch.setattr(orchestrator_module, "ContextBuilder", FakeContextBuilder)

    result = orchestrator.extract(
        "https://example.com",
        extraction_mode="full_page",
    )

    assert result.recreation_prompt == "Build the landing page"
    assert orchestrator.last_normalized_output.mode.value == "full_page"
    browser.start.assert_called_once()
    browser.navigate.assert_called_once_with("https://example.com")
    browser.close.assert_called_once()


def test_extract_component_passes_frame_scope(monkeypatch):
    """Component mode should propagate frame metadata and scope-aware collectors."""
    monkeypatch.setattr(orchestrator_module, "OpenAISynthesizer", FakeSynthesizer)

    page = Mock()
    page.url = "https://example.com"
    page.title.return_value = "Component"
    page.viewport_size = {"width": 1280, "height": 720}
    page.evaluate.side_effect = [
        ["https://cdn.example.com/app.js"],
        ["https://cdn.example.com/app.css"],
    ]

    browser = Mock()
    browser.page = page

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
    orchestrator._capture_target_screenshot = Mock(return_value="/tmp/target.png")
    orchestrator._save_normalized = Mock()

    class FakeDOMExtractor:
        def __init__(self, _page):
            pass

        def extract(self, _target):
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

        def extract(self, _target, scope=None):
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

        def map(self, _target):
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

        def play_all(self, _target, _interactions, scope=None):
            FakeInteractionPlayer.seen_scope = scope
            return []

    class FakeAnimationRecorder:
        def __init__(self, _page, _output_dir):
            pass

        def record(self, _target):
            return None

    class FakeAssetDownloader:
        seen_scope = None

        def __init__(self, _page, _output_dir, scope=None):
            FakeAssetDownloader.seen_scope = scope
            self.last_limitations = ["Could not extract @font-face rules from the target frame stylesheets."]

        def download_all(self, _target):
            return []

    class FakeRichMediaCollector:
        seen_scope = None

        def __init__(self, _page, _output_dir, scope=None):
            FakeRichMediaCollector.seen_scope = scope
            self.last_limitations = ["Canvas export fell back to screenshot."]

        def collect(self, _target):
            return []

    class FakeLibraryDetector:
        seen_scope = None

        def __init__(self, _page):
            self.last_limitations = ["Could not inspect external libraries in the frame document."]

        def detect(self, scope=None):
            FakeLibraryDetector.seen_scope = scope
            return []

    class FakeResponsiveCollector:
        seen_scope = None

        def __init__(self, _page):
            pass

        def collect_all(self, _target, scope=None):
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
                styles=StyleSummary(
                    layout={},
                    spacing={},
                    typography={},
                    colors={},
                    effects={},
                ),
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

    monkeypatch.setattr(orchestrator_module.TargetFinder, "find", Mock(return_value=scope))
    monkeypatch.setattr(orchestrator_module, "DOMExtractor", FakeDOMExtractor)
    monkeypatch.setattr(orchestrator_module, "StyleExtractor", FakeStyleExtractor)
    monkeypatch.setattr(orchestrator_module, "InteractionMapper", FakeInteractionMapper)
    monkeypatch.setattr(orchestrator_module, "InteractionPlayer", FakeInteractionPlayer)
    monkeypatch.setattr(orchestrator_module, "AnimationRecorder", FakeAnimationRecorder)
    monkeypatch.setattr(orchestrator_module, "AssetDownloader", FakeAssetDownloader)
    monkeypatch.setattr(orchestrator_module, "RichMediaCollector", FakeRichMediaCollector)
    monkeypatch.setattr(orchestrator_module, "LibraryDetector", FakeLibraryDetector)
    monkeypatch.setattr(orchestrator_module, "ResponsiveCollector", FakeResponsiveCollector)
    monkeypatch.setattr(orchestrator_module, "ContextBuilder", FakeContextBuilder)

    result = orchestrator.extract(
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
