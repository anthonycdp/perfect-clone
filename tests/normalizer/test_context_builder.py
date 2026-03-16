"""Tests for ContextBuilder."""

from normalizer import ContextBuilder
from models.extraction import ExtractionMode


def build_common_payload() -> dict:
    """Create the raw extraction fields shared by both modes."""
    return {
        "page": {
            "url": "https://example.com",
            "title": "Example",
            "viewport": {"width": 1440, "height": 900},
            "loaded_scripts": [],
            "loaded_stylesheets": [],
        },
        "dom_tree": {
            "tag": "div",
            "attributes": {},
            "children": [],
            "text_content": "",
            "computed_styles": {},
        },
        "styles": {
            "display": "grid",
            "padding": "24px",
            "font-size": "16px",
            "color": "rgb(255, 255, 255)",
        },
        "assets": [],
        "interactions": {
            "hoverable": [],
            "clickable": [],
            "focusable": [],
            "scroll_containers": [],
            "observed_states": [],
        },
        "animations": {
            "animations": [],
            "transitions": [],
            "keyframes": {},
            "observed_scroll_effects": [],
            "recording": None,
        },
        "responsive": {
            "breakpoints": [],
            "is_fluid": True,
            "has_mobile_menu": False,
            "grid_changes": [],
        },
        "libraries": [],
        "rich_media": [],
        "collection_limitations": [],
    }


def test_build_component_output():
    """ContextBuilder should return the component output model by default."""
    builder = ContextBuilder()
    payload = build_common_payload()
    payload["mode"] = ExtractionMode.COMPONENT.value
    payload["target"] = {
        "selector_used": ".hero",
        "strategy": "css",
        "html": "<section class='hero'></section>",
        "bounding_box": {"x": 0, "y": 100, "width": 1200, "height": 600},
        "depth": 3,
        "screenshot_path": "/tmp/visual_reference.png",
        "element_screenshot_path": "/tmp/hero.png",
        "visual_reference": {
            "promoted": True,
            "source": "scroll_probe_frame",
            "source_path": "/tmp/scroll_probe/frames/frame_0000.png",
            "reason": "Promoted from the scroll probe.",
        },
        "frame_url": "https://example.com/embed",
        "frame_name": "hero-frame",
        "same_origin_accessible": False,
        "within_shadow_dom": True,
        "frame_limitations": ["Could not inspect external libraries in the frame document."],
    }
    payload["collection_limitations"] = ["Canvas export fell back to screenshot."]
    payload["animations"]["observed_scroll_effects"] = [
        "Document-level WebGL canvas offsets rendered columns based on viewport scroll velocity."
    ]
    payload["animations"]["scroll_probe"] = {
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
        "observations": ["Source images stay hidden while overlay media changes across scroll."],
        "state_changes": [
            {
                "selector": ".webgl-img",
                "property_changes": {"opacity": {"first": "0", "last": "1"}},
                "first_changed_step": 1,
                "peak_changed_step": 7,
                "notes": ["Opacity changed during viewport scroll."],
            }
        ],
        "limitations": [],
    }
    payload["rich_media"] = [
        {
            "type": "canvas",
            "selector": "#demo-canvas",
            "bounding_box": {"x": 10, "y": 20, "width": 300, "height": 120},
            "source_urls": [],
            "poster_url": None,
            "snapshot_path": "/tmp/canvas.png",
            "playback_flags": {},
            "document_level": True,
            "linked_selectors": [".webgl-measure", ".webgl-img"],
            "effect_summary": "Document-level WebGL canvas linked to `.webgl-measure` and `.webgl-img` offsets rendered columns based on viewport scroll velocity.",
            "limitations": ["Used element screenshot fallback instead of direct canvas export."],
        }
    ]

    result = builder.build(payload)

    assert result.mode == ExtractionMode.COMPONENT
    assert result.target.selector_used == ".hero"
    assert result.get_primary_screenshot_path() == "/tmp/visual_reference.png"
    assert result.target.element_screenshot_path == "/tmp/hero.png"
    assert result.target.visual_reference.promoted is True
    assert result.target.visual_reference.source_path == "/tmp/scroll_probe/frames/frame_0000.png"
    assert result.target.frame_url == "https://example.com/embed"
    assert result.target.same_origin_accessible is False
    assert result.target.within_shadow_dom is True
    assert result.collection_limitations == ["Canvas export fell back to screenshot."]
    assert result.rich_media[0].selector == "#demo-canvas"
    assert result.rich_media[0].document_level is True
    assert result.rich_media[0].linked_selectors == [".webgl-measure", ".webgl-img"]
    assert result.animations.scroll_effects == [
        "Document-level WebGL canvas offsets rendered columns based on viewport scroll velocity."
    ]
    assert result.animations.scroll_probe is not None
    assert result.animations.scroll_probe.context == "frame"
    assert result.animations.scroll_probe.state_changes[0].selector == ".webgl-img"


def test_build_full_page_output():
    """ContextBuilder should build the full-page output model when requested."""
    builder = ContextBuilder()
    payload = build_common_payload()
    payload["mode"] = ExtractionMode.FULL_PAGE.value
    payload["page_capture"] = {
        "html": "<body><section>Hero</section></body>",
        "screenshot_path": "/tmp/page.png",
        "bounding_box": {"x": 0, "y": 0, "width": 1440, "height": 3200},
        "scroll_completed": True,
        "sections": [
            {
                "section_id": "section-01-hero",
                "name": "Hero",
                "selector": "section.hero",
                "tag": "section",
                "text_excerpt": "Build faster",
                "bounding_box": {
                    "x": 0,
                    "y": 0,
                    "width": 1440,
                    "height": 640,
                },
                "html": "<section class='hero'><h1>Build faster</h1></section>",
                "screenshot_path": "/tmp/sections/section-01-hero/screenshot.png",
                "interactions": {
                    "hoverable": [{"selector": ".hero-card"}],
                    "clickable": [{"selector": ".hero-cta"}],
                    "focusable": [],
                    "scroll_containers": [],
                    "observed_states": [
                        {
                            "selector": ".hero-cta",
                            "before": {"opacity": "0.8"},
                            "after": {"opacity": "1"},
                        }
                    ],
                },
                "animations": {
                    "animations": [],
                    "transitions": [],
                    "keyframes": {},
                    "observed_scroll_effects": [
                        "Hero media shifts vertically while the section enters the viewport."
                    ],
                    "recording": None,
                    "scroll_probe": {
                        "context": "page",
                        "triggered": True,
                        "range_start": 0,
                        "range_end": 640,
                        "step_count": 8,
                        "fps": 12,
                        "frames_dir": "/tmp/sections/section-01-hero/animations/scroll_probe/frames",
                        "video_path": "/tmp/sections/section-01-hero/animations/scroll_probe/recording.webm",
                        "key_frames": [0, 3, 7],
                        "tracked_selectors": ["__target__", ".hero-card"],
                        "overlay_selectors": ["canvas"],
                        "observations": [
                            "Scroll probe confirmed hero media movement tied to viewport entry."
                        ],
                        "state_changes": [],
                        "limitations": [],
                    },
                },
                "rich_media": [
                    {
                        "type": "webgl",
                        "selector": "canvas.hero-overlay",
                        "bounding_box": {
                            "x": 0,
                            "y": 0,
                            "width": 1440,
                            "height": 640,
                        },
                        "source_urls": [],
                        "poster_url": None,
                        "snapshot_path": "/tmp/sections/section-01-hero/rich_media/hero-overlay.png",
                        "playback_flags": {},
                        "document_level": True,
                        "linked_selectors": [".hero-card"],
                        "effect_summary": "Document-level WebGL overlay amplifies the hero reveal during scroll.",
                        "limitations": [],
                    }
                ],
                "collection_limitations": ["Used element screenshot fallback for hero overlay."],
            }
        ],
    }
    payload["collection_limitations"] = ["Could not inspect external libraries in the frame document."]

    result = builder.build(payload)

    assert result.mode == ExtractionMode.FULL_PAGE
    assert result.page_capture.scroll_completed is True
    assert result.page_capture.sections[0].name == "Hero"
    assert result.page_capture.sections[0].section_id == "section-01-hero"
    assert result.page_capture.sections[0].html.startswith("<section")
    assert result.page_capture.sections[0].interactions is not None
    assert result.page_capture.sections[0].interactions.clickable_elements == [".hero-cta"]
    assert result.page_capture.sections[0].animations is not None
    assert result.page_capture.sections[0].animations.scroll_probe is not None
    assert result.page_capture.sections[0].rich_media[0].selector == "canvas.hero-overlay"
    assert result.get_primary_screenshot_path() == "/tmp/page.png"
    assert result.collection_limitations == [
        "Could not inspect external libraries in the frame document."
    ]
