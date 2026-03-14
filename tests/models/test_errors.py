import pytest
from models.errors import (
    ExtractionError,
    NavigationError,
    TargetNotFoundError,
    APIError,
    BrowserCrashError,
)


def test_extraction_error_is_base_exception():
    """ExtractionError should be the base for all extraction exceptions."""
    with pytest.raises(ExtractionError):
        raise NavigationError("Failed to navigate")


def test_navigation_error_message():
    """NavigationError should preserve message."""
    error = NavigationError("URL not reachable")
    assert str(error) == "URL not reachable"
    assert isinstance(error, ExtractionError)


def test_target_not_found_error_with_suggestions():
    """TargetNotFoundError should store suggestions."""
    error = TargetNotFoundError(
        "Selector not found",
        suggestions=[".alternative-1", ".alternative-2"]
    )
    assert error.suggestions == [".alternative-1", ".alternative-2"]
    assert isinstance(error, ExtractionError)


def test_api_error_with_status_code():
    """APIError should store status code."""
    error = APIError("Rate limited", status_code=429)
    assert error.status_code == 429
    assert isinstance(error, ExtractionError)


def test_browser_crash_error():
    """BrowserCrashError should be ExtractionError subclass."""
    error = BrowserCrashError("Browser process died")
    assert isinstance(error, ExtractionError)
