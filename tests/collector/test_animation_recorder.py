"""Tests for AnimationRecorder."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from playwright.async_api import Locator, Page

from collector.animation_recorder import AnimationRecorder
from models.extraction import AnimationRecording


def _build_locator_with_screenshot(side_effect) -> MagicMock:
    """Create a locator double whose screenshot method is awaitable."""
    locator = MagicMock(spec=Locator)
    locator.screenshot = AsyncMock(side_effect=side_effect)
    return locator


class TestAnimationRecorderInit:
    """Tests for AnimationRecorder initialization."""

    def test_init_creates_animation_directory(self, tmp_path):
        """init should create animations directory path."""
        page = MagicMock(spec=Page)
        output_dir = str(tmp_path)

        recorder = AnimationRecorder(page, output_dir)

        assert recorder.page == page
        assert recorder.output_dir == output_dir
        assert recorder.animations_dir == Path(output_dir) / "animations"

    def test_init_with_existing_directory(self, tmp_path):
        """init should work with existing output directory."""
        page = MagicMock(spec=Page)
        output_dir = str(tmp_path)

        recorder = AnimationRecorder(page, output_dir)

        assert recorder.output_dir == output_dir


@pytest.mark.asyncio
class TestAnimationRecorderRecord:
    """Tests for AnimationRecorder.record()."""

    async def test_record_returns_animation_recording(self, tmp_path):
        """record() should return AnimationRecording with correct metadata."""
        page = MagicMock(spec=Page)

        async def mock_screenshot(path, **_kwargs):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

        locator = _build_locator_with_screenshot(mock_screenshot)
        recorder = AnimationRecorder(page, str(tmp_path))

        result = await recorder.record(locator, duration_ms=100)

        assert result is not None
        assert isinstance(result, AnimationRecording)
        assert result.duration_ms == 100.0
        assert result.fps == 30
        assert "frames" in result.frames_dir
        assert isinstance(result.key_frames, list)

    async def test_record_creates_frames_directory(self, tmp_path):
        """record() should create timestamped frames directory."""
        page = MagicMock(spec=Page)

        async def mock_screenshot(path, **_kwargs):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

        locator = _build_locator_with_screenshot(mock_screenshot)
        recorder = AnimationRecorder(page, str(tmp_path))

        result = await recorder.record(locator, duration_ms=100)

        assert result is not None
        frames_dir = Path(result.frames_dir)
        assert frames_dir.exists()
        assert frames_dir.name == "frames"
        assert "animations" in str(frames_dir)

    async def test_record_captures_correct_frame_count(self, tmp_path):
        """record() should capture frames at ~30fps."""
        page = MagicMock(spec=Page)

        async def mock_screenshot(path, **_kwargs):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

        locator = _build_locator_with_screenshot(mock_screenshot)
        recorder = AnimationRecorder(page, str(tmp_path))

        await recorder.record(locator, duration_ms=100)

        assert locator.screenshot.await_count == 3

    async def test_record_returns_none_on_error(self, tmp_path):
        """record() should return None if recording fails."""
        page = MagicMock(spec=Page)
        locator = _build_locator_with_screenshot(Exception("Screenshot failed"))
        recorder = AnimationRecorder(page, str(tmp_path))

        result = await recorder.record(locator, duration_ms=100)

        assert result is None


@pytest.mark.asyncio
class TestAnimationRecorderDetectKeyFrames:
    """Tests for AnimationRecorder._detect_key_frames()."""

    async def test_detect_key_frames_returns_list(self, tmp_path):
        """_detect_key_frames() should return a list of frame indices."""
        page = MagicMock(spec=Page)

        async def mock_screenshot(path, **_kwargs):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            frame_num = int(Path(path).stem.split("_")[1])
            Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + bytes([frame_num % 256] * 50))

        locator = _build_locator_with_screenshot(mock_screenshot)
        recorder = AnimationRecorder(page, str(tmp_path))

        result = await recorder.record(locator, duration_ms=100)

        assert result is not None
        assert isinstance(result.key_frames, list)
        assert 0 in result.key_frames

    async def test_detect_key_frames_includes_first_frame(self, tmp_path):
        """_detect_key_frames() should always include frame 0."""
        page = MagicMock(spec=Page)

        async def mock_screenshot(path, **_kwargs):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

        locator = _build_locator_with_screenshot(mock_screenshot)
        recorder = AnimationRecorder(page, str(tmp_path))

        result = await recorder.record(locator, duration_ms=100)

        assert result is not None
        assert 0 in result.key_frames
