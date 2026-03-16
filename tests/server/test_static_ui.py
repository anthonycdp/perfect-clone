"""Smoke tests for the wizard static UI contract."""

from fastapi.testclient import TestClient

import server.app as app_module


def test_index_keeps_step_four_and_package_controls():
    """Wizard HTML should expose the controls required by the current backend flow."""
    with TestClient(app_module.app) as client:
        response = client.get("/")

    assert response.status_code == 200
    html = response.text
    assert 'id="query-group"' in html
    assert 'id="step4-subtitle"' in html
    assert 'id="btn-download-package"' in html
    assert 'id="package-expiry"' in html


def test_app_js_uses_task_scoped_result_contract():
    """Wizard JS should consume the backend result URLs instead of removed legacy paths."""
    with TestClient(app_module.app) as client:
        response = client.get("/static/app.js")

    assert response.status_code == 200
    script = response.text
    assert "result.screenshot_url" in script
    assert "result.download_url" in script
    assert "asset.url" in script
    assert "asset.filename" in script
    assert "this.isFullPageMode()" in script
    assert "/screenshots/" not in script


def test_styles_define_global_hidden_utility():
    """The wizard uses .hidden outside steps and tabs, so the utility must exist globally."""
    with TestClient(app_module.app) as client:
        response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert ".hidden {" in response.text
