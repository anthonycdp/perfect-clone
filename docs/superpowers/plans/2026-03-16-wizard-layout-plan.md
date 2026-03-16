# Wizard Layout Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace two-panel layout with full-screen wizard cards for Component Extractor UI

**Architecture:** Frontend-only change. HTML structure reorganized into wizard steps with CSS transitions and JS navigation state. API endpoints unchanged.

**Tech Stack:** HTML5, CSS3 (CSS variables, transitions, media queries), Vanilla JS

**Spec:** `docs/superpowers/specs/2026-03-16-wizard-layout-design.md`

---

## File Structure

```
server/static/
├── index.html      # MODIFY: restructure to wizard layout
├── styles.css      # MODIFY: add wizard styles, transitions, responsiveness
└── app.js          # MODIFY: add navigation state, step transitions
```

---

## Chunk 1: HTML Structure

### Task 1: Add wizard container and Steps 1-2

**Files:**
- Modify: `server/static/index.html`

- [ ] **Step 1: Add DOCTYPE and header**

Replace beginning of file with:

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
        <button id="theme-toggle" title="Alternar tema" aria-label="Alternar tema claro/escuro">◐</button>
    </header>

    <main class="wizard-container">
        <div class="wizard-card">
```

- [ ] **Step 2: Add Step 1 (URL input)**

Add after wizard-card div:

```html
            <!-- Step 1: URL -->
            <div class="wizard-step" data-step="1" aria-label="Passo 1 de 4">
                <span class="step-indicator">1 de 4</span>
                <h2 class="step-title">Qual site voce quer extrair?</h2>
                <div class="form-group">
                    <input type="url" id="url" placeholder="https://exemplo.com" aria-label="URL do site">
                    <span class="error-message" id="url-error"></span>
                </div>
                <div class="wizard-actions">
                    <button class="btn-primary" id="btn-next-1">Continuar</button>
                </div>
            </div>
```

- [ ] **Step 3: Add Step 2 (Mode selection)**

Add after Step 1:

```html
            <!-- Step 2: Mode -->
            <div class="wizard-step hidden" data-step="2" aria-label="Passo 2 de 4">
                <span class="step-indicator">2 de 4</span>
                <h2 class="step-title">O que voce quer extrair?</h2>
                <div class="radio-cards" role="radiogroup" aria-label="Modo de extracao">
                    <div class="radio-card selected" data-value="component" role="radio" aria-checked="true" tabindex="0">
                        <div class="radio-card-header">
                            <span class="radio-indicator"></span>
                            <span class="radio-label">Componente unico</span>
                        </div>
                        <p class="radio-card-description">Um elemento especifico da pagina</p>
                    </div>
                    <div class="radio-card" data-value="full_page" role="radio" aria-checked="false" tabindex="0">
                        <div class="radio-card-header">
                            <span class="radio-indicator"></span>
                            <span class="radio-label">Landing Page completa</span>
                        </div>
                        <p class="radio-card-description">Toda a pagina inicial</p>
                    </div>
                </div>
                <div class="wizard-actions">
                    <button class="btn-secondary" id="btn-back-2">Voltar</button>
                    <button class="btn-primary" id="btn-next-2">Continuar</button>
                </div>
            </div>
```

- [ ] **Step 4: Commit HTML Steps 1-2**

```bash
git add server/static/index.html
git commit -m "feat(ui): add wizard steps 1-2 HTML structure"
```

### Task 2: Add Steps 3-4 and state views

**Files:**
- Modify: `server/static/index.html`

- [ ] **Step 1: Add Step 3 (Strategy selection)**

Add after Step 2:

```html
            <!-- Step 3: Strategy -->
            <div class="wizard-step hidden" data-step="3" aria-label="Passo 3 de 4">
                <span class="step-indicator">3 de 4</span>
                <h2 class="step-title">Como encontrar o componente?</h2>
                <div class="radio-cards strategy-cards" role="radiogroup" aria-label="Estrategia de busca">
                    <div class="radio-card" data-value="css" role="radio" aria-checked="false" tabindex="0">
                        <span class="radio-label">CSS</span>
                        <span class="radio-card-hint">Seletor CSS</span>
                    </div>
                    <div class="radio-card" data-value="xpath" role="radio" aria-checked="false" tabindex="0">
                        <span class="radio-label">XPath</span>
                        <span class="radio-card-hint">Expressao XPath</span>
                    </div>
                    <div class="radio-card selected" data-value="text" role="radio" aria-checked="true" tabindex="0">
                        <span class="radio-label">Texto</span>
                        <span class="radio-card-hint">Buscar por texto visivel</span>
                    </div>
                    <div class="radio-card" data-value="html_snippet" role="radio" aria-checked="false" tabindex="0">
                        <span class="radio-label">HTML</span>
                        <span class="radio-card-hint">Trecho de HTML</span>
                    </div>
                </div>
                <p class="strategy-description" id="strategy-description">Buscar por texto visivel na pagina</p>
                <div class="wizard-actions">
                    <button class="btn-secondary" id="btn-back-3">Voltar</button>
                    <button class="btn-primary" id="btn-next-3">Continuar</button>
                </div>
            </div>
```

- [ ] **Step 2: Add Step 4 (Query + Execute)**

Add after Step 3:

```html
            <!-- Step 4: Query + Execute -->
            <div class="wizard-step hidden" data-step="4" aria-label="Passo 4 de 4">
                <span class="step-indicator">4 de 4</span>
                <h2 class="step-title">O que voce quer buscar?</h2>
                <div class="form-group">
                    <textarea id="query" rows="3" placeholder="Digite o texto do botao, titulo ou elemento..." aria-label="Query de busca"></textarea>
                    <span class="error-message" id="query-error"></span>
                </div>
                <div class="wizard-actions">
                    <button class="btn-secondary" id="btn-back-4">Voltar</button>
                    <button class="btn-primary" id="btn-extract">Extrair</button>
                </div>
            </div>
```

- [ ] **Step 3: Add Progress state**

Add after Step 4:

```html
            <!-- Progress State -->
            <div class="wizard-step hidden" data-state="progress" aria-label="Extraindo">
                <h2 class="step-title centered">Extraindo...</h2>
                <div class="progress-container">
                    <div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
                        <div class="progress-fill"></div>
                    </div>
                    <span class="progress-percent">0%</span>
                </div>
                <p class="progress-message" id="progress-message">Preparando...</p>
                <div class="wizard-actions centered">
                    <button class="btn-danger" id="btn-cancel">Cancelar</button>
                </div>
            </div>
```

- [ ] **Step 4: Add Error state**

Add after Progress state:

```html
            <!-- Error State -->
            <div class="wizard-step hidden" data-state="error" aria-label="Erro">
                <div class="error-icon">!</div>
                <h2 class="step-title centered">Erro</h2>
                <p class="error-text" id="error-text"></p>
                <div class="wizard-actions centered">
                    <button class="btn-secondary" id="btn-back-error">Voltar</button>
                    <button class="btn-primary" id="btn-retry">Tentar Novamente</button>
                </div>
            </div>
```

- [ ] **Step 5: Add Result state**

Add after Error state:

```html
            <!-- Result State -->
            <div class="wizard-step hidden" data-state="result">
                <div class="result-header">
                    <span class="success-icon">ok</span>
                    <h2 class="step-title">Extracao concluida!</h2>
                </div>
                <div class="tabs">
                    <button class="tab active" data-tab="prompt" aria-selected="true">Prompt</button>
                    <button class="tab" data-tab="json" aria-selected="false">JSON</button>
                    <button class="tab" data-tab="assets" aria-selected="false">Assets</button>
                </div>
                <div class="tab-content active" data-content="prompt">
                    <div class="screenshot-preview hidden" id="screenshot-container">
                        <img id="screenshot-img" src="" alt="Screenshot do componente">
                    </div>
                    <div class="prompt-container">
                        <pre id="prompt-text"></pre>
                        <button class="btn-copy" id="btn-copy-prompt" aria-label="Copiar prompt">Copiar</button>
                    </div>
                </div>
                <div class="tab-content hidden" data-content="json">
                    <pre id="json-text"></pre>
                </div>
                <div class="tab-content hidden" data-content="assets">
                    <ul id="assets-list"></ul>
                </div>
                <div class="wizard-actions">
                    <button class="btn-secondary" id="btn-new-extraction">Nova Extracao</button>
                </div>
            </div>
```

- [ ] **Step 6: Add Progress Dots and close tags**

Add after Result state:

```html
            <!-- Progress Dots -->
            <div class="wizard-dots" aria-label="Progresso do wizard">
                <span class="dot active" data-dot="1" aria-label="Passo 1" aria-current="step"></span>
                <span class="dot" data-dot="2" aria-label="Passo 2"></span>
                <span class="dot" data-dot="3" aria-label="Passo 3"></span>
                <span class="dot" data-dot="4" aria-label="Passo 4"></span>
            </div>
        </div>
    </main>

    <div id="toast-container" aria-live="polite"></div>

    <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 7: Commit HTML Steps 3-4 and states**

```bash
git add server/static/index.html
git commit -m "feat(ui): add wizard steps 3-4 and state views"
```

---

## Chunk 2: CSS Styles

### Task 3: Add base wizard CSS

**Files:**
- Modify: `server/static/styles.css`

- [ ] **Step 1: Add CSS variables (including --success)**

Add at the top of styles.css or update existing `:root`:

```css
/* CSS Variables */
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
```

- [ ] **Step 2: Add wizard container and card styles**

```css
/* Wizard Layout */
.wizard-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 60px);
    padding: 1rem;
}

.wizard-card {
    width: 100%;
    max-width: 600px;
    background: var(--bg-secondary);
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
    position: relative;
}
```

- [ ] **Step 3: Add wizard step styles**

```css
/* Wizard Steps */
.wizard-step {
    animation: fadeIn 0.25s ease-out;
}

.wizard-step.hidden {
    display: none;
}

.wizard-step.centered {
    text-align: center;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
    .wizard-step { animation: none; }
}

/* Slide transitions */
.wizard-step.slide-left {
    animation: slideLeft 0.25s ease-out;
}

.wizard-step.slide-right {
    animation: slideRight 0.25s ease-out;
}

@keyframes slideLeft {
    from { opacity: 0; transform: translateX(30px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes slideRight {
    from { opacity: 0; transform: translateX(-30px); }
    to { opacity: 1; transform: translateX(0); }
}

@media (prefers-reduced-motion: reduce) {
    .wizard-step.slide-left,
    .wizard-step.slide-right { animation: none; }
}
```

- [ ] **Step 4: Commit base wizard CSS**

```bash
git add server/static/styles.css
git commit -m "feat(ui): add base wizard CSS styles"
```

### Task 4: Add form and button styles

**Files:**
- Modify: `server/static/styles.css`

- [ ] **Step 1: Add step indicator and title styles**

```css
/* Step Indicator & Title */
.step-indicator {
    display: block;
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
}

.step-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
    color: var(--text-primary);
}
```

- [ ] **Step 2: Add form group styles**

```css
/* Form Elements */
.form-group {
    margin-bottom: 1rem;
}

.form-group input[type="url"],
.form-group textarea {
    width: 100%;
    padding: 0.875rem 1rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text-primary);
    font-size: 1rem;
    transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(233, 69, 96, 0.15);
}

.form-group textarea {
    resize: vertical;
    min-height: 80px;
}

.error-message {
    display: block;
    color: var(--error);
    font-size: 0.875rem;
    margin-top: 0.5rem;
    min-height: 1.25rem;
}
```

- [ ] **Step 3: Add button styles**

```css
/* Buttons */
.btn-primary {
    padding: 0.75rem 1.5rem;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s, transform 0.1s;
}

.btn-primary:hover { background: var(--accent-hover); }
.btn-primary:active { transform: scale(0.98); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-secondary {
    padding: 0.75rem 1.5rem;
    background: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-secondary:hover {
    border-color: var(--text-secondary);
    color: var(--text-primary);
}

.btn-danger {
    padding: 0.75rem 1.5rem;
    background: transparent;
    color: var(--error);
    border: 1px solid var(--error);
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-danger:hover {
    background: var(--error);
    color: white;
}

.btn-copy {
    padding: 0.5rem 1rem;
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-copy:hover {
    border-color: var(--accent);
    color: var(--accent);
}
```

- [ ] **Step 4: Commit form and button styles**

```bash
git add server/static/styles.css
git commit -m "feat(ui): add form elements and button styles"
```

### Task 5: Add radio card styles

**Files:**
- Modify: `server/static/styles.css`

- [ ] **Step 1: Add radio cards styles**

```css
/* Radio Cards */
.radio-cards {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
}

.radio-cards.strategy-cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
}

.radio-card {
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s;
}

.radio-card:hover {
    border-color: var(--text-secondary);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.radio-card:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(233, 69, 96, 0.15);
}

.radio-card.selected {
    border: 2px solid var(--accent);
    background: rgba(233, 69, 96, 0.1);
}

.radio-card-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.radio-indicator {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: 2px solid var(--border);
    transition: all 0.2s;
    position: relative;
}

.radio-card.selected .radio-indicator {
    border-color: var(--accent);
}

.radio-card.selected .radio-indicator::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent);
}

.radio-label {
    font-weight: 500;
    color: var(--text-primary);
}

.radio-card-description {
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
}

.radio-card-hint {
    display: block;
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
}

/* Strategy cards compact style */
.strategy-cards .radio-card {
    text-align: center;
    padding: 0.75rem;
}

.strategy-cards .radio-label {
    font-size: 0.875rem;
}

.strategy-description {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
    padding: 0.75rem;
    background: var(--bg-tertiary);
    border-radius: 6px;
}
```

- [ ] **Step 2: Commit radio card styles**

```bash
git add server/static/styles.css
git commit -m "feat(ui): add radio card component styles"
```

### Task 6: Add progress, error, and result styles

**Files:**
- Modify: `server/static/styles.css`

- [ ] **Step 1: Add progress bar styles**

```css
/* Progress */
.progress-container {
    margin: 1.5rem 0;
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

.progress-percent {
    display: block;
    text-align: center;
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
}

.progress-message {
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.875rem;
}
```

- [ ] **Step 2: Add error state styles**

```css
/* Error State */
.error-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--error);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: bold;
    margin: 0 auto 1rem;
}

.error-text {
    text-align: center;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
}
```

- [ ] **Step 3: Add result state styles**

```css
/* Result State */
.result-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
}

.success-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--success);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.875rem;
    font-weight: bold;
}

/* Tabs */
.tabs {
    display: flex;
    gap: 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}

.tab {
    padding: 0.75rem 1rem;
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
}

.tab:hover { color: var(--text-primary); }

.tab.active {
    color: var(--accent);
    border-bottom-color: var(--accent);
}

/* Tab Content */
.tab-content {
    padding: 0.5rem 0;
    max-height: 400px;
    overflow-y: auto;
}

.tab-content.hidden { display: none; }
.tab-content.active { display: block; }

/* Screenshot */
.screenshot-preview {
    margin-bottom: 1rem;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border);
}

.screenshot-preview img {
    width: 100%;
    max-height: 250px;
    object-fit: contain;
    background: var(--bg-tertiary);
}

/* Prompt */
.prompt-container {
    position: relative;
}

.prompt-container pre {
    background: var(--bg-tertiary);
    padding: 1rem;
    border-radius: 8px;
    font-size: 0.875rem;
    white-space: pre-wrap;
    word-wrap: break-word;
    max-height: 300px;
    overflow-y: auto;
}

.prompt-container .btn-copy {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
}

/* Assets List */
#assets-list {
    list-style: none;
    padding: 0;
}

#assets-list li {
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border);
    font-size: 0.875rem;
}

#assets-list li:last-child { border-bottom: none; }

/* JSON */
#json-text {
    background: var(--bg-tertiary);
    padding: 1rem;
    border-radius: 8px;
    font-size: 0.75rem;
    overflow-x: auto;
}
```

- [ ] **Step 4: Commit progress and result styles**

```bash
git add server/static/styles.css
git commit -m "feat(ui): add progress, error, and result state styles"
```

### Task 7: Add navigation and toast styles

**Files:**
- Modify: `server/static/styles.css`

- [ ] **Step 1: Add wizard actions and dots styles**

```css
/* Wizard Actions */
.wizard-actions {
    display: flex;
    gap: 0.75rem;
    margin-top: 1.5rem;
    justify-content: flex-end;
}

.wizard-actions.centered {
    justify-content: center;
}

/* Progress Dots */
.wizard-dots {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
}

.dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--border);
    transition: background 0.2s;
}

.dot.active {
    background: var(--accent);
}
```

- [ ] **Step 2: Add toast notification styles**

```css
/* Toast Notifications */
#toast-container {
    position: fixed;
    bottom: 1rem;
    right: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    z-index: 1000;
}

.toast {
    padding: 0.75rem 1rem;
    border-radius: 6px;
    animation: slideIn 0.3s ease;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.toast.success {
    background: var(--success);
    color: white;
}

.toast.error {
    background: var(--error);
    color: white;
}

@keyframes slideIn {
    from { opacity: 0; transform: translateX(100%); }
    to { opacity: 1; transform: translateX(0); }
}

@media (prefers-reduced-motion: reduce) {
    .toast { animation: none; }
}
```

- [ ] **Step 3: Commit navigation and toast styles**

```bash
git add server/static/styles.css
git commit -m "feat(ui): add wizard navigation and toast styles"
```

### Task 8: Add responsive styles

**Files:**
- Modify: `server/static/styles.css`

- [ ] **Step 1: Add header and base layout styles**

```css
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
    color: var(--text-primary);
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

/* Base Layout */
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
```

- [ ] **Step 2: Add tablet responsive styles**

```css
/* Responsive - Tablet (768px - 1024px) */
@media (max-width: 1024px) {
    .wizard-card {
        max-width: 500px;
    }

    .radio-cards.strategy-cards {
        grid-template-columns: repeat(2, 1fr);
    }
}
```

- [ ] **Step 3: Add mobile responsive styles**

```css
/* Responsive - Mobile (< 768px) */
@media (max-width: 768px) {
    .wizard-container {
        padding: 0;
        min-height: calc(100vh - 50px);
    }

    .wizard-card {
        border-radius: 0;
        padding: 1.5rem;
        max-width: 100%;
        min-height: calc(100vh - 50px);
    }

    .step-title {
        font-size: 1.25rem;
    }

    .radio-cards.strategy-cards {
        grid-template-columns: repeat(2, 1fr);
        gap: 0.5rem;
    }

    .strategy-cards .radio-card {
        padding: 0.5rem;
    }

    .strategy-cards .radio-label {
        font-size: 0.75rem;
    }

    .wizard-actions {
        flex-direction: column-reverse;
    }

    .wizard-actions button {
        width: 100%;
    }

    header {
        padding: 0.75rem 1rem;
    }

    header h1 {
        font-size: 1rem;
    }
}
```

- [ ] **Step 4: Commit responsive styles**

```bash
git add server/static/styles.css
git commit -m "feat(ui): add responsive styles for tablet and mobile"
```

---

## Chunk 3: JavaScript Logic

### Task 9: Add state and initialization

**Files:**
- Modify: `server/static/app.js`

- [ ] **Step 1: Add App state and init function**

```javascript
const App = {
    // State
    state: {
        currentStep: 1,
        totalSteps: 4,
        taskId: null,
        isExtracting: false,
        eventSource: null,
        lastError: null,
        url: '',
        mode: 'component',
        strategy: 'text',
        query: ''
    },

    // Initialization
    init() {
        this.bindEvents();
        this.loadTheme();
        this.initKeyboardNav();
    },
```

- [ ] **Step 2: Commit state structure**

```bash
git add server/static/app.js
git commit -m "feat(ui): add wizard state structure"
```

### Task 10: Add event bindings

**Files:**
- Modify: `server/static/app.js`

- [ ] **Step 1: Add bindEvents function**

```javascript
    // Event Bindings
    bindEvents() {
        // Theme toggle
        document.getElementById('theme-toggle').addEventListener('click', () => this.toggleTheme());

        // Navigation buttons
        document.getElementById('btn-next-1').addEventListener('click', () => this.nextStep());
        document.getElementById('btn-next-2').addEventListener('click', () => this.nextStep());
        document.getElementById('btn-next-3').addEventListener('click', () => this.nextStep());
        document.getElementById('btn-back-2').addEventListener('click', () => this.prevStep());
        document.getElementById('btn-back-3').addEventListener('click', () => this.prevStep());
        document.getElementById('btn-back-4').addEventListener('click', () => this.prevStep());

        // Extraction
        document.getElementById('btn-extract').addEventListener('click', () => this.startExtraction());
        document.getElementById('btn-cancel').addEventListener('click', () => this.cancelExtraction());

        // Error state
        document.getElementById('btn-back-error').addEventListener('click', () => this.goToStep(4));
        document.getElementById('btn-retry').addEventListener('click', () => this.startExtraction());

        // New extraction
        document.getElementById('btn-new-extraction').addEventListener('click', () => this.resetExtraction());

        // Radio cards - Mode
        document.querySelectorAll('.radio-cards:not(.strategy-cards) .radio-card').forEach(card => {
            card.addEventListener('click', () => this.selectRadioCard(card, 'mode'));
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.selectRadioCard(card, 'mode');
                }
            });
        });

        // Radio cards - Strategy
        document.querySelectorAll('.strategy-cards .radio-card').forEach(card => {
            card.addEventListener('click', () => this.selectRadioCard(card, 'strategy'));
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.selectRadioCard(card, 'strategy');
                }
            });
        });

        // Tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Copy button
        document.getElementById('btn-copy-prompt').addEventListener('click', () => this.copyPrompt());

        // Clear errors on input
        document.getElementById('url').addEventListener('input', () => {
            document.getElementById('url-error').textContent = '';
        });
        document.getElementById('query').addEventListener('input', () => {
            document.getElementById('query-error').textContent = '';
        });
    },
```

- [ ] **Step 2: Commit event bindings**

```bash
git add server/static/app.js
git commit -m "feat(ui): add wizard event bindings"
```

### Task 11: Add navigation functions

**Files:**
- Modify: `server/static/app.js`

- [ ] **Step 1: Add navigation functions (nextStep, prevStep, goToStep)**

```javascript
    // Navigation
    nextStep() {
        if (!this.validateCurrentStep()) return;

        this.saveCurrentStepData();

        // Skip step 3 if mode is full_page
        if (this.state.currentStep === 2 && this.state.mode === 'full_page') {
            this.goToStep(4);
            return;
        }

        if (this.state.currentStep < this.state.totalSteps) {
            this.goToStep(this.state.currentStep + 1);
        }
    },

    prevStep() {
        if (this.state.currentStep > 1) {
            // Skip step 3 if mode is full_page
            if (this.state.currentStep === 4 && this.state.mode === 'full_page') {
                this.goToStep(2);
                return;
            }
            this.goToStep(this.state.currentStep - 1);
        }
    },

    goToStep(stepNum) {
        const prevStep = this.state.currentStep;
        this.state.currentStep = stepNum;

        // Hide all steps
        document.querySelectorAll('.wizard-step[data-step]').forEach(step => {
            step.classList.add('hidden');
        });
        document.querySelectorAll('.wizard-step[data-state]').forEach(step => {
            step.classList.add('hidden');
        });

        // Show target step
        const targetStep = document.querySelector(`.wizard-step[data-step="${stepNum}"]`);
        if (targetStep) {
            targetStep.classList.remove('hidden');
            targetStep.classList.remove('slide-left', 'slide-right');
            if (stepNum > prevStep) {
                targetStep.classList.add('slide-left');
            } else if (stepNum < prevStep) {
                targetStep.classList.add('slide-right');
            }
        }

        this.updateDots();

        if (stepNum === 4) {
            this.updateQueryPlaceholder();
        }

        const firstInput = targetStep?.querySelector('input, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    },

    updateDots() {
        document.querySelectorAll('.dot').forEach((dot, index) => {
            // Only current step dot is active (spec: oc oo oo for step 2)
            const isActive = index === this.state.currentStep - 1;
            dot.classList.toggle('active', isActive);
            dot.setAttribute('aria-current', isActive ? 'step' : 'false');
        });
    },
```

- [ ] **Step 2: Commit navigation functions**

```bash
git add server/static/app.js
git commit -m "feat(ui): add wizard navigation functions"
```

### Task 12: Add validation and form data functions

**Files:**
- Modify: `server/static/app.js`

- [ ] **Step 1: Add validation functions**

```javascript
    // Validation
    validateCurrentStep() {
        switch (this.state.currentStep) {
            case 1: return this.validateUrl();
            case 2: return true;
            case 3: return true;
            case 4: return this.validateQuery();
            default: return true;
        }
    },

    validateUrl() {
        const url = document.getElementById('url').value.trim();
        const errorEl = document.getElementById('url-error');

        if (!url) {
            errorEl.textContent = 'Por favor, informe uma URL';
            return false;
        }

        try {
            const parsed = new URL(url);
            if (!['http:', 'https:'].includes(parsed.protocol)) {
                errorEl.textContent = 'Por favor, informe uma URL valida (http:// ou https://)';
                return false;
            }
        } catch {
            errorEl.textContent = 'Por favor, informe uma URL valida (http:// ou https://)';
            return false;
        }

        errorEl.textContent = '';
        return true;
    },

    validateQuery() {
        const query = document.getElementById('query').value.trim();
        const errorEl = document.getElementById('query-error');

        if (!query) {
            errorEl.textContent = 'Por favor, informe o que deseja buscar';
            return false;
        }

        errorEl.textContent = '';
        return true;
    },
```

- [ ] **Step 2: Add form data functions**

```javascript
    // Form Data
    saveCurrentStepData() {
        switch (this.state.currentStep) {
            case 1:
                this.state.url = document.getElementById('url').value.trim();
                break;
            case 4:
                this.state.query = document.getElementById('query').value.trim();
                break;
        }
    },

    selectRadioCard(card, type) {
        const container = card.closest('.radio-cards');
        container.querySelectorAll('.radio-card').forEach(c => {
            c.classList.remove('selected');
            c.setAttribute('aria-checked', 'false');
        });

        card.classList.add('selected');
        card.setAttribute('aria-checked', 'true');

        if (type === 'mode') {
            this.state.mode = card.dataset.value;
        } else if (type === 'strategy') {
            this.state.strategy = card.dataset.value;
            this.updateStrategyDescription();
        }
    },

    updateStrategyDescription() {
        const descriptions = {
            css: 'Buscar por seletor CSS',
            xpath: 'Buscar por expressao XPath',
            text: 'Buscar por texto visivel na pagina',
            html_snippet: 'Buscar por trecho de HTML'
        };
        document.getElementById('strategy-description').textContent = descriptions[this.state.strategy];
    },

    updateQueryPlaceholder() {
        const placeholders = {
            css: 'Digite o seletor CSS (ex: .btn-primary)',
            xpath: 'Digite a expressao XPath',
            text: 'Digite o texto do botao, titulo ou elemento...',
            html_snippet: 'Cole o trecho HTML do elemento'
        };
        document.getElementById('query').placeholder = placeholders[this.state.strategy];
    },
```

- [ ] **Step 3: Commit validation and form data**

```bash
git add server/static/app.js
git commit -m "feat(ui): add validation and form data functions"
```

### Task 13: Add extraction and state management

**Files:**
- Modify: `server/static/app.js`

- [ ] **Step 1: Add extraction functions**

```javascript
    // Extraction
    async startExtraction() {
        if (!this.validateCurrentStep()) return;

        this.saveCurrentStepData();
        this.showState('progress');
        this.state.isExtracting = true;

        try {
            const response = await fetch('/api/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: this.state.url,
                    mode: this.state.mode,
                    strategy: this.state.strategy,
                    query: this.state.query
                })
            });

            if (!response.ok) {
                throw new Error('Falha ao iniciar extracao');
            }

            const { task_id } = await response.json();
            this.state.taskId = task_id;
            this.connectProgressStream(task_id);

        } catch (error) {
            this.showError('Erro ao iniciar extracao. Verifique a conexao.');
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
                    this.showError(data.message);
                }
            }
        };

        this.state.eventSource.onerror = () => {
            this.state.eventSource.close();
            if (this.state.isExtracting) {
                this.showError('Conexao perdida durante a extracao');
            }
        };
    },

    updateProgress(data) {
        const fill = document.querySelector('.progress-fill');
        const percent = document.querySelector('.progress-percent');
        const message = document.getElementById('progress-message');
        const bar = document.querySelector('.progress-bar');

        const pct = Math.round((data.step / data.total_steps) * 100);
        fill.style.width = `${pct}%`;
        percent.textContent = `${pct}%`;
        message.textContent = data.message;

        bar.setAttribute('aria-valuenow', pct);
    },

    async fetchResult(taskId) {
        try {
            const response = await fetch(`/api/extract/${taskId}/result`);
            const result = await response.json();
            this.showResult(result);
            this.showToast('Extracao concluida!', 'success');
        } catch (error) {
            this.showError('Erro ao obter resultado');
        }
    },

    cancelExtraction() {
        if (this.state.eventSource) {
            this.state.eventSource.close();
        }

        if (this.state.taskId) {
            fetch(`/api/extract/${this.state.taskId}/cancel`, { method: 'POST' })
                .catch(() => {});
        }

        this.state.isExtracting = false;
        this.goToStep(4);
        this.showToast('Extracao cancelada', 'error');
    },

    resetExtraction() {
        this.state.query = '';
        document.getElementById('query').value = '';
        this.state.isExtracting = false;
        this.state.lastError = null;
        this.goToStep(1);
    },
```

- [ ] **Step 2: Add state transition functions**

```javascript
    // State Transitions
    showState(stateName) {
        document.querySelectorAll('.wizard-step').forEach(step => {
            step.classList.add('hidden');
        });

        const targetState = document.querySelector(`.wizard-step[data-state="${stateName}"]`);
        if (targetState) {
            targetState.classList.remove('hidden');
        }
    },

    showError(message) {
        this.state.isExtracting = false;
        this.state.lastError = message;
        document.getElementById('error-text').textContent = message;
        this.showState('error');
    },

    showResult(result) {
        this.state.isExtracting = false;
        this.showState('result');

        document.getElementById('prompt-text').textContent = result.prompt;

        const screenshotContainer = document.getElementById('screenshot-container');
        const screenshotImg = document.getElementById('screenshot-img');
        if (result.screenshot_path) {
            screenshotImg.src = `/screenshots/${result.screenshot_path}`;
            screenshotContainer.classList.remove('hidden');
        } else {
            screenshotContainer.classList.add('hidden');
        }

        document.getElementById('json-text').textContent = JSON.stringify(result.full_json, null, 2);

        const assetsList = document.getElementById('assets-list');
        assetsList.innerHTML = result.assets.map(a => `
            <li>${a.type}: ${a.local_path}</li>
        `).join('');

        this.switchTab('prompt');
    },
```

- [ ] **Step 3: Commit extraction and state management**

```bash
git add server/static/app.js
git commit -m "feat(ui): add extraction and state management"
```

### Task 14: Add utilities and keyboard navigation

**Files:**
- Modify: `server/static/app.js`

- [ ] **Step 1: Add utility functions**

```javascript
    // Tabs
    switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(t => {
            const isActive = t.dataset.tab === tabName;
            t.classList.toggle('active', isActive);
            t.setAttribute('aria-selected', isActive);
        });

        document.querySelectorAll('.tab-content').forEach(c => {
            c.classList.toggle('hidden', c.dataset.content !== tabName);
            c.classList.toggle('active', c.dataset.content === tabName);
        });
    },

    // Utilities
    async copyPrompt() {
        const text = document.getElementById('prompt-text').textContent;
        await navigator.clipboard.writeText(text);
        this.showToast('Copiado!', 'success');
    },

    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toast.setAttribute('role', 'alert');
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // Theme
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
    },
```

- [ ] **Step 2: Add keyboard navigation**

```javascript
    // Keyboard Navigation
    initKeyboardNav() {
        document.addEventListener('keydown', (e) => {
            // Escape to cancel extraction
            if (e.key === 'Escape' && this.state.isExtracting) {
                this.cancelExtraction();
            }

            // Enter to advance in input fields
            if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
                const step = document.querySelector(`.wizard-step[data-step="${this.state.currentStep}"]`);
                if (step && !step.classList.contains('hidden')) {
                    const nextBtn = step.querySelector('.btn-primary');
                    if (nextBtn && document.activeElement.tagName !== 'BUTTON') {
                        nextBtn.click();
                    }
                }
            }
        });
    }
};

document.addEventListener('DOMContentLoaded', () => App.init());
```

- [ ] **Step 3: Commit utilities and keyboard navigation**

```bash
git add server/static/app.js
git commit -m "feat(ui): add utilities, theme, and keyboard navigation"
```

---

## Chunk 4: Verification

### Task 15: Verify wizard implementation

- [ ] **Step 1: Start application and verify basic flow**

```bash
python main.py
```

Expected behavior:
1. Browser opens showing Step 1 (URL input)
2. Enter URL and click "Continuar" -> advances to Step 2
3. Select mode and click "Continuar" -> advances to Step 3 (or Step 4 if Landing Page)
4. Select strategy and click "Continuar" -> advances to Step 4
5. Enter query and click "Extrair" -> shows progress state
6. After completion -> shows result state
7. Click "Nova Extracao" -> returns to Step 1 with URL preserved

- [ ] **Step 2: Verify Landing Page mode skip behavior**

Test sequence:
1. Start at Step 1, enter URL
2. At Step 2, select "Landing Page completa"
3. Click "Continuar" -> verify Step 3 is SKIPPED, Step 4 is shown
4. Click "Voltar" from Step 4 -> verify returns to Step 2 (not Step 3)

- [ ] **Step 3: Verify responsive design**

Resize browser to test:
- Desktop (> 1024px): Card centered, 600px max-width
- Tablet (768-1024px): Card 500px, strategy cards 2x2 grid
- Mobile (< 768px): Full-width card, vertical button stack

- [ ] **Step 4: Verify accessibility**

- Tab through all elements
- Enter key advances steps
- Escape cancels extraction
- Screen reader announces step numbers

- [ ] **Step 5: Final commit**

```bash
git add server/static/index.html server/static/styles.css server/static/app.js
git commit -m "feat(ui): complete wizard layout implementation

- Full-screen card wizard with 4 steps
- Progress dots with current-step indication
- Smooth slide transitions with reduced-motion support
- Responsive design for desktop/tablet/mobile
- Keyboard navigation and ARIA labels
- Error state and retry functionality
- Skip step 3 for Landing Page mode"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Add wizard container and Steps 1-2 | `index.html` |
| 2 | Add Steps 3-4 and state views | `index.html` |
| 3 | Add base wizard CSS | `styles.css` |
| 4 | Add form and button styles | `styles.css` |
| 5 | Add radio card styles | `styles.css` |
| 6 | Add progress, error, and result styles | `styles.css` |
| 7 | Add navigation and toast styles | `styles.css` |
| 8 | Add responsive styles | `styles.css` |
| 9 | Add state and initialization | `app.js` |
| 10 | Add event bindings | `app.js` |
| 11 | Add navigation functions | `app.js` |
| 12 | Add validation and form data | `app.js` |
| 13 | Add extraction and state management | `app.js` |
| 14 | Add utilities and keyboard navigation | `app.js` |
| 15 | Verify wizard implementation | - |

**Total:** 15 tasks, ~45 steps
