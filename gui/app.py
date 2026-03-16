"""Main GUI application."""

import queue
import tkinter as tk
from tkinter import ttk, messagebox
import os

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
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
        )
        status_bar.pack(side="bottom", fill="x")

    def _on_extract(self, url: str, extraction_mode: str, strategy: str, query: str):
        """Handle extract button click."""
        # Get API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            messagebox.showerror(
                "Error",
                "OPENAI_API_KEY not configured.\nSet it in your .env file",
            )
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
            extraction_mode=extraction_mode,
            strategy=strategy,
            query=query,
            callback_queue=self.callback_queue,
        )
        self.worker.start()

        self.status_var.set("Extracting...")

        # Setup cancel handler
        self.input_panel.on_cancel = self._on_cancel

    def _on_cancel(self):
        """Handle cancel button click."""
        if self.worker:
            self.worker.cancel()
            self.status_var.set("Cancelling...")

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
            normalized_output = (
                self.orchestrator.last_normalized_output if self.orchestrator else None
            )

            self.result_panel.display_result(
                result,
                full_json=(
                    normalized_output.model_dump(mode="json")
                    if normalized_output is not None
                    else None
                ),
                screenshot_path=(
                    normalized_output.get_primary_screenshot_path()
                    if normalized_output is not None
                    else None
                ),
                result_kind=(
                    "Landing Page"
                    if normalized_output is not None
                    and normalized_output.mode.value == "full_page"
                    else "Component"
                ),
            )
            self.result_panel.display_assets(
                [
                    asset.model_dump(mode="json")
                    for asset in normalized_output.assets
                ]
                if normalized_output is not None
                else []
            )
            self.status_var.set("Complete!")
            self.input_panel.set_extracting_state(False)
            messagebox.showinfo("Success", "Extraction complete!")

        elif msg_type == "error":
            _, error = msg
            self.status_var.set(f"Error: {error}")
            self.input_panel.set_extracting_state(False)
            messagebox.showerror("Error", error)
