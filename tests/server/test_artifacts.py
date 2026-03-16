"""Tests for temporary artifact packaging."""

from pathlib import Path
import zipfile

from models.extraction import BoundingBox, SelectorStrategy
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
    ScrollProbeSummary,
    StyleSummary,
    TargetInfo,
)
from models.requests import ExtractionRequest
from server.artifacts import package_extraction_result


def build_normalized_output(workspace_dir: Path) -> NormalizedOutput:
    """Create a normalized output whose file paths live inside the workspace."""
    screenshot_path = workspace_dir / "screenshots" / "target.png"
    asset_path = workspace_dir / "images" / "hero.png"
    scroll_probe_frames_dir = workspace_dir / "animations" / "scroll_probe" / "frames"
    scroll_probe_video_path = workspace_dir / "animations" / "scroll_probe" / "recording.webm"
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    scroll_probe_frames_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path.write_bytes(b"png")
    asset_path.write_bytes(b"asset")
    (scroll_probe_frames_dir / "frame_0000.png").write_bytes(b"frame")
    scroll_probe_video_path.write_bytes(b"video")

    return NormalizedOutput(
        page=PageInfo(
            url="https://example.com",
            title="Example",
            viewport={"width": 1280, "height": 720},
            loaded_scripts=[],
            loaded_stylesheets=[],
        ),
        target=TargetInfo(
            selector_used=".hero",
            strategy=SelectorStrategy.CSS,
            html="<section class='hero'></section>",
            bounding_box=BoundingBox(x=0, y=0, width=1200, height=500),
            depth_in_dom=2,
            screenshot_path=str(screenshot_path),
        ),
        dom=DOMTree(
            tag="section",
            attributes={"class": "hero"},
            children=[],
            text_content="Hero",
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
            scroll_probe={
                "context": "frame",
                "triggered": True,
                "range_start": 120,
                "range_end": 480,
                "step_count": 8,
                "fps": 12,
                "frames_dir": str(scroll_probe_frames_dir),
                "video_path": str(scroll_probe_video_path),
                "key_frames": [0, 3, 7],
                "tracked_selectors": ["__target__", ".webgl-img"],
                "overlay_selectors": ["canvas"],
                "observations": ["Scroll probe confirmed overlay changes."],
                "state_changes": [],
                "limitations": [],
            },
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
        collection_limitations=[],
        rich_media=[],
    )


def test_package_extraction_result_writes_bundle_files(tmp_path: Path):
    """Packaging should write support files and archive the workspace."""
    normalized = build_normalized_output(tmp_path)
    request = ExtractionRequest(
        url="https://example.com",
        mode="component",
        strategy="css",
        query=".hero",
    )

    packaged = package_extraction_result(
        task_id="task1234",
        request=request,
        workspace_dir=tmp_path,
        normalized=normalized,
        synthesis_prompt="Build the hero section.",
    )

    assert packaged.package_path.exists()
    assert packaged.prompt_text.startswith("Before building, inspect the files in this package")
    assert packaged.normalized_payload["target"]["screenshot_path"] == "screenshots/target.png"
    assert (
        packaged.normalized_payload["animations"]["scroll_probe"]["frames_dir"]
        == "animations/scroll_probe/frames"
    )
    assert (
        packaged.normalized_payload["animations"]["scroll_probe"]["video_path"]
        == "animations/scroll_probe/recording.webm"
    )
    assert packaged.manifest_payload["entrypoints"]["prompt"] == "prompt.txt"
    assert packaged.manifest_payload["scroll_probe"]["video_path"] == "animations/scroll_probe/recording.webm"
    assert "manifest.json" in packaged.manifest_payload["files"]

    with zipfile.ZipFile(packaged.package_path) as archive:
        names = set(archive.namelist())

    assert "prompt.txt" in names
    assert "README.md" in names
    assert "manifest.json" in names
    assert "normalized.json" in names
    assert "screenshots/target.png" in names
    assert "animations/scroll_probe/frames/frame_0000.png" in names
    assert "animations/scroll_probe/recording.webm" in names


def test_package_extraction_result_indexes_full_page_sections(tmp_path: Path):
    """Packaging should preserve section-scoped artifacts for full-page captures."""
    page_screenshot = tmp_path / "screenshots" / "page.png"
    section_screenshot = tmp_path / "sections" / "section-01-hero" / "screenshot.png"
    section_frames_dir = (
        tmp_path
        / "sections"
        / "section-01-hero"
        / "animations"
        / "scroll_probe"
        / "frames"
    )
    section_video = (
        tmp_path
        / "sections"
        / "section-01-hero"
        / "animations"
        / "scroll_probe"
        / "recording.webm"
    )
    section_rich_media = (
        tmp_path / "sections" / "section-01-hero" / "rich_media" / "hero-overlay.png"
    )

    page_screenshot.parent.mkdir(parents=True, exist_ok=True)
    section_screenshot.parent.mkdir(parents=True, exist_ok=True)
    section_frames_dir.mkdir(parents=True, exist_ok=True)
    section_rich_media.parent.mkdir(parents=True, exist_ok=True)
    page_screenshot.write_bytes(b"page")
    section_screenshot.write_bytes(b"section")
    (section_frames_dir / "frame_0000.png").write_bytes(b"frame")
    section_video.write_bytes(b"video")
    section_rich_media.write_bytes(b"rich-media")

    normalized = FullPageNormalizedOutput(
        page=PageInfo(
            url="https://example.com",
            title="Example",
            viewport={"width": 1440, "height": 900},
            loaded_scripts=[],
            loaded_stylesheets=[],
        ),
        page_capture=PageCaptureInfo(
            html="<body><section class='hero'></section></body>",
            screenshot_path=str(page_screenshot),
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
                    screenshot_path=str(section_screenshot),
                    animations=AnimationSummary(
                        css_animations=[],
                        css_transitions=[],
                        scroll_effects=["Hero media lifts on scroll."],
                        recording=None,
                        scroll_probe=ScrollProbeSummary(
                            context="page",
                            triggered=True,
                            range_start=0,
                            range_end=640,
                            step_count=8,
                            fps=12,
                            frames_dir=str(section_frames_dir),
                            video_path=str(section_video),
                            key_frames=[0, 3, 7],
                            tracked_selectors=["__target__"],
                            overlay_selectors=["canvas.hero-overlay"],
                            observations=["Hero overlay changes during scroll."],
                            state_changes=[],
                            limitations=[],
                        ),
                    ),
                    rich_media=[
                        {
                            "type": "webgl",
                            "selector": "canvas.hero-overlay",
                            "bounding_box": BoundingBox(x=0, y=0, width=1440, height=640),
                            "snapshot_path": str(section_rich_media),
                        }
                    ],
                    collection_limitations=["Used screenshot fallback for overlay."],
                )
            ],
        ),
        dom=DOMTree(
            tag="body",
            attributes={},
            children=[],
            text_content="Hero",
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
        collection_limitations=[],
        rich_media=[],
    )
    request = ExtractionRequest(
        url="https://example.com",
        mode="full_page",
        strategy="css",
        query="",
    )

    packaged = package_extraction_result(
        task_id="task5678",
        request=request,
        workspace_dir=tmp_path,
        normalized=normalized,
        synthesis_prompt="Build the landing page.",
    )

    section = packaged.normalized_payload["page_capture"]["sections"][0]
    assert section["screenshot_path"] == "sections/section-01-hero/screenshot.png"
    assert (
        section["animations"]["scroll_probe"]["frames_dir"]
        == "sections/section-01-hero/animations/scroll_probe/frames"
    )
    assert (
        packaged.manifest_payload["sections"][0]["scroll_probe"]["video_path"]
        == "sections/section-01-hero/animations/scroll_probe/recording.webm"
    )
    assert packaged.manifest_payload["summary"]["section_count"] == 1
    assert packaged.manifest_payload["summary"]["animated_section_count"] == 1

    with zipfile.ZipFile(packaged.package_path) as archive:
        names = set(archive.namelist())

    assert "sections/section-01-hero/screenshot.png" in names
    assert "sections/section-01-hero/animations/scroll_probe/frames/frame_0000.png" in names
    assert "sections/section-01-hero/rich_media/hero-overlay.png" in names
