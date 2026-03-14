"""Input panel for extraction configuration."""

import tkinter as tk
from tkinter import ttk


class InputPanel:
    """Panel for inputting extraction parameters."""

    def __init__(self, parent, on_extract_callback):
        self.frame = ttk.Frame(parent, padding="10")
        self.on_extract = on_extract_callback
        self.on_cancel = None

        # URL Input
        ttk.Label(self.frame, text="URL:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.url_entry = ttk.Entry(self.frame, width=50)
        self.url_entry.pack(fill="x", pady=(0, 15))

        # Strategy Selection
        ttk.Label(
            self.frame, text="Strategy:", font=("Arial", 10, "bold")
        ).pack(anchor="w")

        self.strategy_var = tk.StringVar(value="css")
        strategies = [
            ("CSS Selector", "css"),
            ("XPath", "xpath"),
            ("Text", "text"),
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
            self.frame, text="Selector/Query:", font=("Arial", 10, "bold")
        ).pack(anchor="w", pady=(15, 0))
        self.selector_text = tk.Text(self.frame, height=4, width=50)
        self.selector_text.pack(fill="x", pady=(0, 15))

        # Buttons Frame
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill="x", pady=(10, 0))

        self.extract_btn = ttk.Button(
            button_frame,
            text="Extract Component",
            command=self._on_extract_click,
        )
        self.extract_btn.pack(side="left", padx=(0, 10))

        self.cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
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

        self.set_extracting_state(True)

        if self.on_extract:
            self.on_extract(url, strategy, query)

    def _on_cancel_click(self):
        """Handle cancel button click."""
        if self.on_cancel:
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
