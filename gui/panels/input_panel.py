"""Input panel for extraction configuration."""

import tkinter as tk
from tkinter import ttk

from models.extraction import ExtractionMode


class InputPanel:
    """Panel for inputting extraction parameters."""

    def __init__(self, parent, on_extract_callback):
        self.frame = ttk.Frame(parent, padding="10")
        self.on_extract = on_extract_callback
        self.on_cancel = None
        self.strategy_buttons: list[ttk.Radiobutton] = []

        ttk.Label(self.frame, text="URL:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.url_entry = ttk.Entry(self.frame, width=50)
        self.url_entry.pack(fill="x", pady=(0, 15))

        ttk.Label(self.frame, text="Extraction Mode:", font=("Arial", 10, "bold")).pack(
            anchor="w"
        )
        self.mode_var = tk.StringVar(value=ExtractionMode.COMPONENT.value)
        self.mode_var.trace_add("write", self._on_mode_change)

        modes = [
            ("Single Component", ExtractionMode.COMPONENT.value),
            ("Full Landing Page", ExtractionMode.FULL_PAGE.value),
        ]
        for text, value in modes:
            ttk.Radiobutton(
                self.frame,
                text=text,
                variable=self.mode_var,
                value=value,
            ).pack(anchor="w")

        self.strategy_label = ttk.Label(
            self.frame,
            text="Strategy:",
            font=("Arial", 10, "bold"),
        )
        self.strategy_label.pack(anchor="w", pady=(15, 0))

        self.strategy_var = tk.StringVar(value="css")
        strategies = [
            ("CSS Selector", "css"),
            ("XPath", "xpath"),
            ("Text", "text"),
            ("HTML Snippet", "html_snippet"),
        ]

        for text, value in strategies:
            button = ttk.Radiobutton(
                self.frame,
                text=text,
                variable=self.strategy_var,
                value=value,
            )
            button.pack(anchor="w")
            self.strategy_buttons.append(button)

        self.query_label = ttk.Label(
            self.frame,
            text="Selector/Query:",
            font=("Arial", 10, "bold"),
        )
        self.query_label.pack(anchor="w", pady=(15, 0))

        self.selector_text = tk.Text(self.frame, height=4, width=50)
        self.selector_text.pack(fill="x", pady=(0, 5))

        self.hint_var = tk.StringVar(value="")
        self.hint_label = ttk.Label(
            self.frame,
            textvariable=self.hint_var,
            foreground="#666666",
            wraplength=320,
            justify="left",
        )
        self.hint_label.pack(anchor="w", pady=(0, 10))

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

        self._update_mode_controls()

    def _on_extract_click(self):
        """Handle extract button click."""
        url = self.url_entry.get().strip()
        extraction_mode = self.mode_var.get()
        strategy = self.strategy_var.get()
        query = self.selector_text.get("1.0", "end-1c").strip()

        if not url:
            return

        if extraction_mode == ExtractionMode.COMPONENT.value and not query:
            return

        self.set_extracting_state(True)

        if self.on_extract:
            self.on_extract(url, extraction_mode, strategy, query)

    def _on_cancel_click(self):
        """Handle cancel button click."""
        if self.on_cancel:
            self.on_cancel()

    def _on_mode_change(self, *_args):
        """Keep the UI aligned with the selected extraction mode."""
        self._update_mode_controls()

    def _update_mode_controls(self):
        """Toggle strategy and selector controls based on extraction mode."""
        is_component_mode = self.mode_var.get() == ExtractionMode.COMPONENT.value
        strategy_state = "normal" if is_component_mode else "disabled"
        query_state = "normal" if is_component_mode else "disabled"

        for button in self.strategy_buttons:
            button.config(state=strategy_state)

        self.strategy_label.config(
            text="Strategy:" if is_component_mode else "Strategy: not required"
        )
        self.query_label.config(
            text="Selector/Query:" if is_component_mode else "Selector/Query: not required"
        )

        self.selector_text.config(state="normal")
        if not is_component_mode:
            self.selector_text.delete("1.0", "end")
        self.selector_text.config(state=query_state)

        self.extract_btn.config(
            text="Extract Component" if is_component_mode else "Extract Landing Page"
        )
        self.hint_var.set(
            ""
            if is_component_mode
            else "Full-page mode captures the current route with automated scroll and ignores selector/query."
        )

    def set_extracting_state(self, extracting: bool):
        """Set button states based on extraction state."""
        if extracting:
            self.extract_btn.config(state="disabled")
            self.cancel_btn.config(state="normal")
        else:
            self.extract_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")

    def get_values(self) -> tuple[str, str, str, str]:
        """Get current input values."""
        query = self.selector_text.get("1.0", "end-1c").strip()
        return (
            self.url_entry.get().strip(),
            self.mode_var.get(),
            self.strategy_var.get(),
            query,
        )
