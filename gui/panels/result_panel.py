"""Result panel for displaying extraction results."""

import tkinter as tk
from tkinter import ttk, messagebox
import json


class ResultPanel:
    """Panel for displaying extraction results."""

    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding="10")

        # Notebook with tabs
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill="both", expand=True)

        # Prompt Tab
        self.prompt_tab = ttk.Frame(self.notebook)
        self._setup_prompt_tab()
        self.notebook.add(self.prompt_tab, text="Final Prompt")

        # JSON Tab
        self.json_tab = ttk.Frame(self.notebook)
        self._setup_json_tab()
        self.notebook.add(self.json_tab, text="Full JSON")

        # Assets Tab
        self.assets_tab = ttk.Frame(self.notebook)
        self._setup_assets_tab()
        self.notebook.add(self.assets_tab, text="Assets")

    def _setup_prompt_tab(self):
        """Setup prompt display tab."""
        # Text area for prompt
        self.prompt_text = tk.Text(self.prompt_tab, wrap="word", height=20)
        self.prompt_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.prompt_tab, command=self.prompt_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.prompt_text.config(yscrollcommand=scrollbar.set)

        # Copy button
        self.copy_btn = ttk.Button(
            self.prompt_tab,
            text="Copy Prompt",
            command=self._copy_prompt,
        )
        self.copy_btn.pack(pady=5)

    def _setup_json_tab(self):
        """Setup JSON display tab."""
        self.json_text = tk.Text(self.json_tab, wrap="none")
        self.json_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbars
        y_scroll = ttk.Scrollbar(self.json_tab, command=self.json_text.yview)
        y_scroll.pack(side="right", fill="y")
        x_scroll = ttk.Scrollbar(
            self.json_tab, orient="horizontal", command=self.json_text.xview
        )
        x_scroll.pack(side="bottom", fill="x")
        self.json_text.config(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    def _setup_assets_tab(self):
        """Setup assets display tab."""
        # Treeview for assets
        columns = ("type", "path", "size")
        self.assets_tree = ttk.Treeview(self.assets_tab, columns=columns, show="headings")

        self.assets_tree.heading("type", text="Type")
        self.assets_tree.heading("path", text="Path")
        self.assets_tree.heading("size", text="Size")

        self.assets_tree.column("type", width=80)
        self.assets_tree.column("path", width=400)
        self.assets_tree.column("size", width=100)

        self.assets_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def display_result(self, result):
        """Display extraction result."""
        # Display prompt
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", result.recreation_prompt)

        # Display JSON
        self.json_text.delete("1.0", "end")
        json_str = json.dumps(result.model_dump(), indent=2, ensure_ascii=False)
        self.json_text.insert("1.0", json_str)

    def display_assets(self, assets: list):
        """Display assets in treeview."""
        # Clear existing
        for item in self.assets_tree.get_children():
            self.assets_tree.delete(item)

        # Add assets
        for asset in assets:
            size_kb = asset.get("file_size_bytes", 0) / 1024
            self.assets_tree.insert(
                "",
                "end",
                values=(
                    asset.get("type", "unknown"),
                    asset.get("local_path", ""),
                    f"{size_kb:.1f} KB",
                ),
            )

    def _copy_prompt(self):
        """Copy prompt to clipboard."""
        prompt = self.prompt_text.get("1.0", "end-1c")
        self.prompt_text.clipboard_clear()
        self.prompt_text.clipboard_append(prompt)
        messagebox.showinfo("Copied", "Prompt copied to clipboard!")

    def clear(self):
        """Clear all results."""
        self.prompt_text.delete("1.0", "end")
        self.json_text.delete("1.0", "end")
        for item in self.assets_tree.get_children():
            self.assets_tree.delete(item)
