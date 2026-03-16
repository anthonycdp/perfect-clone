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

    assert "## Target Component" in prompt
    assert "Selector: .hero" in prompt
    assert "Frame URL: https://example.com/embed" in prompt
    assert "Same Origin Accessible: False" in prompt
    assert "Within Shadow DOM: True" in prompt
    assert "## Frame Limitations" in prompt
    assert "## Collection Limitations" in prompt


def test_build_user_prompt_for_full_page():
    """Full-page mode should include landing page capture details and sections."""
    output = FullPageNormalizedOutput(
        **build_shared_fields(),
        page_capture=PageCaptureInfo(
            html="<body><section>Hero</section><section>Pricing</section></body>",
            screenshot_path=None,
            bounding_box=BoundingBox(x=0, y=0, width=1440, height=3200),
            scroll_completed=True,
            sections=[
                PageSectionSummary(
                    name="Hero",
                    selector="section.hero",
                    tag="section",
                    text_excerpt="Build faster",
                    bounding_box=BoundingBox(x=0, y=0, width=1440, height=640),
                ),
                PageSectionSummary(
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
    assert "## Landing Page Capture" in prompt
    assert "## Sections" in prompt
    assert "Pricing" in prompt
    assert "## Collection Limitations" in prompt
