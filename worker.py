"""Threading worker for extraction pipeline."""

import queue
import threading

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
            self.callback_queue.put(("error", f"Unexpected error: {str(e)}"))

    def cancel(self):
        """Signal cancellation."""
        self._cancel_event.set()

    def _progress_callback(self, step: int, message: str):
        """Report progress to callback queue."""
        self.callback_queue.put(("progress", step, message))
