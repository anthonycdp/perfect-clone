"""Tests for normalized data models."""

import pytest
from pydantic import ValidationError

from models.normalized import (
    BaseNormalizedOutput,
    PageInfo,
    TargetInfo,
    DOMTree,
    ScrollProbeStateChange,
    ScrollProbeSummary,
    StyleSummary,
    AnimationSummary,
    InteractionSummary,
    ResponsiveBehavior,
    PageSectionSummary,
    PageCaptureInfo,
    NormalizedOutput,
    FullPageNormalizedOutput,
)
from models.extraction import (
    ExtractionMode,
    SelectorStrategy,
    BoundingBox,
    InteractionType,
    InteractionState,
    Asset,
    AssetType,
    ExternalLibrary,
)


class TestPageInfo:
    """Tests for PageInfo model."""

    def test_page_info_with_all_fields(self):
        """PageInfo should accept all fields."""
        page_info = PageInfo(
            url="https://example.com/page",
            title="Example Page",
            viewport={"width": 1920, "height": 1080},
            loaded_scripts=["script1.js", "script2.js"],
            loaded_stylesheets=["style1.css", "style2.css"],
        )
        assert page_info.url == "https://example.com/page"
        assert page_info.title == "Example Page"
        assert page_info.viewport == {"width": 1920, "height": 1080}
        assert page_info.loaded_scripts == ["script1.js", "script2.js"]
        assert page_info.loaded_stylesheets == ["style1.css", "style2.css"]

    def test_page_info_with_empty_lists(self):
        """PageInfo should work with empty lists."""
        page_info = PageInfo(
            url="https://example.com",
            title="Empty Page",
            viewport={"width": 800, "height": 600},
            loaded_scripts=[],
            loaded_stylesheets=[],
        )
        assert page_info.loaded_scripts == []
        assert page_info.loaded_stylesheets == []

    def test_page_info_requires_all_fields(self):
        """PageInfo should require all fields."""
        with pytest.raises(ValidationError):
            PageInfo(url="https://example.com")


class TestTargetInfo:
    """Tests for TargetInfo model."""

    def test_target_info_with_all_fields(self):
        """TargetInfo should accept all fields."""
        target_info = TargetInfo(
            selector_used=".hero-section",
            strategy=SelectorStrategy.CSS,
            html="<div class=\"hero-section\">Content</div>",
            bounding_box=BoundingBox(x=0, y=100, width=1200, height=600),
            depth_in_dom=5,
            screenshot_path="/output/screenshots/visual_reference.png",
            element_screenshot_path="/output/screenshots/target.png",
            visual_reference={
                "promoted": True,
                "source": "scroll_probe_frame",
                "source_path": "/output/animations/scroll_probe/frame_0000.png",
                "reason": "Promoted from the scroll probe.",
            },
            frame_url="https://example.com",
            frame_name="main",
            same_origin_accessible=True,
            frame_limitations=[],
        )
        assert target_info.selector_used == ".hero-section"
        assert target_info.strategy == SelectorStrategy.CSS
        assert target_info.html == "<div class=\"hero-section\">Content</div>"
        assert target_info.bounding_box.width == 1200
        assert target_info.depth_in_dom == 5
        assert target_info.screenshot_path == "/output/screenshots/visual_reference.png"
        assert target_info.element_screenshot_path == "/output/screenshots/target.png"
        assert target_info.visual_reference.promoted is True
        assert target_info.frame_url == "https://example.com"
        assert target_info.frame_name == "main"

    def test_target_info_with_string_strategy(self):
        """TargetInfo should accept string for strategy."""
        target_info = TargetInfo(
            selector_used="//div[@id='content']",
            strategy="xpath",
            html="<div id=\"content\">Text</div>",
            bounding_box=BoundingBox(x=10, y=20, width=500, height=300),
            depth_in_dom=3,
            frame_limitations=["Limited"],
        )
        assert target_info.strategy == SelectorStrategy.XPATH
        assert target_info.screenshot_path is None
        assert target_info.frame_limitations == ["Limited"]

    def test_target_info_requires_all_fields(self):
        """TargetInfo should require all fields."""
        with pytest.raises(ValidationError):
            TargetInfo(selector_used=".test")


class TestDOMTree:
    """Tests for DOMTree model - RECURSIVE structure."""

    def test_dom_tree_leaf_node(self):
        """DOMTree should work as a leaf node without children."""
        dom_tree = DOMTree(
            tag="span",
            attributes={"class": "text"},
            children=[],
            text_content="Hello World",
            computed_styles={"color": "red", "font-size": "16px"},
        )
        assert dom_tree.tag == "span"
        assert dom_tree.attributes == {"class": "text"}
        assert dom_tree.children == []
        assert dom_tree.text_content == "Hello World"
        assert dom_tree.computed_styles == {"color": "red", "font-size": "16px"}

    def test_dom_tree_with_nested_children(self):
        """DOMTree should support recursive nesting."""
        # Create nested structure: div > p > span
        span = DOMTree(
            tag="span",
            attributes={},
            children=[],
            text_content="nested text",
            computed_styles={},
        )
        p = DOMTree(
            tag="p",
            attributes={"class": "paragraph"},
            children=[span],
            text_content="",
            computed_styles={"margin": "10px"},
        )
        div = DOMTree(
            tag="div",
            attributes={"id": "container"},
            children=[p],
            text_content="",
            computed_styles={"display": "block"},
        )

        assert div.tag == "div"
        assert len(div.children) == 1
        assert div.children[0].tag == "p"
        assert div.children[0].children[0].tag == "span"
        assert div.children[0].children[0].text_content == "nested text"

    def test_dom_tree_with_multiple_children(self):
        """DOMTree should support multiple children."""
        child1 = DOMTree(
            tag="li",
            attributes={},
            children=[],
            text_content="Item 1",
            computed_styles={},
        )
        child2 = DOMTree(
            tag="li",
            attributes={},
            children=[],
            text_content="Item 2",
            computed_styles={},
        )
        ul = DOMTree(
            tag="ul",
            attributes={},
            children=[child1, child2],
            text_content="",
            computed_styles={"list-style": "disc"},
        )

        assert ul.tag == "ul"
        assert len(ul.children) == 2
        assert ul.children[0].text_content == "Item 1"
        assert ul.children[1].text_content == "Item 2"

    def test_dom_tree_requires_all_fields(self):
        """DOMTree should require all fields."""
        with pytest.raises(ValidationError):
            DOMTree(tag="div")


class TestStyleSummary:
    """Tests for StyleSummary model."""

    def test_style_summary_with_all_fields(self):
        """StyleSummary should accept all field categories."""
        style_summary = StyleSummary(
            layout={"display": "flex", "flex-direction": "column"},
            spacing={"padding": "20px", "margin": "10px"},
            typography={"font-family": "Arial", "font-size": "16px"},
            colors={"background": "#ffffff", "color": "#000000"},
            effects={"box-shadow": "0 2px 4px rgba(0,0,0,0.1)"},
        )
        assert style_summary.layout == {"display": "flex", "flex-direction": "column"}
        assert style_summary.spacing == {"padding": "20px", "margin": "10px"}
        assert style_summary.typography == {"font-family": "Arial", "font-size": "16px"}
        assert style_summary.colors == {"background": "#ffffff", "color": "#000000"}
        assert style_summary.effects == {"box-shadow": "0 2px 4px rgba(0,0,0,0.1)"}

    def test_style_summary_with_empty_dicts(self):
        """StyleSummary should work with empty dicts."""
        style_summary = StyleSummary(
            layout={},
            spacing={},
            typography={},
            colors={},
            effects={},
        )
        assert style_summary.layout == {}
        assert style_summary.spacing == {}

    def test_style_summary_requires_all_fields(self):
        """StyleSummary should require all fields."""
        with pytest.raises(ValidationError):
            StyleSummary(layout={"display": "block"})


class TestAnimationSummary:
    """Tests for AnimationSummary model."""

    def test_animation_summary_with_all_fields(self):
        """AnimationSummary should accept all fields."""
        from models.extraction import AnimationData, TransitionData, AnimationRecording

        animation = AnimationData(
            duration="0.5s",
            delay="0s",
            timing_function="ease",
            iteration_count="1",
            direction="normal",
            fill_mode="both",
        )
        transition = TransitionData(
            property="opacity",
            duration="0.3s",
            timing_function="ease-in",
            delay="0s",
        )
        recording = AnimationRecording(
            video_path="/video.mp4",
            duration_ms=500.0,
            fps=30,
            frames_dir="/frames",
            key_frames=[0, 15],
        )
        scroll_probe = ScrollProbeSummary(
            context="frame",
            triggered=True,
            range_start=100,
            range_end=500,
            step_count=8,
            fps=12,
            frames_dir="/scroll-probe/frames",
            video_path="/scroll-probe/recording.webm",
            key_frames=[0, 3, 7],
            tracked_selectors=["__target__", ".probe-img"],
            overlay_selectors=["canvas"],
            observations=["Probe confirmed scroll-linked opacity changes."],
            state_changes=[
                ScrollProbeStateChange(
                    selector=".probe-img",
                    property_changes={"opacity": {"first": "0", "last": "1"}},
                    first_changed_step=1,
                    peak_changed_step=7,
                    notes=["Opacity changed during viewport scroll."],
                )
            ],
            limitations=[],
        )

        animation_summary = AnimationSummary(
            css_animations=[animation],
            css_transitions=[transition],
            scroll_effects=["parallax"],
            recording=recording,
            scroll_probe=scroll_probe,
        )

        assert len(animation_summary.css_animations) == 1
        assert animation_summary.css_animations[0].duration == "0.5s"
        assert len(animation_summary.css_transitions) == 1
        assert animation_summary.scroll_effects == ["parallax"]
        assert animation_summary.recording.video_path == "/video.mp4"
        assert animation_summary.scroll_probe.video_path == "/scroll-probe/recording.webm"

    def test_animation_summary_with_empty_lists(self):
        """AnimationSummary should work with empty animation lists."""
        animation_summary = AnimationSummary(
            css_animations=[],
            css_transitions=[],
            scroll_effects=[],
            recording=None,
        )
        assert animation_summary.css_animations == []
        assert animation_summary.recording is None

    def test_animation_summary_requires_lists(self):
        """AnimationSummary should require css_animations, css_transitions, scroll_effects."""
        with pytest.raises(ValidationError):
            AnimationSummary(css_animations=[])


class TestInteractionSummary:
    """Tests for InteractionSummary model."""

    def test_interaction_summary_with_all_fields(self):
        """InteractionSummary should accept all fields."""
        interaction_state = InteractionState(
            type=InteractionType.HOVER,
            selector=".button",
            before={"opacity": "1"},
            after={"opacity": "0.8"},
            duration_ms=150.0,
        )
        interaction_summary = InteractionSummary(
            hoverable_elements=[".button", ".card"],
            clickable_elements=["a", "button"],
            focusable_elements=["input", "textarea"],
            scroll_containers=[".scrollable"],
            observed_states={"hover": interaction_state},
        )
        assert interaction_summary.hoverable_elements == [".button", ".card"]
        assert interaction_summary.clickable_elements == ["a", "button"]
        assert interaction_summary.focusable_elements == ["input", "textarea"]
        assert interaction_summary.scroll_containers == [".scrollable"]
        assert interaction_summary.observed_states == {"hover": interaction_state}

    def test_interaction_summary_with_empty_lists(self):
        """InteractionSummary should work with empty lists and empty dict."""
        interaction_summary = InteractionSummary(
            hoverable_elements=[],
            clickable_elements=[],
            focusable_elements=[],
            scroll_containers=[],
            observed_states={},
        )
        assert interaction_summary.hoverable_elements == []

    def test_interaction_summary_requires_all_fields(self):
        """InteractionSummary should require all fields."""
        with pytest.raises(ValidationError):
            InteractionSummary(hoverable_elements=[])


class TestResponsiveBehavior:
    """Tests for ResponsiveBehavior model."""

    def test_responsive_behavior_with_all_fields(self):
        """ResponsiveBehavior should accept all fields."""
        from models.extraction import ResponsiveBreakpoint

        breakpoint = ResponsiveBreakpoint(
            width=768,
            height=1024,
            source="media_query",
            styles_diff={},
            layout_changes=["column layout"],
        )
        responsive_behavior = ResponsiveBehavior(
            breakpoints=[breakpoint],
            is_fluid=True,
            has_mobile_menu=True,
            grid_changes=[{"from": "1-column", "to": "2-column"}],
        )
        assert len(responsive_behavior.breakpoints) == 1
        assert responsive_behavior.is_fluid is True
        assert responsive_behavior.has_mobile_menu is True
        assert responsive_behavior.grid_changes == [{"from": "1-column", "to": "2-column"}]

    def test_responsive_behavior_desktop_only(self):
        """ResponsiveBehavior should work for desktop-only sites."""
        responsive_behavior = ResponsiveBehavior(
            breakpoints=[],
            is_fluid=False,
            has_mobile_menu=False,
            grid_changes=[],
        )
        assert responsive_behavior.breakpoints == []
        assert responsive_behavior.is_fluid is False
        assert responsive_behavior.has_mobile_menu is False

    def test_responsive_behavior_requires_all_fields(self):
        """ResponsiveBehavior should require all fields."""
        with pytest.raises(ValidationError):
            ResponsiveBehavior(breakpoints=[])


class TestNormalizedOutput:
    """Tests for NormalizedOutput model - combines all above."""

    def test_normalized_output_with_all_fields(self):
        """NormalizedOutput should combine all normalized models."""
        from models.extraction import AnimationRecording

        page_info = PageInfo(
            url="https://example.com",
            title="Test",
            viewport={"width": 1920, "height": 1080},
            loaded_scripts=[],
            loaded_stylesheets=[],
        )
        target_info = TargetInfo(
            selector_used=".test",
            strategy=SelectorStrategy.CSS,
            html="<div>Test</div>",
            bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
            depth_in_dom=1,
            screenshot_path="/output/screenshots/target.png",
            frame_url="https://example.com",
            frame_name=None,
            same_origin_accessible=True,
            frame_limitations=["Frame stylesheets blocked"],
        )
        dom_tree = DOMTree(
            tag="div",
            attributes={},
            children=[],
            text_content="",
            computed_styles={},
        )
        style_summary = StyleSummary(
            layout={},
            spacing={},
            typography={},
            colors={},
            effects={},
        )
        animation_summary = AnimationSummary(
            css_animations=[],
            css_transitions=[],
            scroll_effects=[],
            recording=None,
        )
        interaction_summary = InteractionSummary(
            hoverable_elements=[],
            clickable_elements=[],
            focusable_elements=[],
            scroll_containers=[],
            observed_states={},
        )
        responsive_behavior = ResponsiveBehavior(
            breakpoints=[],
            is_fluid=True,
            has_mobile_menu=False,
            grid_changes=[],
        )
        asset = Asset(
            type=AssetType.IMAGE,
            original_url="https://example.com/image.png",
            local_path="/assets/image.png",
            file_size_bytes=12345,
            dimensions=[100, 100],
        )
        external_library = ExternalLibrary(
            name="jQuery",
            version="3.6.0",
            source_url="https://cdn.example.com/jquery.js",
            usage_snippets=["$('.test')"],
            init_code=None,
        )

        output = NormalizedOutput(
            page=page_info,
            target=target_info,
            dom=dom_tree,
            styles=style_summary,
            animations=animation_summary,
            interactions=interaction_summary,
            responsive_behavior=responsive_behavior,
            assets=[asset],
            external_libraries=[external_library],
        )

        assert output.page.url == "https://example.com"
        assert output.target.selector_used == ".test"
        assert output.dom.tag == "div"
        assert output.styles.layout == {}
        assert output.animations.css_animations == []
        assert output.interactions.hoverable_elements == []
        assert output.responsive_behavior.is_fluid is True
        assert len(output.assets) == 1
        assert output.assets[0].type == AssetType.IMAGE
        assert len(output.external_libraries) == 1
        assert output.external_libraries[0].name == "jQuery"
        assert output.mode == ExtractionMode.COMPONENT
        assert output.get_primary_screenshot_path() == "/output/screenshots/target.png"
        assert output.target.frame_limitations == ["Frame stylesheets blocked"]

    def test_normalized_output_requires_all_fields(self):
        """NormalizedOutput should require all component models."""
        with pytest.raises(ValidationError):
            NormalizedOutput()


class TestPageSectionSummary:
    """Tests for landing page section summaries."""

    def test_page_section_summary(self):
        """PageSectionSummary should capture basic section metadata."""
        section = PageSectionSummary(
            name="Hero",
            selector="section.hero",
            tag="section",
            text_excerpt="Launch your product faster",
            bounding_box=BoundingBox(x=0, y=0, width=1440, height=680),
        )

        assert section.name == "Hero"
        assert section.selector == "section.hero"
        assert section.bounding_box.height == 680


class TestPageCaptureInfo:
    """Tests for full-page capture metadata."""

    def test_page_capture_info(self):
        """PageCaptureInfo should store screenshot and section data."""
        capture = PageCaptureInfo(
            html="<body><section>Hero</section></body>",
            screenshot_path="/output/screenshots/page.png",
            bounding_box=BoundingBox(x=0, y=0, width=1440, height=3200),
            scroll_completed=True,
            sections=[
                PageSectionSummary(
                    name="Hero",
                    selector="section.hero",
                    tag="section",
                    text_excerpt="Build faster",
                    bounding_box=BoundingBox(x=0, y=0, width=1440, height=640),
                )
            ],
        )

        assert capture.scroll_completed is True
        assert capture.screenshot_path == "/output/screenshots/page.png"
        assert len(capture.sections) == 1


class TestFullPageNormalizedOutput:
    """Tests for full-page normalized output."""

    def test_full_page_output_with_all_fields(self):
        """FullPageNormalizedOutput should store landing page capture data."""
        page_info = PageInfo(
            url="https://example.com",
            title="Landing",
            viewport={"width": 1440, "height": 900},
            loaded_scripts=[],
            loaded_stylesheets=[],
        )
        dom_tree = DOMTree(
            tag="body",
            attributes={},
            children=[],
            text_content="",
            computed_styles={},
        )
        style_summary = StyleSummary(
            layout={},
            spacing={},
            typography={},
            colors={},
            effects={},
        )
        animation_summary = AnimationSummary(
            css_animations=[],
            css_transitions=[],
            scroll_effects=[],
            recording=None,
        )
        interaction_summary = InteractionSummary(
            hoverable_elements=[],
            clickable_elements=[],
            focusable_elements=[],
            scroll_containers=[],
            observed_states={},
        )
        responsive_behavior = ResponsiveBehavior(
            breakpoints=[],
            is_fluid=True,
            has_mobile_menu=True,
            grid_changes=[],
        )

        output = FullPageNormalizedOutput(
            page=page_info,
            page_capture=PageCaptureInfo(
                html="<body><section>Hero</section></body>",
                screenshot_path="/output/screenshots/page.png",
                bounding_box=BoundingBox(x=0, y=0, width=1440, height=3200),
                scroll_completed=True,
                sections=[],
            ),
            dom=dom_tree,
            styles=style_summary,
            animations=animation_summary,
            interactions=interaction_summary,
            responsive_behavior=responsive_behavior,
            assets=[],
            external_libraries=[],
        )

        assert output.mode == ExtractionMode.FULL_PAGE
        assert output.get_primary_screenshot_path() == "/output/screenshots/page.png"
