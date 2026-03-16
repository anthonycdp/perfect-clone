"""Tests for the async extraction runner."""

from pathlib import Path

import pytest

from models.extraction import BoundingBox, SelectorStrategy
from models.normalized import (
    AnimationSummary,
    DOMTree,
    InteractionSummary,
    NormalizedOutput,
    PageInfo,
    ResponsiveBehavior,
    StyleSummary,
    TargetInfo,
)
from models.requests import ExtractionRequest
from models.synthesis import (
    ComponentDescription,
    ComponentTree,
    Dependency,
    ResponsiveRule,
    SynthesisOutput,
)
from server.runner import run_extraction
from server.task import ExtractionTask


def build_normalized_output(workspace_dir: Path) -> NormalizedOutput:
    """Create a normalized output with packageable artifact paths."""
    screenshot_path = workspace_dir / "screenshots" / "target.png"
    asset_path = workspace_dir / "images" / "hero.png"
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    screenshot_path.write_bytes(b"png")
    asset_path.write_bytes(b"asset")

    return NormalizedOutput(
        page=PageInfo(
            url="https://example.com",
            title="Example",
            viewport={"width": 1280, "height": 720},
            loaded_scripts=[],
            loaded_stylesheets=[],
        ),
        target=TargetInfo(
            selector_used=".hero",
            strategy=SelectorStrategy.CSS,
            html="<section class='hero'></section>",
            bounding_box=BoundingBox(x=0, y=0, width=1200, height=500),
            depth_in_dom=2,
            screenshot_path=str(screenshot_path),
        ),
        dom=DOMTree(
            tag="section",
            attributes={"class": "hero"},
            children=[],
            text_content="Hero",
            computed_styles={},
        ),
        styles=StyleSummary(
            layout={},
            spacing={},
            typography={},
            colors={},
            effects={},
        ),
        animations=AnimationSummary(
            css_animations=[],
            css_transitions=[],
            scroll_effects=[],
            recording=None,
        ),
        interactions=InteractionSummary(
            hoverable_elements=[],
            clickable_elements=[],
            focusable_elements=[],
            scroll_containers=[],
            observed_states={},
        ),
        responsive_behavior=ResponsiveBehavior(
            breakpoints=[],
            is_fluid=True,
            has_mobile_menu=False,
            grid_changes=[],
        ),
        assets=[],
        external_libraries=[],
        collection_limitations=[],
        rich_media=[],
    )


def build_synthesis_output() -> SynthesisOutput:
    """Create the synthesis object returned by the fake orchestrator."""
    return SynthesisOutput(
        description=ComponentDescription(
            technical="Technical",
            visual="Visual",
            purpose="Purpose",
        ),
        component_tree=ComponentTree(name="Hero", role="section", children=[]),
        interactions=[],
        responsive_rules=[ResponsiveRule(breakpoint="768px", changes=["stack"])],
        dependencies=[Dependency(name="None", reason="No dependency")],
        recreation_prompt="Build the hero section.",
    )


@pytest.mark.asyncio
async def test_run_extraction_builds_downloadable_package(monkeypatch):
    """The runner should package task artifacts and expose task-scoped URLs."""
    import orchestrator as orchestrator_module

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeOrchestrator:
        def __init__(self, api_key: str, output_dir: str = "output"):
            assert api_key == "test-key"
            self.output_dir = Path(output_dir)
            self.last_normalized_output = build_normalized_output(self.output_dir)

        async def extract(self, **_kwargs):
            return build_synthesis_output()

    monkeypatch.setattr(orchestrator_module, "ExtractionOrchestrator", FakeOrchestrator)

    task = ExtractionTask(
        "task1234",
        ExtractionRequest(
            url="https://example.com",
            mode="component",
            strategy="css",
            query=".hero",
        ),
    )

    await run_extraction(task)

    assert task.completed is True
    assert task.package_path is not None and task.package_path.exists()
    assert task.result is not None
    assert task.result["download_url"] == "/api/extract/task1234/package"
    assert task.result["download_filename"] == "component-extractor-task1234.zip"
    assert task.result["screenshot_url"] == "/api/extract/task1234/artifacts/screenshots/target.png"
    assert task.result["full_json"]["target"]["screenshot_path"] == "screenshots/target.png"
    assert task.result["prompt"].startswith("Before building, inspect the files in this package")
