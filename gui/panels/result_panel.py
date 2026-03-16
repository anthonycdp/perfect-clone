"""Result panel for displaying extraction results."""

from pathlib import Path
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json

from PIL import Image, ImageTk


class ResultPanel:
    """Panel for displaying extraction results."""

    def __init__(self, parent):
        self.frame = ttk.Frame(parent, padding="10")
        self.current_screenshot_path: str | None = None
        self.screenshot_preview_image = None
        self.result_summary_var = tk.StringVar(value="No extraction yet")

        summary_label = ttk.Label(
            self.frame,
            textvariable=self.result_summary_var,
            font=("Arial", 10, "bold"),
        )
        summary_label.pack(anchor="w", pady=(0, 8))

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

        # Screenshot Tab
        self.screenshot_tab = ttk.Frame(self.notebook)
        self._setup_screenshot_tab()
        self.notebook.add(self.screenshot_tab, text="Screenshot")

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

    def _setup_screenshot_tab(self):
        """Setup screenshot preview tab."""
        controls = ttk.Frame(self.screenshot_tab)
        controls.pack(fill="x", padx=5, pady=(5, 10))

        self.screenshot_path_var = tk.StringVar(value="No screenshot available")
        self.screenshot_path_label = ttk.Label(
            controls,
            textvariable=self.screenshot_path_var,
        )
        self.screenshot_path_label.pack(side="left", fill="x", expand=True)

        self.save_image_btn = ttk.Button(
            controls,
            text="Save Image",
            command=self._save_screenshot,
            state="disabled",
        )
        self.save_image_btn.pack(side="right")

        preview_frame = ttk.Frame(self.screenshot_tab, padding="5")
        preview_frame.pack(fill="both", expand=True)

        self.screenshot_preview_label = ttk.Label(
            preview_frame,
            text="No screenshot available",
            anchor="center",
            justify="center",
        )
        self.screenshot_preview_label.pack(fill="both", expand=True)

    def display_result(
        self,
        result,
        full_json: dict | None = None,
        screenshot_path: str | None = None,
        result_kind: str = "Component",
    ):
        """Display extraction result."""
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", result.recreation_prompt)

        self.json_text.delete("1.0", "end")
        json_data = full_json if full_json is not None else result.model_dump(mode="json")
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        self.json_text.insert("1.0", json_str)

        self.result_summary_var.set(f"Current result: {result_kind}")
        self.display_screenshot(screenshot_path)

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

    def display_screenshot(self, screenshot_path: str | None):
        """Display a screenshot preview of the extracted element."""
        self.current_screenshot_path = screenshot_path

        if not screenshot_path:
            self._clear_screenshot_preview()
            return

        screenshot_file = Path(screenshot_path)
        if not screenshot_file.exists():
            self._clear_screenshot_preview()
            return

        try:
            with Image.open(screenshot_file) as image:
                preview_image = image.copy()
        except Exception:
            self._clear_screenshot_preview()
            return

        preview_image.thumbnail((720, 460))
        self.screenshot_preview_image = ImageTk.PhotoImage(preview_image)
        self.screenshot_preview_label.config(
            image=self.screenshot_preview_image,
            text="",
        )
        self.screenshot_path_var.set(str(screenshot_file))
        self.save_image_btn.config(state="normal")

    def _clear_screenshot_preview(self):
        """Reset screenshot preview state."""
        self.current_screenshot_path = None
        self.screenshot_preview_image = None
        self.screenshot_preview_label.config(image="", text="No screenshot available")
        self.screenshot_path_var.set("No screenshot available")
        self.save_image_btn.config(state="disabled")

    def _copy_prompt(self):
        """Copy prompt to clipboard."""
        prompt = self.prompt_text.get("1.0", "end-1c")
        self.prompt_text.clipboard_clear()
        self.prompt_text.clipboard_append(prompt)
        messagebox.showinfo("Copied", "Prompt copied to clipboard!")

    def _save_screenshot(self):
        """Save the current screenshot to a user-selected path."""
        if not self.current_screenshot_path:
            messagebox.showerror("Error", "No screenshot available to save.")
            return

        source_path = Path(self.current_screenshot_path)
        if not source_path.exists():
            messagebox.showerror("Error", "Screenshot file no longer exists.")
            return

        destination = filedialog.asksaveasfilename(
            title="Save Screenshot",
            defaultextension=source_path.suffix or ".png",
            initialfile=source_path.name,
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg;*.jpeg"),
                ("All Files", "*.*"),
            ],
        )
        if not destination:
            return

        shutil.copyfile(source_path, destination)
        messagebox.showinfo("Saved", "Screenshot saved successfully!")

    def clear(self):
        """Clear all results."""
        self.prompt_text.delete("1.0", "end")
        self.json_text.delete("1.0", "end")
        for item in self.assets_tree.get_children():
            self.assets_tree.delete(item)
        self.result_summary_var.set("No extraction yet")
        self._clear_screenshot_preview()
