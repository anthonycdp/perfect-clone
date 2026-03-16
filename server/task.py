"""Task management for extraction operations."""

import asyncio

from models.requests import ExtractionRequest, ProgressEvent


class ExtractionTask:
    """Manages state for a single extraction operation."""

    def __init__(self, task_id: str, request: ExtractionRequest):
        self.id = task_id
        self.request = request
        self.progress_queue: asyncio.Queue = asyncio.Queue()
        self.result = None
        self.completed = False
        self.cancelled = False
        self.error: str | None = None

    async def progress_generator(self):
        """Yield progress events for SSE stream."""
        while True:
            progress_json = await self.progress_queue.get()
            yield progress_json
            if '"done": true' in progress_json or '"done":true' in progress_json:
                break

    async def emit_progress(
        self,
        step: int,
        step_name: str,
        message: str,
        done: bool = False,
    ):
        """Put a progress event into the queue."""
        event = ProgressEvent(
            step=step,
            step_name=step_name,
            message=message,
            done=done,
        )
        await self.progress_queue.put(event.model_dump_json())

    def check_cancelled(self) -> bool:
        """Return True if extraction was cancelled."""
        return self.cancelled

    def cancel(self):
        """Mark the task as cancelled."""
        self.cancelled = True
