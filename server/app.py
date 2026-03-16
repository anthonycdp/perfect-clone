"""FastAPI application for Component Extractor web UI."""

import asyncio
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from models.requests import (
    CancelResponse,
    ExtractionRequest,
    ExtractionResponse,
)
from server.task import ExtractionTask

app = FastAPI(title="Component Extractor")

# In-memory task storage (sufficient for single-user local use)
tasks: dict[str, ExtractionTask] = {}

# Directory paths
STATIC_DIR = Path(__file__).parent / "static"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


@app.get("/")
async def index():
    """Serve the main HTML page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/static/{file_path:path}")
async def static_files(file_path: str):
    """Serve static files (CSS, JS)."""
    return FileResponse(STATIC_DIR / file_path)


@app.get("/screenshots/{file_path:path}")
async def serve_screenshot(file_path: str):
    """Serve screenshot files from output directory."""
    screenshot_path = OUTPUT_DIR / "screenshots" / file_path
    if not screenshot_path.exists():
        raise HTTPException(404, "Screenshot not found")
    return FileResponse(screenshot_path)


@app.post("/api/extract", response_model=ExtractionResponse)
async def start_extraction(request: ExtractionRequest):
    """Start a new extraction task."""
    task_id = str(uuid.uuid4())[:8]
    task = ExtractionTask(task_id, request)
    tasks[task_id] = task

    # Import runner here to avoid circular imports
    from server.runner import run_extraction

    asyncio.create_task(run_extraction(task))
    return ExtractionResponse(task_id=task_id)


@app.get("/api/extract/{task_id}/progress")
async def get_progress(task_id: str):
    """Get SSE stream of extraction progress."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    return StreamingResponse(
        task.progress_generator(),
        media_type="text/event-stream",
    )


@app.get("/api/extract/{task_id}/result")
async def get_result(task_id: str):
    """Get the final extraction result."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if not task.completed:
        raise HTTPException(400, "Extraction not completed")
    if task.error:
        raise HTTPException(500, task.error)
    return task.result


@app.post("/api/extract/{task_id}/cancel", response_model=CancelResponse)
async def cancel_extraction(task_id: str):
    """Cancel an in-progress extraction."""
    task = tasks.get(task_id)
    if task:
        task.cancel()
    return CancelResponse(cancelled=True)
