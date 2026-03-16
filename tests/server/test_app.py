"""Tests for FastAPI routes that expose task artifacts and packages."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from models.requests import ExtractionRequest
import server.app as app_module
from server.task import ExtractionTask


@pytest.fixture(autouse=True)
def reset_task_state():
    """Keep task state isolated across route tests."""
    app_module.tasks.clear()
    for job in app_module.cleanup_jobs.values():
        job.cancel()
    app_module.cleanup_jobs.clear()
    yield
    app_module.tasks.clear()
    for job in app_module.cleanup_jobs.values():
        job.cancel()
    app_module.cleanup_jobs.clear()


def build_completed_task(tmp_path: Path) -> ExtractionTask:
    """Create a completed task with a package and a preview artifact."""
    workspace_dir = tmp_path / "task1234"
    screenshots_dir = workspace_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshots_dir / "target.png"
    screenshot_path.write_bytes(b"png")

    package_path = workspace_dir / "component-extractor-task1234.zip"
    package_path.write_bytes(b"zip")

    task = ExtractionTask("task1234", ExtractionRequest(url="https://example.com"))
    task.workspace_dir = workspace_dir
    task.package_path = package_path
    task.package_filename = package_path.name
    task.completed = True
    task.result = {
        "prompt": "Prompt",
        "component_tree": {"name": "Hero", "role": "section", "children": []},
        "interactions": [],
        "responsive_rules": [],
        "dependencies": [],
        "screenshot_path": "screenshots/target.png",
        "screenshot_url": "/api/extract/task1234/artifacts/screenshots/target.png",
        "download_url": "/api/extract/task1234/package",
        "download_filename": package_path.name,
        "expires_at": None,
        "assets": [],
        "full_json": {"mode": "component"},
    }
    return task


def test_package_route_downloads_zip_and_marks_expiry(tmp_path: Path):
    """Package download should return the ZIP and schedule short retention."""
    with TestClient(app_module.app) as client:
        task = build_completed_task(tmp_path)
        app_module.tasks[task.id] = task

        response = client.get(f"/api/extract/{task.id}/package")

        assert response.status_code == 200
        assert response.content == b"zip"
        assert response.headers["content-type"] == "application/zip"
        assert task.downloaded_at is not None
        assert task.expires_at is not None
        assert task.result["expires_at"] is not None


def test_artifact_route_serves_task_preview_file(tmp_path: Path):
    """Artifact preview URLs should resolve within the task workspace only."""
    with TestClient(app_module.app) as client:
        task = build_completed_task(tmp_path)
        app_module.tasks[task.id] = task

        response = client.get(f"/api/extract/{task.id}/artifacts/screenshots/target.png")

        assert response.status_code == 200
        assert response.content == b"png"


def test_artifact_route_rejects_path_traversal(tmp_path: Path):
    """Artifact route should reject traversal outside the task workspace."""
    with TestClient(app_module.app) as client:
        task = build_completed_task(tmp_path)
        app_module.tasks[task.id] = task

        response = client.get(f"/api/extract/{task.id}/artifacts/%2E%2E/secret.txt")

        assert response.status_code == 400
