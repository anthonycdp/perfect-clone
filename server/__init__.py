"""FastAPI web server for Component Extractor."""

from server.task import ExtractionTask

__all__ = ["ExtractionTask"]

def get_app():
    """Lazy import of FastAPI app to avoid circular dependencies."""
    from server.app import app
    return app
