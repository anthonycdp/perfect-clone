# Web UI Migration - Design Document

**Data:** 2026-03-15
**Status:** Rascunho
**Contexto:** Substituir interface Tkinter por interface web moderna

## Visão Geral

Migração da interface GUI Tkinter atual para uma interface web que roda localmente no navegador. O objetivo é modernizar a experiência visual mantendo toda a funcionalidade existente e adicionando melhorias de UX.

### Motivação

- Interface Tkinter visualmente datada
- Desejo por UX mais moderna com feedback visual aprimorado

### Escopo

- Manter paridade total de funcionalidades
- Adicionar: preview de screenshot, toasts, transições, loading states

---

## Stack Tecnológica

| Componente | Tecnologia |
|------------|------------|
| Backend | FastAPI + Uvicorn |
| Tempo real | Server-Sent Events (SSE) |
| Frontend | HTML/CSS/JS puro (sem build) |
| Browser Automation | Playwright async API |
| Concorrência | asyncio (substituindo threading) |

---

## Estrutura do Projeto

```
component-extractor/
├── main.py                    # Ponto de entrada, inicia FastAPI + abre browser
├── server/
│   ├── __init__.py
│   ├── app.py                 # FastAPI app, rotas, SSE
│   └── static/                # Arquivos estáticos
│       ├── index.html         # UI principal
│       ├── styles.css         # Estilos modernos
│       └── app.js             # Lógica frontend
├── collector/                 # (inalterado, adaptado para async)
├── normalizer/                # (inalterado)
├── synthesizer/               # (inalterado)
├── models/                    # (inalterado, + request models)
│   └── requests.py            # Novo: Pydantic models para API
├── orchestrator.py            # Adaptado para async
└── output/
    ├── assets/
    ├── animations/
    └── extractions/
```

---

## Arquitetura

### Fluxo de Comunicação

```
┌──────────┐  POST /api/extract   ┌──────────┐
│  Browser │ ───────────────────► │ FastAPI  │
│   (JS)   │                      │  (async) │
│          │ ◄─────────────────── │          │
│          │   SSE: progress      │          │
│          │ ◄─────────────────── │          │
│          │   JSON: resultado    │          │
└──────────┘                      └──────────┘
```

### Execução

1. `python main.py` → inicia FastAPI em `127.0.0.1:8000`
2. Abre navegador automaticamente (`webbrowser.open`)
3. Usuário preenche URL + modo + estratégia + seletor
4. POST `/api/extract` → retorna `{task_id}`
5. SSE `/api/extract/{task_id}/progress` → envia updates em tempo real
6. GET `/api/extract/{task_id}/result` → resultado final

---

## API Endpoints

### Rotas

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Serve `index.html` |
| `GET` | `/static/{file}` | Serve CSS/JS |
| `POST` | `/api/extract` | Inicia extração, retorna `{task_id}` |
| `GET` | `/api/extract/{task_id}/progress` | SSE stream de progresso |
| `GET` | `/api/extract/{task_id}/result` | Resultado final |
| `POST` | `/api/extract/{task_id}/cancel` | Cancela extração em andamento |
| `GET` | `/screenshots/{filename}` | Serve screenshots salvos |

### Request Models

```python
# models/requests.py
from pydantic import BaseModel
from typing import Optional

class ExtractionRequest(BaseModel):
    url: str
    mode: str  # "component" | "full_page"
    strategy: str  # "css" | "xpath" | "text" | "html_snippet"
    query: str

class ExtractionResponse(BaseModel):
    task_id: str

class ProgressEvent(BaseModel):
    step: int
    step_name: str
    message: str
    total_steps: int = 11
    done: bool = False

class ResultResponse(BaseModel):
    prompt: str
    component_tree: dict
    interactions: list
    responsive_rules: list
    dependencies: list
    screenshot_path: Optional[str]
    assets: list
    full_json: dict
```

### Exemplo de Uso (Frontend)

```javascript
// 1. Iniciar extração
const response = await fetch('/api/extract', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, mode, strategy, query })
});
const { task_id } = await response.json();

// 2. Conectar no SSE para progresso
const eventSource = new EventSource(`/api/extract/${task_id}/progress`);
eventSource.onmessage = (e) => {
    const data = JSON.parse(e.data);
    updateProgress(data.step, data.message);
    if (data.done) {
        eventSource.close();
        fetchResult(task_id);
    }
};

// 3. Buscar resultado
async function fetchResult(taskId) {
    const result = await fetch(`/api/extract/${taskId}/result`);
    const data = await result.json();
    showResult(data);
}
```

---

## Backend (FastAPI)

### `server/app.py`

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio
import uuid

from models.requests import ExtractionRequest, ExtractionResponse, ProgressEvent
from orchestrator import ExtractionOrchestrator

app = FastAPI()

# Estado em memória (suficiente para uso local single-user)
tasks: dict[str, ExtractionTask] = {}

# Serve arquivos estáticos
STATIC_DIR = Path(__file__).parent / "static"
OUTPUT_DIR = Path(__file__).parent.parent / "output"

@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/static/{file_path:path}")
async def static_files(file_path: str):
    return FileResponse(STATIC_DIR / file_path)

@app.get("/screenshots/{file_path:path}")
async def serve_screenshot(file_path: str):
    return FileResponse(OUTPUT_DIR / "assets" / "images" / file_path)

@app.post("/api/extract", response_model=ExtractionResponse)
async def start_extraction(request: ExtractionRequest):
    task_id = str(uuid.uuid4())[:8]
    task = ExtractionTask(id=task_id, request=request)
    tasks[task_id] = task
    asyncio.create_task(run_extraction(task))
    return ExtractionResponse(task_id=task_id)

@app.get("/api/extract/{task_id}/progress")
async def get_progress(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    async def event_stream():
        async for progress in task.progress_generator():
            yield f"data: {progress}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/api/extract/{task_id}/result")
async def get_result(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if not task.completed:
        raise HTTPException(400, "Extraction not completed")
    return task.result

@app.post("/api/extract/{task_id}/cancel")
async def cancel_extraction(task_id: str):
    task = tasks.get(task_id)
    if task:
        task.cancelled = True
    return {"cancelled": True}
```

### Task Manager

```python
class ExtractionTask:
    def __init__(self, id: str, request: ExtractionRequest):
        self.id = id
        self.request = request
        self.progress_queue: asyncio.Queue = asyncio.Queue()
        self.result = None
        self.completed = False
        self.cancelled = False
        self.error = None

    async def progress_generator(self):
        while True:
            progress = await self.progress_queue.get()
            yield progress
            if '"done": true' in progress or '"done":true' in progress:
                break

    async def emit_progress(self, step: int, step_name: str, message: str, done: bool = False):
        event = ProgressEvent(
            step=step,
            step_name=step_name,
            message=message,
            done=done
        )
        await self.progress_queue.put(event.model_dump_json())

    def check_cancelled(self) -> bool:
        return self.cancelled


async def run_extraction(task: ExtractionTask):
    try:
        orchestrator = ExtractionOrchestrator(
            progress_callback=lambda s, n, m: task.emit_progress(s, n, m),
            cancel_check=task.check_cancelled
        )

        result = await orchestrator.extract(
            url=task.request.url,
            mode=task.request.mode,
            strategy=task.request.strategy,
            query=task.request.query
        )

        task.result = result
        task.completed = True
        await task.emit_progress(11, "complete", "Extração concluída!", done=True)

    except ExtractionError as e:
        task.error = str(e)
        await task.emit_progress(0, "error", str(e), done=True)
    except Exception as e:
        task.error = str(e)
        await task.emit_progress(0, "error", f"Erro inesperado: {e}", done=True)
```

---

## Orchestrator (Async)

### Mudanças Principais

**Antes (threading):**
```python
from playwright.sync_api import sync_playwright

def extract(self, url, strategy, query, progress_callback, cancel_check):
    # código síncrono bloqueante
    self.browser.navigate(url)
    dom_data = self.dom_extractor.extract(target)
```

**Depois (async):**
```python
from playwright.async_api import async_playwright

async def extract(self, url, mode, strategy, query):
    # código assíncrono
    await self.browser.navigate(url)
    dom_data = await self.dom_extractor.extract(target)
```

### Estrutura do Orchestrator Async

```python
class ExtractionOrchestrator:
    def __init__(self, progress_callback=None, cancel_check=None, output_dir: str = "output"):
        self.progress_callback = progress_callback
        self.cancel_check = cancel_check or (lambda: False)
        self.output_dir = output_dir
        self.browser = None
        self.synthesizer = None

    async def emit_progress(self, step: int, step_name: str, message: str):
        if self.progress_callback:
            await self.progress_callback(step, step_name, message)

    async def extract(self, url: str, mode: str, strategy: str, query: str) -> dict:
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=True)
            page = await self.browser.new_page()

            # 1. Navegar
            if self.cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            await self.emit_progress(1, "navigating", "Conectando ao browser...")
            await page.goto(url, timeout=30000)

            # 2. Localizar componente
            if self.cancel_check():
                raise ExtractionError("Cancelado pelo usuário")
            await self.emit_progress(2, "locating", "Localizando componente...")
            target = await TargetFinder(page).find(strategy, query)

            # 3-11: Continua com cada etapa...
            # (DOM extraction, styles, interactions, etc.)

            await self.browser.close()

        return {
            "prompt": synthesis.recreation_prompt,
            "component_tree": synthesis.component_tree.model_dump(),
            "interactions": [i.model_dump() for i in synthesis.interactions],
            "responsive_rules": [r.model_dump() for r in synthesis.responsive_rules],
            "dependencies": [d.model_dump() for d in synthesis.dependencies],
            "screenshot_path": normalized.get_primary_screenshot_path(),
            "assets": [a.model_dump() for a in normalized.assets],
            "full_json": normalized.model_dump(mode="json")
        }
```

### Collector Modules (Async)

Todos os módulos do collector precisam ser adaptados para async:

```python
# collector/browser.py
class BrowserManager:
    async def navigate(self, url: str, timeout: int = 30000):
        await self.page.goto(url, timeout=timeout)

    async def resize_viewport(self, width: int, height: int):
        await self.page.set_viewport_size({"width": width, "height": height})

# collector/dom_extractor.py
class DOMExtractor:
    async def extract(self, target: Locator) -> dict:
        html = await target.inner_html()
        # ...

# collector/style_extractor.py
class StyleExtractor:
    async def extract(self, target: Locator) -> dict:
        styles = await self.page.evaluate(...)
        # ...
```

---

## Frontend

### Layout

```
┌────────────────────────────────────────────────────────────┐
│  Component Extractor                              [●/○]   │  ← Header + theme toggle
├──────────────────────┬─────────────────────────────────────┤
│                      │                                     │
│   INPUT PANEL        │        RESULT PANEL                 │
│                      │                                     │
│  ┌────────────────┐  │  ┌─────────────────────────────┐   │
│  │ URL            │  │  │ [Prompt] [JSON] [Assets]    │   │
│  └────────────────┘  │  ├─────────────────────────────┤   │
│  ┌────────────────┐  │  │                             │   │
│  │ ○ Componente   │  │  │   CONTEÚDO DA ABA          │   │
│  │ ● Landing Page │  │  │                             │   │
│  └────────────────┘  │  │   + Preview Screenshot      │   │
│  ┌────────────────┐  │  │                             │   │
│  │ ○ CSS ○ XPath  │  │  │                             │   │
│  │ ● Texto ○ HTML │  │  └─────────────────────────────┘   │
│  └────────────────┘  │                                     │
│  ┌────────────────┐  │                                     │
│  │ Seletor/Query  │  │                                     │
│  └────────────────┘  │                                     │
│                      │                                     │
│  [═══════════════]   │                                     │  ← Progress bar
│  [Extrair]           │                                     │
│                      │                                     │
├──────────────────────┴─────────────────────────────────────┤
│  Ready                                                     │  ← Status bar
└────────────────────────────────────────────────────────────┘
```

### `index.html`

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
        <button id="theme-toggle" title="Alternar tema">◐</button>
    </header>

    <main>
        <section class="input-panel">
            <div class="form-group">
                <label for="url">URL</label>
                <input type="url" id="url" placeholder="https://exemplo.com" required>
            </div>

            <div class="form-group">
                <label>Modo</label>
                <div class="radio-group">
                    <label><input type="radio" name="mode" value="component" checked> Componente</label>
                    <label><input type="radio" name="mode" value="full_page"> Landing Page</label>
                </div>
            </div>

            <div class="form-group">
                <label>Estratégia</label>
                <div class="radio-group">
                    <label><input type="radio" name="strategy" value="css"> CSS</label>
                    <label><input type="radio" name="strategy" value="xpath"> XPath</label>
                    <label><input type="radio" name="strategy" value="text" checked> Texto</label>
                    <label><input type="radio" name="strategy" value="html_snippet"> HTML</label>
                </div>
            </div>

            <div class="form-group">
                <label for="query">Seletor / Query</label>
                <textarea id="query" rows="3" placeholder="Texto para buscar..."></textarea>
            </div>

            <div class="progress-container hidden">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <p class="progress-text">Preparando...</p>
            </div>

            <button id="extract-btn" class="btn-primary">Extrair</button>
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
                    <button class="btn-copy" data-copy="prompt-text">Copiar</button>
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

### `styles.css`

```css
/* Temas */
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

/* Base */
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

/* Layout */
header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
}

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
}

input[type="url"], textarea {
    width: 100%;
    padding: 0.75rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text-primary);
    transition: border-color 0.2s;
}

input:focus, textarea:focus {
    outline: none;
    border-color: var(--accent);
}

.radio-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
}

/* Progress Bar */
.progress-container {
    margin-top: 1rem;
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

/* Buttons */
.btn-primary {
    padding: 0.75rem 1.5rem;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    transition: background 0.2s, transform 0.1s;
}

.btn-primary:hover {
    background: var(--accent-hover);
}

.btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
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
    transition: color 0.2s, background 0.2s;
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
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.toast.success { background: var(--success); color: #000; }
.toast.error { background: var(--error); color: #fff; }

@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

/* Status Bar */
.status-bar {
    padding: 0.5rem 2rem;
    background: var(--bg-secondary);
    border-top: 1px solid var(--border);
    color: var(--text-secondary);
    font-size: 0.875rem;
}

/* Utilities */
.hidden { display: none !important; }
```

### `app.js`

```javascript
const App = {
    state: {
        taskId: null,
        isExtracting: false,
        eventSource: null
    },

    init() {
        this.bindEvents();
        this.loadTheme();
    },

    bindEvents() {
        document.getElementById('extract-btn').addEventListener('click', () => this.startExtraction());
        document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());

        // Tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Copy buttons
        document.querySelectorAll('[data-copy]').forEach(btn => {
            btn.addEventListener('click', (e) => this.copyToClipboard(e.target.dataset.copy));
        });
    },

    async startExtraction() {
        const url = document.getElementById('url').value;
        const mode = document.querySelector('input[name="mode"]:checked').value;
        const strategy = document.querySelector('input[name="strategy"]:checked').value;
        const query = document.getElementById('query').value;

        if (!url) {
            this.showToast('Informe uma URL', 'error');
            return;
        }

        this.setExtractingState(true);

        try {
            const response = await fetch('/api/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, mode, strategy, query })
            });

            const { task_id } = await response.json();
            this.state.taskId = task_id;
            this.connectProgressStream(task_id);

        } catch (error) {
            this.showToast('Erro ao iniciar extração', 'error');
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
                if (data.step_name === 'complete') {
                    this.fetchResult(taskId);
                } else {
                    this.setExtractingState(false);
                    this.showToast(data.message, 'error');
                }
            }
        };

        this.state.eventSource.onerror = () => {
            this.state.eventSource.close();
            this.setExtractingState(false);
            this.showToast('Conexão perdida', 'error');
        };
    },

    updateProgress(data) {
        const container = document.querySelector('.progress-container');
        const fill = document.querySelector('.progress-fill');
        const text = document.querySelector('.progress-text');

        container.classList.remove('hidden');
        fill.style.width = `${(data.step / data.total_steps) * 100}%`;
        text.textContent = data.message;
        this.setStatus(data.message);
    },

    async fetchResult(taskId) {
        try {
            const response = await fetch(`/api/extract/${taskId}/result`);
            const result = await response.json();
            this.showResult(result);
            this.setExtractingState(false);
            this.showToast('Extração concluída!', 'success');
        } catch (error) {
            this.showToast('Erro ao obter resultado', 'error');
            this.setExtractingState(false);
        }
    },

    showResult(result) {
        const panel = document.querySelector('.result-panel');
        panel.classList.remove('hidden');

        // Prompt
        document.getElementById('prompt-text').textContent = result.prompt;

        // Screenshot
        const screenshotDiv = document.querySelector('.screenshot-preview');
        const screenshotImg = document.getElementById('screenshot-img');
        if (result.screenshot_path) {
            screenshotImg.src = `/screenshots/${result.screenshot_path}`;
            screenshotDiv.classList.remove('hidden');
        } else {
            screenshotDiv.classList.add('hidden');
        }

        // JSON
        document.getElementById('json-text').textContent = JSON.stringify(result.full_json, null, 2);

        // Assets
        const assetsList = document.getElementById('assets-list');
        assetsList.innerHTML = result.assets.map(a => `
            <li>${a.type}: ${a.local_path}</li>
        `).join('');

        this.switchTab('prompt');
    },

    setExtractingState(extracting) {
        this.state.isExtracting = extracting;
        const btn = document.getElementById('extract-btn');
        btn.disabled = extracting;
        btn.textContent = extracting ? 'Extraindo...' : 'Extrair';

        if (!extracting) {
            document.querySelector('.progress-container').classList.add('hidden');
        }
    },

    switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
        document.querySelector(`.tab-content[data-content="${tabName}"]`).classList.add('active');
    },

    async copyToClipboard(elementId) {
        const text = document.getElementById(elementId).textContent;
        await navigator.clipboard.writeText(text);
        this.showToast('Copiado!', 'success');
    },

    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    setStatus(message) {
        document.getElementById('status').textContent = message;
    },

    toggleTheme() {
        const html = document.documentElement;
        const current = html.dataset.theme;
        const next = current === 'dark' ? 'light' : 'dark';
        html.dataset.theme = next;
        localStorage.setItem('theme', next);
    },

    loadTheme() {
        const saved = localStorage.getItem('theme') || 'dark';
        document.documentElement.dataset.theme = saved;
    }
};

document.addEventListener('DOMContentLoaded', () => App.init());
```

---

## Entry Point

### `main.py`

```python
"""Component Extractor - Web UI Entry Point."""

import webbrowser
import uvicorn
from dotenv import load_dotenv
from server.app import app


def main():
    """Start the application."""
    load_dotenv()

    host = "127.0.0.1"
    port = 8000

    # Abre navegador após pequeno delay (para servidor iniciar)
    import threading
    threading.Timer(1.0, lambda: webbrowser.open(f"http://{host}:{port}")).start()

    print(f"Starting Component Extractor at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
```

---

## Dependências

### Adições ao `requirements.txt`

```
fastapi>=0.100.0
uvicorn>=0.23.0
```

### Remoções

```
# Tkinter é built-in, nenhuma remoção necessária
```

---

## Migração dos Módulos Collector

Todos os módulos do `collector/` precisam ser adaptados de `sync_api` para `async_api` do Playwright:

| Arquivo | Mudança Principal |
|---------|-------------------|
| `browser.py` | `sync_playwright` → `async_playwright` |
| `target_finder.py` | Métodos async |
| `dom_extractor.py` | Métodos async |
| `style_extractor.py` | Métodos async |
| `interaction_mapper.py` | Métodos async |
| `interaction_player.py` | Métodos async |
| `animation_recorder.py` | Métodos async |
| `asset_downloader.py` | Métodos async + `aiohttp` para downloads |
| `library_detector.py` | Métodos async |
| `responsive_collector.py` | Métodos async |

---

## Arquivos a Remover

Após migração completa:

- `gui/app.py`
- `gui/panels/input_panel.py`
- `gui/panels/result_panel.py`
- `gui/widgets/progress_display.py`
- `worker.py` (substituído por `ExtractionTask` async)

---

## Decisões de Design

| Aspecto | Decisão | Racional |
|---------|---------|----------|
| Backend | FastAPI | Moderno, tipagem automática, excelente suporte async |
| Tempo real | SSE | Mais simples que WebSocket para comunicação unidirecional |
| Frontend | HTML/CSS/JS puro | Sem build steps, adequado para app local simples |
| Estado | Em memória | Single-user local, não precisa de persistência |
| Concorrência | asyncio | Nativo do Python, integra bem com Playwright async |
| Tema | CSS variables | Simples, sem dependências |

---

## Próximos Passos

Após aprovação deste documento, seguir para o plano de implementação usando a skill `writing-plans`.
