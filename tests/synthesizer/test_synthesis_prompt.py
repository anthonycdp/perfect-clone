"""Tests for synthesis prompt builders."""

from models.extraction import BoundingBox, ExtractionMode, SelectorStrategy
from models.normalized import (
    AnimationSummary,
    DOMTree,
    FullPageNormalizedOutput,
    InteractionSummary,
    NormalizedOutput,
    PageCaptureInfo,
    PageInfo,
    PageSectionSummary,
    ResponsiveBehavior,
    ScrollProbeStateChange,
    ScrollProbeSummary,
    StyleSummary,
    TargetInfo,
)
from synthesizer.prompts.synthesis_prompt import build_user_prompt


def build_page_info() -> PageInfo:
    """Create a shared page info fixture."""
    return PageInfo(
        url="https://example.com",
        title="Example",
        viewport={"width": 1440, "height": 900},
        loaded_scripts=[],
        loaded_stylesheets=[],
    )


def build_shared_fields() -> dict:
    """Create the shared normalized output fields."""
    return {
        "page": build_page_info(),
        "dom": DOMTree(
            tag="div",
            attributes={},
            children=[],
            text_content="",
            computed_styles={},
        ),
        "styles": StyleSummary(
            layout={},
            spacing={},
            typography={},
            colors={},
            effects={},
        ),
        "animations": AnimationSummary(
            css_animations=[],
            css_transitions=[],
            scroll_effects=[],
            recording=None,
        ),
        "interactions": InteractionSummary(
            hoverable_elements=[],
            clickable_elements=[],
            focusable_elements=[],
            scroll_containers=[],
            observed_states={},
        ),
        "responsive_behavior": ResponsiveBehavior(
            breakpoints=[],
            is_fluid=True,
            has_mobile_menu=False,
            grid_changes=[],
        ),
        "assets": [],
        "external_libraries": [],
    }


def test_build_user_prompt_for_component():
    """Component mode should keep the target component section in the prompt."""
    output = NormalizedOutput(
        **build_shared_fields(),
        target=TargetInfo(
            selector_used=".hero",
            strategy=SelectorStrategy.CSS,
            html="<section class='hero'></section>",
            bounding_box=BoundingBox(x=0, y=0, width=1200, height=600),
            depth_in_dom=2,
            screenshot_path=None,
            frame_url="https://example.com/embed",
            frame_name="marketing-frame",
            same_origin_accessible=False,
            within_shadow_dom=True,
            frame_limitations=["Could not inspect external libraries in the frame document."],
        ),
        collection_limitations=["Canvas export fell back to screenshot."],
        rich_media=[],
    )

    prompt = build_user_prompt(output)

    assert "## Package Context" in prompt
    assert "## Target Component" in prompt
    assert "Selector: .hero" in prompt
    assert "Frame URL: https://example.com/embed" in prompt
    assert "Same Origin Accessible: False" in prompt
    assert "Within Shadow DOM: True" in prompt
    assert "## Frame Limitations" in prompt
    assert "## Collection Limitations" in prompt


def test_build_user_prompt_includes_document_level_rich_media_effects():
    """Component prompts should surface document-level WebGL overlay behavior."""
    shared_fields = build_shared_fields()
    shared_fields["animations"] = AnimationSummary(
        css_animations=[],
        css_transitions=[],
        scroll_effects=[
            "Document-level WebGL canvas linked to `.webgl-measure` offsets rendered columns based on viewport scroll velocity."
        ],
        recording=None,
        scroll_probe=ScrollProbeSummary(
            context="frame",
            triggered=True,
            range_start=100,
            range_end=500,
            step_count=8,
            fps=12,
            frames_dir="animations/scroll_probe/frames",
            video_path="animations/scroll_probe/recording.webm",
            key_frames=[0, 3, 7],
            tracked_selectors=["__target__", ".webgl-img"],
            overlay_selectors=["canvas"],
            observations=["Source images stay hidden while overlay media changes across scroll."],
            state_changes=[
                ScrollProbeStateChange(
                    selector=".webgl-img",
                    property_changes={"opacity": {"first": "0", "last": "1"}},
                    first_changed_step=1,
                    peak_changed_step=7,
                    notes=["Opacity changed during viewport scroll."],
                )
            ],
            limitations=[],
        ),
    )

    output = NormalizedOutput(
        **shared_fields,
        target=TargetInfo(
            selector_used=".hero",
            strategy=SelectorStrategy.CSS,
            html="<section class='hero'></section>",
            bounding_box=BoundingBox(x=0, y=0, width=1200, height=600),
            depth_in_dom=2,
            screenshot_path=None,
        ),
        rich_media=[
            {
                "type": "webgl",
                "selector": "canvas:nth-of-type(1)",
                "bounding_box": BoundingBox(x=0, y=0, width=1440, height=900),
                "document_level": True,
                "linked_selectors": [".webgl-measure", ".webgl-img"],
                "effect_summary": "Document-level WebGL canvas linked to `.webgl-measure` and `.webgl-img` replaces hidden source images and offsets rendered columns based on viewport scroll velocity.",
            }
        ],
    )

    prompt = build_user_prompt(output)

    assert "Scroll Effects:" in prompt
    assert "viewport scroll velocity" in prompt
    assert "## Scroll Probe" in prompt
    assert "Frames Dir: animations/scroll_probe/frames" in prompt
    assert "Video Path: animations/scroll_probe/recording.webm" in prompt
    assert "Scope: document-level overlay outside the component subtree" in prompt
    assert "Linked Selectors: `.webgl-measure`, `.webgl-img`" in prompt
    assert "Effect: Document-level WebGL canvas linked to `.webgl-measure` and `.webgl-img`" in prompt


def test_build_user_prompt_for_full_page():
    """Full-page mode should include landing page capture details and sections."""
    shared_fields = build_shared_fields()
    shared_fields["animations"] = AnimationSummary(
        css_animations=[],
        css_transitions=[],
        scroll_effects=["Global parallax movement is visible across the landing."],
        recording=None,
        scroll_probe=ScrollProbeSummary(
            context="page",
            triggered=True,
            range_start=0,
            range_end=2200,
            step_count=14,
            fps=12,
            frames_dir="animations/scroll_probe/frames",
            video_path="animations/scroll_probe/recording.webm",
            key_frames=[0, 5, 9, 13],
            tracked_selectors=["__target__"],
            overlay_selectors=[],
            observations=["Landing-level probe confirmed multiple animated sections."],
            state_changes=[],
            limitations=[],
        ),
    )
    output = FullPageNormalizedOutput(
        **shared_fields,
        page_capture=PageCaptureInfo(
            html="<body><section>Hero</section><section>Pricing</section></body>",
            screenshot_path=None,
            bounding_box=BoundingBox(x=0, y=0, width=1440, height=3200),
            scroll_completed=True,
            sections=[
                PageSectionSummary(
                    section_id="section-01-hero",
                    name="Hero",
                    selector="section.hero",
                    tag="section",
                    text_excerpt="Build faster",
                    bounding_box=BoundingBox(x=0, y=0, width=1440, height=640),
                    html="<section class='hero'><h1>Build faster</h1></section>",
                    screenshot_path="sections/section-01-hero/screenshot.png",
                    interactions=InteractionSummary(
                        hoverable_elements=[".hero-card"],
                        clickable_elements=[".hero-cta"],
                        focusable_elements=[],
                        scroll_containers=[],
                        observed_states={},
                    ),
                    animations=AnimationSummary(
                        css_animations=[],
                        css_transitions=[],
                        scroll_effects=[
                            "Hero media lifts and fades in as the section enters the viewport."
                        ],
                        recording=None,
                        scroll_probe=ScrollProbeSummary(
                            context="page",
                            triggered=True,
                            range_start=0,
                            range_end=640,
                            step_count=8,
                            fps=12,
                            frames_dir="sections/section-01-hero/animations/scroll_probe/frames",
                            video_path="sections/section-01-hero/animations/scroll_probe/recording.webm",
                            key_frames=[0, 3, 7],
                            tracked_selectors=["__target__", ".hero-card"],
                            overlay_selectors=["canvas.hero-overlay"],
                            observations=[
                                "Hero overlay changes while the section enters the viewport."
                            ],
                            state_changes=[],
                            limitations=[],
                        ),
                    ),
                    rich_media=[
                        {
                            "type": "webgl",
                            "selector": "canvas.hero-overlay",
                            "bounding_box": BoundingBox(x=0, y=0, width=1440, height=640),
                            "document_level": True,
                            "linked_selectors": [".hero-card"],
                            "effect_summary": "Document-level WebGL overlay amplifies the hero reveal during scroll.",
                        }
                    ],
                    collection_limitations=["Used element screenshot fallback for hero overlay."],
                ),
                PageSectionSummary(
                    section_id="section-02-pricing",
                    name="Pricing",
                    selector="section.pricing",
                    tag="section",
                    text_excerpt="Plans for every team",
                    bounding_box=BoundingBox(x=0, y=1200, width=1440, height=700),
                ),
            ],
        ),
        collection_limitations=["Could not export canvas pixels directly; the canvas may be tainted or GPU-backed."],
    )

    prompt = build_user_prompt(output)

    assert output.mode == ExtractionMode.FULL_PAGE
    assert "## Package Context" in prompt
    assert "## Landing Page Capture" in prompt
    assert "## Sections" in prompt
    assert "Pricing" in prompt
    assert "### section-01-hero" in prompt
    assert "Screenshot: sections/section-01-hero/screenshot.png" in prompt
    assert "Scroll Probe Frames: sections/section-01-hero/animations/scroll_probe/frames" in prompt
    assert "Rich Media: webgl via `canvas.hero-overlay`" in prompt
    assert "## Collection Limitations" in prompt
