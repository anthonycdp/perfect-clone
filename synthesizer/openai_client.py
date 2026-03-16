"""OpenAI API client for synthesis."""

import base64
import io
import mimetypes
import os
from pathlib import Path

from openai import OpenAI
from PIL import Image

from models.errors import APIError
from models.normalized import FullPageNormalizedOutput, NormalizedOutput
from models.synthesis import SynthesisOutput
from synthesizer.prompts import SYSTEM_PROMPT, build_user_prompt


class OpenAISynthesizer:
    """Generate synthesis using OpenAI API."""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5.4"

    def synthesize(
        self,
        normalized_data: NormalizedOutput | FullPageNormalizedOutput,
    ) -> SynthesisOutput:
        """Generate synthesis from normalized data."""
        user_prompt = build_user_prompt(normalized_data)
        response_input = self._build_response_input(normalized_data, user_prompt)

        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=SYSTEM_PROMPT,
                input=response_input,
                text_format=SynthesisOutput,
            )
        except Exception as exc:
            raise APIError(f"Failed to communicate with OpenAI: {exc}") from exc

        if response.output_parsed is None:
            raise APIError("OpenAI returned a response that could not be parsed")

        return response.output_parsed

    def _build_response_input(
        self,
        normalized_data: NormalizedOutput | FullPageNormalizedOutput,
        user_prompt: str,
    ) -> list[dict]:
        """Build the multimodal user message for the Responses API."""
        content: list[dict[str, str]] = [
            {
                "type": "input_text",
                "text": user_prompt,
            }
        ]

        screenshot_data_url = self._build_screenshot_data_url(
            normalized_data.get_primary_screenshot_path()
        )
        if screenshot_data_url is not None:
            content.append(
                {
                    "type": "input_image",
                    "image_url": screenshot_data_url,
                }
            )

        return [
            {
                "role": "user",
                "content": content,
            }
        ]

    def _build_screenshot_data_url(self, screenshot_path: str | None) -> str | None:
        """Convert the target screenshot into a data URL for vision input."""
        if not screenshot_path:
            return None
        if not isinstance(screenshot_path, (str, os.PathLike)):
            return None

        screenshot_file = Path(screenshot_path)
        if not screenshot_file.exists():
            return None

        image_bytes, mime_type = self._load_image_bytes(screenshot_file)
        if image_bytes is None:
            return None

        mime_type = mime_type or "image/png"
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    def _load_image_bytes(self, screenshot_file: Path) -> tuple[bytes | None, str | None]:
        """Load an image, shrinking very large screenshots before upload."""
        mime_type, _ = mimetypes.guess_type(screenshot_file.name)

        try:
            with Image.open(screenshot_file) as image:
                if max(image.size) <= 2200:
                    return screenshot_file.read_bytes(), mime_type

                resized = image.copy()
                resized.thumbnail((2200, 2200))
                buffer = io.BytesIO()
                format_name = image.format or "PNG"
                resized.save(buffer, format=format_name)
                resized_bytes = buffer.getvalue()
                resized_mime = mime_type or Image.MIME.get(format_name, "image/png")
                return resized_bytes, resized_mime
        except Exception:
            try:
                return screenshot_file.read_bytes(), mime_type
            except Exception:
                return None, None
