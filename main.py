"""Component Extractor - Web UI Entry Point."""

import threading
import webbrowser

import uvicorn
from dotenv import load_dotenv

from server.app import app


def main():
    """Start the application."""
    load_dotenv()

    host = "127.0.0.1"
    port = 8000

    # Open browser after short delay (let server start first)
    threading.Timer(
        1.0,
        lambda: webbrowser.open(f"http://{host}:{port}"),
    ).start()

    print(f"Starting Component Extractor at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
