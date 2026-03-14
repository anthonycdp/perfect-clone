"""Component Extractor - Extract web components and generate recreation prompts."""

import os
import tkinter as tk
from dotenv import load_dotenv
from gui.app import ComponentExtractorApp


def main():
    """Start the application."""
    # Load environment variables
    load_dotenv()

    # Create and run the GUI
    root = tk.Tk()
    app = ComponentExtractorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
