"""Transform animation data into AnimationSummary."""

from typing import Any

from models.extraction import AnimationData, TransitionData
from models.normalized import AnimationSummary


class AnimationTransformer:
    """Process animation and transition data."""

    def transform(
        self,
        animations: list[dict],
        transitions: list[dict],
        keyframes: dict,
        recording: dict | None = None,
    ) -> AnimationSummary:
        """Transform animation data into AnimationSummary."""
        return AnimationSummary(
            css_animations=[
                AnimationData(**anim) for anim in animations
            ],
            css_transitions=[
                TransitionData(**trans) for trans in transitions
            ],
            scroll_effects=self._detect_scroll_effects(keyframes),
            recording=recording,
        )

    def _detect_scroll_effects(self, keyframes: dict) -> list[str]:
        """Detect scroll-driven animation patterns."""
        effects = []

        for name, frames in keyframes.items():
            # Check for parallax-like patterns
            if isinstance(frames, dict):
                for frame_key, frame_styles in frames.items():
                    if isinstance(frame_styles, dict) and "transform" in frame_styles:
                        transform_val = frame_styles.get("transform", "")
                        if "translateY" in transform_val or "translate3d" in transform_val:
                            effects.append(f"potential-parallax: {name}")
                            break

        return effects
