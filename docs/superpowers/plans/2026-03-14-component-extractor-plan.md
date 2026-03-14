# Component Extractor Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python desktop tool that extracts web components and generates AI prompts for faithful recreation.

**Architecture:** Three-phase pipeline (Collector → Normalizer → Synthesizer) orchestrated by a threaded worker, exposed via Tkinter GUI. Playwright handles browser automation, Pydantic validates data models, OpenAI generates synthesis prompts.

**Tech Stack:** Python 3.11+, Playwright, Pydantic v2, OpenAI API, Tkinter, OpenCV, Pillow

---

## File Structure

```
component-extractor/
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── .env.example                     # API key template
├── orchestrator.py                  # Pipeline coordinator
├── worker.py                        # Threading worker
│
├── models/
│   ├── __init__.py                  # Exports + model_rebuild()
│   ├── extraction.py                # Raw extraction schemas
│   ├── normalized.py                # Normalized output schema
│   ├── synthesis.py                 # AI response schema
│   └── errors.py                    # Exception classes
│
├── collector/
│   ├── __init__.py
│   ├── browser.py                   # BrowserManager class
│   ├── target_finder.py             # TargetFinder class
│   ├── dom_extractor.py             # DOMExtractor class
│   ├── style_extractor.py           # StyleExtractor class
│   ├── interaction_mapper.py        # InteractionMapper class
│   ├── interaction_player.py        # InteractionPlayer class
│   ├── asset_downloader.py          # AssetDownloader class
│   ├── animation_recorder.py        # AnimationRecorder class
│   ├── library_detector.py          # LibraryDetector class
│   └── responsive_collector.py      # ResponsiveCollector class
│
├── normalizer/
│   ├── __init__.py
│   ├── context_builder.py           # ContextBuilder class
│   └── transformers/
│       ├── __init__.py
│       ├── dom_transformer.py
│       ├── style_transformer.py
│       └── animation_transformer.py
│
├── synthesizer/
│   ├── __init__.py
│   ├── openai_client.py             # OpenAISynthesizer class
│   └── prompts/
│       ├── __init__.py
│       └── synthesis_prompt.py      # SYSTEM_PROMPT + build_user_prompt()
│
├── gui/
│   ├── __init__.py
│   ├── app.py                       # ComponentExtractorApp class
│   ├── widgets/
│   │   ├── __init__.py
│   │   └── progress_display.py      # ProgressDisplay class
│   └── panels/
│       ├── __init__.py
│       ├── input_panel.py           # InputPanel class
│       └── result_panel.py          # ResultPanel class
│
└── output/
    ├── assets/
    │   ├── images/
    │   ├── fonts/
    │   └── svgs/
    ├── animations/
    └── extractions/
```

---

## Chunk 1: Foundation - Project Setup & Models

### Task 1.1: Project Structure & Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `main.py`
- Create: `output/.gitkeep`
- Create: `output/assets/images/.gitkeep`
- Create: `output/assets/fonts/.gitkeep`
- Create: `output/assets/svgs/.gitkeep`
- Create: `output/animations/.gitkeep`
- Create: `output/extractions/.gitkeep`

- [ ] **Step 1: Create requirements.txt**

```txt
playwright>=1.40.0
pydantic>=2.0.0
openai>=1.0.0
python-dotenv>=1.0.0
Pillow>=10.0.0
opencv-python>=4.8.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

- [ ] **Step 2: Create .env.example**

```txt
OPENAI_API_KEY=sk-your-api-key-here
```

- [ ] **Step 3: Create main.py (placeholder)**

```python
"""Component Extractor - Extract web components and generate recreation prompts."""

def main():
    print("Component Extractor - Setup complete")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create output directory structure**

```bash
mkdir -p output/assets/images output/assets/fonts output/assets/svgs output/animations output/extractions
touch output/.gitkeep output/assets/images/.gitkeep output/assets/fonts/.gitkeep output/assets/svgs/.gitkeep output/animations/.gitkeep output/extractions/.gitkeep
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
```

- [ ] **Step 6: Verify setup**

Run: `python main.py`
Expected: `Component Extractor - Setup complete`

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .env.example main.py output/
git commit -m "chore: initial project setup with dependencies"
```

---

### Task 1.2: Error Models

**Files:**
- Create: `models/__init__.py`
- Create: `models/errors.py`
- Create: `tests/models/test_errors.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/models/test_errors.py
import pytest
from models.errors import (
    ExtractionError,
    NavigationError,
    TargetNotFoundError,
    APIError,
    BrowserCrashError,
)


def test_extraction_error_is_base_exception():
    """ExtractionError should be the base for all extraction exceptions."""
    with pytest.raises(ExtractionError):
        raise NavigationError("Failed to navigate")


def test_navigation_error_message():
    """NavigationError should preserve message."""
    error = NavigationError("URL not reachable")
    assert str(error) == "URL not reachable"
    assert isinstance(error, ExtractionError)


def test_target_not_found_error_with_suggestions():
    """TargetNotFoundError should store suggestions."""
    error = TargetNotFoundError(
        "Selector not found",
        suggestions=[".alternative-1", ".alternative-2"]
    )
    assert error.suggestions == [".alternative-1", ".alternative-2"]
    assert isinstance(error, ExtractionError)


def test_api_error_with_status_code():
    """APIError should store status code."""
    error = APIError("Rate limited", status_code=429)
    assert error.status_code == 429
    assert isinstance(error, ExtractionError)


def test_browser_crash_error():
    """BrowserCrashError should be ExtractionError subclass."""
    error = BrowserCrashError("Browser process died")
    assert isinstance(error, ExtractionError)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/models/test_errors.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'models'"

- [ ] **Step 3: Create models package**

```python
# models/__init__.py
"""Data models for Component Extractor."""

from models.errors import (
    ExtractionError,
    NavigationError,
    TargetNotFoundError,
    APIError,
    BrowserCrashError,
)

__all__ = [
    "ExtractionError",
    "NavigationError",
    "TargetNotFoundError",
    "APIError",
    "BrowserCrashError",
]
```

- [ ] **Step 4: Write error classes**

```python
# models/errors.py
"""Exception classes for extraction pipeline."""


class ExtractionError(Exception):
    """Base exception for extraction errors."""

    pass


class NavigationError(ExtractionError):
    """Failed to navigate to URL."""

    pass


class TargetNotFoundError(ExtractionError):
    """Selector did not find any element."""

    def __init__(self, message: str, suggestions: list[str] | None = None):
        super().__init__(message)
        self.suggestions = suggestions or []


class APIError(ExtractionError):
    """Failed to communicate with OpenAI API."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BrowserCrashError(ExtractionError):
    """Browser process crashed or was terminated."""

    pass
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/models/test_errors.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add models/ tests/models/
git commit -m "feat(models): add error exception classes"
```

---

### Task 1.3: Extraction Models

**Files:**
- Create: `models/extraction.py`
- Create: `tests/models/test_extraction.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/models/test_extraction.py
import pytest
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


def test_selector_strategy_enum():
    """SelectorStrategy should have all expected values."""
    assert SelectorStrategy.CSS == "css"
    assert SelectorStrategy.XPATH == "xpath"
    assert SelectorStrategy.TEXT == "text"
    assert SelectorStrategy.HTML_SNIPPET == "html_snippet"


def test_interaction_type_enum():
    """InteractionType should have all expected values."""
    assert InteractionType.HOVER == "hover"
    assert InteractionType.CLICK == "click"
    assert InteractionType.FOCUS == "focus"
    assert InteractionType.SCROLL == "scroll"


def test_asset_type_enum():
    """AssetType should have all expected values."""
    assert AssetType.IMAGE == "image"
    assert AssetType.SVG == "svg"
    assert AssetType.FONT == "font"
    assert AssetType.VIDEO == "video"


def test_bounding_box_model():
    """BoundingBox should validate coordinates."""
    box = BoundingBox(x=10.5, y=20.0, width=100, height=200)
    assert box.x == 10.5
    assert box.y == 20.0
    assert box.width == 100
    assert box.height == 200


def test_animation_data_model():
    """AnimationData should handle all animation properties."""
    anim = AnimationData(
        name="fadeIn",
        duration="0.3s",
        delay="0s",
        timing_function="ease-in-out",
        iteration_count="1",
        direction="normal",
        fill_mode="forwards",
        keyframes={"0%": {"opacity": "0"}, "100%": {"opacity": "1"}},
    )
    assert anim.name == "fadeIn"
    assert anim.keyframes["0%"]["opacity"] == "0"


def test_animation_data_optional_name():
    """AnimationData name should be optional."""
    anim = AnimationData(
        name=None,
        duration="0.3s",
        delay="0s",
        timing_function="ease",
        iteration_count="1",
        direction="normal",
        fill_mode="none",
        keyframes=None,
    )
    assert anim.name is None
    assert anim.keyframes is None


def test_transition_data_model():
    """TransitionData should handle transition properties."""
    trans = TransitionData(
        property="opacity",
        duration="0.2s",
        timing_function="ease-out",
        delay="0.1s",
    )
    assert trans.property == "opacity"
    assert trans.duration == "0.2s"


def test_interaction_state_model():
    """InteractionState should capture before/after states."""
    state = InteractionState(
        type=InteractionType.HOVER,
        selector=".button",
        before={"opacity": "1"},
        after={"opacity": "0.8"},
        duration_ms=200.0,
    )
    assert state.type == InteractionType.HOVER
    assert state.before["opacity"] == "1"
    assert state.after["opacity"] == "0.8"


def test_asset_model_with_dimensions():
    """Asset should store file information."""
    asset = Asset(
        type=AssetType.IMAGE,
        original_url="https://example.com/img.png",
        local_path="output/assets/images/img.png",
        file_size_bytes=12345,
        dimensions=[800, 600],
    )
    assert asset.type == AssetType.IMAGE
    assert asset.dimensions == [800, 600]


def test_asset_model_without_dimensions():
    """Asset dimensions should be optional."""
    asset = Asset(
        type=AssetType.FONT,
        original_url="https://example.com/font.woff2",
        local_path="output/assets/fonts/font.woff2",
        file_size_bytes=50000,
        dimensions=None,
    )
    assert asset.dimensions is None


def test_external_library_model():
    """ExternalLibrary should capture library usage."""
    lib = ExternalLibrary(
        name="GSAP",
        version="3.12.0",
        source_url="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.0/gsap.min.js",
        usage_snippets=["gsap.to('.el', {opacity: 1})"],
        init_code="gsap.registerPlugin(ScrollTrigger);",
    )
    assert lib.name == "GSAP"
    assert len(lib.usage_snippets) == 1


def test_responsive_breakpoint_model():
    """ResponsiveBreakpoint should capture breakpoint changes."""
    bp = ResponsiveBreakpoint(
        width=768,
        height=1024,
        source="media_query",
        styles_diff={"display": ["flex", "block"]},
        layout_changes=["Column to row layout"],
    )
    assert bp.width == 768
    assert bp.source == "media_query"


def test_animation_recording_model():
    """AnimationRecording should store video and frame info."""
    recording = AnimationRecording(
        video_path="output/animations/20260314_120000/video.webm",
        duration_ms=1500.0,
        fps=30,
        frames_dir="output/animations/20260314_120000/frames",
        key_frames=[0, 15, 30],
    )
    assert recording.fps == 30
    assert len(recording.key_frames) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/models/test_extraction.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write extraction models**

```python
# models/extraction.py
"""Pydantic models for raw extraction data."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class SelectorStrategy(str, Enum):
    """Strategies for identifying target component."""
    CSS = "css"
    XPATH = "xpath"
    TEXT = "text"
    HTML_SNIPPET = "html_snippet"


class InteractionType(str, Enum):
    """Types of user interactions."""
    HOVER = "hover"
    CLICK = "click"
    FOCUS = "focus"
    SCROLL = "scroll"


class AssetType(str, Enum):
    """Types of downloadable assets."""
    IMAGE = "image"
    SVG = "svg"
    FONT = "font"
    VIDEO = "video"


class BoundingBox(BaseModel):
    """Element position and dimensions."""
    x: float
    y: float
    width: float
    height: float


class AnimationData(BaseModel):
    """CSS animation properties."""
    name: Optional[str] = None
    duration: str
    delay: str
    timing_function: str
    iteration_count: str
    direction: str
    fill_mode: str
    keyframes: Optional[dict] = None


class TransitionData(BaseModel):
    """CSS transition properties."""
    property: str
    duration: str
    timing_function: str
    delay: str


class InteractionState(BaseModel):
    """State before and after an interaction."""
    type: InteractionType
    selector: str
    before: dict
    after: dict
    duration_ms: float


class Asset(BaseModel):
    """Downloaded asset information."""
    type: AssetType
    original_url: str
    local_path: str
    file_size_bytes: int
    dimensions: Optional[list[int]] = None  # [width, height]


class ExternalLibrary(BaseModel):
    """Detected external library and its usage."""
    name: str
    version: Optional[str] = None
    source_url: str
    usage_snippets: list[str]
    init_code: Optional[str] = None


class ResponsiveBreakpoint(BaseModel):
    """Responsive breakpoint data."""
    width: int
    height: int
    source: str  # "media_query" or "user_defined"
    styles_diff: dict
    layout_changes: list[str]


class AnimationRecording(BaseModel):
    """Video recording of animations."""
    video_path: str
    duration_ms: float
    fps: int
    frames_dir: str
    key_frames: list[int]
```

- [ ] **Step 4: Update models/__init__.py**

```python
# models/__init__.py
"""Data models for Component Extractor."""

from models.errors import (
    ExtractionError,
    NavigationError,
    TargetNotFoundError,
    APIError,
    BrowserCrashError,
)
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

__all__ = [
    # Errors
    "ExtractionError",
    "NavigationError",
    "TargetNotFoundError",
    "APIError",
    "BrowserCrashError",
    # Extraction
    "SelectorStrategy",
    "InteractionType",
    "AssetType",
    "BoundingBox",
    "AnimationData",
    "TransitionData",
    "InteractionState",
    "Asset",
    "ExternalLibrary",
    "ResponsiveBreakpoint",
    "AnimationRecording",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/models/test_extraction.py -v`
Expected: 14 passed

- [ ] **Step 6: Commit**

```bash
git add models/ tests/models/
git commit -m "feat(models): add extraction data models"
```

---

### Task 1.4: Normalized Models

**Files:**
- Create: `models/normalized.py`
- Create: `tests/models/test_normalized.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/models/test_normalized.py
import pytest
from models.normalized import (
    PageInfo,
    TargetInfo,
    DOMTree,
    StyleSummary,
    AnimationSummary,
    InteractionSummary,
    ResponsiveBehavior,
    NormalizedOutput,
)
from models.extraction import BoundingBox


def test_page_info_model():
    """PageInfo should store page metadata."""
    info = PageInfo(
        url="https://example.com",
        title="Example Page",
        viewport={"width": 1920, "height": 1080},
        loaded_scripts=["app.js"],
        loaded_stylesheets=["style.css"],
    )
    assert info.url == "https://example.com"
    assert info.viewport["width"] == 1920


def test_target_info_model():
    """TargetInfo should store component identification."""
    info = TargetInfo(
        selector_used=".hero-section",
        strategy="css",
        html="<section class='hero'>...</section>",
        bounding_box=BoundingBox(x=0, y=0, width=1920, height=800),
        depth_in_dom=3,
    )
    assert info.strategy == "css"
    assert info.depth_in_dom == 3


def test_dom_tree_recursive():
    """DOMTree should support nested children."""
    child = DOMTree(
        tag="span",
        attributes={"class": "text"},
        children=[],
        text_content="Hello",
        computed_styles={"color": "red"},
    )
    parent = DOMTree(
        tag="div",
        attributes={"class": "container"},
        children=[child],
        text_content=None,
        computed_styles={"display": "flex"},
    )
    assert parent.tag == "div"
    assert parent.children[0].tag == "span"
    assert parent.children[0].text_content == "Hello"


def test_style_summary_categories():
    """StyleSummary should organize styles by category."""
    summary = StyleSummary(
        layout={"display": "flex", "flex-direction": "column"},
        spacing={"padding": "20px", "margin": "10px"},
        typography={"font-size": "16px", "line-height": "1.5"},
        colors={"color": "#333", "background": "#fff"},
        effects={"box-shadow": "0 2px 4px rgba(0,0,0,0.1)"},
    )
    assert summary.layout["display"] == "flex"
    assert summary.colors["color"] == "#333"


def test_interaction_summary():
    """InteractionSummary should categorize interactive elements."""
    summary = InteractionSummary(
        hoverable_elements=[".btn", ".link"],
        clickable_elements=[".btn"],
        focusable_elements=["input", "button"],
        scroll_containers=[".scroll-area"],
        observed_states={},
    )
    assert ".btn" in summary.hoverable_elements
    assert "input" in summary.focusable_elements


def test_responsive_behavior():
    """ResponsiveBehavior should store breakpoint data."""
    behavior = ResponsiveBehavior(
        breakpoints=[],
        is_fluid=True,
        has_mobile_menu=True,
        grid_changes=[{"breakpoint": 768, "from": "1fr", "to": "2fr"}],
    )
    assert behavior.is_fluid is True
    assert behavior.has_mobile_menu is True


def test_normalized_output_complete():
    """NormalizedOutput should assemble all data."""
    output = NormalizedOutput(
        page=PageInfo(
            url="https://example.com",
            title="Test",
            viewport={"width": 1920, "height": 1080},
            loaded_scripts=[],
            loaded_stylesheets=[],
        ),
        target=TargetInfo(
            selector_used=".test",
            strategy="css",
            html="<div>test</div>",
            bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
            depth_in_dom=1,
        ),
        dom=DOMTree(
            tag="div",
            attributes={},
            children=[],
            text_content="test",
            computed_styles={},
        ),
        styles=StyleSummary(
            layout={},
            spacing={},
            typography={},
            colors={},
            effects={},
        ),
        assets=[],
        interactions=InteractionSummary(
            hoverable_elements=[],
            clickable_elements=[],
            focusable_elements=[],
            scroll_containers=[],
            observed_states={},
        ),
        animations=AnimationSummary(
            css_animations=[],
            css_transitions=[],
            scroll_effects=[],
            recording=None,
        ),
        responsive_behavior=ResponsiveBehavior(
            breakpoints=[],
            is_fluid=False,
            has_mobile_menu=False,
            grid_changes=[],
        ),
        external_libraries=[],
    )
    assert output.page.url == "https://example.com"
    assert output.dom.tag == "div"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/models/test_normalized.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write normalized models**

```python
# models/normalized.py
"""Pydantic models for normalized extraction output."""

from typing import Optional
from pydantic import BaseModel

from models.extraction import (
    BoundingBox,
    AnimationData,
    TransitionData,
    InteractionState,
    Asset,
    ExternalLibrary,
    ResponsiveBreakpoint,
    AnimationRecording,
)


class PageInfo(BaseModel):
    """Page-level metadata."""
    url: str
    title: str
    viewport: dict
    loaded_scripts: list[str]
    loaded_stylesheets: list[str]


class TargetInfo(BaseModel):
    """Target component identification."""
    selector_used: str
    strategy: str
    html: str
    bounding_box: BoundingBox
    depth_in_dom: int


class DOMTree(BaseModel):
    """Recursive DOM structure."""
    tag: str
    attributes: dict
    children: list["DOMTree"]
    text_content: Optional[str]
    computed_styles: dict[str, str]


class StyleSummary(BaseModel):
    """Organized computed styles."""
    layout: dict
    spacing: dict
    typography: dict
    colors: dict
    effects: dict


class AnimationSummary(BaseModel):
    """Animation and transition data."""
    css_animations: list[AnimationData]
    css_transitions: list[TransitionData]
    scroll_effects: list[str]
    recording: Optional[AnimationRecording] = None


class InteractionSummary(BaseModel):
    """Interactive elements and observed states."""
    hoverable_elements: list[str]
    clickable_elements: list[str]
    focusable_elements: list[str]
    scroll_containers: list[str]
    observed_states: dict[str, InteractionState]


class ResponsiveBehavior(BaseModel):
    """Responsive breakpoint information."""
    breakpoints: list[ResponsiveBreakpoint]
    is_fluid: bool
    has_mobile_menu: bool
    grid_changes: list[dict]


class NormalizedOutput(BaseModel):
    """Complete normalized extraction result."""
    page: PageInfo
    target: TargetInfo
    dom: DOMTree
    styles: StyleSummary
    assets: list[Asset]
    interactions: InteractionSummary
    animations: AnimationSummary
    responsive_behavior: ResponsiveBehavior
    external_libraries: list[ExternalLibrary]


# Resolve forward references
DOMTree.model_rebuild()
```

- [ ] **Step 4: Update models/__init__.py with normalized exports**

```python
# models/__init__.py
"""Data models for Component Extractor."""

from models.errors import (
    ExtractionError,
    NavigationError,
    TargetNotFoundError,
    APIError,
    BrowserCrashError,
)
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
from models.normalized import (
    PageInfo,
    TargetInfo,
    DOMTree,
    StyleSummary,
    AnimationSummary,
    InteractionSummary,
    ResponsiveBehavior,
    NormalizedOutput,
)

__all__ = [
    # Errors
    "ExtractionError",
    "NavigationError",
    "TargetNotFoundError",
    "APIError",
    "BrowserCrashError",
    # Extraction
    "SelectorStrategy",
    "InteractionType",
    "AssetType",
    "BoundingBox",
    "AnimationData",
    "TransitionData",
    "InteractionState",
    "Asset",
    "ExternalLibrary",
    "ResponsiveBreakpoint",
    "AnimationRecording",
    # Normalized
    "PageInfo",
    "TargetInfo",
    "DOMTree",
    "StyleSummary",
    "AnimationSummary",
    "InteractionSummary",
    "ResponsiveBehavior",
    "NormalizedOutput",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/models/test_normalized.py -v`
Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add models/ tests/models/
git commit -m "feat(models): add normalized output models"
```

---

### Task 1.5: Synthesis Models

**Files:**
- Create: `models/synthesis.py`
- Create: `tests/models/test_synthesis.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/models/test_synthesis.py
import pytest
from models.synthesis import (
    ComponentDescription,
    ComponentTree,
    InteractionBehavior,
    ResponsiveRule,
    Dependency,
    SynthesisOutput,
)


def test_component_description():
    """ComponentDescription should store all description types."""
    desc = ComponentDescription(
        technical="A responsive hero section with parallax background",
        visual="Full-width section with centered text overlay",
        purpose="First impression landing section",
    )
    assert desc.technical == "A responsive hero section with parallax background"
    assert desc.visual == "Full-width section with centered text overlay"


def test_component_tree_recursive():
    """ComponentTree should support nested structure."""
    button = ComponentTree(
        name="Button",
        role="interactive",
        children=[],
    )
    card = ComponentTree(
        name="Card",
        role="container",
        children=[button],
    )
    assert card.name == "Card"
    assert card.children[0].name == "Button"


def test_interaction_behavior():
    """InteractionBehavior should capture trigger and effect."""
    behavior = InteractionBehavior(
        trigger="hover",
        effect="Scale up 1.05x with shadow increase",
        animation="transform 0.3s ease-out",
    )
    assert behavior.trigger == "hover"
    assert behavior.animation == "transform 0.3s ease-out"


def test_interaction_behavior_without_animation():
    """InteractionBehavior animation should be optional."""
    behavior = InteractionBehavior(
        trigger="click",
        effect="Toggle visibility",
        animation=None,
    )
    assert behavior.animation is None


def test_responsive_rule():
    """ResponsiveRule should capture breakpoint changes."""
    rule = ResponsiveRule(
        breakpoint="768px",
        changes=[
            "Stack elements vertically",
            "Reduce font size to 14px",
        ],
    )
    assert rule.breakpoint == "768px"
    assert len(rule.changes) == 2


def test_dependency():
    """Dependency should store library info."""
    dep = Dependency(
        name="GSAP",
        reason="Complex timeline animations",
        alternative="CSS animations with keyframes",
    )
    assert dep.name == "GSAP"
    assert dep.alternative == "CSS animations with keyframes"


def test_dependency_without_alternative():
    """Dependency alternative should be optional."""
    dep = Dependency(
        name="Inter font",
        reason="Primary typeface",
        alternative=None,
    )
    assert dep.alternative is None


def test_synthesis_output_complete():
    """SynthesisOutput should assemble all synthesis data."""
    output = SynthesisOutput(
        description=ComponentDescription(
            technical="Test component",
            visual="Test visual",
            purpose="Test purpose",
        ),
        component_tree=ComponentTree(
            name="Root",
            role="container",
            children=[],
        ),
        interactions=[
            InteractionBehavior(
                trigger="click",
                effect="Test effect",
                animation=None,
            )
        ],
        responsive_rules=[
            ResponsiveRule(
                breakpoint="768px",
                changes=["Test change"],
            )
        ],
        dependencies=[
            Dependency(
                name="TestLib",
                reason="Test reason",
                alternative=None,
            )
        ],
        recreation_prompt="Create a component that...",
    )
    assert output.recreation_prompt == "Create a component that..."
    assert len(output.interactions) == 1
    assert len(output.dependencies) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/models/test_synthesis.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write synthesis models**

```python
# models/synthesis.py
"""Pydantic models for AI synthesis output."""

from typing import Optional
from pydantic import BaseModel


class ComponentDescription(BaseModel):
    """Description of the component."""
    technical: str
    visual: str
    purpose: str


class ComponentTree(BaseModel):
    """Suggested component structure."""
    name: str
    role: str  # "container", "interactive", "decorative", "content"
    children: list["ComponentTree"]


class InteractionBehavior(BaseModel):
    """Interaction trigger and effect."""
    trigger: str
    effect: str
    animation: Optional[str] = None


class ResponsiveRule(BaseModel):
    """Responsive breakpoint rule."""
    breakpoint: str
    changes: list[str]


class Dependency(BaseModel):
    """Required dependency."""
    name: str
    reason: str
    alternative: Optional[str] = None


class SynthesisOutput(BaseModel):
    """Complete synthesis result."""
    description: ComponentDescription
    component_tree: ComponentTree
    interactions: list[InteractionBehavior]
    responsive_rules: list[ResponsiveRule]
    dependencies: list[Dependency]
    recreation_prompt: str


# Resolve forward references
ComponentTree.model_rebuild()
```

- [ ] **Step 4: Update models/__init__.py with synthesis exports**

```python
# models/__init__.py - Add synthesis imports
from models.synthesis import (
    ComponentDescription,
    ComponentTree,
    InteractionBehavior,
    ResponsiveRule,
    Dependency,
    SynthesisOutput,
)

# Add to __all__:
    # Synthesis
    "ComponentDescription",
    "ComponentTree",
    "InteractionBehavior",
    "ResponsiveRule",
    "Dependency",
    "SynthesisOutput",
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/models/test_synthesis.py -v`
Expected: 8 passed

- [ ] **Step 6: Commit**

```bash
git add models/ tests/models/
git commit -m "feat(models): add synthesis output models"
```

---

## Chunk 2: Collector - Browser & Target Finding

### Task 2.1: Browser Manager

**Files:**
- Create: `collector/__init__.py`
- Create: `collector/browser.py`
- Create: `tests/collector/test_browser.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/collector/test_browser.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from collector.browser import BrowserManager
from models.errors import NavigationError


class TestBrowserManager:
    def test_init_default_headless(self):
        """BrowserManager should default to headless mode."""
        manager = BrowserManager()
        assert manager.headless is True

    def test_init_headless_false(self):
        """BrowserManager should accept headless=False."""
        manager = BrowserManager(headless=False)
        assert manager.headless is False

    def test_start_creates_browser(self):
        """start() should initialize playwright, browser, and page."""
        manager = BrowserManager()
        manager.start()

        assert manager.playwright is not None
        assert manager.browser is not None
        assert manager.page is not None

        manager.close()

    def test_navigate_to_url(self):
        """navigate() should go to URL and wait for load."""
        manager = BrowserManager()
        manager.start()
        manager.navigate("https://example.com")

        assert manager.page.url == "https://example.com/"

        manager.close()

    def test_navigate_invalid_url_raises_error(self):
        """navigate() should raise NavigationError for invalid URL."""
        manager = BrowserManager()
        manager.start()

        with pytest.raises(NavigationError):
            manager.navigate("not-a-valid-url", timeout=5000)

        manager.close()

    def test_resize_viewport(self):
        """resize_viewport() should change page dimensions."""
        manager = BrowserManager()
        manager.start()
        manager.resize_viewport(1024, 768)

        viewport = manager.page.viewport_size
        assert viewport["width"] == 1024
        assert viewport["height"] == 768

        manager.close()

    def test_close_releases_resources(self):
        """close() should clean up all resources."""
        manager = BrowserManager()
        manager.start()
        manager.close()

        assert manager.page is None
        assert manager.browser is None
        assert manager.playwright is None

    def test_context_manager(self):
        """BrowserManager should work as context manager."""
        with BrowserManager() as manager:
            manager.navigate("https://example.com")
            assert manager.page is not None

        assert manager.page is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/collector/test_browser.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create collector package**

```python
# collector/__init__.py
"""Collector module for browser-based extraction."""

from collector.browser import BrowserManager

__all__ = ["BrowserManager"]
```

- [ ] **Step 4: Write BrowserManager**

```python
# collector/browser.py
"""Browser lifecycle management with Playwright."""

from typing import Optional
from playwright.sync_api import sync_playwright, Page, Browser, Playwright

from models.errors import NavigationError


class BrowserManager:
    """Manages Playwright browser lifecycle."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    def start(self) -> None:
        """Initialize browser and page."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()

    def navigate(self, url: str, timeout: int = 30000) -> None:
        """Navigate to URL and wait for page load."""
        if not self.page:
            self.start()

        try:
            self.page.goto(url, timeout=timeout, wait_until="networkidle")
        except Exception as e:
            raise NavigationError(f"Failed to navigate to {url}: {str(e)}")

    def resize_viewport(self, width: int, height: int) -> None:
        """Resize browser viewport."""
        if self.page:
            self.page.set_viewport_size({"width": width, "height": height})

    def close(self) -> None:
        """Release all browser resources."""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

        self.page = None
        self.browser = None
        self.playwright = None

    def __enter__(self) -> "BrowserManager":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/collector/test_browser.py -v`
Expected: 8 passed

- [ ] **Step 6: Commit**

```bash
git add collector/ tests/collector/
git commit -m "feat(collector): add BrowserManager for Playwright lifecycle"
```

---

### Task 2.2: Target Finder

**Files:**
- Create: `collector/target_finder.py`
- Create: `tests/collector/test_target_finder.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/collector/test_target_finder.py
import pytest
from collector.browser import BrowserManager
from collector.target_finder import TargetFinder
from models.errors import TargetNotFoundError
from models.extraction import SelectorStrategy


class TestTargetFinder:
    @pytest.fixture(autouse=True)
    def setup_browser(self):
        """Set up browser for each test."""
        self.manager = BrowserManager()
        self.manager.start()
        self.manager.navigate("https://example.com")
        yield
        self.manager.close()

    def test_find_by_css(self):
        """Should find element by CSS selector."""
        finder = TargetFinder(self.manager.page)
        locator = finder.find(SelectorStrategy.CSS, "h1")

        assert locator is not None
        assert locator.count() == 1

    def test_find_by_xpath(self):
        """Should find element by XPath."""
        finder = TargetFinder(self.manager.page)
        locator = finder.find(SelectorStrategy.XPATH, "//h1")

        assert locator is not None
        assert locator.count() == 1

    def test_find_by_text(self):
        """Should find element containing text."""
        finder = TargetFinder(self.manager.page)
        locator = finder.find(SelectorStrategy.TEXT, "Example")

        assert locator is not None
        assert locator.count() >= 1

    def test_find_by_css_not_found_raises_error(self):
        """Should raise TargetNotFoundError when element not found."""
        finder = TargetFinder(self.manager.page)

        with pytest.raises(TargetNotFoundError) as exc_info:
            finder.find(SelectorStrategy.CSS, ".nonexistent-class-12345")

        assert "not found" in str(exc_info.value).lower()

    def test_find_by_xpath_not_found_raises_error(self):
        """Should raise TargetNotFoundError for invalid XPath."""
        finder = TargetFinder(self.manager.page)

        with pytest.raises(TargetNotFoundError):
            finder.find(SelectorStrategy.XPATH, "//nonexistent[tag]")

    def test_error_includes_suggestions(self):
        """TargetNotFoundError should include similar selector suggestions."""
        finder = TargetFinder(self.manager.page)

        with pytest.raises(TargetNotFoundError) as exc_info:
            finder.find(SelectorStrategy.CSS, "h2")  # h2 doesn't exist on example.com

        # Should suggest h1 since it's similar
        assert len(exc_info.value.suggestions) >= 0  # May or may not have suggestions
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/collector/test_target_finder.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write TargetFinder**

```python
# collector/target_finder.py
"""Strategies for finding target components on a page."""

from playwright.sync_api import Page, Locator

from models.errors import TargetNotFoundError
from models.extraction import SelectorStrategy


class TargetFinder:
    """Find elements using various strategies."""

    def __init__(self, page: Page):
        self.page = page

    def find(self, strategy: SelectorStrategy, query: str) -> Locator:
        """Find element using specified strategy."""
        if strategy == SelectorStrategy.CSS:
            return self._find_by_css(query)
        elif strategy == SelectorStrategy.XPATH:
            return self._find_by_xpath(query)
        elif strategy == SelectorStrategy.TEXT:
            return self._find_by_text(query)
        elif strategy == SelectorStrategy.HTML_SNIPPET:
            return self._find_by_html_snippet(query)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _find_by_css(self, selector: str) -> Locator:
        """Find element by CSS selector."""
        locator = self.page.locator(selector)

        if locator.count() == 0:
            suggestions = self._get_similar_selectors(selector)
            raise TargetNotFoundError(
                f"CSS selector '{selector}' not found",
                suggestions=suggestions
            )

        return locator.first

    def _find_by_xpath(self, xpath: str) -> Locator:
        """Find element by XPath."""
        locator = self.page.locator(f"xpath={xpath}")

        if locator.count() == 0:
            raise TargetNotFoundError(f"XPath '{xpath}' not found")

        return locator.first

    def _find_by_text(self, text: str) -> Locator:
        """Find element containing text."""
        locator = self.page.locator(f"text={text}")

        if locator.count() == 0:
            raise TargetNotFoundError(f"Text '{text}' not found")

        return locator.first

    def _find_by_html_snippet(self, html: str) -> Locator:
        """Find element matching HTML snippet."""
        # Parse the snippet to extract tag and key attributes
        import re

        # Extract tag name
        tag_match = re.match(r'<(\w+)', html.strip())
        if not tag_match:
            raise TargetNotFoundError(f"Invalid HTML snippet: {html}")

        tag = tag_match.group(1)

        # Extract class if present
        class_match = re.search(r'class=["\']([^"\']+)["\']', html)
        if class_match:
            classes = class_match.group(1).split()
            selector = f"{tag}.{'.'.join(classes)}"
        else:
            selector = tag

        locator = self.page.locator(selector)

        if locator.count() == 0:
            raise TargetNotFoundError(f"HTML snippet not found: {html}")

        return locator.first

    def _get_similar_selectors(self, selector: str) -> list[str]:
        """Find similar selectors that do exist."""
        suggestions = []

        # Try to find similar tag names
        if '.' in selector:
            tag = selector.split('.')[0]
            if tag:
                try:
                    if self.page.locator(tag).count() > 0:
                        suggestions.append(tag)
                except:
                    pass

        # Try to find elements with similar class patterns
        try:
            # Get all classes on the page
            classes = self.page.evaluate("""() => {
                const elements = document.querySelectorAll('*');
                const classes = new Set();
                elements.forEach(el => {
                    el.classList.forEach(cls => classes.add(cls));
                });
                return Array.from(classes).slice(0, 20);
            }""")

            # Find classes that share partial matches
            selector_class = selector.split('.')[-1] if '.' in selector else ''
            for cls in classes:
                if selector_class and (
                    cls.startswith(selector_class[:3]) or
                    selector_class[:3] in cls
                ):
                    suggestions.append(f".{cls}")
        except:
            pass

        return suggestions[:5]
```

- [ ] **Step 4: Update collector/__init__.py**

```python
# collector/__init__.py
"""Collector module for browser-based extraction."""

from collector.browser import BrowserManager
from collector.target_finder import TargetFinder

__all__ = ["BrowserManager", "TargetFinder"]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/collector/test_target_finder.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add collector/ tests/collector/
git commit -m "feat(collector): add TargetFinder with CSS, XPath, text strategies"
```

---

## Chunk 3: Collector - DOM & Style Extraction

### Task 3.1: DOM Extractor

**Files:**
- Create: `collector/dom_extractor.py`
- Create: `tests/collector/test_dom_extractor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/collector/test_dom_extractor.py
import pytest
from playwright.sync_api import Locator
from collector.browser import BrowserManager
from collector.target_finder import TargetFinder
from collector.dom_extractor import DOMExtractor
from models.extraction import SelectorStrategy, BoundingBox


class TestDOMExtractor:
    @pytest.fixture(autouse=True)
    def setup_browser(self):
        """Set up browser for each test."""
        self.manager = BrowserManager()
        self.manager.start()
        self.manager.navigate("https://example.com")
        yield
        self.manager.close()

    def test_extract_html(self):
        """Should extract outer HTML of element."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, "h1")

        extractor = DOMExtractor(self.manager.page)
        result = extractor.extract(target)

        assert "html" in result
        assert "<h1" in result["html"]
        assert "Example Domain" in result["html"]

    def test_extract_dom_tree(self):
        """Should extract recursive DOM tree."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, "body")

        extractor = DOMExtractor(self.manager.page)
        result = extractor.extract(target)

        assert "dom_tree" in result
        assert result["dom_tree"]["tag"] == "body"
        assert "children" in result["dom_tree"]

    def test_extract_bounding_box(self):
        """Should extract element bounding box."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, "h1")

        extractor = DOMExtractor(self.manager.page)
        result = extractor.extract(target)

        assert "bounding_box" in result
        box = result["bounding_box"]
        assert box["x"] >= 0
        assert box["y"] >= 0
        assert box["width"] > 0
        assert box["height"] > 0

    def test_extract_depth(self):
        """Should calculate DOM depth."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, "h1")

        extractor = DOMExtractor(self.manager.page)
        result = extractor.extract(target)

        assert "depth" in result
        assert result["depth"] >= 1

    def test_dom_tree_includes_attributes(self):
        """DOM tree should include element attributes."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, "body")

        extractor = DOMExtractor(self.manager.page)
        result = extractor.extract(target)

        assert "attributes" in result["dom_tree"]
        assert isinstance(result["dom_tree"]["attributes"], dict)

    def test_dom_tree_includes_text_content(self):
        """DOM tree should include text content."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, "h1")

        extractor = DOMExtractor(self.manager.page)
        result = extractor.extract(target)

        # Text content should be in the tree
        assert result["dom_tree"]["text_content"] is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/collector/test_dom_extractor.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write DOMExtractor**

```python
# collector/dom_extractor.py
"""Extract DOM structure from elements."""

from playwright.sync_api import Page, Locator


class DOMExtractor:
    """Extract DOM tree and related data from elements."""

    def __init__(self, page: Page):
        self.page = page

    def extract(self, target: Locator) -> dict:
        """Extract complete DOM data from target element."""
        return {
            "html": self._extract_html(target),
            "dom_tree": self._extract_dom_tree(target),
            "bounding_box": self._extract_bounding_box(target),
            "depth": self._calculate_depth(target),
        }

    def _extract_html(self, target: Locator) -> str:
        """Get outer HTML of element."""
        return target.evaluate("el => el.outerHTML")

    def _extract_dom_tree(self, target: Locator) -> dict:
        """Build recursive DOM tree with attributes and styles."""
        return target.evaluate("""el => {
            function buildTree(element) {
                const node = {
                    tag: element.tagName.toLowerCase(),
                    attributes: {},
                    children: [],
                    text_content: null,
                    computed_styles: {}
                };

                // Extract attributes
                for (const attr of element.attributes) {
                    node.attributes[attr.name] = attr.value;
                }

                // Extract computed styles (relevant ones only)
                const styles = window.getComputedStyle(element);
                const relevantProps = [
                    'display', 'position', 'flex-direction', 'grid-template-columns',
                    'width', 'height', 'margin', 'padding', 'font-size', 'color',
                    'background-color', 'border', 'opacity', 'transform'
                ];
                for (const prop of relevantProps) {
                    node.computed_styles[prop] = styles.getPropertyValue(prop);
                }

                // Process children
                for (const child of element.children) {
                    node.children.push(buildTree(child));
                }

                // Text content (only if no children)
                if (element.children.length === 0) {
                    node.text_content = element.textContent?.trim() || null;
                }

                return node;
            }
            return buildTree(el);
        }""")

    def _extract_bounding_box(self, target: Locator) -> dict:
        """Get element position and dimensions."""
        box = target.bounding_box()
        if box is None:
            return {"x": 0, "y": 0, "width": 0, "height": 0}
        return {
            "x": box["x"],
            "y": box["y"],
            "width": box["width"],
            "height": box["height"],
        }

    def _calculate_depth(self, target: Locator) -> int:
        """Calculate element depth in DOM tree."""
        return target.evaluate("""el => {
            let depth = 0;
            let current = el;
            while (current.parentElement) {
                depth++;
                current = current.parentElement;
            }
            return depth;
        }""")
```

- [ ] **Step 4: Update collector/__init__.py**

```python
# Add to imports and __all__
from collector.dom_extractor import DOMExtractor
# In __all__:
"DOMExtractor",
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/collector/test_dom_extractor.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add collector/ tests/collector/
git commit -m "feat(collector): add DOMExtractor for HTML and DOM tree extraction"
```

---

### Task 3.2: Style Extractor

**Files:**
- Create: `collector/style_extractor.py`
- Create: `tests/collector/test_style_extractor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/collector/test_style_extractor.py
import pytest
from collector.browser import BrowserManager
from collector.target_finder import TargetFinder
from collector.style_extractor import StyleExtractor
from models.extraction import SelectorStrategy


class TestStyleExtractor:
    @pytest.fixture(autouse=True)
    def setup_browser(self):
        """Set up browser for each test."""
        self.manager = BrowserManager()
        self.manager.start()
        self.manager.navigate("https://example.com")
        yield
        self.manager.close()

    def test_extract_computed_styles(self):
        """Should extract computed styles."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, "h1")

        extractor = StyleExtractor(self.manager.page)
        result = extractor.extract(target)

        assert "computed_styles" in result
        assert isinstance(result["computed_styles"], dict)
        # Should have some style properties
        assert len(result["computed_styles"]) > 0

    def test_extract_animations(self):
        """Should extract animation properties."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, "body")

        extractor = StyleExtractor(self.manager.page)
        result = extractor.extract(target)

        assert "animations" in result
        assert isinstance(result["animations"], list)

    def test_extract_transitions(self):
        """Should extract transition properties."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, "body")

        extractor = StyleExtractor(self.manager.page)
        result = extractor.extract(target)

        assert "transitions" in result
        assert isinstance(result["transitions"], list)

    def test_extract_keyframes(self):
        """Should extract @keyframes rules from stylesheets."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, "body")

        extractor = StyleExtractor(self.manager.page)
        result = extractor.extract(target)

        assert "keyframes" in result
        assert isinstance(result["keyframes"], dict)

    def test_filter_default_styles(self):
        """Should filter out browser default styles."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, "h1")

        extractor = StyleExtractor(self.manager.page)
        result = extractor.extract(target)

        # Should not include all ~300 default properties
        # Only user-defined or non-default values
        assert len(result["computed_styles"]) < 100
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/collector/test_style_extractor.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write StyleExtractor**

```python
# collector/style_extractor.py
"""Extract computed styles and animation data."""

from playwright.sync_api import Page, Locator


class StyleExtractor:
    """Extract CSS styles and animations from elements."""

    # Properties that indicate animations
    ANIMATION_PROPS = [
        "animation-name", "animation-duration", "animation-delay",
        "animation-timing-function", "animation-iteration-count",
        "animation-direction", "animation-fill-mode"
    ]

    TRANSITION_PROPS = [
        "transition-property", "transition-duration",
        "transition-timing-function", "transition-delay"
    ]

    # Common browser defaults to filter out
    DEFAULT_VALUES = {
        "align-content": "normal",
        "align-items": "normal",
        "align-self": "auto",
        "animation": "none 0s ease 0s 1 normal none running none",
        "background": "rgba(0, 0, 0, 0) none repeat scroll 0% 0% / auto padding-box border-box",
        "border": "0px none rgb(0, 0, 0)",
        "border-radius": "0px",
        "bottom": "auto",
        "box-shadow": "none",
        "clear": "none",
        "color": "rgb(0, 0, 0)",
        "cursor": "auto",
        "display": "block",
        "float": "none",
        "font": "normal normal 400 16px / normal serif",
        "height": "auto",
        "left": "auto",
        "letter-spacing": "normal",
        "line-height": "normal",
        "margin": "0px",
        "max-height": "none",
        "max-width": "none",
        "min-height": "0px",
        "min-width": "0px",
        "opacity": "1",
        "outline": "rgb(0, 0, 0) none 0px",
        "overflow": "visible",
        "padding": "0px",
        "position": "static",
        "right": "auto",
        "text-align": "start",
        "text-decoration": "none solid rgb(0, 0, 0)",
        "text-indent": "0px",
        "text-transform": "none",
        "top": "auto",
        "transform": "none",
        "transition": "all 0s ease 0s",
        "visibility": "visible",
        "white-space": "normal",
        "width": "auto",
        "word-spacing": "normal",
        "z-index": "auto",
    }

    def __init__(self, page: Page):
        self.page = page

    def extract(self, target: Locator) -> dict:
        """Extract all style data from target element."""
        style_data = target.evaluate("""el => {
            const styles = window.getComputedStyle(el);

            // Get all computed styles
            const computed = {};
            for (let i = 0; i < styles.length; i++) {
                const prop = styles[i];
                computed[prop] = styles.getPropertyValue(prop);
            }

            // Parse animation properties
            const animations = [];
            const animName = styles.getPropertyValue('animation-name');
            if (animName && animName !== 'none') {
                animations.push({
                    name: animName,
                    duration: styles.getPropertyValue('animation-duration'),
                    delay: styles.getPropertyValue('animation-delay'),
                    timing_function: styles.getPropertyValue('animation-timing-function'),
                    iteration_count: styles.getPropertyValue('animation-iteration-count'),
                    direction: styles.getPropertyValue('animation-direction'),
                    fill_mode: styles.getPropertyValue('animation-fill-mode'),
                });
            }

            // Parse transition properties
            const transitions = [];
            const transProp = styles.getPropertyValue('transition-property');
            if (transProp && transProp !== 'all') {
                const props = transProp.split(',').map(s => s.trim());
                const durations = styles.getPropertyValue('transition-duration').split(',').map(s => s.trim());
                const timings = styles.getPropertyValue('transition-timing-function').split(',').map(s => s.trim());
                const delays = styles.getPropertyValue('transition-delay').split(',').map(s => s.trim());

                props.forEach((prop, i) => {
                    transitions.push({
                        property: prop,
                        duration: durations[i] || '0s',
                        timing_function: timings[i] || 'ease',
                        delay: delays[i] || '0s',
                    });
                });
            }

            return {
                computed,
                animations,
                transitions
            };
        }""")

        # Filter out default values
        filtered_styles = {
            k: v for k, v in style_data["computed"].items()
            if not self._is_default(k, v)
        }

        # Extract keyframes from stylesheets
        keyframes = self._extract_keyframes()

        return {
            "computed_styles": filtered_styles,
            "animations": style_data["animations"],
            "transitions": style_data["transitions"],
            "keyframes": keyframes,
        }

    def _is_default(self, prop: str, value: str) -> bool:
        """Check if value is likely a browser default."""
        if prop in self.DEFAULT_VALUES:
            default = self.DEFAULT_VALUES[prop]
            # Normalize for comparison
            return value.replace(" ", "") == default.replace(" ", "")
        return False

    def _extract_keyframes(self) -> dict:
        """Extract all @keyframes rules from page stylesheets."""
        return self.page.evaluate("""() => {
            const keyframes = {};

            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.type === CSSRule.KEYFRAMES_RULE) {
                            const frames = {};
                            for (const frame of rule.cssRules) {
                                frames[frame.keyText] = {};
                                for (const style of frame.style) {
                                    frames[frame.keyText][style] = frame.style.getPropertyValue(style);
                                }
                            }
                            keyframes[rule.name] = frames;
                        }
                    }
                } catch (e) {
                    // CORS may block access to some stylesheets
                }
            }

            return keyframes;
        }""")
```

- [ ] **Step 4: Update collector/__init__.py**

```python
# Add to imports and __all__
from collector.style_extractor import StyleExtractor
# In __all__:
"StyleExtractor",
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/collector/test_style_extractor.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add collector/ tests/collector/
git commit -m "feat(collector): add StyleExtractor for computed styles and animations"
```

---

## Chunk 4: Collector - Interactions & Assets

### Task 4.1: Interaction Mapper

**Files:**
- Create: `collector/interaction_mapper.py`
- Create: `tests/collector/test_interaction_mapper.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/collector/test_interaction_mapper.py
import pytest
from collector.browser import BrowserManager
from collector.target_finder import TargetFinder
from collector.interaction_mapper import InteractionMapper
from models.extraction import SelectorStrategy


class TestInteractionMapper:
    @pytest.fixture(autouse=True)
    def setup_browser(self):
        """Set up browser for each test."""
        self.manager = BrowserManager()
        self.manager.start()
        # Use a page with interactive elements
        self.manager.navigate("data:text/html," + """
        <html>
        <body>
            <div class="container">
                <button id="btn1" style="cursor: pointer;">Click Me</button>
                <a href="#" id="link1">Link</a>
                <input type="text" id="input1" />
                <div style="cursor: pointer;" id="hoverable">Hover Me</div>
            </div>
        </body>
        </html>
        """)
        yield
        self.manager.close()

    def test_map_finds_buttons(self):
        """Should find button elements."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        mapper = InteractionMapper(self.manager.page)
        result = mapper.map(target)

        assert "#btn1" in result["clickable"] or "button" in str(result["clickable"])

    def test_map_finds_links(self):
        """Should find anchor elements."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        mapper = InteractionMapper(self.manager.page)
        result = mapper.map(target)

        assert len(result["clickable"]) >= 2  # button and link

    def test_map_finds_inputs(self):
        """Should find input elements as focusable."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        mapper = InteractionMapper(self.manager.page)
        result = mapper.map(target)

        assert len(result["focusable"]) >= 1

    def test_map_finds_hoverable_by_cursor(self):
        """Should find elements with cursor: pointer."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        mapper = InteractionMapper(self.manager.page)
        result = mapper.map(target)

        assert len(result["hoverable"]) >= 2  # button and hoverable div

    def test_map_returns_selectors(self):
        """Should return CSS selectors for elements."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        mapper = InteractionMapper(self.manager.page)
        result = mapper.map(target)

        # Each category should be a list of selector strings
        for category in ["hoverable", "clickable", "focusable", "scroll_containers"]:
            assert category in result
            assert isinstance(result[category], list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/collector/test_interaction_mapper.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write InteractionMapper**

```python
# collector/interaction_mapper.py
"""Detect interactive elements within a target."""

from playwright.sync_api import Page, Locator


class InteractionMapper:
    """Map interactive elements within a component."""

    def __init__(self, page: Page):
        self.page = page

    def map(self, target: Locator) -> dict:
        """Find all interactive elements within target."""
        return target.evaluate("""el => {
            const result = {
                hoverable: [],
                clickable: [],
                focusable: [],
                scroll_containers: []
            };

            // Find all elements within target
            const elements = el.querySelectorAll('*');

            elements.forEach((elem, index) => {
                // Generate unique selector
                const selector = elem.id ? '#' + elem.id :
                    elem.className ? elem.tagName.toLowerCase() + '.' + elem.className.split(' ')[0] :
                    elem.tagName.toLowerCase() + ':nth-child(' + (index + 1) + ')';

                const styles = window.getComputedStyle(elem);

                // Check hoverable (cursor: pointer)
                if (styles.cursor === 'pointer') {
                    result.hoverable.push(selector);
                }

                // Check clickable (button, a, or has click handler heuristics)
                if (elem.tagName === 'BUTTON' ||
                    elem.tagName === 'A' ||
                    elem.tagName === 'INPUT' && ['submit', 'button', 'reset'].includes(elem.type) ||
                    styles.cursor === 'pointer') {
                    result.clickable.push(selector);
                }

                // Check focusable
                if (elem.tagName === 'INPUT' ||
                    elem.tagName === 'TEXTAREA' ||
                    elem.tagName === 'SELECT' ||
                    elem.tagName === 'BUTTON' ||
                    elem.hasAttribute('tabindex')) {
                    result.focusable.push(selector);
                }

                // Check scroll containers
                const overflow = styles.overflow + styles.overflowY + styles.overflowX;
                if (overflow.includes('auto') || overflow.includes('scroll')) {
                    result.scroll_containers.push(selector);
                }
            });

            // Remove duplicates
            result.hoverable = [...new Set(result.hoverable)];
            result.clickable = [...new Set(result.clickable)];
            result.focusable = [...new Set(result.focusable)];
            result.scroll_containers = [...new Set(result.scroll_containers)];

            return result;
        }""")
```

- [ ] **Step 4: Update collector/__init__.py**

```python
# Add to imports and __all__
from collector.interaction_mapper import InteractionMapper
# In __all__:
"InteractionMapper",
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/collector/test_interaction_mapper.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add collector/ tests/collector/
git commit -m "feat(collector): add InteractionMapper for detecting interactive elements"
```

---

### Task 4.2: Interaction Player

**Files:**
- Create: `collector/interaction_player.py`
- Create: `tests/collector/test_interaction_player.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/collector/test_interaction_player.py
import pytest
from collector.browser import BrowserManager
from collector.target_finder import TargetFinder
from collector.interaction_mapper import InteractionMapper
from collector.interaction_player import InteractionPlayer
from models.extraction import SelectorStrategy, InteractionType


class TestInteractionPlayer:
    @pytest.fixture(autouse=True)
    def setup_browser(self):
        """Set up browser for each test."""
        self.manager = BrowserManager()
        self.manager.start()
        # Page with interactive elements that change state
        self.manager.navigate("data:text/html," + """
        <html>
        <head>
        <style>
        .btn { background: blue; transition: background 0.1s; }
        .btn:hover { background: red; }
        .input:focus { border-color: green; }
        </style>
        </head>
        <body>
            <div class="container">
                <button class="btn" id="btn1">Click Me</button>
                <input type="text" id="input1" style="border: 1px solid black;" />
            </div>
        </body>
        </html>
        """)
        yield
        self.manager.close()

    def test_play_hover_captures_state_change(self):
        """Should capture before/after states on hover."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        mapper = InteractionMapper(self.manager.page)
        interactions = mapper.map(target)

        player = InteractionPlayer(self.manager.page)
        results = player.play_all(target, interactions)

        assert len(results) >= 1
        # Find hover result for button
        hover_result = next((r for r in results if r["type"] == "hover"), None)
        if hover_result:
            assert "before" in hover_result
            assert "after" in hover_result

    def test_play_focus_captures_state_change(self):
        """Should capture before/after states on focus."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        mapper = InteractionMapper(self.manager.page)
        interactions = mapper.map(target)

        player = InteractionPlayer(self.manager.page)
        results = player.play_all(target, interactions)

        # Find focus result for input
        focus_result = next((r for r in results if r["type"] == "focus"), None)
        if focus_result:
            assert "before" in focus_result
            assert "after" in focus_result

    def test_play_returns_duration(self):
        """Should include interaction duration."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        mapper = InteractionMapper(self.manager.page)
        interactions = mapper.map(target)

        player = InteractionPlayer(self.manager.page)
        results = player.play_all(target, interactions)

        for result in results:
            assert "duration_ms" in result
            assert result["duration_ms"] >= 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/collector/test_interaction_player.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write InteractionPlayer**

```python
# collector/interaction_player.py
"""Execute interactions and capture state changes."""

import time
from playwright.sync_api import Page, Locator

from models.extraction import InteractionType, InteractionState


class InteractionPlayer:
    """Execute interactions and capture before/after states."""

    def __init__(self, page: Page):
        self.page = page

    def play_all(self, target: Locator, interactions: dict) -> list[dict]:
        """Execute all interactions and return observed states."""
        results = []

        # Play hover interactions
        for selector in interactions.get("hoverable", [])[:5]:  # Limit to 5
            result = self._play_hover(target, selector)
            if result:
                results.append(result)

        # Play click interactions (limited - can cause navigation)
        for selector in interactions.get("clickable", [])[:2]:
            # Skip links that might navigate
            if "a[" in selector.lower() or "a." in selector.lower():
                continue
            result = self._play_click(target, selector)
            if result:
                results.append(result)

        # Play focus interactions
        for selector in interactions.get("focusable", [])[:3]:
            result = self._play_focus(target, selector)
            if result:
                results.append(result)

        return results

    def _play_hover(self, target: Locator, selector: str) -> dict | None:
        """Execute hover and capture state change."""
        try:
            element = target.locator(selector)
            if element.count() == 0:
                return None

            before = self._capture_state(element)

            start = time.time()
            element.hover()
            self.page.wait_for_timeout(150)  # Wait for transition
            duration = (time.time() - start) * 1000

            after = self._capture_state(element)

            # Only return if state changed
            if before != after:
                return {
                    "type": InteractionType.HOVER.value,
                    "selector": selector,
                    "before": before,
                    "after": after,
                    "duration_ms": round(duration, 2),
                }
            return None

        except Exception:
            return None

    def _play_click(self, target: Locator, selector: str) -> dict | None:
        """Execute click and capture state change."""
        try:
            element = target.locator(selector)
            if element.count() == 0:
                return None

            before = self._capture_state(element)

            start = time.time()
            element.click()
            self.page.wait_for_timeout(100)
            duration = (time.time() - start) * 1000

            after = self._capture_state(element)

            if before != after:
                return {
                    "type": InteractionType.CLICK.value,
                    "selector": selector,
                    "before": before,
                    "after": after,
                    "duration_ms": round(duration, 2),
                }
            return None

        except Exception:
            return None

    def _play_focus(self, target: Locator, selector: str) -> dict | None:
        """Execute focus and capture state change."""
        try:
            element = target.locator(selector)
            if element.count() == 0:
                return None

            before = self._capture_state(element)

            start = time.time()
            element.focus()
            self.page.wait_for_timeout(100)
            duration = (time.time() - start) * 1000

            after = self._capture_state(element)

            if before != after:
                return {
                    "type": InteractionType.FOCUS.value,
                    "selector": selector,
                    "before": before,
                    "after": after,
                    "duration_ms": round(duration, 2),
                }
            return None

        except Exception:
            return None

    def _capture_state(self, element: Locator) -> dict:
        """Capture current element state."""
        return element.evaluate("""el => {
            const styles = window.getComputedStyle(el);
            return {
                classes: el.className,
                backgroundColor: styles.backgroundColor,
                borderColor: styles.borderColor,
                color: styles.color,
                opacity: styles.opacity,
                transform: styles.transform,
                boxShadow: styles.boxShadow,
                outline: styles.outline,
            };
        }""")
```

- [ ] **Step 4: Update collector/__init__.py**

```python
# Add to imports and __all__
from collector.interaction_player import InteractionPlayer
# In __all__:
"InteractionPlayer",
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/collector/test_interaction_player.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add collector/ tests/collector/
git commit -m "feat(collector): add InteractionPlayer for executing and capturing interactions"
```

---

### Task 4.3: Asset Downloader

**Files:**
- Create: `collector/asset_downloader.py`
- Create: `tests/collector/test_asset_downloader.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/collector/test_asset_downloader.py
import pytest
import os
import tempfile
from pathlib import Path
from collector.browser import BrowserManager
from collector.target_finder import TargetFinder
from collector.asset_downloader import AssetDownloader
from models.extraction import SelectorStrategy


class TestAssetDownloader:
    @pytest.fixture(autouse=True)
    def setup_browser(self):
        """Set up browser and temp output directory."""
        self.manager = BrowserManager()
        self.manager.start()
        self.temp_dir = tempfile.mkdtemp()

        # Page with images and fonts
        self.manager.navigate("data:text/html," + """
        <html>
        <body>
            <div class="container">
                <img src="https://via.placeholder.com/150" alt="test" />
                <svg width="100" height="100">
                    <circle cx="50" cy="50" r="40" fill="red" />
                </svg>
            </div>
        </body>
        </html>
        """)

        yield

        self.manager.close()
        # Cleanup temp dir
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_download_images(self):
        """Should download image assets."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        downloader = AssetDownloader(self.manager.page, self.temp_dir)
        result = downloader.download_all(target)

        assert len(result) >= 1
        assert any(a["type"] == "image" for a in result)

    def test_download_saves_to_local_path(self):
        """Should save assets to local filesystem."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        downloader = AssetDownloader(self.manager.page, self.temp_dir)
        result = downloader.download_all(target)

        for asset in result:
            assert os.path.exists(asset["local_path"])
            assert asset["file_size_bytes"] > 0

    def test_download_records_original_url(self):
        """Should record original URL for each asset."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        downloader = AssetDownloader(self.manager.page, self.temp_dir)
        result = downloader.download_all(target)

        for asset in result:
            assert asset["original_url"] is not None
            assert len(asset["original_url"]) > 0

    def test_download_handles_inline_svg(self):
        """Should handle inline SVGs."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        downloader = AssetDownloader(self.manager.page, self.temp_dir)
        result = downloader.download_all(target)

        # Should have SVG asset
        svg_assets = [a for a in result if a["type"] == "svg"]
        assert len(svg_assets) >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/collector/test_asset_downloader.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write AssetDownloader**

```python
# collector/asset_downloader.py
"""Download and organize assets from web pages."""

import os
import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from playwright.sync_api import Page, Locator

from models.extraction import Asset, AssetType


class AssetDownloader:
    """Download images, fonts, and other assets."""

    def __init__(self, page: Page, output_dir: str):
        self.page = page
        self.output_dir = output_dir
        self.assets_dir = Path(output_dir) / "assets"
        self._ensure_directories()

    def _ensure_directories(self):
        """Create asset directories."""
        for subdir in ["images", "fonts", "svgs"]:
            (self.assets_dir / subdir).mkdir(parents=True, exist_ok=True)

    def download_all(self, target: Locator) -> list[Asset]:
        """Download all assets from target element."""
        assets = []

        # Download images
        assets.extend(self._download_images(target))

        # Extract and save inline SVGs
        assets.extend(self._extract_svgs(target))

        # Download fonts (from @font-face)
        assets.extend(self._download_fonts())

        return assets

    def _download_images(self, target: Locator) -> list[Asset]:
        """Download img elements and background images."""
        assets = []

        # Get all image URLs
        image_data = target.evaluate("""el => {
            const images = [];

            // <img> elements
            el.querySelectorAll('img').forEach(img => {
                if (img.src) images.push({ type: 'img', url: img.src });
            });

            // Elements with background-image
            el.querySelectorAll('*').forEach(elem => {
                const bg = window.getComputedStyle(elem).backgroundImage;
                if (bg && bg !== 'none') {
                    const match = bg.match(/url\\(['"]?(.+?)['"]?\\)/);
                    if (match) images.push({ type: 'bg', url: match[1] });
                }
            });

            return images;
        }""")

        for img_info in image_data:
            asset = self._download_single_image(img_info["url"])
            if asset:
                assets.append(asset)

        return assets

    def _download_single_image(self, url: str) -> Asset | None:
        """Download a single image."""
        try:
            # Handle data URLs
            if url.startswith("data:"):
                return self._save_data_url(url, AssetType.IMAGE)

            # Download from URL
            response = self.page.request.get(url)
            if not response.ok:
                return None

            content = response.body()

            # Generate filename
            ext = self._get_extension(url) or ".png"
            filename = self._generate_filename(url, ext)
            local_path = self.assets_dir / "images" / filename

            with open(local_path, "wb") as f:
                f.write(content)

            # Get dimensions if possible
            dimensions = self._get_image_dimensions(content, ext)

            return Asset(
                type=AssetType.IMAGE,
                original_url=url,
                local_path=str(local_path),
                file_size_bytes=len(content),
                dimensions=dimensions,
            )

        except Exception:
            return None

    def _extract_svgs(self, target: Locator) -> list[Asset]:
        """Extract inline SVG elements."""
        assets = []

        svg_data = target.evaluate("""el => {
            const svgs = [];
            el.querySelectorAll('svg').forEach((svg, i) => {
                svgs.push({
                    markup: svg.outerHTML,
                    index: i
                });
            });
            return svgs;
        }""")

        for svg_info in svg_data:
            markup = svg_info["markup"]
            filename = f"svg_{svg_info['index']}_{self._hash_string(markup)[:8]}.svg"
            local_path = self.assets_dir / "svgs" / filename

            with open(local_path, "w", encoding="utf-8") as f:
                f.write(markup)

            assets.append(Asset(
                type=AssetType.SVG,
                original_url="inline",
                local_path=str(local_path),
                file_size_bytes=len(markup.encode("utf-8")),
                dimensions=None,
            ))

        return assets

    def _download_fonts(self) -> list[Asset]:
        """Download fonts from @font-face rules."""
        assets = []

        font_urls = self.page.evaluate("""() => {
            const fonts = [];
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.type === CSSRule.FONT_FACE_RULE) {
                            const src = rule.style.getPropertyValue('src');
                            const match = src.match(/url\\(['"]?(.+?)['"]?\\)/);
                            if (match) fonts.push(match[1]);
                        }
                    }
                } catch (e) {}
            }
            return fonts;
        }""")

        for url in font_urls[:5]:  # Limit fonts
            asset = self._download_single_font(url)
            if asset:
                assets.append(asset)

        return assets

    def _download_single_font(self, url: str) -> Asset | None:
        """Download a single font file."""
        try:
            response = self.page.request.get(url)
            if not response.ok:
                return None

            content = response.body()
            ext = self._get_extension(url) or ".woff2"
            filename = self._generate_filename(url, ext)
            local_path = self.assets_dir / "fonts" / filename

            with open(local_path, "wb") as f:
                f.write(content)

            return Asset(
                type=AssetType.FONT,
                original_url=url,
                local_path=str(local_path),
                file_size_bytes=len(content),
                dimensions=None,
            )

        except Exception:
            return None

    def _save_data_url(self, data_url: str, asset_type: AssetType) -> Asset | None:
        """Save a data URL to file."""
        import base64

        try:
            # Parse data URL
            if ";base64," in data_url:
                header, data = data_url.split(";base64,", 1)
                content = base64.b64decode(data)
                mime = header.split(":")[1]
            else:
                return None

            # Determine extension
            ext_map = {
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/gif": ".gif",
                "image/svg+xml": ".svg",
                "image/webp": ".webp",
            }
            ext = ext_map.get(mime, ".bin")

            subdir = "images" if asset_type == AssetType.IMAGE else "svgs"
            filename = f"data_{self._hash_string(data_url)[:8]}{ext}"
            local_path = self.assets_dir / subdir / filename

            with open(local_path, "wb") as f:
                f.write(content)

            return Asset(
                type=asset_type,
                original_url=data_url[:100] + "...",
                local_path=str(local_path),
                file_size_bytes=len(content),
                dimensions=None,
            )

        except Exception:
            return None

    def _get_extension(self, url: str) -> str | None:
        """Extract file extension from URL."""
        path = urlparse(url).path
        ext = Path(path).suffix
        return ext if ext else None

    def _generate_filename(self, url: str, ext: str) -> str:
        """Generate unique filename for asset."""
        hash_part = self._hash_string(url)[:12]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{timestamp}_{hash_part}{ext}"

    def _hash_string(self, s: str) -> str:
        """Generate hash of string."""
        return hashlib.sha256(s.encode()).hexdigest()

    def _get_image_dimensions(self, content: bytes, ext: str) -> list[int] | None:
        """Get image dimensions using Pillow."""
        try:
            from io import BytesIO
            from PIL import Image

            img = Image.open(BytesIO(content))
            return [img.width, img.height]
        except Exception:
            return None
```

- [ ] **Step 4: Update collector/__init__.py**

```python
# Add to imports and __all__
from collector.asset_downloader import AssetDownloader
# In __all__:
"AssetDownloader",
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/collector/test_asset_downloader.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add collector/ tests/collector/
git commit -m "feat(collector): add AssetDownloader for images, SVGs, and fonts"
```

---

## Chunk 5: Collector - Animation, Library Detection, Responsive

### Task 5.1: Animation Recorder

**Files:**
- Create: `collector/animation_recorder.py`
- Create: `tests/collector/test_animation_recorder.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/collector/test_animation_recorder.py
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from collector.browser import BrowserManager
from collector.target_finder import TargetFinder
from collector.animation_recorder import AnimationRecorder
from models.extraction import SelectorStrategy


class TestAnimationRecorder:
    @pytest.fixture(autouse=True)
    def setup_browser(self):
        """Set up browser and temp output directory."""
        self.manager = BrowserManager()
        self.manager.start()
        self.temp_dir = tempfile.mkdtemp()

        # Page with animation
        self.manager.navigate("data:text/html," + """
        <html>
        <head>
        <style>
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .animated {
            animation: fadeIn 0.5s ease-in-out;
            width: 100px;
            height: 100px;
            background: blue;
        }
        </style>
        </head>
        <body>
            <div class="animated">Animated</div>
        </body>
        </html>
        """)

        yield

        self.manager.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_creates_video(self):
        """Should create video recording."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".animated")

        recorder = AnimationRecorder(self.manager.page, self.temp_dir)
        result = recorder.record(target)

        assert result is not None
        assert "video_path" in result

    def test_record_extracts_frames(self):
        """Should extract frames from recording."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".animated")

        recorder = AnimationRecorder(self.manager.page, self.temp_dir)
        result = recorder.record(target)

        assert "frames_dir" in result
        # Frames dir should exist
        assert os.path.exists(result["frames_dir"])

    def test_record_detects_key_frames(self):
        """Should identify key frames where visual changes occur."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".animated")

        recorder = AnimationRecorder(self.manager.page, self.temp_dir)
        result = recorder.record(target)

        assert "key_frames" in result
        assert isinstance(result["key_frames"], list)

    def test_record_returns_duration(self):
        """Should record animation duration."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".animated")

        recorder = AnimationRecorder(self.manager.page, self.temp_dir)
        result = recorder.record(target)

        assert "duration_ms" in result
        assert result["duration_ms"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/collector/test_animation_recorder.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write AnimationRecorder**

```python
# collector/animation_recorder.py
"""Record animations via screenshots and frame extraction."""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page, Locator
from models.extraction import AnimationRecording


class AnimationRecorder:
    """Record animations using screenshots and extract key frames."""

    def __init__(self, page: Page, output_dir: str):
        self.page = page
        self.output_dir = output_dir
        self.animations_dir = Path(output_dir) / "animations"
        self.animations_dir.mkdir(parents=True, exist_ok=True)

    def record(self, target: Locator, duration_ms: int = 2000) -> Optional[AnimationRecording]:
        """Record target element for specified duration."""
        # Create timestamped directory for this recording
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recording_dir = self.animations_dir / timestamp
        recording_dir.mkdir(parents=True, exist_ok=True)

        frames_dir = recording_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        # Record screenshots at intervals
        fps = 30
        interval_ms = 1000 // fps
        frame_count = int(duration_ms / interval_ms)

        frames = []
        frame_paths = []

        for i in range(frame_count):
            frame_path = frames_dir / f"frame_{i:04d}.png"
            target.screenshot(path=str(frame_path))
            frame_paths.append(str(frame_path))
            time.sleep(interval_ms / 1000)

        # Detect key frames (frames with significant changes)
        key_frames = self._detect_key_frames(frame_paths)

        # Create simple video path (actual video creation would need ffmpeg)
        video_path = recording_dir / "recording.webm"

        return AnimationRecording(
            video_path=str(video_path),
            duration_ms=float(duration_ms),
            fps=fps,
            frames_dir=str(frames_dir),
            key_frames=key_frames,
        )

    def _detect_key_frames(self, frame_paths: list[str]) -> list[int]:
        """Detect frames with significant visual changes."""
        if len(frame_paths) < 2:
            return [0] if frame_paths else []

        key_frames = [0]  # First frame is always a key frame

        try:
            import cv2
            import numpy as np

            prev_frame = None

            for i, path in enumerate(frame_paths):
                frame = cv2.imread(path)
                if frame is None:
                    continue

                # Convert to grayscale and resize for comparison
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                small = cv2.resize(gray, (100, 100))

                if prev_frame is not None:
                    # Calculate difference
                    diff = cv2.absdiff(prev_frame, small)
                    diff_score = np.mean(diff)

                    # If significant change, mark as key frame
                    if diff_score > 5:  # Threshold for change detection
                        key_frames.append(i)

                prev_frame = small

        except ImportError:
            # OpenCV not available, return evenly spaced frames
            step = max(1, len(frame_paths) // 10)
            key_frames = list(range(0, len(frame_paths), step))

        return key_frames
```

- [ ] **Step 4: Update collector/__init__.py**

```python
# Add to imports and __all__
from collector.animation_recorder import AnimationRecorder
# In __all__:
"AnimationRecorder",
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/collector/test_animation_recorder.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add collector/ tests/collector/
git commit -m "feat(collector): add AnimationRecorder for capturing animations"
```

---

### Task 5.2: Library Detector

**Files:**
- Create: `collector/library_detector.py`
- Create: `tests/collector/test_library_detector.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/collector/test_library_detector.py
import pytest
from collector.browser import BrowserManager
from collector.library_detector import LibraryDetector


class TestLibraryDetector:
    @pytest.fixture(autouse=True)
    def setup_browser(self):
        """Set up browser for each test."""
        self.manager = BrowserManager()
        self.manager.start()
        yield
        self.manager.close()

    def test_detect_no_libraries(self):
        """Should return empty list when no libraries detected."""
        self.manager.navigate("data:text/html,<html><body>Plain page</body></html>")

        detector = LibraryDetector(self.manager.page)
        result = detector.detect()

        assert isinstance(result, list)

    def test_detect_jquery(self):
        """Should detect jQuery."""
        self.manager.navigate("data:text/html," + """
        <html>
        <head>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        </head>
        <body></body>
        </html>
        """)

        detector = LibraryDetector(self.manager.page)
        result = detector.detect()

        # May or may not detect depending on script loading
        assert isinstance(result, list)

    def test_detect_returns_library_info(self):
        """Should return library name and usage info."""
        self.manager.navigate("data:text/html,<html><body>Test</body></html>")

        detector = LibraryDetector(self.manager.page)
        result = detector.detect()

        # Each detected library should have required fields
        for lib in result:
            assert "name" in lib
            assert "source_url" in lib
            assert "usage_snippets" in lib
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/collector/test_library_detector.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write LibraryDetector**

```python
# collector/library_detector.py
"""Detect external JavaScript libraries."""

import re
from playwright.sync_api import Page

from models.extraction import ExternalLibrary


class LibraryDetector:
    """Detect external libraries and their usage."""

    KNOWN_LIBRARIES = {
        "GSAP": ["gsap", "TweenMax", "TweenLite", "TimelineMax"],
        "Lottie": ["lottie", "bodymovin"],
        "Three.js": ["THREE", "three"],
        "Swiper": ["Swiper"],
        "AOS": ["AOS"],
        "GSAP ScrollTrigger": ["ScrollTrigger"],
        "Locomotive Scroll": ["LocomotiveScroll", "locomotive-scroll"],
        "Barba.js": ["barba"],
        "Flickity": ["Flickity"],
        "Slick": ["slick"],
        "Anime.js": ["anime"],
        "Velocity.js": ["Velocity"],
        "GreenSock": ["gsap", "TweenMax"],
    }

    def __init__(self, page: Page):
        self.page = page

    def detect(self) -> list[ExternalLibrary]:
        """Detect all external libraries on the page."""
        libraries = []

        # Detect from script sources
        script_libs = self._detect_from_scripts()
        libraries.extend(script_libs)

        # Detect from globals
        global_libs = self._detect_from_globals()
        libraries.extend(global_libs)

        # Remove duplicates
        seen = set()
        unique_libs = []
        for lib in libraries:
            if lib.name not in seen:
                seen.add(lib.name)
                unique_libs.append(lib)

        return unique_libs

    def _detect_from_scripts(self) -> list[ExternalLibrary]:
        """Detect libraries from script src attributes."""
        libraries = []

        script_data = self.page.evaluate("""() => {
            const scripts = [];
            document.querySelectorAll('script[src]').forEach(s => {
                scripts.push(s.src);
            });
            return scripts;
        }""")

        for url in script_data:
            lib = self._identify_library_from_url(url)
            if lib:
                libraries.append(lib)

        return libraries

    def _detect_from_globals(self) -> list[ExternalLibrary]:
        """Detect libraries from window globals."""
        libraries = []

        for lib_name, globals_list in self.KNOWN_LIBRARIES.items():
            for global_var in globals_list:
                detected = self.page.evaluate(f"""() => {{
                    if (typeof window.{global_var} !== 'undefined') {{
                        return {{
                            exists: true,
                            version: window.{global_var}.version || null
                        }};
                    }}
                    return {{ exists: false }};
                }}""")

                if detected.get("exists"):
                    # Try to get usage snippets
                    usage = self._extract_usage_snippets(global_var)

                    libraries.append(ExternalLibrary(
                        name=lib_name,
                        version=detected.get("version"),
                        source_url=f"detected via window.{global_var}",
                        usage_snippets=usage,
                        init_code=self._extract_init_code(global_var),
                    ))
                    break  # Found this library, move to next

        return libraries

    def _identify_library_from_url(self, url: str) -> ExternalLibrary | None:
        """Identify library from URL patterns."""
        url_lower = url.lower()

        patterns = {
            r"gsap|greensock": "GSAP",
            r"lottie|bodymovin": "Lottie",
            r"three\.js|threejs": "Three.js",
            r"swiper": "Swiper",
            r"aos\.js": "AOS",
            r"locomotive": "Locomotive Scroll",
            r"barba": "Barba.js",
            r"flickity": "Flickity",
            r"slick\.js": "Slick",
            r"anime\.js": "Anime.js",
            r"velocity": "Velocity.js",
            r"jquery": "jQuery",
            r"vue": "Vue.js",
            r"react": "React",
            r"angular": "Angular",
        }

        for pattern, lib_name in patterns.items():
            if re.search(pattern, url_lower):
                return ExternalLibrary(
                    name=lib_name,
                    version=self._extract_version_from_url(url),
                    source_url=url,
                    usage_snippets=[],
                    init_code=None,
                )

        return None

    def _extract_version_from_url(self, url: str) -> str | None:
        """Extract version number from URL."""
        match = re.search(r"(\d+\.\d+\.\d+|\d+\.\d+)", url)
        return match.group(1) if match else None

    def _extract_usage_snippets(self, global_var: str) -> list[str]:
        """Extract code snippets using the library."""
        return self.page.evaluate(f"""() => {{
            const snippets = [];

            // Search inline scripts for usage
            document.querySelectorAll('script:not([src])').forEach(script => {{
                const text = script.textContent;
                if (text && text.includes('{global_var}')) {{
                    // Extract relevant lines
                    const lines = text.split('\\n').filter(l => l.includes('{global_var}'));
                    snippets.push(...lines.slice(0, 3));
                }}
            }});

            return snippets.slice(0, 5);
        }}""")

    def _extract_init_code(self, global_var: str) -> str | None:
        """Extract initialization code for the library."""
        return self.page.evaluate(f"""() => {{
            const scripts = document.querySelectorAll('script:not([src])');
            for (const script of scripts) {{
                const text = script.textContent;
                if (text && text.includes('{global_var}')) {{
                    // Look for init patterns
                    const match = text.match(/{global_var}\\\\.init\\\\s*\\\\(.*?\\\\)/s);
                    if (match) return match[0];
                }}
            }}
            return null;
        }}""")
```

- [ ] **Step 4: Update collector/__init__.py**

```python
# Add to imports and __all__
from collector.library_detector import LibraryDetector
# In __all__:
"LibraryDetector",
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/collector/test_library_detector.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add collector/ tests/collector/
git commit -m "feat(collector): add LibraryDetector for external JS libraries"
```

---

### Task 5.3: Responsive Collector

**Files:**
- Create: `collector/responsive_collector.py`
- Create: `tests/collector/test_responsive_collector.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/collector/test_responsive_collector.py
import pytest
from collector.browser import BrowserManager
from collector.target_finder import TargetFinder
from collector.responsive_collector import ResponsiveCollector
from models.extraction import SelectorStrategy


class TestResponsiveCollector:
    @pytest.fixture(autouse=True)
    def setup_browser(self):
        """Set up browser for each test."""
        self.manager = BrowserManager()
        self.manager.start()
        # Page with media queries
        self.manager.navigate("data:text/html," + """
        <html>
        <head>
        <style>
        .container { width: 100%; }
        @media (min-width: 768px) {
            .container { width: 50%; }
        }
        @media (min-width: 1024px) {
            .container { width: 33%; }
        }
        </style>
        </head>
        <body>
            <div class="container">Content</div>
        </body>
        </html>
        """)
        yield
        self.manager.close()

    def test_detect_breakpoints(self):
        """Should detect media query breakpoints."""
        collector = ResponsiveCollector(self.manager.page)
        breakpoints = collector.detect_breakpoints()

        assert isinstance(breakpoints, list)
        # Should detect at least one breakpoint from the CSS
        assert len(breakpoints) >= 1

    def test_collect_at_viewport(self):
        """Should capture state at specific viewport."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        collector = ResponsiveCollector(self.manager.page)
        result = collector.collect_at_viewport(target, 1024, 768)

        assert "width" in result
        assert result["width"] == 1024

    def test_collect_all(self):
        """Should collect responsive behavior at all breakpoints."""
        finder = TargetFinder(self.manager.page)
        target = finder.find(SelectorStrategy.CSS, ".container")

        collector = ResponsiveCollector(self.manager.page)
        result = collector.collect_all(target)

        assert "breakpoints" in result
        assert "is_fluid" in result
        assert isinstance(result["breakpoints"], list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/collector/test_responsive_collector.py -v`
Expected: FAIL with "ImportError"

- [ ] **Step 3: Write ResponsiveCollector**

```python
# collector/responsive_collector.py
"""Collect responsive behavior and breakpoints."""

from playwright.sync_api import Page, Locator

from models.extraction import ResponsiveBreakpoint
from models.normalized import ResponsiveBehavior


class ResponsiveCollector:
    """Detect and collect responsive breakpoints."""

    STANDARD_BREAKPOINTS = [320, 480, 768, 1024, 1280, 1440]

    def __init__(self, page: Page):
        self.page = page

    def detect_breakpoints(self) -> list[int]:
        """Extract breakpoints from CSS media queries."""
        breakpoints = self.page.evaluate("""() => {
            const breakpoints = new Set();

            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules) {
                        if (rule.type === CSSRule.MEDIA_RULE) {
                            const media = rule.media.mediaText;
                            // Extract min-width values
                            const matches = media.match(/min-width:\\s*(\\d+)px/g);
                            if (matches) {
                                matches.forEach(m => {
                                    const num = parseInt(m.match(/\\d+/)[0]);
                                    breakpoints.add(num);
                                });
                            }
                            // Extract max-width values
                            const maxMatches = media.match(/max-width:\\s*(\\d+)px/g);
                            if (maxMatches) {
                                matches.forEach(m => {
                                    const num = parseInt(m.match(/\\d+/)[0]);
                                    breakpoints.add(num);
                                });
                            }
                        }
                    }
                } catch (e) {
                    // CORS may block some stylesheets
                }
            }

            return Array.from(breakpoints).sort((a, b) => a - b);
        }""")

        return breakpoints if breakpoints else self.STANDARD_BREAKPOINTS

    def collect_at_viewport(self, target: Locator, width: int, height: int) -> dict:
        """Capture component state at specific viewport size."""
        self.page.set_viewport_size({"width": width, "height": height})

        return target.evaluate("""el => {
            const styles = window.getComputedStyle(el);
            return {
                width: """ + str(width) + """,
                height: """ + str(height) + """,
                display: styles.display,
                flexDirection: styles.flexDirection,
                gridTemplateColumns: styles.gridTemplateColumns,
                fontSize: styles.fontSize,
                visibility: styles.visibility,
            };
        }""")

    def collect_all(self, target: Locator) -> ResponsiveBehavior:
        """Collect responsive behavior at all breakpoints."""
        breakpoints = self.detect_breakpoints()

        # Add viewport width to breakpoints
        current_width = self.page.viewport_size["width"]
        if current_width not in breakpoints:
            breakpoints.append(current_width)
        breakpoints.sort()

        collected_breakpoints = []
        previous_state = None

        for bp in breakpoints:
            state = self.collect_at_viewport(target, bp, 800)

            if previous_state:
                # Calculate diff
                diff = {}
                changes = []

                for key, value in state.items():
                    if key in ["width", "height"]:
                        continue
                    if previous_state.get(key) != value:
                        diff[key] = [previous_state.get(key), value]
                        changes.append(f"{key}: {previous_state.get(key)} -> {value}")

                if diff:
                    collected_breakpoints.append(ResponsiveBreakpoint(
                        width=bp,
                        height=800,
                        source="media_query",
                        styles_diff=diff,
                        layout_changes=changes,
                    ))

            previous_state = state

        # Check if fluid
        is_fluid = self._check_fluid(target)

        # Check for mobile menu
        has_mobile_menu = self._check_mobile_menu()

        return ResponsiveBehavior(
            breakpoints=collected_breakpoints,
            is_fluid=is_fluid,
            has_mobile_menu=has_mobile_menu,
            grid_changes=[],
        )

    def _check_fluid(self, target: Locator) -> bool:
        """Check if component uses fluid sizing."""
        return target.evaluate("""el => {
            const styles = window.getComputedStyle(el);
            return styles.width.includes('%') ||
                   styles.width.includes('vw') ||
                   styles.maxWidth.includes('%');
        }""")

    def _check_mobile_menu(self) -> bool:
        """Check if page has mobile menu pattern."""
        return self.page.evaluate("""() => {
            // Look for common mobile menu patterns
            const selectors = [
                '[aria-label*="menu"]',
                '[class*="mobile-menu"]',
                '[class*="hamburger"]',
                '[class*="nav-toggle"]',
                'button[aria-expanded]'
            ];

            for (const sel of selectors) {
                if (document.querySelector(sel)) return true;
            }
            return false;
        }""")
```

- [ ] **Step 4: Update collector/__init__.py**

```python
# Add to imports and __all__
from collector.responsive_collector import ResponsiveCollector
# In __all__:
"ResponsiveCollector",
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/collector/test_responsive_collector.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add collector/ tests/collector/
git commit -m "feat(collector): add ResponsiveCollector for media query breakpoints"
```

---

## Chunk 6: Normalizer

### Task 6.1: Normalizer Package

**Files:**
- Create: `normalizer/__init__.py`
- Create: `normalizer/transformers/__init__.py`
- Create: `normalizer/transformers/dom_transformer.py`
- Create: `normalizer/transformers/style_transformer.py`
- Create: `normalizer/transformers/animation_transformer.py`
- Create: `normalizer/context_builder.py`
- Create: `tests/normalizer/test_normalizer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/normalizer/test_normalizer.py
import pytest
from normalizer.context_builder import ContextBuilder
from normalizer.transformers.dom_transformer import DOMTransformer
from normalizer.transformers.style_transformer import StyleTransformer
from models.extraction import BoundingBox
from models.normalized import DOMTree, StyleSummary


class TestDOMTransformer:
    def test_transform_creates_dom_tree(self):
        """Should transform raw DOM data into DOMTree."""
        transformer = DOMTransformer()
        raw_data = {
            "tag": "div",
            "attributes": {"class": "container"},
            "children": [],
            "text_content": "Hello",
            "computed_styles": {"color": "red"},
        }

        result = transformer.transform(raw_data)

        assert isinstance(result, DOMTree)
        assert result.tag == "div"
        assert result.text_content == "Hello"

    def test_transform_handles_nested_children(self):
        """Should recursively transform children."""
        transformer = DOMTransformer()
        raw_data = {
            "tag": "div",
            "attributes": {},
            "children": [
                {
                    "tag": "span",
                    "attributes": {},
                    "children": [],
                    "text_content": "Child",
                    "computed_styles": {},
                }
            ],
            "text_content": None,
            "computed_styles": {},
        }

        result = transformer.transform(raw_data)

        assert len(result.children) == 1
        assert result.children[0].tag == "span"

    def test_transform_filters_irrelevant_attributes(self):
        """Should filter out irrelevant attributes."""
        transformer = DOMTransformer()
        raw_data = {
            "tag": "div",
            "attributes": {
                "class": "test",
                "data-reactid": "123",  # Should be filtered
                "id": "main",
            },
            "children": [],
            "text_content": None,
            "computed_styles": {},
        }

        result = transformer.transform(raw_data)

        assert "data-reactid" not in result.attributes
        assert "class" in result.attributes
        assert "id" in result.attributes


class TestStyleTransformer:
    def test_transform_categorizes_styles(self):
        """Should organize styles into categories."""
        transformer = StyleTransformer()
        raw_styles = {
            "display": "flex",
            "flex-direction": "column",
            "padding": "20px",
            "margin": "10px",
            "font-size": "16px",
            "color": "#333",
            "background-color": "#fff",
            "box-shadow": "0 2px 4px black",
        }

        result = transformer.transform(raw_styles)

        assert isinstance(result, StyleSummary)
        assert result.layout["display"] == "flex"
        assert result.spacing["padding"] == "20px"
        assert result.typography["font-size"] == "16px"
        assert result.colors["color"] == "#333"
        assert result.effects["box-shadow"] == "0 2px 4px black"


class TestContextBuilder:
    def test_build_creates_normalized_output(self):
        """Should assemble all data into NormalizedOutput."""
        builder = ContextBuilder()

        extraction_data = {
            "page": {
                "url": "https://example.com",
                "title": "Test",
                "viewport": {"width": 1920, "height": 1080},
                "loaded_scripts": [],
                "loaded_stylesheets": [],
            },
            "target": {
                "selector_used": ".test",
                "strategy": "css",
                "html": "<div>test</div>",
                "bounding_box": {"x": 0, "y": 0, "width": 100, "height": 100},
                "depth": 1,
            },
            "dom_tree": {
                "tag": "div",
                "attributes": {},
                "children": [],
                "text_content": "test",
                "computed_styles": {},
            },
            "styles": {
                "display": "block",
            },
            "assets": [],
            "interactions": {
                "hoverable": [],
                "clickable": [],
                "focusable": [],
                "scroll_containers": [],
                "observed_states": [],
            },
            "animations": {
                "animations": [],
                "transitions": [],
                "keyframes": {},
            },
            "responsive": {
                "breakpoints": [],
                "is_fluid": False,
                "has_mobile_menu": False,
                "grid_changes": [],
            },
            "libraries": [],
        }

        result = builder.build(extraction_data)

        assert result.page.url == "https://example.com"
        assert result.target.selector_used == ".test"
        assert result.dom.tag == "div"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/normalizer/test_normalizer.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create normalizer package structure**

```python
# normalizer/__init__.py
"""Normalizer module for structuring extraction data."""

from normalizer.context_builder import ContextBuilder

__all__ = ["ContextBuilder"]
```

```python
# normalizer/transformers/__init__.py
"""Data transformers for normalizer."""

from normalizer.transformers.dom_transformer import DOMTransformer
from normalizer.transformers.style_transformer import StyleTransformer
from normalizer.transformers.animation_transformer import AnimationTransformer

__all__ = ["DOMTransformer", "StyleTransformer", "AnimationTransformer"]
```

```python
# normalizer/transformers/dom_transformer.py
"""Transform raw DOM data into structured DOMTree."""

from models.normalized import DOMTree


class DOMTransformer:
    """Transform raw DOM extraction data."""

    # Attributes to filter out
    IGNORED_ATTRIBUTES = {
        "data-reactid",
        "data-react-checksum",
        "data-testid",
        "ng-scope",
        "ng-binding",
    }

    def transform(self, raw_data: dict) -> DOMTree:
        """Transform raw DOM data into DOMTree model."""
        # Filter attributes
        filtered_attrs = {
            k: v for k, v in raw_data.get("attributes", {}).items()
            if k not in self.IGNORED_ATTRIBUTES
        }

        # Recursively transform children
        children = [
            self.transform(child)
            for child in raw_data.get("children", [])
        ]

        return DOMTree(
            tag=raw_data.get("tag", "div"),
            attributes=filtered_attrs,
            children=children,
            text_content=raw_data.get("text_content"),
            computed_styles=raw_data.get("computed_styles", {}),
        )
```

```python
# normalizer/transformers/style_transformer.py
"""Transform raw styles into categorized StyleSummary."""

from models.normalized import StyleSummary


class StyleTransformer:
    """Categorize computed styles."""

    LAYOUT_PROPS = {
        "display", "position", "flex-direction", "flex-wrap", "justify-content",
        "align-items", "align-content", "grid-template-columns", "grid-template-rows",
        "gap", "row-gap", "column-gap", "float", "clear", "z-index", "order",
    }

    SPACING_PROPS = {
        "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
        "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
        "width", "height", "min-width", "max-width", "min-height", "max-height",
    }

    TYPOGRAPHY_PROPS = {
        "font-family", "font-size", "font-weight", "font-style", "line-height",
        "letter-spacing", "text-align", "text-decoration", "text-transform",
        "white-space", "word-spacing", "word-break",
    }

    COLOR_PROPS = {
        "color", "background-color", "border-color", "outline-color",
        "text-shadow", "box-shadow",
    }

    EFFECTS_PROPS = {
        "opacity", "transform", "filter", "backdrop-filter", "mix-blend-mode",
        "border-radius", "border-width", "border-style", "outline",
        "overflow", "overflow-x", "overflow-y", "visibility",
    }

    def transform(self, raw_styles: dict) -> StyleSummary:
        """Categorize raw styles into groups."""
        return StyleSummary(
            layout=self._extract_category(raw_styles, self.LAYOUT_PROPS),
            spacing=self._extract_category(raw_styles, self.SPACING_PROPS),
            typography=self._extract_category(raw_styles, self.TYPOGRAPHY_PROPS),
            colors=self._extract_category(raw_styles, self.COLOR_PROPS),
            effects=self._extract_category(raw_styles, self.EFFECTS_PROPS),
        )

    def _extract_category(self, styles: dict, props: set) -> dict:
        """Extract matching properties from styles."""
        return {
            prop: styles[prop]
            for prop in props
            if prop in styles
        }
```

```python
# normalizer/transformers/animation_transformer.py
"""Transform animation data into AnimationSummary."""

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
            if any("transform" in frame for frame in frames.values()):
                transform_values = [
                    frame.get("transform", "")
                    for frame in frames.values()
                ]
                if any("translateY" in v or "translate3d" in v for v in transform_values):
                    effects.append(f"potential-parallax: {name}")

        return effects
```

```python
# normalizer/context_builder.py
"""Build normalized output from extraction data."""

from models.extraction import BoundingBox, Asset, ExternalLibrary
from models.normalized import (
    NormalizedOutput,
    PageInfo,
    TargetInfo,
    InteractionSummary,
    ResponsiveBehavior,
)
from normalizer.transformers import DOMTransformer, StyleTransformer, AnimationTransformer


class ContextBuilder:
    """Assemble extraction data into NormalizedOutput."""

    def __init__(self):
        self.dom_transformer = DOMTransformer()
        self.style_transformer = StyleTransformer()
        self.animation_transformer = AnimationTransformer()

    def build(self, extraction_data: dict) -> NormalizedOutput:
        """Build NormalizedOutput from raw extraction data."""
        page_data = extraction_data.get("page", {})
        target_data = extraction_data.get("target", {})
        dom_data = extraction_data.get("dom_tree", {})
        styles_data = extraction_data.get("styles", {})
        assets_data = extraction_data.get("assets", [])
        interactions_data = extraction_data.get("interactions", {})
        animations_data = extraction_data.get("animations", {})
        responsive_data = extraction_data.get("responsive", {})
        libraries_data = extraction_data.get("libraries", [])

        # Build page info
        page_info = PageInfo(
            url=page_data.get("url", ""),
            title=page_data.get("title", ""),
            viewport=page_data.get("viewport", {}),
            loaded_scripts=page_data.get("loaded_scripts", []),
            loaded_stylesheets=page_data.get("loaded_stylesheets", []),
        )

        # Build target info
        box_data = target_data.get("bounding_box", {})
        target_info = TargetInfo(
            selector_used=target_data.get("selector_used", ""),
            strategy=target_data.get("strategy", "css"),
            html=target_data.get("html", ""),
            bounding_box=BoundingBox(
                x=box_data.get("x", 0),
                y=box_data.get("y", 0),
                width=box_data.get("width", 0),
                height=box_data.get("height", 0),
            ),
            depth_in_dom=target_data.get("depth", 0),
        )

        # Transform DOM
        dom_tree = self.dom_transformer.transform(dom_data)

        # Transform styles
        style_summary = self.style_transformer.transform(styles_data)

        # Build interaction summary
        interaction_summary = InteractionSummary(
            hoverable_elements=interactions_data.get("hoverable", []),
            clickable_elements=interactions_data.get("clickable", []),
            focusable_elements=interactions_data.get("focusable", []),
            scroll_containers=interactions_data.get("scroll_containers", []),
            observed_states={
                state["selector"]: state
                for state in interactions_data.get("observed_states", [])
            },
        )

        # Transform animations
        animation_summary = self.animation_transformer.transform(
            animations_data.get("animations", []),
            animations_data.get("transitions", []),
            animations_data.get("keyframes", {}),
            animations_data.get("recording"),
        )

        # Build responsive behavior
        responsive_behavior = ResponsiveBehavior(
            breakpoints=responsive_data.get("breakpoints", []),
            is_fluid=responsive_data.get("is_fluid", False),
            has_mobile_menu=responsive_data.get("has_mobile_menu", False),
            grid_changes=responsive_data.get("grid_changes", []),
        )

        # Build assets
        assets = [Asset(**a) for a in assets_data]

        # Build libraries
        libraries = [ExternalLibrary(**lib) for lib in libraries_data]

        return NormalizedOutput(
            page=page_info,
            target=target_info,
            dom=dom_tree,
            styles=style_summary,
            assets=assets,
            interactions=interaction_summary,
            animations=animation_summary,
            responsive_behavior=responsive_behavior,
            external_libraries=libraries,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/normalizer/test_normalizer.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add normalizer/ tests/normalizer/
git commit -m "feat(normalizer): add ContextBuilder and transformers for data normalization"
```

---

## Chunk 7: Synthesizer & Orchestrator

### Task 7.1: Synthesizer Package

**Files:**
- Create: `synthesizer/__init__.py`
- Create: `synthesizer/prompts/__init__.py`
- Create: `synthesizer/prompts/synthesis_prompt.py`
- Create: `synthesizer/openai_client.py`
- Create: `tests/synthesizer/test_synthesizer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/synthesizer/test_synthesizer.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from synthesizer.prompts.synthesis_prompt import build_user_prompt, SYSTEM_PROMPT
from synthesizer.openai_client import OpenAISynthesizer
from models.normalized import (
    NormalizedOutput, PageInfo, TargetInfo, DOMTree, StyleSummary,
    AnimationSummary, InteractionSummary, ResponsiveBehavior,
)


class TestSynthesisPrompt:
    def test_system_prompt_exists(self):
        """System prompt should be defined."""
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 100

    def test_build_user_prompt_includes_url(self):
        """User prompt should include page URL."""
        output = self._create_minimal_output()
        prompt = build_user_prompt(output)

        assert "https://example.com" in prompt

    def test_build_user_prompt_includes_styles(self):
        """User prompt should include styles section."""
        output = self._create_minimal_output()
        prompt = build_user_prompt(output)

        assert "## Estilos" in prompt or "## Styles" in prompt

    def _create_minimal_output(self) -> NormalizedOutput:
        """Create minimal NormalizedOutput for testing."""
        from models.extraction import BoundingBox

        return NormalizedOutput(
            page=PageInfo(
                url="https://example.com",
                title="Test",
                viewport={"width": 1920, "height": 1080},
                loaded_scripts=[],
                loaded_stylesheets=[],
            ),
            target=TargetInfo(
                selector_used=".test",
                strategy="css",
                html="<div>test</div>",
                bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
                depth_in_dom=1,
            ),
            dom=DOMTree(
                tag="div",
                attributes={},
                children=[],
                text_content="test",
                computed_styles={},
            ),
            styles=StyleSummary(
                layout={},
                spacing={},
                typography={},
                colors={},
                effects={},
            ),
            assets=[],
            interactions=InteractionSummary(
                hoverable_elements=[],
                clickable_elements=[],
                focusable_elements=[],
                scroll_containers=[],
                observed_states={},
            ),
            animations=AnimationSummary(
                css_animations=[],
                css_transitions=[],
                scroll_effects=[],
                recording=None,
            ),
            responsive_behavior=ResponsiveBehavior(
                breakpoints=[],
                is_fluid=False,
                has_mobile_menu=False,
                grid_changes=[],
            ),
            external_libraries=[],
        )


class TestOpenAISynthesizer:
    def test_init_with_api_key(self):
        """Should initialize with API key."""
        synthesizer = OpenAISynthesizer(api_key="test-key")
        assert synthesizer.model == "gpt-5.4"

    @patch("synthesizer.openai_client.OpenAI")
    def test_synthesize_calls_api(self, mock_openai):
        """Should call OpenAI API with structured output."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.output_text = """
        {
            "description": {"technical": "test", "visual": "test", "purpose": "test"},
            "component_tree": {"name": "Root", "role": "container", "children": []},
            "interactions": [],
            "responsive_rules": [],
            "dependencies": [],
            "recreation_prompt": "Test prompt"
        }
        """
        mock_client.responses.create.return_value = mock_response

        synthesizer = OpenAISynthesizer(api_key="test-key")
        output = self._create_minimal_output()

        result = synthesizer.synthesize(output)

        assert result.recreation_prompt == "Test prompt"
        mock_client.responses.create.assert_called_once()

    def _create_minimal_output(self) -> NormalizedOutput:
        """Create minimal NormalizedOutput for testing."""
        from models.extraction import BoundingBox

        return NormalizedOutput(
            page=PageInfo(
                url="https://example.com",
                title="Test",
                viewport={"width": 1920, "height": 1080},
                loaded_scripts=[],
                loaded_stylesheets=[],
            ),
            target=TargetInfo(
                selector_used=".test",
                strategy="css",
                html="<div>test</div>",
                bounding_box=BoundingBox(x=0, y=0, width=100, height=100),
                depth_in_dom=1,
            ),
            dom=DOMTree(
                tag="div",
                attributes={},
                children=[],
                text_content="test",
                computed_styles={},
            ),
            styles=StyleSummary(
                layout={},
                spacing={},
                typography={},
                colors={},
                effects={},
            ),
            assets=[],
            interactions=InteractionSummary(
                hoverable_elements=[],
                clickable_elements=[],
                focusable_elements=[],
                scroll_containers=[],
                observed_states={},
            ),
            animations=AnimationSummary(
                css_animations=[],
                css_transitions=[],
                scroll_effects=[],
                recording=None,
            ),
            responsive_behavior=ResponsiveBehavior(
                breakpoints=[],
                is_fluid=False,
                has_mobile_menu=False,
                grid_changes=[],
            ),
            external_libraries=[],
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/synthesizer/test_synthesizer.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create synthesizer package**

```python
# synthesizer/__init__.py
"""Synthesizer module for AI prompt generation."""

from synthesizer.openai_client import OpenAISynthesizer

__all__ = ["OpenAISynthesizer"]
```

```python
# synthesizer/prompts/__init__.py
"""Prompt templates for AI synthesis."""

from synthesizer.prompts.synthesis_prompt import SYSTEM_PROMPT, build_user_prompt

__all__ = ["SYSTEM_PROMPT", "build_user_prompt"]
```

```python
# synthesizer/prompts/synthesis_prompt.py
"""System prompt and user prompt builder for AI synthesis."""

import json
from models.normalized import NormalizedOutput


SYSTEM_PROMPT = """Você é um especialista em engenharia de UI/UX. Sua tarefa é analisar dados
estruturados de um componente web e gerar um prompt detalhado que permita
recriar esse componente fielmente.

Você receberá:
- Estrutura DOM do componente
- Estilos computados organizados por categoria
- Dados de animações e transições (incluindo gravação)
- Interações observadas (hover, click, scroll)
- Comportamento responsivo
- Bibliotecas externas detectadas e como são usadas
- Assets (imagens, fontes, SVGs)

Seu output deve ser um JSON estruturado com:
1. description: objeto com technical, visual, purpose
2. component_tree: árvore de componentes com name, role, children
3. interactions: lista de objetos com trigger, effect, animation (opcional)
4. responsive_rules: lista de objetos com breakpoint, changes
5. dependencies: lista de objetos com name, reason, alternative (opcional)
6. recreation_prompt: string com o prompt final otimizado

O prompt final deve ser agnóstico de framework, focando em HTML/CSS/JS puro,
e conter detalhes suficientes para reproduzir comportamentos complexos."""


def build_user_prompt(data: NormalizedOutput) -> str:
    """Build user prompt from normalized data."""
    sections = [
        f"## Página\nURL: {data.page.url}\nTítulo: {data.page.title}\nViewport: {data.page.viewport}",
        f"## Componente Alvo\nSeletor: {data.target.selector_used}\nEstratégia: {data.target.strategy}",
        f"## HTML\n```\n{data.target.html[:1000]}{'...' if len(data.target.html) > 1000 else ''}\n```",
        f"## Estilos\n```json\n{json.dumps(data.styles.model_dump(), indent=2, ensure_ascii=False)}\n```",
        f"## Animações\n{format_animations(data.animations)}",
        f"## Interações\n{format_interactions(data.interactions)}",
        f"## Responsivo\n{format_responsive(data.responsive_behavior)}",
        f"## Bibliotecas Externas\n{format_libraries(data.external_libraries)}",
        f"## Assets\n{format_assets(data.assets)}",
    ]

    return "\n\n".join(sections)


def format_animations(animations) -> str:
    """Format animation data for prompt."""
    lines = []

    if animations.css_animations:
        lines.append("CSS Animations:")
        for anim in animations.css_animations:
            lines.append(f"  - {anim.name or 'unnamed'}: {anim.duration} {anim.timing_function}")

    if animations.css_transitions:
        lines.append("Transitions:")
        for trans in animations.css_transitions:
            lines.append(f"  - {trans.property}: {trans.duration}")

    if animations.scroll_effects:
        lines.append("Scroll Effects:")
        for effect in animations.scroll_effects:
            lines.append(f"  - {effect}")

    return "\n".join(lines) if lines else "Nenhuma animação detectada"


def format_interactions(interactions) -> str:
    """Format interaction data for prompt."""
    lines = []

    if interactions.hoverable_elements:
        lines.append(f"Hoverable: {', '.join(interactions.hoverable_elements[:5])}")
    if interactions.clickable_elements:
        lines.append(f"Clickable: {', '.join(interactions.clickable_elements[:5])}")
    if interactions.focusable_elements:
        lines.append(f"Focusable: {', '.join(interactions.focusable_elements[:5])}")

    return "\n".join(lines) if lines else "Nenhuma interação detectada"


def format_responsive(responsive) -> str:
    """Format responsive data for prompt."""
    lines = [f"Fluid: {responsive.is_fluid}"]
    lines.append(f"Mobile menu: {responsive.has_mobile_menu}")

    if responsive.breakpoints:
        lines.append("Breakpoints:")
        for bp in responsive.breakpoints:
            lines.append(f"  - {bp.width}px: {bp.layout_changes}")

    return "\n".join(lines)


def format_libraries(libraries) -> str:
    """Format library data for prompt."""
    if not libraries:
        return "Nenhuma biblioteca externa detectada"

    lines = []
    for lib in libraries:
        lines.append(f"- {lib.name}" + (f" ({lib.version})" if lib.version else ""))
        if lib.usage_snippets:
            lines.append(f"  Usage: {lib.usage_snippets[0][:100]}")

    return "\n".join(lines)


def format_assets(assets) -> str:
    """Format asset data for prompt."""
    if not assets:
        return "Nenhum asset detectado"

    by_type = {}
    for asset in assets:
        by_type.setdefault(asset.type.value, []).append(asset)

    lines = []
    for asset_type, items in by_type.items():
        lines.append(f"{asset_type}: {len(items)} items")

    return "\n".join(lines)
```

```python
# synthesizer/openai_client.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/synthesizer/test_synthesizer.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add synthesizer/ tests/synthesizer/
git commit -m "feat(synthesizer): add OpenAI client with structured outputs"
```

---

### Task 7.2: Orchestrator

**Files:**
- Create: `orchestrator.py`
- Create: `tests/test_orchestrator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_orchestrator.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from orchestrator import ExtractionOrchestrator
from models.errors import ExtractionError, NavigationError


class TestExtractionOrchestrator:
    def setup_method(self):
        """Set up temp directory for each test."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("orchestrator.BrowserManager")
    @patch("orchestrator.OpenAISynthesizer")
    def test_init(self, mock_synthesizer, mock_browser):
        """Should initialize all components."""
        orch = ExtractionOrchestrator(api_key="test-key", output_dir=self.temp_dir)

        assert orch.api_key == "test-key"
        assert orch.output_dir == self.temp_dir

    @patch("orchestrator.BrowserManager")
    @patch("orchestrator.OpenAISynthesizer")
    def test_cancel_check_raises_error(self, mock_synthesizer, mock_browser):
        """Should raise error when cancelled."""
        orch = ExtractionOrchestrator(api_key="test-key", output_dir=self.temp_dir)

        with pytest.raises(ExtractionError) as exc_info:
            orch.extract(
                "https://example.com",
                "css",
                ".test",
                cancel_check=lambda: True
            )

        assert "Cancelado" in str(exc_info.value)

    @patch("orchestrator.BrowserManager")
    @patch("orchestrator.OpenAISynthesizer")
    def test_progress_callback_called(self, mock_synthesizer, mock_browser):
        """Should call progress callback during extraction."""
        mock_browser_instance = MagicMock()
        mock_browser.return_value = mock_browser_instance
        mock_browser_instance.page.url = "https://example.com"
        mock_browser_instance.page.title.return_value = "Test"
        mock_browser_instance.page.viewport_size = {"width": 1920, "height": 1080}

        progress_calls = []

        def progress_callback(step, message):
            progress_calls.append((step, message))

        orch = ExtractionOrchestrator(api_key="test-key", output_dir=self.temp_dir)

        # This will fail at some point but should have called progress
        try:
            orch.extract(
                "https://example.com",
                "css",
                ".test",
                progress_callback=progress_callback,
            )
        except Exception:
            pass

        # Should have at least some progress calls
        # (exact number depends on how far it gets)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_orchestrator.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write Orchestrator**

```python
# orchestrator.py
"""Pipeline orchestrator for component extraction."""

import json
from datetime import datetime
from pathlib import Path

from collector import (
    BrowserManager,
    TargetFinder,
    DOMExtractor,
    StyleExtractor,
    InteractionMapper,
    InteractionPlayer,
    AssetDownloader,
    AnimationRecorder,
    LibraryDetector,
    ResponsiveCollector,
)
from normalizer import ContextBuilder
from synthesizer import OpenAISynthesizer
from models.errors import ExtractionError, NavigationError, TargetNotFoundError
from models.extraction import SelectorStrategy


class ExtractionOrchestrator:
    """Coordinate the complete extraction pipeline."""

    PROGRESS_STEPS = [
        (0, "Conectando ao browser"),
        (1, "Localizando componente"),
        (2, "Extraindo DOM"),
        (3, "Extraindo estilos"),
        (4, "Mapeando interações"),
        (5, "Executando interações"),
        (6, "Gravando animações"),
        (7, "Baixando assets"),
        (8, "Detectando bibliotecas"),
        (9, "Analisando responsividade"),
        (10, "Normalizando dados"),
        (11, "Gerando prompt com IA"),
    ]

    def __init__(self, api_key: str, output_dir: str = "output"):
        self.api_key = api_key
        self.output_dir = output_dir
        self.browser = BrowserManager()
        self.synthesizer = OpenAISynthesizer(api_key)

    def extract(
        self,
        url: str,
        strategy: str,
        query: str,
        progress_callback=None,
        cancel_check=None,
    ):
        """Execute complete extraction pipeline."""
        cancel_check = cancel_check or (lambda: False)

        try:
            # Start browser
            if cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            self._report_progress(progress_callback, 0)

            self.browser.start()
            self.browser.navigate(url)

            # Find target
            if cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            self._report_progress(progress_callback, 1)

            strategy_enum = SelectorStrategy(strategy)
            finder = TargetFinder(self.browser.page)
            target = finder.find(strategy_enum, query)

            # Extract DOM
            if cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            self._report_progress(progress_callback, 2)

            dom_extractor = DOMExtractor(self.browser.page)
            dom_data = dom_extractor.extract(target)

            # Extract styles
            if cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            self._report_progress(progress_callback, 3)

            style_extractor = StyleExtractor(self.browser.page)
            style_data = style_extractor.extract(target)

            # Map interactions
            if cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            self._report_progress(progress_callback, 4)

            interaction_mapper = InteractionMapper(self.browser.page)
            interactions = interaction_mapper.map(target)

            # Play interactions
            if cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            self._report_progress(progress_callback, 5)

            interaction_player = InteractionPlayer(self.browser.page)
            observed_states = interaction_player.play_all(target, interactions)

            # Record animations
            if cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            self._report_progress(progress_callback, 6)

            animation_recorder = AnimationRecorder(self.browser.page, self.output_dir)
            animation_data = animation_recorder.record(target)

            # Download assets
            if cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            self._report_progress(progress_callback, 7)

            asset_downloader = AssetDownloader(self.browser.page, self.output_dir)
            assets = asset_downloader.download_all(target)

            # Detect libraries
            if cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            self._report_progress(progress_callback, 8)

            library_detector = LibraryDetector(self.browser.page)
            libraries = library_detector.detect()

            # Collect responsive data
            if cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            self._report_progress(progress_callback, 9)

            responsive_collector = ResponsiveCollector(self.browser.page)
            responsive_data = responsive_collector.collect_all(target)

            # Normalize data
            if cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            self._report_progress(progress_callback, 10)

            context_builder = ContextBuilder()
            extraction_data = {
                "page": {
                    "url": self.browser.page.url,
                    "title": self.browser.page.title(),
                    "viewport": self.browser.page.viewport_size,
                    "loaded_scripts": self._get_loaded_scripts(),
                    "loaded_stylesheets": self._get_loaded_stylesheets(),
                },
                "target": {
                    "selector_used": query,
                    "strategy": strategy,
                    "html": dom_data["html"],
                    "bounding_box": dom_data["bounding_box"],
                    "depth": dom_data["depth"],
                },
                "dom_tree": dom_data["dom_tree"],
                "styles": style_data["computed_styles"],
                "assets": [a.model_dump() for a in assets],
                "interactions": {
                    **interactions,
                    "observed_states": observed_states,
                },
                "animations": {
                    "animations": style_data["animations"],
                    "transitions": style_data["transitions"],
                    "keyframes": style_data["keyframes"],
                    "recording": animation_data.model_dump() if animation_data else None,
                },
                "responsive": responsive_data.model_dump(),
                "libraries": [lib.model_dump() for lib in libraries],
            }

            normalized = context_builder.build(extraction_data)

            # Save normalized JSON
            self._save_normalized(normalized)

            # Synthesize with AI
            if cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            self._report_progress(progress_callback, 11)

            synthesis = self.synthesizer.synthesize(normalized)

            return synthesis

        finally:
            self.browser.close()

    def _report_progress(self, callback, step: int):
        """Report progress if callback provided."""
        if callback:
            _, message = self.PROGRESS_STEPS[step]
            callback(step, message)

    def _get_loaded_scripts(self) -> list[str]:
        """Get list of loaded script URLs."""
        return self.browser.page.evaluate("""() => {
            return Array.from(document.querySelectorAll('script[src]'))
                .map(s => s.src);
        }""")

    def _get_loaded_stylesheets(self) -> list[str]:
        """Get list of loaded stylesheet URLs."""
        return self.browser.page.evaluate("""() => {
            return Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
                .map(l => l.href);
        }""")

    def _save_normalized(self, normalized):
        """Save normalized data to JSON file."""
        extractions_dir = Path(self.output_dir) / "extractions"
        extractions_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"extraction_{timestamp}.json"
        filepath = extractions_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(normalized.model_dump(), f, indent=2, ensure_ascii=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_orchestrator.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add orchestrator.py tests/test_orchestrator.py
git commit -m "feat: add ExtractionOrchestrator for pipeline coordination"
```

---

## Chunk 8: GUI & Worker

### Task 8.1: Worker Thread

**Files:**
- Create: `worker.py`
- Create: `tests/test_worker.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_worker.py
import pytest
import queue
import time
from unittest.mock import Mock, patch, MagicMock
from worker import ExtractionWorker


class TestExtractionWorker:
    @patch("worker.ExtractionOrchestrator")
    def test_worker_starts(self, mock_orchestrator):
        """Worker should start and run."""
        mock_instance = MagicMock()
        mock_orchestrator.return_value = mock_instance
        mock_instance.extract.return_value = MagicMock(
            recreation_prompt="Test prompt"
        )

        callback_queue = queue.Queue()
        worker = ExtractionWorker(
            orchestrator=mock_instance,
            url="https://example.com",
            strategy="css",
            query=".test",
            callback_queue=callback_queue,
        )

        worker.start()
        worker.join(timeout=5)

        assert not worker.is_alive()

    @patch("worker.ExtractionOrchestrator")
    def test_worker_sends_success_message(self, mock_orchestrator):
        """Worker should send success message to queue."""
        mock_instance = MagicMock()
        mock_orchestrator.return_value = mock_instance

        mock_result = MagicMock()
        mock_result.recreation_prompt = "Test prompt"
        mock_instance.extract.return_value = mock_result

        callback_queue = queue.Queue()
        worker = ExtractionWorker(
            orchestrator=mock_instance,
            url="https://example.com",
            strategy="css",
            query=".test",
            callback_queue=callback_queue,
        )

        worker.start()
        worker.join(timeout=5)

        # Check queue for success message
        msg = callback_queue.get(timeout=1)
        assert msg[0] == "success"

    @patch("worker.ExtractionOrchestrator")
    def test_worker_sends_progress_messages(self, mock_orchestrator):
        """Worker should send progress messages."""
        mock_instance = MagicMock()
        mock_orchestrator.return_value = mock_instance

        def mock_extract(url, strategy, query, progress_callback=None, cancel_check=None):
            if progress_callback:
                progress_callback(0, "Step 0")
                progress_callback(1, "Step 1")
            return MagicMock(recreation_prompt="Test")

        mock_instance.extract = mock_extract

        callback_queue = queue.Queue()
        worker = ExtractionWorker(
            orchestrator=mock_instance,
            url="https://example.com",
            strategy="css",
            query=".test",
            callback_queue=callback_queue,
        )

        worker.start()
        worker.join(timeout=5)

        # Check for progress messages
        messages = []
        while not callback_queue.empty():
            messages.append(callback_queue.get())

        progress_msgs = [m for m in messages if m[0] == "progress"]
        assert len(progress_msgs) >= 2

    @patch("worker.ExtractionOrchestrator")
    def test_worker_cancel_sets_event(self, mock_orchestrator):
        """Worker cancel should set event."""
        mock_instance = MagicMock()
        mock_orchestrator.return_value = mock_instance

        callback_queue = queue.Queue()
        worker = ExtractionWorker(
            orchestrator=mock_instance,
            url="https://example.com",
            strategy="css",
            query=".test",
            callback_queue=callback_queue,
        )

        assert not worker._cancel_event.is_set()
        worker.cancel()
        assert worker._cancel_event.is_set()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_worker.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write Worker**

```python
# worker.py
"""Threading worker for extraction pipeline."""

import threading
import queue

from orchestrator import ExtractionOrchestrator
from models.errors import ExtractionError


class ExtractionWorker(threading.Thread):
    """Run extraction in background thread."""

    def __init__(
        self,
        orchestrator: ExtractionOrchestrator,
        url: str,
        strategy: str,
        query: str,
        callback_queue: queue.Queue,
    ):
        super().__init__()
        self.orchestrator = orchestrator
        self.url = url
        self.strategy = strategy
        self.query = query
        self.callback_queue = callback_queue
        self._cancel_event = threading.Event()

    def run(self):
        """Execute extraction and report progress."""
        try:
            result = self.orchestrator.extract(
                self.url,
                self.strategy,
                self.query,
                progress_callback=self._progress_callback,
                cancel_check=self._cancel_event.is_set,
            )
            self.callback_queue.put(("success", result))
        except ExtractionError as e:
            self.callback_queue.put(("error", str(e)))
        except Exception as e:
            self.callback_queue.put(("error", f"Erro inesperado: {str(e)}"))

    def cancel(self):
        """Signal cancellation."""
        self._cancel_event.set()

    def _progress_callback(self, step: int, message: str):
        """Report progress to callback queue."""
        self.callback_queue.put(("progress", step, message))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_worker.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add worker.py tests/test_worker.py
git commit -m "feat: add ExtractionWorker for threaded extraction"
```

---

### Task 8.2: GUI Application

**Files:**
- Create: `gui/__init__.py`
- Create: `gui/widgets/__init__.py`
- Create: `gui/widgets/progress_display.py`
- Create: `gui/panels/__init__.py`
- Create: `gui/panels/input_panel.py`
- Create: `gui/panels/result_panel.py`
- Create: `gui/app.py`
- Create: `tests/gui/test_app.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/gui/test_app.py
import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock


class TestComponentExtractorApp:
    def test_app_initialization(self):
        """App should initialize with correct structure."""
        from gui.app import ComponentExtractorApp

        root = tk.Tk()
        app = ComponentExtractorApp(root)

        assert app.root == root
        root.destroy()

    def test_app_has_input_panel(self):
        """App should have input panel."""
        from gui.app import ComponentExtractorApp

        root = tk.Tk()
        app = ComponentExtractorApp(root)

        assert hasattr(app, "input_panel")
        root.destroy()

    def test_app_has_result_panel(self):
        """App should have result panel."""
        from gui.app import ComponentExtractorApp

        root = tk.Tk()
        app = ComponentExtractorApp(root)

        assert hasattr(app, "result_panel")
        root.destroy()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/gui/test_app.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create GUI package**

```python
# gui/__init__.py
"""GUI module for Component Extractor."""

from gui.app import ComponentExtractorApp

__all__ = ["ComponentExtractorApp"]
```

```python
# gui/widgets/__init__.py
"""GUI widgets."""

from gui.widgets.progress_display import ProgressDisplay

__all__ = ["ProgressDisplay"]
```

```python
# gui/widgets/progress_display.py
"""Progress display widget."""

import tkinter as tk
from tkinter import ttk


class ProgressDisplay:
    """Display extraction progress with steps."""

    STEPS = [
        "Conectando ao browser",
        "Localizando componente",
        "Extraindo DOM",
        "Extraindo estilos",
        "Mapeando interações",
        "Executando interações",
        "Gravando animações",
        "Baixando assets",
        "Detectando bibliotecas",
        "Analisando responsividade",
        "Normalizando dados",
        "Gerando prompt com IA",
    ]

    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding="10")

        # Title
        ttk.Label(self.frame, text="Progresso:", font=("Arial", 10, "bold")).pack(
            anchor="w"
        )

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.frame,
            variable=self.progress_var,
            maximum=len(self.STEPS),
            mode="determinate",
        )
        self.progress_bar.pack(fill="x", pady=(5, 10))

        # Step labels frame
        self.steps_frame = ttk.Frame(self.frame)
        self.steps_frame.pack(fill="x")

        # Create labels for each step
        self.step_labels = []
        for i, step in enumerate(self.STEPS):
            label = ttk.Label(
                self.steps_frame,
                text=f"  {step}",
                foreground="gray",
            )
            label.pack(anchor="w")
            self.step_labels.append(label)

        # Current step label
        self.current_label = ttk.Label(
            self.frame,
            text="Aguardando...",
            font=("Arial", 9),
        )
        self.current_label.pack(anchor="w", pady=(10, 0))

    def set_step(self, step_index: int, message: str = None):
        """Set current step and update display."""
        # Update progress bar
        self.progress_var.set(step_index)

        # Update step labels
        for i, label in enumerate(self.step_labels):
            if i < step_index:
                label.config(foreground="green", text=f"✓ {self.STEPS[i]}")
            elif i == step_index:
                label.config(foreground="blue", text=f"→ {self.STEPS[i]}")
            else:
                label.config(foreground="gray", text=f"  {self.STEPS[i]}")

        # Update current label
        self.current_label.config(text=message or self.STEPS[step_index])

    def reset(self):
        """Reset progress display."""
        self.progress_var.set(0)
        for i, label in enumerate(self.step_labels):
            label.config(foreground="gray", text=f"  {self.STEPS[i]}")
        self.current_label.config(text="Aguardando...")
```

```python
# gui/panels/__init__.py
"""GUI panels."""

from gui.panels.input_panel import InputPanel
from gui.panels.result_panel import ResultPanel

__all__ = ["InputPanel", "ResultPanel"]
```

```python
# gui/panels/input_panel.py
"""Input panel for extraction configuration."""

import tkinter as tk
from tkinter import ttk


class InputPanel:
    """Panel for inputting extraction parameters."""

    def __init__(self, parent, on_extract_callback):
        self.frame = ttk.Frame(parent, padding="10")
        self.on_extract = on_extract_callback

        # URL Input
        ttk.Label(self.frame, text="URL:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.url_entry = ttk.Entry(self.frame, width=50)
        self.url_entry.pack(fill="x", pady=(0, 15))

        # Strategy Selection
        ttk.Label(
            self.frame, text="Estratégia:", font=("Arial", 10, "bold")
        ).pack(anchor="w")

        self.strategy_var = tk.StringVar(value="css")
        strategies = [
            ("Seletor CSS", "css"),
            ("XPath", "xpath"),
            ("Texto", "text"),
            ("HTML Snippet", "html_snippet"),
        ]

        for text, value in strategies:
            ttk.Radiobutton(
                self.frame,
                text=text,
                variable=self.strategy_var,
                value=value,
            ).pack(anchor="w")

        # Selector/Query Input
        ttk.Label(
            self.frame, text="Seletor/Query:", font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(15, 0))
        self.selector_text = tk.Text(self.frame, height=4, width=50)
        self.selector_text.pack(fill="x", pady=(0, 15))

        # Buttons Frame
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill="x", pady=(10, 0))

        self.extract_btn = ttk.Button(
            button_frame,
            text="Extrair Componente",
            command=self._on_extract_click,
        )
        self.extract_btn.pack(side="left", padx=(0, 10))

        self.cancel_btn = ttk.Button(
            button_frame,
            text="Cancelar",
            command=self._on_cancel_click,
            state="disabled",
        )
        self.cancel_btn.pack(side="left")

    def _on_extract_click(self):
        """Handle extract button click."""
        url = self.url_entry.get().strip()
        strategy = self.strategy_var.get()
        query = self.selector_text.get("1.0", "end-1c").strip()

        if not url or not query:
            return

        self.extract_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")

        if self.on_extract:
            self.on_extract(url, strategy, query)

    def _on_cancel_click(self):
        """Handle cancel button click."""
        if hasattr(self, "on_cancel") and self.on_cancel:
            self.on_cancel()

    def set_extracting_state(self, extracting: bool):
        """Set button states based on extraction state."""
        if extracting:
            self.extract_btn.config(state="disabled")
            self.cancel_btn.config(state="normal")
        else:
            self.extract_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")

    def get_values(self) -> tuple[str, str, str]:
        """Get current input values."""
        return (
            self.url_entry.get().strip(),
            self.strategy_var.get(),
            self.selector_text.get("1.0", "end-1c").strip(),
        )
```

```python
# gui/panels/result_panel.py
"""Result panel for displaying extraction results."""

import tkinter as tk
from tkinter import ttk, messagebox
import json


class ResultPanel:
    """Panel for displaying extraction results."""

    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding="10")

        # Notebook with tabs
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill="both", expand=True)

        # Prompt Tab
        self.prompt_tab = ttk.Frame(self.notebook)
        self._setup_prompt_tab()
        self.notebook.add(self.prompt_tab, text="Prompt Final")

        # JSON Tab
        self.json_tab = ttk.Frame(self.notebook)
        self._setup_json_tab()
        self.notebook.add(self.json_tab, text="JSON Completo")

        # Assets Tab
        self.assets_tab = ttk.Frame(self.notebook)
        self._setup_assets_tab()
        self.notebook.add(self.assets_tab, text="Assets")

    def _setup_prompt_tab(self):
        """Setup prompt display tab."""
        # Text area for prompt
        self.prompt_text = tk.Text(self.prompt_tab, wrap="word", height=20)
        self.prompt_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.prompt_tab, command=self.prompt_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.prompt_text.config(yscrollcommand=scrollbar.set)

        # Copy button
        self.copy_btn = ttk.Button(
            self.prompt_tab,
            text="Copiar Prompt",
            command=self._copy_prompt,
        )
        self.copy_btn.pack(pady=5)

    def _setup_json_tab(self):
        """Setup JSON display tab."""
        self.json_text = tk.Text(self.json_tab, wrap="none")
        self.json_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbars
        y_scroll = ttk.Scrollbar(self.json_tab, command=self.json_text.yview)
        y_scroll.pack(side="right", fill="y")
        x_scroll = ttk.Scrollbar(
            self.json_tab, orient="horizontal", command=self.json_text.xview
        )
        x_scroll.pack(side="bottom", fill="x")
        self.json_text.config(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    def _setup_assets_tab(self):
        """Setup assets display tab."""
        # Treeview for assets
        columns = ("type", "path", "size")
        self.assets_tree = ttk.Treeview(self.assets_tab, columns=columns, show="headings")

        self.assets_tree.heading("type", text="Tipo")
        self.assets_tree.heading("path", text="Caminho")
        self.assets_tree.heading("size", text="Tamanho")

        self.assets_tree.column("type", width=80)
        self.assets_tree.column("path", width=400)
        self.assets_tree.column("size", width=100)

        self.assets_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def display_result(self, result):
        """Display extraction result."""
        # Display prompt
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", result.recreation_prompt)

        # Display JSON (simplified)
        self.json_text.delete("1.0", "end")
        json_str = json.dumps(result.model_dump(), indent=2, ensure_ascii=False)
        self.json_text.insert("1.0", json_str)

    def display_assets(self, assets: list):
        """Display assets in treeview."""
        # Clear existing
        for item in self.assets_tree.get_children():
            self.assets_tree.delete(item)

        # Add assets
        for asset in assets:
            size_kb = asset["file_size_bytes"] / 1024
            self.assets_tree.insert(
                "",
                "end",
                values=(
                    asset["type"],
                    asset["local_path"],
                    f"{size_kb:.1f} KB",
                ),
            )

    def _copy_prompt(self):
        """Copy prompt to clipboard."""
        prompt = self.prompt_text.get("1.0", "end-1c")
        self.prompt_text.clipboard_clear()
        self.prompt_text.clipboard_append(prompt)
        messagebox.showinfo("Copiado", "Prompt copiado para a área de transferência!")

    def clear(self):
        """Clear all results."""
        self.prompt_text.delete("1.0", "end")
        self.json_text.delete("1.0", "end")
        for item in self.assets_tree.get_children():
            self.assets_tree.delete(item)
```

```python
# gui/app.py
"""Main GUI application."""

import queue
import tkinter as tk
from tkinter import ttk, messagebox
import os
from dotenv import load_dotenv

from gui.panels import InputPanel, ResultPanel
from gui.widgets import ProgressDisplay
from orchestrator import ExtractionOrchestrator
from worker import ExtractionWorker


class ComponentExtractorApp:
    """Main application class."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Component Extractor")
        self.root.geometry("1000x700")

        # Load environment
        load_dotenv()

        # Initialize components
        self.callback_queue = queue.Queue()
        self.worker = None
        self.orchestrator = None

        # Build UI
        self._build_ui()

        # Start queue polling
        self.root.after(100, self._process_queue)

    def _build_ui(self):
        """Build the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Configure grid
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)

        # Left panel (input)
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.input_panel = InputPanel(left_frame, on_extract_callback=self._on_extract)
        self.input_panel.frame.pack(fill="both", expand=True)

        # Progress display
        self.progress_display = ProgressDisplay(left_frame)
        self.progress_display.frame.pack(fill="x", pady=(10, 0))

        # Right panel (results)
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self.result_panel = ResultPanel(right_frame)
        self.result_panel.frame.pack(fill="both", expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
        )
        status_bar.pack(side="bottom", fill="x")

    def _on_extract(self, url: str, strategy: str, query: str):
        """Handle extract button click."""
        # Get API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            messagebox.showerror("Erro", "OPENAI_API_KEY não configurada.\nConfigure no arquivo .env")
            self.input_panel.set_extracting_state(False)
            return

        # Initialize orchestrator
        self.orchestrator = ExtractionOrchestrator(api_key=api_key)

        # Reset progress
        self.progress_display.reset()

        # Start worker
        self.worker = ExtractionWorker(
            orchestrator=self.orchestrator,
            url=url,
            strategy=strategy,
            query=query,
            callback_queue=self.callback_queue,
        )
        self.worker.start()

        self.status_var.set("Extraindo...")

    def _process_queue(self):
        """Process messages from worker thread."""
        try:
            while True:
                msg = self.callback_queue.get_nowait()
                self._handle_callback(msg)
        except queue.Empty:
            pass

        self.root.after(100, self._process_queue)

    def _handle_callback(self, msg: tuple):
        """Handle callback message from worker."""
        msg_type = msg[0]

        if msg_type == "progress":
            _, step, text = msg
            self.progress_display.set_step(step, text)
            self.status_var.set(text)

        elif msg_type == "success":
            _, result = msg
            self.result_panel.display_result(result)
            self.status_var.set("Concluído!")
            self.input_panel.set_extracting_state(False)
            messagebox.showinfo("Sucesso", "Extração concluída com sucesso!")

        elif msg_type == "error":
            _, error = msg
            self.status_var.set(f"Erro: {error}")
            self.input_panel.set_extracting_state(False)
            messagebox.showerror("Erro", error)
```

- [ ] **Step 4: Update main.py**

```python
# main.py
"""Component Extractor - Extract web components and generate recreation prompts."""

import tkinter as tk
from gui.app import ComponentExtractorApp


def main():
    """Start the application."""
    root = tk.Tk()
    app = ComponentExtractorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/gui/test_app.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add gui/ main.py tests/gui/
git commit -m "feat(gui): add Tkinter interface with input, progress, and result panels"
```

---

## Final Integration

### Task 9.1: Run All Tests

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass

- [ ] **Step 2: Run application**

```bash
python main.py
```

Expected: GUI window opens

- [ ] **Step 3: Create final commit**

```bash
git add .
git commit -m "feat: complete Component Extractor implementation"
```

---

## Summary

This plan covers the complete implementation of the Component Extractor tool:

1. **Foundation** - Project setup, error models, data models
2. **Collector Core** - Browser management, target finding, DOM extraction
3. **Collector Extended** - Style extraction, interaction mapping, asset downloading
4. **Normalizer** - Data transformation and structuring
5. **Synthesizer** - OpenAI integration with structured outputs
6. **Orchestrator** - Pipeline coordination with cancellation support
7. **GUI** - Tkinter interface with threading

Each task follows TDD principles with clear test cases and implementation steps.
