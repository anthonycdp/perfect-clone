"""Tests for OpenAISynthesizer."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from models.extraction import BoundingBox, SelectorStrategy
from models.normalized import TargetInfo
from models.errors import APIError
from models.synthesis import (
    ComponentDescription,
    ComponentTree,
    Dependency,
    ResponsiveRule,
    SynthesisOutput,
)
from synthesizer.openai_client import OpenAISynthesizer
from synthesizer.prompts import SYSTEM_PROMPT


def build_synthesis_output() -> SynthesisOutput:
    """Create a valid synthesis output for tests."""
    return SynthesisOutput(
        description=ComponentDescription(
            technical="Technical description",
            visual="Visual description",
            purpose="Purpose description",
        ),
        component_tree=ComponentTree(
            name="HeroSection",
            role="container",
            children=[],
        ),
        interactions=[],
        responsive_rules=[
            ResponsiveRule(
                breakpoint="768px",
                changes=["Stack items vertically"],
            )
        ],
        dependencies=[
            Dependency(
                name="None",
                reason="No external dependency required",
            )
        ],
        recreation_prompt="Recreate the hero section",
    )


class TestOpenAISynthesizer:
    """Tests for the OpenAI synthesis client."""

    @patch("synthesizer.openai_client.build_user_prompt", return_value="user prompt")
    @patch("synthesizer.openai_client.OpenAI")
    def test_synthesize_uses_responses_parse(
        self,
        mock_openai,
        mock_build_user_prompt,
    ):
        """synthesize() should request a parsed structured response."""
        expected_output = build_synthesis_output()
        mock_client = Mock()
        mock_client.responses.parse.return_value = Mock(output_parsed=expected_output)
        mock_openai.return_value = mock_client

        synthesizer = OpenAISynthesizer(api_key="test-key")

        result = synthesizer.synthesize(Mock())

        assert result == expected_output
        mock_build_user_prompt.assert_called_once()
        mock_client.responses.parse.assert_called_once_with(
            model="gpt-5.4",
            instructions=SYSTEM_PROMPT,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "user prompt",
                        }
                    ],
                }
            ],
            text_format=SynthesisOutput,
        )

    @patch("synthesizer.openai_client.build_user_prompt", return_value="user prompt")
    @patch("synthesizer.openai_client.OpenAI")
    def test_synthesize_raises_api_error_when_response_is_not_parsed(
        self,
        mock_openai,
        _mock_build_user_prompt,
    ):
        """synthesize() should fail fast when the SDK returns no parsed object."""
        mock_client = Mock()
        mock_client.responses.parse.return_value = Mock(output_parsed=None)
        mock_openai.return_value = mock_client

        synthesizer = OpenAISynthesizer(api_key="test-key")

        with pytest.raises(APIError, match="could not be parsed"):
            synthesizer.synthesize(Mock())

    @patch("synthesizer.openai_client.build_user_prompt", return_value="user prompt")
    @patch("synthesizer.openai_client.OpenAI")
    def test_synthesize_sends_screenshot_when_available(
        self,
        mock_openai,
        _mock_build_user_prompt,
        tmp_path: Path,
    ):
        """synthesize() should include the target screenshot as vision input."""
        screenshot_path = tmp_path / "target.png"
        screenshot_path.write_bytes(b"fake-image")

        normalized_data = Mock()
        normalized_data.target = TargetInfo(
            selector_used=".target",
            strategy=SelectorStrategy.CSS,
            html="<div></div>",
            bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
            depth_in_dom=1,
            screenshot_path=str(screenshot_path),
        )
        normalized_data.get_primary_screenshot_path.return_value = str(screenshot_path)

        expected_output = build_synthesis_output()
        mock_client = Mock()
        mock_client.responses.parse.return_value = Mock(output_parsed=expected_output)
        mock_openai.return_value = mock_client

        synthesizer = OpenAISynthesizer(api_key="test-key")
        synthesizer.synthesize(normalized_data)

        parse_call = mock_client.responses.parse.call_args.kwargs
        assert parse_call["input"][0]["content"][0] == {
            "type": "input_text",
            "text": "user prompt",
        }
        image_part = parse_call["input"][0]["content"][1]
        assert image_part["type"] == "input_image"
        assert image_part["image_url"].startswith("data:image/png;base64,")

    @patch("synthesizer.openai_client.build_user_prompt", return_value="user prompt")
    @patch("synthesizer.openai_client.OpenAI")
    def test_synthesize_uses_full_page_screenshot_when_available(
        self,
        mock_openai,
        _mock_build_user_prompt,
        tmp_path: Path,
    ):
        """synthesize() should use the page screenshot for full-page mode."""
        screenshot_path = tmp_path / "page.png"
        screenshot_path.write_bytes(b"fake-image")

        normalized_data = Mock()
        normalized_data.get_primary_screenshot_path.return_value = str(screenshot_path)

        expected_output = build_synthesis_output()
        mock_client = Mock()
        mock_client.responses.parse.return_value = Mock(output_parsed=expected_output)
        mock_openai.return_value = mock_client

        synthesizer = OpenAISynthesizer(api_key="test-key")
        synthesizer.synthesize(normalized_data)

        parse_call = mock_client.responses.parse.call_args.kwargs
        image_part = parse_call["input"][0]["content"][1]
        assert image_part["type"] == "input_image"
        assert image_part["image_url"].startswith("data:image/png;base64,")
