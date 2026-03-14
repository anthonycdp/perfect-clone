"""OpenAI API client for synthesis."""

from openai import OpenAI

from models.normalized import NormalizedOutput
from models.synthesis import SynthesisOutput
from synthesizer.prompts import SYSTEM_PROMPT, build_user_prompt


class OpenAISynthesizer:
    """Generate synthesis using OpenAI API."""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5.4"

    def synthesize(self, normalized_data: NormalizedOutput) -> SynthesisOutput:
        """Generate synthesis from normalized data."""
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(normalized_data)},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "synthesis_output",
                    "schema": SynthesisOutput.model_json_schema(),
                }
            },
        )

        return SynthesisOutput.model_validate_json(response.output_text)
