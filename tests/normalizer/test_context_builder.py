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
        "screenshot_path": "/tmp/hero.png",
        "frame_url": "https://example.com/embed",
        "frame_name": "hero-frame",
        "same_origin_accessible": False,
        "within_shadow_dom": True,
        "frame_limitations": ["Could not inspect external libraries in the frame document."],
    }
    payload["collection_limitations"] = ["Canvas export fell back to screenshot."]
    payload["rich_media"] = [
        {
            "type": "canvas",
            "selector": "#demo-canvas",
            "bounding_box": {"x": 10, "y": 20, "width": 300, "height": 120},
            "source_urls": [],
            "poster_url": None,
            "snapshot_path": "/tmp/canvas.png",
            "playback_flags": {},
            "limitations": ["Used element screenshot fallback instead of direct canvas export."],
        }
    ]

    result = builder.build(payload)

    assert result.mode == ExtractionMode.COMPONENT
    assert result.target.selector_used == ".hero"
    assert result.get_primary_screenshot_path() == "/tmp/hero.png"
    assert result.target.frame_url == "https://example.com/embed"
    assert result.target.same_origin_accessible is False
    assert result.target.within_shadow_dom is True
    assert result.collection_limitations == ["Canvas export fell back to screenshot."]
    assert result.rich_media[0].selector == "#demo-canvas"


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
            }
        ],
    }
    payload["collection_limitations"] = ["Could not inspect external libraries in the frame document."]

    result = builder.build(payload)

    assert result.mode == ExtractionMode.FULL_PAGE
    assert result.page_capture.scroll_completed is True
    assert result.page_capture.sections[0].name == "Hero"
    assert result.get_primary_screenshot_path() == "/tmp/page.png"
    assert result.collection_limitations == [
        "Could not inspect external libraries in the frame document."
    ]
