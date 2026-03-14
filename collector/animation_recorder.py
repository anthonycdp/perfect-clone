"""AnimationRecorder - Records animations via screenshots."""

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import Locator, Page

from models.extraction import AnimationRecording


class AnimationRecorder:
    """Records element animations using screenshots.

    Captures frames at ~30fps and detects key frames with significant
    visual changes for animation analysis.
    """

    def __init__(self, page: Page, output_dir: str):
        """Initialize AnimationRecorder.

        Args:
            page: Playwright Page object.
            output_dir: Directory to save animation recordings.
        """
        self.page = page
        self.output_dir = output_dir
        self.animations_dir = Path(output_dir) / "animations"

    def record(
        self, target: Locator, duration_ms: int = 2000
    ) -> Optional[AnimationRecording]:
        """Record target element animation via screenshots.

        Args:
            target: Locator for the element to record.
            duration_ms: Duration of recording in milliseconds.

        Returns:
            AnimationRecording with metadata, or None on failure.
        """
        try:
            # Create timestamped directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            recording_dir = self.animations_dir / timestamp
            frames_dir = recording_dir / "frames"
            frames_dir.mkdir(parents=True, exist_ok=True)

            # Capture frames at ~30fps
            fps = 30
            interval_ms = 1000 // fps
            frame_count = max(1, duration_ms // interval_ms)

            frames = []
            for i in range(frame_count):
                frame_path = frames_dir / f"frame_{i:04d}.png"
                target.screenshot(path=str(frame_path))
                frames.append(frame_path)

                # Sleep between frames (but not after the last one)
                if i < frame_count - 1:
                    time.sleep(interval_ms / 1000)

            # Detect key frames (significant visual changes)
            key_frames = self._detect_key_frames(frames_dir, frame_count)

            return AnimationRecording(
                video_path=str(recording_dir / "recording.webm"),
                duration_ms=float(duration_ms),
                fps=fps,
                frames_dir=str(frames_dir),
                key_frames=key_frames,
            )
        except Exception:
            return None

    def _detect_key_frames(self, frames_dir: Path, frame_count: int) -> list[int]:
        """Detect frames with significant visual changes.

        Uses simple file-based comparison to detect changes between frames.
        For more accurate detection, OpenCV could be used for frame diff analysis.

        Args:
            frames_dir: Directory containing frame images.
            frame_count: Total number of frames.

        Returns:
            List of frame indices that are key frames.
        """
        key_frames = [0]  # First frame is always a key frame

        if frame_count <= 1:
            return key_frames

        try:
            # Try to use OpenCV for better detection if available
            return self._detect_key_frames_opencv(frames_dir, frame_count)
        except ImportError:
            # Fall back to simple file-size based detection
            return self._detect_key_frames_simple(frames_dir, frame_count)

    def _detect_key_frames_opencv(self, frames_dir: Path, frame_count: int) -> list[int]:
        """Detect key frames using OpenCV frame differencing.

        Args:
            frames_dir: Directory containing frame images.
            frame_count: Total number of frames.

        Returns:
            List of frame indices that are key frames.
        """
        import cv2
        import numpy as np

        key_frames = [0]
        threshold = 30  # Mean pixel difference threshold

        # Load first frame
        prev_frame_path = frames_dir / "frame_0000.png"
        prev_frame = cv2.imread(str(prev_frame_path), cv2.IMREAD_GRAYSCALE)

        if prev_frame is None:
            return key_frames

        for i in range(1, frame_count):
            frame_path = frames_dir / f"frame_{i:04d}.png"
            curr_frame = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)

            if curr_frame is None:
                continue

            # Resize frames to match if needed
            if prev_frame.shape != curr_frame.shape:
                curr_frame = cv2.resize(
                    curr_frame, (prev_frame.shape[1], prev_frame.shape[0])
                )

            # Calculate absolute difference
            diff = cv2.absdiff(prev_frame, curr_frame)
            mean_diff = np.mean(diff)

            # If significant change detected, mark as key frame
            if mean_diff > threshold:
                key_frames.append(i)

            prev_frame = curr_frame

        return key_frames

    def _detect_key_frames_simple(self, frames_dir: Path, frame_count: int) -> list[int]:
        """Detect key frames using simple file size comparison.

        A fallback method when OpenCV is not available.

        Args:
            frames_dir: Directory containing frame images.
            frame_count: Total number of frames.

        Returns:
            List of frame indices that are key frames.
        """
        key_frames = [0]

        if frame_count <= 1:
            return key_frames

        # Get file sizes and detect significant changes
        sizes = []
        for i in range(frame_count):
            frame_path = frames_dir / f"frame_{i:04d}.png"
            if frame_path.exists():
                sizes.append((i, frame_path.stat().st_size))

        # Detect frames with size changes > 5%
        for i in range(1, len(sizes)):
            prev_size = sizes[i - 1][1]
            curr_size = sizes[i][1]

            if prev_size > 0:
                change_ratio = abs(curr_size - prev_size) / prev_size
                if change_ratio > 0.05:  # 5% threshold
                    key_frames.append(sizes[i][0])

        return key_frames
