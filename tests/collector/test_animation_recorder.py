"""Tests for AnimationRecorder."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is at the FRONT of sys.path
project_root = str(Path(__file__).resolve().parent.parent.parent)
while project_root in sys.path:
    sys.path.remove(project_root)
sys.path.insert(0, project_root)

import pytest
from playwright.sync_api import Page, Locator

from collector.animation_recorder import AnimationRecorder
from models.extraction import AnimationRecording


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


class TestAnimationRecorderRecord:
    """Tests for AnimationRecorder.record()."""

    def test_record_returns_animation_recording(self, tmp_path):
        """record() should return AnimationRecording with correct metadata."""
        page = MagicMock(spec=Page)
        locator = MagicMock(spec=Locator)

        # Mock screenshot to create actual files
        def mock_screenshot(path):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            # Create a minimal valid PNG file (1x1 pixel)
            with open(path, "wb") as f:
                # Minimal PNG header + data
                f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 50)

        locator.screenshot.side_effect = mock_screenshot

        recorder = AnimationRecorder(page, str(tmp_path))
        result = recorder.record(locator, duration_ms=100)  # Short duration for test

        assert result is not None
        assert isinstance(result, AnimationRecording)
        assert result.duration_ms == 100.0
        assert result.fps == 30
        assert "frames" in result.frames_dir
        assert isinstance(result.key_frames, list)

    def test_record_creates_frames_directory(self, tmp_path):
        """record() should create timestamped frames directory."""
        page = MagicMock(spec=Page)
        locator = MagicMock(spec=Locator)

        def mock_screenshot(path):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 50)

        locator.screenshot.side_effect = mock_screenshot

        recorder = AnimationRecorder(page, str(tmp_path))
        result = recorder.record(locator, duration_ms=100)

        assert result is not None
        frames_dir = Path(result.frames_dir)
        assert frames_dir.exists()
        assert frames_dir.name == "frames"
        assert "animations" in str(frames_dir)

    def test_record_captures_correct_frame_count(self, tmp_path):
        """record() should capture frames at ~30fps."""
        page = MagicMock(spec=Page)
        locator = MagicMock(spec=Locator)

        def mock_screenshot(path):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 50)

        locator.screenshot.side_effect = mock_screenshot

        recorder = AnimationRecorder(page, str(tmp_path))
        result = recorder.record(locator, duration_ms=100)

        # 100ms at 30fps = 3 frames (interval is 33ms)
        assert locator.screenshot.call_count == 3

    def test_record_returns_none_on_error(self, tmp_path):
        """record() should return None if recording fails."""
        page = MagicMock(spec=Page)
        locator = MagicMock(spec=Locator)
        locator.screenshot.side_effect = Exception("Screenshot failed")

        recorder = AnimationRecorder(page, str(tmp_path))
        result = recorder.record(locator, duration_ms=100)

        assert result is None


class TestAnimationRecorderDetectKeyFrames:
    """Tests for AnimationRecorder._detect_key_frames()."""

    def test_detect_key_frames_returns_list(self, tmp_path):
        """_detect_key_frames() should return a list of frame indices."""
        page = MagicMock(spec=Page)
        locator = MagicMock(spec=Locator)

        def mock_screenshot(path):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            # Create different frames with varying content
            frame_num = int(Path(path).stem.split("_")[1])
            with open(path, "wb") as f:
                # Vary content slightly per frame
                f.write(b'\x89PNG\r\n\x1a\n' + bytes([frame_num % 256] * 50))

        locator.screenshot.side_effect = mock_screenshot

        recorder = AnimationRecorder(page, str(tmp_path))
        result = recorder.record(locator, duration_ms=100)

        assert result is not None
        assert isinstance(result.key_frames, list)
        # First frame is always a key frame
        assert 0 in result.key_frames

    def test_detect_key_frames_includes_first_frame(self, tmp_path):
        """_detect_key_frames() should always include frame 0."""
        page = MagicMock(spec=Page)
        locator = MagicMock(spec=Locator)

        def mock_screenshot(path):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 50)

        locator.screenshot.side_effect = mock_screenshot

        recorder = AnimationRecorder(page, str(tmp_path))
        result = recorder.record(locator, duration_ms=100)

        assert result is not None
        assert 0 in result.key_frames
