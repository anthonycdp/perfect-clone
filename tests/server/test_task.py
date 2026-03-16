"""Tests for ExtractionTask."""

import pytest

from models.requests import ExtractionRequest
import server.task as task_module


@pytest.mark.asyncio
async def test_emit_progress():
    """Test that progress events are emitted correctly."""
    request = ExtractionRequest(url="https://example.com")
    task = task_module.ExtractionTask("test-id", request)

    await task.emit_progress(1, "navigating", "Connecting...")

    progress_json = await task.progress_queue.get()
    assert '"step":1' in progress_json or '"step": 1' in progress_json
    assert "navigating" in progress_json


@pytest.mark.asyncio
async def test_progress_generator_yields_events():
    """Test that progress_generator yields all events until done."""
    request = ExtractionRequest(url="https://example.com")
    task = task_module.ExtractionTask("test-id", request)

    await task.emit_progress(1, "step1", "First", done=False)
    await task.emit_progress(2, "step2", "Done", done=True)

    events = []
    async for event in task.progress_generator():
        events.append(event)

    assert len(events) == 2
    assert "done" in events[1]


def test_check_cancelled():
    """Test cancellation check."""
    request = ExtractionRequest(url="https://example.com")
    task = task_module.ExtractionTask("test-id", request)

    assert task.check_cancelled() is False

    task.cancel()
    assert task.check_cancelled() is True
