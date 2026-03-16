# Web UI Migration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Tkinter GUI with a modern web interface using FastAPI + SSE

**Architecture:** FastAPI backend serves static HTML/CSS/JS frontend. Server-Sent Events provide real-time progress updates. Orchestrator and all collector modules migrate from sync to async Playwright API.

**Tech Stack:** FastAPI, Uvicorn, SSE, HTML/CSS/JS, Playwright async_api

---

## File Structure

```
component-extractor/
├── main.py                    # MODIFIED: FastAPI entry point
├── server/                    # NEW
│   ├── __init__.py            # NEW
│   ├── app.py                 # NEW: FastAPI app, routes, SSE
│   └── static/                # NEW
│       ├── index.html         # NEW
│       ├── styles.css         # NEW
│       └── app.js             # NEW
├── models/
│   └── requests.py            # NEW: API request/response models
├── orchestrator.py            # MODIFIED: async version
├── collector/                 # MODIFIED: all modules to async
│   ├── browser.py             # MODIFIED
│   ├── target_finder.py       # MODIFIED
│   ├── dom_extractor.py       # MODIFIED
│   ├── style_extractor.py     # MODIFIED
│   ├── interaction_mapper.py  # MODIFIED
│   ├── interaction_player.py  # MODIFIED
│   ├── animation_recorder.py  # MODIFIED
│   ├── asset_downloader.py    # MODIFIED
│   ├── library_detector.py    # MODIFIED
│   ├── responsive_collector.py # MODIFIED
│   ├── rich_media_collector.py # MODIFIED
│   └── extraction_scope.py    # MODIFIED
├── gui/                       # DELETE after migration
│   └── ...
└── worker.py                  # DELETE after migration
```

---

## Chunk 1: Backend Foundation

### Task 1.1: Add Dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add FastAPI and Uvicorn to requirements.txt**

```txt
playwright>=1.40.0
pydantic>=2.0.0
openai>=1.0.0
python-dotenv>=1.0.0
Pillow>=10.0.0
opencv-python>=4.8.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
fastapi>=0.100.0
uvicorn>=0.23.0
httpx>=0.24.0
aiohttp>=3.8.0
```

- [ ] **Step 2: Install new dependencies**

Run: `pip install fastapi uvicorn httpx aiohttp`
Expected: Packages installed successfully

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add FastAPI and async HTTP dependencies"
```

---

### Task 1.2: Create API Request/Response Models

**Files:**
- Create: `models/requests.py`

- [ ] **Step 1: Create request models file**

```python
"""API request and response models."""

from typing import Any, Literal, Optional

from pydantic import BaseModel


class ExtractionRequest(BaseModel):
    """Request to start an extraction."""

    url: str
    mode: Literal["component", "full_page"] = "component"
    strategy: Literal["css", "xpath", "text", "html_snippet"] = "text"
    query: str = ""


class ExtractionResponse(BaseModel):
    """Response after starting an extraction."""

    task_id: str


class ProgressEvent(BaseModel):
    """Progress event sent via SSE."""

    step: int
    step_name: str
    message: str
    total_steps: int = 12
    done: bool = False


class ResultResponse(BaseModel):
    """Final extraction result."""

    prompt: str
    component_tree: dict[str, Any]
    interactions: list[dict[str, Any]]
    responsive_rules: list[dict[str, Any]]
    dependencies: list[dict[str, Any]]
    screenshot_path: Optional[str] = None
    assets: list[dict[str, Any]]
    full_json: dict[str, Any]


class CancelResponse(BaseModel):
    """Response after cancelling an extraction."""

    cancelled: bool
```

- [ ] **Step 2: Commit**

```bash
git add models/requests.py
git commit -m "feat: add API request/response models"
```

---

### Task 1.3: Create ExtractionTask Class

**Files:**
- Create: `server/__init__.py`
- Create: `server/task.py`

- [ ] **Step 1: Create server package init**

```python
"""FastAPI web server for Component Extractor."""

from server.task import ExtractionTask

__all__ = ["ExtractionTask"]
```

- [ ] **Step 2: Create ExtractionTask class**

```python
"""Task management for extraction operations."""

import asyncio
from typing import Callable

from models.errors import ExtractionError
from models.requests import ExtractionRequest, ProgressEvent


class ExtractionTask:
    """Manages state for a single extraction operation."""

    def __init__(self, task_id: str, request: ExtractionRequest):
        self.id = task_id
        self.request = request
        self.progress_queue: asyncio.Queue = asyncio.Queue()
        self.result = None
        self.completed = False
        self.cancelled = False
        self.error: str | None = None

    async def progress_generator(self):
        """Yield progress events for SSE stream."""
        while True:
            progress_json = await self.progress_queue.get()
            yield progress_json
            if '"done": true' in progress_json or '"done":true' in progress_json:
                break

    async def emit_progress(
        self,
        step: int,
        step_name: str,
        message: str,
        done: bool = False,
    ):
        """Put a progress event into the queue."""
        event = ProgressEvent(
            step=step,
            step_name=step_name,
            message=message,
            done=done,
        )
        await self.progress_queue.put(event.model_dump_json())

    def check_cancelled(self) -> bool:
        """Return True if extraction was cancelled."""
        return self.cancelled

    def cancel(self):
        """Mark the task as cancelled."""
        self.cancelled = True
```

- [ ] **Step 3: Write test for ExtractionTask**

Create: `tests/server/test_task.py`

```python
"""Tests for ExtractionTask."""

import asyncio
import pytest

from models.requests import ExtractionRequest
from server.task import ExtractionTask


@pytest.mark.asyncio
async def test_emit_progress():
    """Test that progress events are emitted correctly."""
    request = ExtractionRequest(url="https://example.com")
    task = ExtractionTask("test-id", request)

    await task.emit_progress(1, "navigating", "Connecting...")

    progress_json = await task.progress_queue.get()
    assert '"step": 1' in progress_json
    assert "navigating" in progress_json


@pytest.mark.asyncio
async def test_progress_generator_yields_events():
    """Test that progress_generator yields all events until done."""
    request = ExtractionRequest(url="https://example.com")
    task = ExtractionTask("test-id", request)

    await task.emit_progress(1, "step1", "First", done=False)
    await task.emit_progress(2, "step2", "Done", done=True)

    events = []
    async for event in task.progress_generator():
        events.append(event)

    assert len(events) == 2
    assert "done" in events[1]


def test_check_cancelled():
    """Test cancellation check."""
    request = ExtractionRequest(url="https://example.com")
    task = ExtractionTask("test-id", request)

    assert task.check_cancelled() is False

    task.cancel()
    assert task.check_cancelled() is True
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/server/test_task.py -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add server/ tests/server/
git commit -m "feat: add ExtractionTask for async extraction management"
```

---

### Task 1.4: Create FastAPI Application

**Files:**
- Modify: `server/__init__.py`
- Create: `server/app.py`

- [ ] **Step 1: Create FastAPI app with routes**

```python
"""FastAPI application for Component Extractor web UI."""

import asyncio
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from models.requests import (
    CancelResponse,
    ExtractionRequest,
    ExtractionResponse,
)
from server.task import ExtractionTask

app = FastAPI(title="Component Extractor")

# In-memory task storage (sufficient for single-user local use)
tasks: dict[str, ExtractionTask] = {}

# Directory paths
STATIC_DIR = Path(__file__).parent / "static"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


@app.get("/")
async def index():
    """Serve the main HTML page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/static/{file_path:path}")
async def static_files(file_path: str):
    """Serve static files (CSS, JS)."""
    return FileResponse(STATIC_DIR / file_path)


@app.get("/screenshots/{file_path:path}")
async def serve_screenshot(file_path: str):
    """Serve screenshot files from output directory."""
    screenshot_path = OUTPUT_DIR / "screenshots" / file_path
    if not screenshot_path.exists():
        raise HTTPException(404, "Screenshot not found")
    return FileResponse(screenshot_path)


@app.post("/api/extract", response_model=ExtractionResponse)
async def start_extraction(request: ExtractionRequest):
    """Start a new extraction task."""
    task_id = str(uuid.uuid4())[:8]
    task = ExtractionTask(task_id, request)
    tasks[task_id] = task

    # Import orchestrator here to avoid circular imports
    from server.runner import run_extraction

    asyncio.create_task(run_extraction(task))
    return ExtractionResponse(task_id=task_id)


@app.get("/api/extract/{task_id}/progress")
async def get_progress(task_id: str):
    """Get SSE stream of extraction progress."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    return StreamingResponse(
        task.progress_generator(),
        media_type="text/event-stream",
    )


@app.get("/api/extract/{task_id}/result")
async def get_result(task_id: str):
    """Get the final extraction result."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if not task.completed:
        raise HTTPException(400, "Extraction not completed")
    if task.error:
        raise HTTPException(500, task.error)
    return task.result


@app.post("/api/extract/{task_id}/cancel", response_model=CancelResponse)
async def cancel_extraction(task_id: str):
    """Cancel an in-progress extraction."""
    task = tasks.get(task_id)
    if task:
        task.cancel()
    return CancelResponse(cancelled=True)
```

- [ ] **Step 2: Create extraction runner**

Create: `server/runner.py`

```python
"""Extraction runner for async pipeline execution."""

import os

from models.errors import ExtractionError
from server.task import ExtractionTask


async def run_extraction(task: ExtractionTask):
    """Execute the extraction pipeline for a task."""
    try:
        # Lazy import to avoid circular dependencies
        from orchestrator import ExtractionOrchestrator

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            await task.emit_progress(
                0, "error", "OPENAI_API_KEY not configured", done=True
            )
            return

        async def progress_callback(step: int, step_name: str, message: str):
            await task.emit_progress(step, step_name, message)

        orchestrator = ExtractionOrchestrator(
            api_key=api_key,
            progress_callback=progress_callback,
            cancel_check=task.check_cancelled,
        )

        synthesis = await orchestrator.extract(
            url=task.request.url,
            mode=task.request.mode,
            strategy=task.request.strategy,
            query=task.request.query,
        )

        normalized = orchestrator.last_normalized_output

        task.result = {
            "prompt": synthesis.recreation_prompt,
            "component_tree": synthesis.component_tree.model_dump(),
            "interactions": [i.model_dump() for i in synthesis.interactions],
            "responsive_rules": [r.model_dump() for r in synthesis.responsive_rules],
            "dependencies": [d.model_dump() for d in synthesis.dependencies],
            "screenshot_path": normalized.get_primary_screenshot_path() if normalized else None,
            "assets": [a.model_dump() for a in normalized.assets] if normalized else [],
            "full_json": normalized.model_dump(mode="json") if normalized else {},
        }
        task.completed = True
        await task.emit_progress(12, "complete", "Extraction complete!", done=True)

    except ExtractionError as e:
        task.error = str(e)
        await task.emit_progress(0, "error", str(e), done=True)
    except Exception as e:
        task.error = str(e)
        await task.emit_progress(0, "error", f"Unexpected error: {e}", done=True)
```

- [ ] **Step 3: Update server package init**

```python
"""FastAPI web server for Component Extractor."""

from server.app import app
from server.task import ExtractionTask

__all__ = ["app", "ExtractionTask"]
```

- [ ] **Step 4: Commit**

```bash
git add server/
git commit -m "feat: add FastAPI app with extraction routes"
```

---

## Chunk 2: Frontend

### Task 2.1: Create HTML Template

**Files:**
- Create: `server/static/index.html`

- [ ] **Step 1: Create index.html**

```html
<!DOCTYPE html>
<html lang="pt-BR" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Component Extractor</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <header>
        <h1>Component Extractor</h1>
        <button id="theme-toggle" title="Toggle theme">◐</button>
    </header>

    <main>
        <section class="input-panel">
            <div class="form-group">
                <label for="url">URL</label>
                <input type="url" id="url" placeholder="https://example.com" required>
            </div>

            <div class="form-group">
                <label>Mode</label>
                <div class="radio-group">
                    <label><input type="radio" name="mode" value="component" checked> Component</label>
                    <label><input type="radio" name="mode" value="full_page"> Landing Page</label>
                </div>
            </div>

            <div class="form-group">
                <label>Strategy</label>
                <div class="radio-group">
                    <label><input type="radio" name="strategy" value="css"> CSS</label>
                    <label><input type="radio" name="strategy" value="xpath"> XPath</label>
                    <label><input type="radio" name="strategy" value="text" checked> Text</label>
                    <label><input type="radio" name="strategy" value="html_snippet"> HTML</label>
                </div>
            </div>

            <div class="form-group">
                <label for="query">Selector / Query</label>
                <textarea id="query" rows="3" placeholder="Text to search..."></textarea>
            </div>

            <div class="progress-container hidden">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <p class="progress-text">Preparing...</p>
            </div>

            <button id="extract-btn" class="btn-primary">Extract</button>
        </section>

        <section class="result-panel hidden">
            <div class="tabs">
                <button class="tab active" data-tab="prompt">Prompt</button>
                <button class="tab" data-tab="json">JSON</button>
                <button class="tab" data-tab="assets">Assets</button>
            </div>

            <div class="tab-content active" data-content="prompt">
                <div class="screenshot-preview hidden">
                    <img id="screenshot-img" src="" alt="Screenshot">
                </div>
                <div class="prompt-container">
                    <pre id="prompt-text"></pre>
                    <button class="btn-copy" data-copy="prompt-text">Copy</button>
                </div>
            </div>

            <div class="tab-content" data-content="json">
                <pre id="json-text"></pre>
            </div>

            <div class="tab-content" data-content="assets">
                <ul id="assets-list"></ul>
            </div>
        </section>
    </main>

    <footer class="status-bar">
        <span id="status">Ready</span>
    </footer>

    <div id="toast-container"></div>

    <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add server/static/index.html
git commit -m "feat: add HTML template for web UI"
```

---

### Task 2.2: Create CSS Styles

**Files:**
- Create: `server/static/styles.css`

- [ ] **Step 1: Create styles.css**

```css
/* Theme Variables */
:root {
    --bg-primary: #1a1a2e;
    --bg-secondary: #16213e;
    --bg-tertiary: #0f3460;
    --text-primary: #eaeaea;
    --text-secondary: #a0a0a0;
    --accent: #e94560;
    --accent-hover: #ff6b6b;
    --border: #2a2a4a;
    --success: #4ade80;
    --error: #f87171;
}

[data-theme="light"] {
    --bg-primary: #f8f9fa;
    --bg-secondary: #ffffff;
    --bg-tertiary: #e9ecef;
    --text-primary: #212529;
    --text-secondary: #6c757d;
    --border: #dee2e6;
}

/* Reset */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    transition: background 0.3s, color 0.3s;
}

/* Header */
header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
}

header h1 {
    font-size: 1.25rem;
    font-weight: 600;
}

#theme-toggle {
    background: none;
    border: none;
    font-size: 1.25rem;
    cursor: pointer;
    color: var(--text-primary);
    padding: 0.5rem;
    border-radius: 4px;
    transition: background 0.2s;
}

#theme-toggle:hover {
    background: var(--bg-tertiary);
}

/* Main Layout */
main {
    display: grid;
    grid-template-columns: 350px 1fr;
    gap: 1rem;
    padding: 1rem 2rem;
    height: calc(100vh - 120px);
}

/* Input Panel */
.input-panel {
    background: var(--bg-secondary);
    padding: 1.5rem;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    font-size: 0.875rem;
}

input[type="url"],
textarea {
    width: 100%;
    padding: 0.75rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text-primary);
    font-size: 0.875rem;
    transition: border-color 0.2s;
}

input:focus,
textarea:focus {
    outline: none;
    border-color: var(--accent);
}

textarea {
    resize: vertical;
    font-family: inherit;
}

.radio-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
}

.radio-group label {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.875rem;
    cursor: pointer;
}

/* Progress */
.progress-container {
    margin-top: 0.5rem;
}

.progress-bar {
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    width: 0%;
    background: var(--accent);
    transition: width 0.3s ease;
}

.progress-text {
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: var(--text-secondary);
}

/* Buttons */
.btn-primary {
    padding: 0.75rem 1.5rem;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 500;
    transition: background 0.2s, opacity 0.2s;
}

.btn-primary:hover {
    background: var(--accent-hover);
}

.btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-copy {
    padding: 0.5rem 1rem;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    border: 1px solid var(--border);
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
    transition: background 0.2s;
}

.btn-copy:hover {
    background: var(--accent);
    color: white;
}

/* Result Panel */
.result-panel {
    background: var(--bg-secondary);
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.tabs {
    display: flex;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border);
}

.tab {
    padding: 0.75rem 1.5rem;
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 0.875rem;
    transition: color 0.2s, background 0.2s;
}

.tab:hover {
    color: var(--text-primary);
}

.tab.active {
    color: var(--accent);
    background: var(--bg-secondary);
}

.tab-content {
    display: none;
    padding: 1rem;
    overflow: auto;
    flex: 1;
}

.tab-content.active {
    display: block;
}

/* Screenshot Preview */
.screenshot-preview {
    margin-bottom: 1rem;
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid var(--border);
}

.screenshot-preview img {
    width: 100%;
    max-height: 300px;
    object-fit: contain;
    display: block;
}

/* Prompt Container */
.prompt-container {
    position: relative;
}

.prompt-container pre {
    background: var(--bg-tertiary);
    padding: 1rem;
    border-radius: 4px;
    overflow: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 0.875rem;
    line-height: 1.5;
    max-height: 400px;
}

.prompt-container .btn-copy {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
}

/* JSON Tab */
#json-text {
    background: var(--bg-tertiary);
    padding: 1rem;
    border-radius: 4px;
    overflow: auto;
    font-size: 0.75rem;
    white-space: pre;
}

/* Assets Tab */
#assets-list {
    list-style: none;
}

#assets-list li {
    padding: 0.5rem;
    background: var(--bg-tertiary);
    margin-bottom: 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
}

/* Toast */
#toast-container {
    position: fixed;
    bottom: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    z-index: 1000;
}

.toast {
    padding: 1rem 1.5rem;
    border-radius: 4px;
    animation: slideIn 0.3s ease;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    font-size: 0.875rem;
}

.toast.success {
    background: var(--success);
    color: #000;
}

.toast.error {
    background: var(--error);
    color: #fff;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Status Bar */
.status-bar {
    padding: 0.5rem 2rem;
    background: var(--bg-secondary);
    border-top: 1px solid var(--border);
    color: var(--text-secondary);
    font-size: 0.875rem;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
}

/* Utilities */
.hidden {
    display: none !important;
}
```

- [ ] **Step 2: Commit**

```bash
git add server/static/styles.css
git commit -m "feat: add CSS styles with dark/light theme support"
```

---

### Task 2.3: Create JavaScript Application

**Files:**
- Create: `server/static/app.js`

- [ ] **Step 1: Create app.js**

```javascript
const App = {
    state: {
        taskId: null,
        isExtracting: false,
        eventSource: null,
    },

    init() {
        this.bindEvents();
        this.loadTheme();
    },

    bindEvents() {
        document.getElementById("extract-btn").addEventListener("click", () => {
            this.startExtraction();
        });

        document.getElementById("theme-toggle").addEventListener("click", () => {
            this.toggleTheme();
        });

        document.querySelectorAll(".tab").forEach((tab) => {
            tab.addEventListener("click", (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        document.querySelectorAll("[data-copy]").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                this.copyToClipboard(e.target.dataset.copy);
            });
        });
    },

    async startExtraction() {
        const url = document.getElementById("url").value.trim();
        const mode = document.querySelector('input[name="mode"]:checked').value;
        const strategy = document.querySelector('input[name="strategy"]:checked').value;
        const query = document.getElementById("query").value.trim();

        if (!url) {
            this.showToast("Please enter a URL", "error");
            return;
        }

        this.setExtractingState(true);
        this.hideResult();

        try {
            const response = await fetch("/api/extract", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url, mode, strategy, query }),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const { task_id } = await response.json();
            this.state.taskId = task_id;
            this.connectProgressStream(task_id);
        } catch (error) {
            this.showToast(`Failed to start extraction: ${error.message}`, "error");
            this.setExtractingState(false);
        }
    },

    connectProgressStream(taskId) {
        this.state.eventSource = new EventSource(`/api/extract/${taskId}/progress`);

        this.state.eventSource.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.updateProgress(data);

            if (data.done) {
                this.state.eventSource.close();

                if (data.step_name === "complete") {
                    this.fetchResult(taskId);
                } else {
                    this.setExtractingState(false);
                    if (data.step_name === "error") {
                        this.showToast(data.message, "error");
                    }
                }
            }
        };

        this.state.eventSource.onerror = () => {
            this.state.eventSource.close();
            this.setExtractingState(false);
            this.showToast("Connection lost", "error");
        };
    },

    updateProgress(data) {
        const container = document.querySelector(".progress-container");
        const fill = document.querySelector(".progress-fill");
        const text = document.querySelector(".progress-text");

        container.classList.remove("hidden");
        fill.style.width = `${(data.step / data.total_steps) * 100}%`;
        text.textContent = data.message;
        this.setStatus(data.message);
    },

    async fetchResult(taskId) {
        try {
            const response = await fetch(`/api/extract/${taskId}/result`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const result = await response.json();
            this.showResult(result);
            this.setExtractingState(false);
            this.showToast("Extraction complete!", "success");
        } catch (error) {
            this.showToast(`Failed to get result: ${error.message}`, "error");
            this.setExtractingState(false);
        }
    },

    showResult(result) {
        const panel = document.querySelector(".result-panel");
        panel.classList.remove("hidden");

        // Prompt
        document.getElementById("prompt-text").textContent = result.prompt || "";

        // Screenshot
        const screenshotDiv = document.querySelector(".screenshot-preview");
        const screenshotImg = document.getElementById("screenshot-img");

        if (result.screenshot_path) {
            screenshotImg.src = `/screenshots/${result.screenshot_path}`;
            screenshotDiv.classList.remove("hidden");
        } else {
            screenshotDiv.classList.add("hidden");
        }

        // JSON
        document.getElementById("json-text").textContent = JSON.stringify(
            result.full_json,
            null,
            2
        );

        // Assets
        const assetsList = document.getElementById("assets-list");
        if (result.assets && result.assets.length > 0) {
            assetsList.innerHTML = result.assets
                .map((a) => `<li>${a.type}: ${a.local_path}</li>`)
                .join("");
        } else {
            assetsList.innerHTML = "<li>No assets extracted</li>";
        }

        this.switchTab("prompt");
    },

    hideResult() {
        document.querySelector(".result-panel").classList.add("hidden");
    },

    setExtractingState(extracting) {
        this.state.isExtracting = extracting;
        const btn = document.getElementById("extract-btn");
        btn.disabled = extracting;
        btn.textContent = extracting ? "Extracting..." : "Extract";

        if (!extracting) {
            document.querySelector(".progress-container").classList.add("hidden");
        }
    },

    switchTab(tabName) {
        document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach((c) =>
            c.classList.remove("active")
        );

        document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add("active");
        document
            .querySelector(`.tab-content[data-content="${tabName}"]`)
            .classList.add("active");
    },

    async copyToClipboard(elementId) {
        const text = document.getElementById(elementId).textContent;
        try {
            await navigator.clipboard.writeText(text);
            this.showToast("Copied!", "success");
        } catch {
            this.showToast("Failed to copy", "error");
        }
    },

    showToast(message, type = "success") {
        const container = document.getElementById("toast-container");
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = "slideIn 0.3s ease reverse";
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    setStatus(message) {
        document.getElementById("status").textContent = message;
    },

    toggleTheme() {
        const html = document.documentElement;
        const current = html.dataset.theme;
        const next = current === "dark" ? "light" : "dark";
        html.dataset.theme = next;
        localStorage.setItem("theme", next);
    },

    loadTheme() {
        const saved = localStorage.getItem("theme") || "dark";
        document.documentElement.dataset.theme = saved;
    },
};

document.addEventListener("DOMContentLoaded", () => App.init());
```

- [ ] **Step 2: Commit**

```bash
git add server/static/app.js
git commit -m "feat: add JavaScript frontend application"
```

---

## Chunk 3: Orchestrator Async Migration

### Task 3.1: Migrate BrowserManager to Async

**Files:**
- Modify: `collector/browser.py`

- [ ] **Step 1: Update imports and convert to async**

```python
"""Browser lifecycle management using Playwright async API."""

from typing import Optional

from playwright.async_api import Browser, Page, Playwright, async_playwright

from models.errors import NavigationError


class BrowserManager:
    """Manages Playwright browser lifecycle."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def start(self) -> None:
        """Initialize browser and page."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()

    async def navigate(self, url: str, timeout: int = 30000) -> None:
        """Navigate to URL and wait for page load."""
        if not self.page:
            await self.start()

        try:
            await self.page.goto(url, timeout=timeout, wait_until="networkidle")
        except Exception as e:
            raise NavigationError(f"Failed to navigate to {url}: {str(e)}")

    async def resize_viewport(self, width: int, height: int) -> None:
        """Resize browser viewport."""
        if self.page:
            await self.page.set_viewport_size({"width": width, "height": height})

    async def close(self) -> None:
        """Release all browser resources."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        self.page = None
        self.browser = None
        self.playwright = None

    async def __aenter__(self) -> "BrowserManager":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
```

- [ ] **Step 2: Update test for async browser**

Modify: `tests/collector/test_browser.py`

```python
"""Tests for BrowserManager async API."""

import pytest

from collector.browser import BrowserManager


@pytest.mark.asyncio
async def test_browser_start_and_close():
    """Test that browser starts and closes properly."""
    browser = BrowserManager(headless=True)
    await browser.start()

    assert browser.playwright is not None
    assert browser.browser is not None
    assert browser.page is not None

    await browser.close()

    assert browser.playwright is None
    assert browser.browser is None
    assert browser.page is None


@pytest.mark.asyncio
async def test_browser_context_manager():
    """Test async context manager usage."""
    async with BrowserManager(headless=True) as browser:
        assert browser.page is not None


@pytest.mark.asyncio
async def test_navigate_to_url():
    """Test navigation to a URL."""
    async with BrowserManager(headless=True) as browser:
        await browser.navigate("https://example.com")
        assert "example.com" in browser.page.url
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/collector/test_browser.py -v`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add collector/browser.py tests/collector/test_browser.py
git commit -m "refactor: migrate BrowserManager to async API"
```

---

### Task 3.2: Migrate Orchestrator to Async

**Files:**
- Modify: `orchestrator.py`

- [ ] **Step 1: Update orchestrator imports**

Change:
```python
from playwright.sync_api import Locator
```

To:
```python
from playwright.async_api import Locator
```

- [ ] **Step 2: Convert extract method to async**

Change method signature:
```python
def extract(
    self,
    url: str,
    strategy: str = "css",
    query: str = "",
    extraction_mode: str = ExtractionMode.COMPONENT.value,
    progress_callback: Callable[[int, str], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> SynthesisOutput:
```

To:
```python
async def extract(
    self,
    url: str,
    strategy: str = "css",
    query: str = "",
    mode: str = "component",
    progress_callback: Callable[[int, str, str], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> SynthesisOutput:
```

- [ ] **Step 3: Add await to all async calls**

Add `await` to:
- `self.browser.start()`
- `self.browser.navigate(url)`
- `self.browser.close()`
- All collector method calls
- All page method calls (`page.evaluate`, `page.wait_for_timeout`, etc.)

- [ ] **Step 4: Update progress callback signature**

Change from `(step, message)` to `(step, step_name, message)`:

```python
async def _report_progress(
    self,
    callback: Callable[[int, str, str], None] | None,
    step: int,
    mode: ExtractionMode,
):
    """Report progress if a callback was provided."""
    if not callback:
        return

    message = self.PROGRESS_STEPS[step]
    if isinstance(message, dict):
        message = message[mode]
    step_name = message.lower().replace(" ", "_")
    callback(step, step_name, message)
```

- [ ] **Step 5: Commit**

```bash
git add orchestrator.py
git commit -m "refactor: migrate orchestrator extract to async API"
```

---

## Chunk 4: Collector Async Migration

### Task 4.1: Migrate TargetFinder to Async

**Files:**
- Modify: `collector/target_finder.py`

- [ ] **Step 1: Update imports**

Change:
```python
from playwright.sync_api import Frame, Locator, Page
```

To:
```python
from playwright.async_api import Frame, Locator, Page
```

- [ ] **Step 2: Convert find method to async**

```python
async def find(self, strategy: SelectorStrategy, query: str) -> ExtractionScope:
```

- [ ] **Step 3: Add await to all page/locator calls**

- All `locator.count()` → `await locator.count()`
- All `frame.evaluate()` → `await frame.evaluate()`
- All `locator.evaluate()` → `await locator.evaluate()`

- [ ] **Step 4: Update test**

Modify: `tests/collector/test_target_finder.py`

- [ ] **Step 5: Commit**

```bash
git add collector/target_finder.py tests/collector/test_target_finder.py
git commit -m "refactor: migrate TargetFinder to async API"
```

---

### Task 4.2: Migrate Remaining Collectors

Apply the same pattern to each collector module:

**Files to modify:**
- `collector/dom_extractor.py`
- `collector/style_extractor.py`
- `collector/interaction_mapper.py`
- `collector/interaction_player.py`
- `collector/animation_recorder.py`
- `collector/asset_downloader.py`
- `collector/library_detector.py`
- `collector/responsive_collector.py`
- `collector/rich_media_collector.py`
- `collector/extraction_scope.py`

**Pattern for each:**

- [ ] **Step 1: Update imports**
```python
from playwright.sync_api import ...  # remove
from playwright.async_api import ...  # add
```

- [ ] **Step 2: Add async to methods**
```python
async def method_name(self, ...):
```

- [ ] **Step 3: Add await to Playwright calls**
```python
result = await self.page.evaluate(...)
element = await locator.something()
```

- [ ] **Step 4: Update corresponding tests**

- [ ] **Step 5: Commit each module**
```bash
git add collector/<module>.py tests/collector/test_<module>.py
git commit -m "refactor: migrate <module> to async API"
```

---

### Task 4.3: Update Collector __init__.py

**Files:**
- Modify: `collector/__init__.py`

- [ ] **Step 1: Ensure all exports work with async**

```python
"""Collector module for web scraping and extraction."""

from collector.animation_recorder import AnimationRecorder
from collector.asset_downloader import AssetDownloader
from collector.browser import BrowserManager
from collector.dom_extractor import DOMExtractor
from collector.extraction_scope import ExtractionScope
from collector.interaction_mapper import InteractionMapper
from collector.interaction_player import InteractionPlayer
from collector.library_detector import LibraryDetector
from collector.responsive_collector import ResponsiveCollector
from collector.rich_media_collector import RichMediaCollector
from collector.style_extractor import StyleExtractor
from collector.target_finder import TargetFinder

__all__ = [
    "AnimationRecorder",
    "AssetDownloader",
    "BrowserManager",
    "DOMExtractor",
    "ExtractionScope",
    "InteractionMapper",
    "InteractionPlayer",
    "LibraryDetector",
    "ResponsiveCollector",
    "RichMediaCollector",
    "StyleExtractor",
    "TargetFinder",
]
```

- [ ] **Step 2: Commit**

```bash
git add collector/__init__.py
git commit -m "refactor: update collector exports for async API"
```

---

## Chunk 5: Entry Point and Cleanup

### Task 5.1: Update main.py

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Replace Tkinter entry point with FastAPI**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add main.py
git commit -m "feat: replace Tkinter entry point with FastAPI"
```

---

### Task 5.2: Remove Old GUI Files

**Files:**
- Delete: `gui/app.py`
- Delete: `gui/panels/input_panel.py`
- Delete: `gui/panels/result_panel.py`
- Delete: `gui/widgets/progress_display.py`
- Delete: `gui/__init__.py`
- Delete: `gui/panels/__init__.py`
- Delete: `gui/widgets/__init__.py`
- Delete: `worker.py`
- Delete: `tests/gui/` (directory)

- [ ] **Step 1: Remove GUI directory**

```bash
rm -rf gui/
rm -rf tests/gui/
rm worker.py
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "chore: remove Tkinter GUI and threading worker"
```

---

### Task 5.3: Final Integration Test

- [ ] **Step 1: Start the application**

Run: `python main.py`
Expected: Server starts, browser opens automatically

- [ ] **Step 2: Test extraction**

1. Enter URL: `https://example.com`
2. Select mode: Component
3. Select strategy: Text
4. Enter query: `Example Domain`
5. Click Extract
6. Verify progress updates appear
7. Verify result appears with prompt
8. Test Copy button
9. Test theme toggle
10. Test tab switching

- [ ] **Step 3: Run all tests**

Run: `pytest -v`
Expected: All tests pass

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete Web UI migration"
```

---

## Summary

| Chunk | Description | Key Files |
|-------|-------------|-----------|
| 1 | Backend Foundation | `models/requests.py`, `server/app.py`, `server/task.py` |
| 2 | Frontend | `server/static/index.html`, `styles.css`, `app.js` |
| 3 | Orchestrator Async | `orchestrator.py`, `collector/browser.py` |
| 4 | Collectors Async | All `collector/*.py` files |
| 5 | Entry Point & Cleanup | `main.py`, remove `gui/`, `worker.py` |

**Total Tasks:** 14
**Estimated Steps:** ~50
