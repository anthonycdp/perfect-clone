"""API request and response models."""

from typing import Any, Literal, Optional

from pydantic import BaseModel


class ExtractionRequest(BaseModel):
    """Request to start an extraction."""
    url: str
    mode: Literal["component", "full_page"] = "component"
    strategy: Literal["css", "xpath", "text", "html_snippet"] = "text"
    query: str = ""


class ExtractionResponse(BaseModel):
    """Response after starting an extraction."""
    task_id: str


class ProgressEvent(BaseModel):
    """Progress event sent via SSE."""
    step: int
    step_name: str
    message: str
    total_steps: int = 12
    done: bool = False


class ResultResponse(BaseModel):
    """Final extraction result."""
    prompt: str
    component_tree: dict[str, Any]
    interactions: list[dict[str, Any]]
    responsive_rules: list[dict[str, Any]]
    dependencies: list[dict[str, Any]]
    screenshot_path: Optional[str] = None
    screenshot_url: Optional[str] = None
    download_url: Optional[str] = None
    download_filename: Optional[str] = None
    expires_at: Optional[str] = None
    assets: list[dict[str, Any]]
    full_json: dict[str, Any]


class CancelResponse(BaseModel):
    """Response after cancelling an extraction."""
    cancelled: bool
