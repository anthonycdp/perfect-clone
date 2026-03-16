"""FastAPI application for the Component Extractor web UI."""

import asyncio
from contextlib import asynccontextmanager
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from starlette.background import BackgroundTask

from models.requests import (
    CancelResponse,
    ExtractionRequest,
    ExtractionResponse,
    ResultResponse,
)
from server.artifacts import cleanup_task_workspace, reset_artifact_root
from server.task import ExtractionTask

DEFAULT_RESULT_TTL_SECONDS = 15 * 60
FAILED_TASK_TTL_SECONDS = 60
POST_DOWNLOAD_TTL_SECONDS = 60

tasks: dict[str, ExtractionTask] = {}
cleanup_jobs: dict[str, asyncio.Task] = {}

STATIC_DIR = Path(__file__).parent / "static"

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Clean stale temp artifacts on startup and cancel cleanup jobs on shutdown."""
    reset_artifact_root()
    yield
    for job in cleanup_jobs.values():
        job.cancel()
    cleanup_jobs.clear()
    tasks.clear()


app = FastAPI(title="Component Extractor", lifespan=lifespan)


@app.get("/")
async def index():
    """Serve the main HTML page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/static/{file_path:path}")
async def static_files(file_path: str):
    """Serve static files (CSS and JS)."""
    return FileResponse(STATIC_DIR / file_path)


@app.post("/api/extract", response_model=ExtractionResponse)
async def start_extraction(request: ExtractionRequest):
    """Start a new extraction task."""
    task_id = str(uuid.uuid4())[:8]
    task = ExtractionTask(task_id, request)
    tasks[task_id] = task
    asyncio.create_task(_run_task(task_id))
    return ExtractionResponse(task_id=task_id)


@app.get("/api/extract/{task_id}/progress")
async def get_progress(task_id: str):
    """Get the SSE stream of extraction progress."""
    task = _get_task(task_id)
    return StreamingResponse(
        task.progress_generator(),
        media_type="text/event-stream",
    )


@app.get("/api/extract/{task_id}/result", response_model=ResultResponse)
async def get_result(task_id: str):
    """Get the final extraction result."""
    task = _get_task(task_id)
    if not task.completed:
        raise HTTPException(400, "Extraction not completed")
    if task.error:
        raise HTTPException(500, task.error)
    return task.result


@app.get("/api/extract/{task_id}/package")
async def download_package(task_id: str):
    """Download the ZIP package for a completed task."""
    task = _get_task(task_id)
    if not task.completed:
        raise HTTPException(400, "Extraction not completed")
    if task.error:
        raise HTTPException(500, task.error)
    if not task.package_path or not task.package_path.exists():
        raise HTTPException(404, "Package not found")

    return FileResponse(
        task.package_path,
        media_type="application/zip",
        filename=task.package_filename,
        background=BackgroundTask(_mark_package_downloaded, task_id),
    )


@app.get("/api/extract/{task_id}/artifacts/{artifact_path:path}")
async def serve_task_artifact(task_id: str, artifact_path: str):
    """Serve a temporary artifact that belongs to a specific task."""
    task = _get_task(task_id)
    artifact_file = _resolve_task_artifact(task, artifact_path)
    if not artifact_file.exists():
        raise HTTPException(404, "Artifact not found")
    return FileResponse(artifact_file)


@app.post("/api/extract/{task_id}/cancel", response_model=CancelResponse)
async def cancel_extraction(task_id: str):
    """Cancel an in-progress extraction."""
    task = tasks.get(task_id)
    if task:
        task.cancel()
    return CancelResponse(cancelled=True)


async def _run_task(task_id: str) -> None:
    """Run one extraction task and schedule cleanup afterwards."""
    task = tasks.get(task_id)
    if task is None:
        return

    from server.runner import run_extraction

    await run_extraction(task)

    if task_id not in tasks:
        return

    if task.completed and task.package_path:
        _schedule_task_cleanup(task_id, DEFAULT_RESULT_TTL_SECONDS)
        return

    if task.error or task.cancelled or task.workspace_dir:
        _schedule_task_cleanup(task_id, FAILED_TASK_TTL_SECONDS)


async def _mark_package_downloaded(task_id: str) -> None:
    """Record the package download and shorten the cleanup deadline."""
    task = tasks.get(task_id)
    if task is None:
        return

    task.downloaded_at = datetime.now(UTC)
    _schedule_task_cleanup(task_id, POST_DOWNLOAD_TTL_SECONDS)


def _schedule_task_cleanup(task_id: str, delay_seconds: int) -> None:
    """Schedule a task and its workspace to be deleted after a delay."""
    task = tasks.get(task_id)
    if task is None:
        return

    existing_job = cleanup_jobs.pop(task_id, None)
    if existing_job:
        existing_job.cancel()

    expires_at = datetime.now(UTC) + timedelta(seconds=delay_seconds)
    task.expires_at = expires_at
    if task.result is not None:
        task.result["expires_at"] = expires_at.isoformat()

    cleanup_jobs[task_id] = asyncio.create_task(
        _cleanup_task_after_delay(task_id, delay_seconds)
    )


async def _cleanup_task_after_delay(task_id: str, delay_seconds: int) -> None:
    """Delete task state and temporary files after the retention period."""
    try:
        await asyncio.sleep(delay_seconds)
        task = tasks.pop(task_id, None)
        if task:
            cleanup_task_workspace(task.workspace_dir)
    except asyncio.CancelledError:
        return
    finally:
        cleanup_jobs.pop(task_id, None)


def _get_task(task_id: str) -> ExtractionTask:
    """Return a task or raise a 404."""
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    return task


def _resolve_task_artifact(task: ExtractionTask, artifact_path: str) -> Path:
    """Resolve a task artifact path and reject traversal outside the workspace."""
    if task.workspace_dir is None:
        raise HTTPException(404, "Task artifacts are not available")

    workspace_dir = task.workspace_dir.resolve()
    candidate = (workspace_dir / artifact_path).resolve()
    if candidate != workspace_dir and workspace_dir not in candidate.parents:
        raise HTTPException(400, "Invalid artifact path")
    return candidate
