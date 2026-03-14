"""Progress display widget."""

import tkinter as tk
from tkinter import ttk


class ProgressDisplay:
    """Display extraction progress with steps."""

    STEPS = [
        "Connecting to browser",
        "Locating component",
        "Extracting DOM",
        "Extracting styles",
        "Mapping interactions",
        "Executing interactions",
        "Recording animations",
        "Downloading assets",
        "Detecting libraries",
        "Analyzing responsiveness",
        "Normalizing data",
        "Generating prompt with AI",
    ]

    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding="10")

        # Title
        ttk.Label(self.frame, text="Progress:", font=("Arial", 10, "bold")).pack(
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

        # Current step label
        self.current_label = ttk.Label(
            self.frame,
            text="Ready",
            font=("Arial", 9),
        )
        self.current_label.pack(anchor="w")

    def set_step(self, step_index: int, message: str = None):
        """Set current step and update display."""
        # Update progress bar
        self.progress_var.set(step_index)

        # Update current label
        self.current_label.config(text=message or self.STEPS[step_index])

    def reset(self):
        """Reset progress display."""
        self.progress_var.set(0)
        self.current_label.config(text="Ready")
