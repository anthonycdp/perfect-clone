"""Exception classes for extraction pipeline."""


class ExtractionError(Exception):
    """Base exception for extraction errors."""

    pass


class NavigationError(ExtractionError):
    """Failed to navigate to URL."""

    pass


class TargetNotFoundError(ExtractionError):
    """Selector did not find any element."""

    def __init__(self, message: str, suggestions: list[str] | None = None):
        super().__init__(message)
        self.suggestions = suggestions or []


class APIError(ExtractionError):
    """Failed to communicate with OpenAI API."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BrowserCrashError(ExtractionError):
    """Browser process crashed or was terminated."""

    pass
