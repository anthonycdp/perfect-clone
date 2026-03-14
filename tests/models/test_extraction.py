"""Tests for extraction data models."""

import pytest
from pydantic import ValidationError

from models.extraction import (
    SelectorStrategy,
    InteractionType,
    AssetType,
    BoundingBox,
    AnimationData,
    TransitionData,
    InteractionState,
    Asset,
    ExternalLibrary,
    ResponsiveBreakpoint,
    AnimationRecording,
)


class TestSelectorStrategy:
    """Tests for SelectorStrategy enum."""

    def test_css_value(self):
        """SelectorStrategy.CSS should be 'css'."""
        assert SelectorStrategy.CSS == "css"

    def test_xpath_value(self):
        """SelectorStrategy.XPATH should be 'xpath'."""
        assert SelectorStrategy.XPATH == "xpath"

    def test_text_value(self):
        """SelectorStrategy.TEXT should be 'text'."""
        assert SelectorStrategy.TEXT == "text"

    def test_html_snippet_value(self):
        """SelectorStrategy.HTML_SNIPPET should be 'html_snippet'."""
        assert SelectorStrategy.HTML_SNIPPET == "html_snippet"

    def test_all_values_count(self):
        """SelectorStrategy should have 4 values."""
        assert len(SelectorStrategy) == 4


class TestInteractionType:
    """Tests for InteractionType enum."""

    def test_hover_value(self):
        """InteractionType.HOVER should be 'hover'."""
        assert InteractionType.HOVER == "hover"

    def test_click_value(self):
        """InteractionType.CLICK should be 'click'."""
        assert InteractionType.CLICK == "click"

    def test_focus_value(self):
        """InteractionType.FOCUS should be 'focus'."""
        assert InteractionType.FOCUS == "focus"

    def test_scroll_value(self):
        """InteractionType.SCROLL should be 'scroll'."""
        assert InteractionType.SCROLL == "scroll"

    def test_all_values_count(self):
        """InteractionType should have 4 values."""
        assert len(InteractionType) == 4


class TestAssetType:
    """Tests for AssetType enum."""

    def test_image_value(self):
        """AssetType.IMAGE should be 'image'."""
        assert AssetType.IMAGE == "image"

    def test_svg_value(self):
        """AssetType.SVG should be 'svg'."""
        assert AssetType.SVG == "svg"

    def test_font_value(self):
        """AssetType.FONT should be 'font'."""
        assert AssetType.FONT == "font"

    def test_video_value(self):
        """AssetType.VIDEO should be 'video'."""
        assert AssetType.VIDEO == "video"

    def test_all_values_count(self):
        """AssetType should have 4 values."""
        assert len(AssetType) == 4


class TestBoundingBox:
    """Tests for BoundingBox model."""

    def test_bounding_box_with_floats(self):
        """BoundingBox should accept float values."""
        bbox = BoundingBox(x=10.5, y=20.3, width=100.7, height=50.2)
        assert bbox.x == 10.5
        assert bbox.y == 20.3
        assert bbox.width == 100.7
        assert bbox.height == 50.2

    def test_bounding_box_with_integers(self):
        """BoundingBox should accept integer values (converted to floats)."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        assert bbox.x == 10.0
        assert bbox.y == 20.0
        assert bbox.width == 100.0
        assert bbox.height == 50.0

    def test_bounding_box_requires_all_fields(self):
        """BoundingBox should require all fields."""
        with pytest.raises(ValidationError):
            BoundingBox(x=10, y=20)


class TestAnimationData:
    """Tests for AnimationData model."""

    def test_animation_data_with_all_fields(self):
        """AnimationData should accept all fields."""
        animation = AnimationData(
            name="fadeIn",
            duration="0.5s",
            delay="0.1s",
            timing_function="ease-in-out",
            iteration_count="infinite",
            direction="alternate",
            fill_mode="both",
            keyframes={"0%": {"opacity": "0"}, "100%": {"opacity": "1"}},
        )
        assert animation.name == "fadeIn"
        assert animation.duration == "0.5s"
        assert animation.delay == "0.1s"
        assert animation.timing_function == "ease-in-out"
        assert animation.iteration_count == "infinite"
        assert animation.direction == "alternate"
        assert animation.fill_mode == "both"
        assert animation.keyframes == {"0%": {"opacity": "0"}, "100%": {"opacity": "1"}}

    def test_animation_data_without_optional_fields(self):
        """AnimationData should work without optional name and keyframes."""
        animation = AnimationData(
            duration="0.3s",
            delay="0s",
            timing_function="linear",
            iteration_count="1",
            direction="normal",
            fill_mode="none",
        )
        assert animation.name is None
        assert animation.keyframes is None
        assert animation.duration == "0.3s"

    def test_animation_data_requires_required_fields(self):
        """AnimationData should require all non-optional fields."""
        with pytest.raises(ValidationError):
            AnimationData(name="test")


class TestTransitionData:
    """Tests for TransitionData model."""

    def test_transition_data(self):
        """TransitionData should accept all fields."""
        transition = TransitionData(
            property="opacity",
            duration="0.3s",
            timing_function="ease",
            delay="0.1s",
        )
        assert transition.property == "opacity"
        assert transition.duration == "0.3s"
        assert transition.timing_function == "ease"
        assert transition.delay == "0.1s"

    def test_transition_data_requires_all_fields(self):
        """TransitionData should require all fields."""
        with pytest.raises(ValidationError):
            TransitionData(property="opacity")


class TestInteractionState:
    """Tests for InteractionState model."""

    def test_interaction_state_with_enum(self):
        """InteractionState should accept InteractionType enum."""
        state = InteractionState(
            type=InteractionType.HOVER,
            selector=".button",
            before={"opacity": "1"},
            after={"opacity": "0.8"},
            duration_ms=150.5,
        )
        assert state.type == InteractionType.HOVER
        assert state.type == "hover"
        assert state.selector == ".button"
        assert state.before == {"opacity": "1"}
        assert state.after == {"opacity": "0.8"}
        assert state.duration_ms == 150.5

    def test_interaction_state_with_string(self):
        """InteractionState should accept string for type."""
        state = InteractionState(
            type="click",
            selector="#submit",
            before={},
            after={},
            duration_ms=50.0,
        )
        assert state.type == InteractionType.CLICK

    def test_interaction_state_requires_all_fields(self):
        """InteractionState should require all fields."""
        with pytest.raises(ValidationError):
            InteractionState(type=InteractionType.CLICK)


class TestAsset:
    """Tests for Asset model."""

    def test_asset_with_dimensions(self):
        """Asset should accept dimensions."""
        asset = Asset(
            type=AssetType.IMAGE,
            original_url="https://example.com/image.png",
            local_path="/assets/image.png",
            file_size_bytes=1024,
            dimensions=[200, 150],
        )
        assert asset.type == AssetType.IMAGE
        assert asset.original_url == "https://example.com/image.png"
        assert asset.local_path == "/assets/image.png"
        assert asset.file_size_bytes == 1024
        assert asset.dimensions == [200, 150]

    def test_asset_without_dimensions(self):
        """Asset should work without optional dimensions."""
        asset = Asset(
            type=AssetType.FONT,
            original_url="https://example.com/font.woff2",
            local_path="/assets/font.woff2",
            file_size_bytes=2048,
        )
        assert asset.dimensions is None

    def test_asset_requires_required_fields(self):
        """Asset should require type, original_url, local_path, and file_size_bytes."""
        with pytest.raises(ValidationError):
            Asset(type=AssetType.SVG)


class TestExternalLibrary:
    """Tests for ExternalLibrary model."""

    def test_external_library_with_all_fields(self):
        """ExternalLibrary should accept all fields."""
        library = ExternalLibrary(
            name="Swiper",
            version="9.0.0",
            source_url="https://cdn.jsdelivr.net/npm/swiper@9.0.0",
            usage_snippets=["new Swiper('.swiper')"],
            init_code="const swiper = new Swiper('.swiper');",
        )
        assert library.name == "Swiper"
        assert library.version == "9.0.0"
        assert library.source_url == "https://cdn.jsdelivr.net/npm/swiper@9.0.0"
        assert library.usage_snippets == ["new Swiper('.swiper')"]
        assert library.init_code == "const swiper = new Swiper('.swiper');"

    def test_external_library_without_optional_fields(self):
        """ExternalLibrary should work without optional version and init_code."""
        library = ExternalLibrary(
            name="GSAP",
            source_url="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.0/gsap.min.js",
            usage_snippets=["gsap.to('.el', {x: 100})"],
        )
        assert library.version is None
        assert library.init_code is None

    def test_external_library_requires_required_fields(self):
        """ExternalLibrary should require name, source_url, and usage_snippets."""
        with pytest.raises(ValidationError):
            ExternalLibrary(name="Test")


class TestResponsiveBreakpoint:
    """Tests for ResponsiveBreakpoint model."""

    def test_responsive_breakpoint_media_query(self):
        """ResponsiveBreakpoint should accept media_query source."""
        breakpoint = ResponsiveBreakpoint(
            width=768,
            height=1024,
            source="media_query",
            styles_diff={"font-size": "14px"},
            layout_changes=["column layout", "hidden sidebar"],
        )
        assert breakpoint.width == 768
        assert breakpoint.height == 1024
        assert breakpoint.source == "media_query"
        assert breakpoint.styles_diff == {"font-size": "14px"}
        assert breakpoint.layout_changes == ["column layout", "hidden sidebar"]

    def test_responsive_breakpoint_user_defined(self):
        """ResponsiveBreakpoint should accept user_defined source."""
        breakpoint = ResponsiveBreakpoint(
            width=480,
            height=800,
            source="user_defined",
            styles_diff={},
            layout_changes=[],
        )
        assert breakpoint.source == "user_defined"

    def test_responsive_breakpoint_requires_all_fields(self):
        """ResponsiveBreakpoint should require all fields."""
        with pytest.raises(ValidationError):
            ResponsiveBreakpoint(width=768)


class TestAnimationRecording:
    """Tests for AnimationRecording model."""

    def test_animation_recording(self):
        """AnimationRecording should accept all fields."""
        recording = AnimationRecording(
            video_path="/recordings/animation.mp4",
            duration_ms=2500.0,
            fps=60,
            frames_dir="/recordings/frames/",
            key_frames=[0, 15, 30, 60],
        )
        assert recording.video_path == "/recordings/animation.mp4"
        assert recording.duration_ms == 2500.0
        assert recording.fps == 60
        assert recording.frames_dir == "/recordings/frames/"
        assert recording.key_frames == [0, 15, 30, 60]

    def test_animation_recording_requires_all_fields(self):
        """AnimationRecording should require all fields."""
        with pytest.raises(ValidationError):
            AnimationRecording(video_path="/test.mp4")
