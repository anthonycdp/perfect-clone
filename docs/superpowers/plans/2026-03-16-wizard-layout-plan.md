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

### Task 1: Restructure index.html for wizard layout

**Files:**
- Modify: `server/static/index.html`

- [ ] **Step 1: Replace two-panel layout with wizard container**

Replace the entire `<main>` section with wizard structure:

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
        <!-- Wizard Card -->
        <div class="wizard-card">
            <!-- Step 1: URL -->
            <div class="wizard-step" data-step="1" aria-label="Passo 1 de 4">
                <span class="step-indicator">1 de 4</span>
                <h2 class="step-title">Qual site você quer extrair?</h2>
                <div class="form-group">
                    <input type="url" id="url" placeholder="https://exemplo.com" aria-label="URL do site">
                    <span class="error-message" id="url-error"></span>
                </div>
                <div class="wizard-actions">
                    <button class="btn-primary" id="btn-next-1">Continuar →</button>
                </div>
            </div>

            <!-- Step 2: Mode -->
            <div class="wizard-step hidden" data-step="2" aria-label="Passo 2 de 4">
                <span class="step-indicator">2 de 4</span>
                <h2 class="step-title">O que você quer extrair?</h2>
                <div class="radio-cards" role="radiogroup" aria-label="Modo de extração">
                    <div class="radio-card selected" data-value="component" role="radio" aria-checked="true" tabindex="0">
                        <div class="radio-card-header">
                            <span class="radio-indicator"></span>
                            <span class="radio-label">Componente único</span>
                        </div>
                        <p class="radio-card-description">Um elemento específico da página</p>
                    </div>
                    <div class="radio-card" data-value="full_page" role="radio" aria-checked="false" tabindex="0">
                        <div class="radio-card-header">
                            <span class="radio-indicator"></span>
                            <span class="radio-label">Landing Page completa</span>
                        </div>
                        <p class="radio-card-description">Toda a página inicial</p>
                    </div>
                </div>
                <div class="wizard-actions">
                    <button class="btn-secondary" id="btn-back-2">← Voltar</button>
                    <button class="btn-primary" id="btn-next-2">Continuar →</button>
                </div>
            </div>

            <!-- Step 3: Strategy -->
            <div class="wizard-step hidden" data-step="3" aria-label="Passo 3 de 4">
                <span class="step-indicator">3 de 4</span>
                <h2 class="step-title">Como encontrar o componente?</h2>
                <div class="radio-cards strategy-cards" role="radiogroup" aria-label="Estratégia de busca">
                    <div class="radio-card" data-value="css" role="radio" aria-checked="false" tabindex="0">
                        <span class="radio-label">CSS</span>
                        <span class="radio-card-hint">Seletor CSS</span>
                    </div>
                    <div class="radio-card" data-value="xpath" role="radio" aria-checked="false" tabindex="0">
                        <span class="radio-label">XPath</span>
                        <span class="radio-card-hint">Expressão XPath</span>
                    </div>
                    <div class="radio-card selected" data-value="text" role="radio" aria-checked="true" tabindex="0">
                        <span class="radio-label">Texto</span>
                        <span class="radio-card-hint">Buscar por texto visível</span>
                    </div>
                    <div class="radio-card" data-value="html_snippet" role="radio" aria-checked="false" tabindex="0">
                        <span class="radio-label">HTML</span>
                        <span class="radio-card-hint">Trecho de HTML</span>
                    </div>
                </div>
                <p class="strategy-description" id="strategy-description">Buscar por texto visível na página</p>
                <div class="wizard-actions">
                    <button class="btn-secondary" id="btn-back-3">← Voltar</button>
                    <button class="btn-primary" id="btn-next-3">Continuar →</button>
                </div>
            </div>

            <!-- Step 4: Query + Execute -->
            <div class="wizard-step hidden" data-step="4" aria-label="Passo 4 de 4">
                <span class="step-indicator">4 de 4</span>
                <h2 class="step-title">O que você quer buscar?</h2>
                <div class="form-group">
                    <textarea id="query" rows="3" placeholder="Digite o texto do botão, título ou elemento..." aria-label="Query de busca"></textarea>
                    <span class="error-message" id="query-error"></span>
                </div>
                <div class="wizard-actions">
                    <button class="btn-secondary" id="btn-back-4">← Voltar</button>
                    <button class="btn-primary" id="btn-extract">🚀 Extrair</button>
                </div>
            </div>

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

            <!-- Error State -->
            <div class="wizard-step hidden" data-state="error" aria-label="Erro">
                <div class="error-icon">⚠</div>
                <h2 class="step-title centered">Erro</h2>
                <p class="error-text" id="error-text"></p>
                <div class="wizard-actions centered">
                    <button class="btn-secondary" id="btn-back-error">← Voltar</button>
                    <button class="btn-primary" id="btn-retry">Tentar Novamente</button>
                </div>
            </div>

            <!-- Result State -->
            <div class="wizard-step hidden" data-state="result">
                <div class="result-header">
                    <span class="success-icon">✓</span>
                    <h2 class="step-title">Extração concluída!</h2>
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
                    <button class="btn-secondary" id="btn-new-extraction">← Nova Extração</button>
                </div>
            </div>

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

- [ ] **Step 2: Commit HTML changes**

```bash
git add server/static/index.html
git commit -m "feat(ui): restructure HTML for wizard layout"
```

---

## Chunk 2: CSS Styles

### Task 2: Add wizard CSS styles

**Files:**
- Modify: `server/static/styles.css`

- [ ] **Step 1: Add wizard container and card styles**

Add to `styles.css`:

```css
/* ========================================
   Wizard Layout
   ======================================== */

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

/* ========================================
   Wizard Steps
   ======================================== */

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
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (prefers-reduced-motion: reduce) {
    .wizard-step {
        animation: none;
    }
}

/* Slide transitions */
.wizard-step.slide-left {
    animation: slideLeft 0.25s ease-out;
}

.wizard-step.slide-right {
    animation: slideRight 0.25s ease-out;
}

@keyframes slideLeft {
    from {
        opacity: 0;
        transform: translateX(30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slideRight {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* ========================================
   Step Indicator & Title
   ======================================== */

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

/* ========================================
   Form Elements
   ======================================== */

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

/* ========================================
   Radio Cards
   ======================================== */

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

/* ========================================
   Strategy Description
   ======================================== */

.strategy-description {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
    padding: 0.75rem;
    background: var(--bg-tertiary);
    border-radius: 6px;
}

/* ========================================
   Wizard Actions
   ======================================== */

.wizard-actions {
    display: flex;
    gap: 0.75rem;
    margin-top: 1.5rem;
    justify-content: flex-end;
}

.wizard-actions.centered {
    justify-content: center;
}

/* ========================================
   Buttons
   ======================================== */

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

.btn-primary:hover {
    background: var(--accent-hover);
}

.btn-primary:active {
    transform: scale(0.98);
}

.btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

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

/* ========================================
   Progress
   ======================================== */

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

/* ========================================
   Error State
   ======================================== */

.error-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.error-text {
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
}

/* ========================================
   Result State
   ======================================== */

.result-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
}

.success-icon {
    font-size: 1.5rem;
    color: var(--success);
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

.tab:hover {
    color: var(--text-primary);
}

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

.tab-content.hidden {
    display: none;
}

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

#assets-list li:last-child {
    border-bottom: none;
}

/* JSON */
#json-text {
    background: var(--bg-tertiary);
    padding: 1rem;
    border-radius: 8px;
    font-size: 0.75rem;
    overflow-x: auto;
}

/* ========================================
   Progress Dots
   ======================================== */

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

/* Hide dots on result/progress/error states */
.wizard-step[data-state="progress"] ~ .wizard-dots,
.wizard-step[data-state="result"] ~ .wizard-dots,
.wizard-step[data-state="error"] ~ .wizard-dots {
    visibility: hidden;
}

/* ========================================
   Responsive Design
   ======================================== */

/* Tablet (768px - 1024px) */
@media (max-width: 1024px) {
    .wizard-card {
        max-width: 500px;
    }

    .radio-cards.strategy-cards {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Mobile (< 768px) */
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

/* Remove old two-panel layout styles */
main {
    display: block;
    padding: 0;
}

.input-panel,
.result-panel {
    display: none;
}
```

- [ ] **Step 2: Commit CSS changes**

```bash
git add server/static/styles.css
git commit -m "feat(ui): add wizard layout CSS styles"
```

---

## Chunk 3: JavaScript Logic

### Task 3: Implement wizard navigation in app.js

**Files:**
- Modify: `server/static/app.js`

- [ ] **Step 1: Replace entire app.js with wizard implementation**

```javascript
const App = {
    // ========================================
    // State
    // ========================================
    state: {
        currentStep: 1,
        totalSteps: 4,
        taskId: null,
        isExtracting: false,
        eventSource: null,
        lastError: null,
        // Form data
        url: '',
        mode: 'component',
        strategy: 'text',
        query: ''
    },

    // ========================================
    // Initialization
    // ========================================
    init() {
        this.bindEvents();
        this.loadTheme();
        this.initKeyboardNav();
    },

    // ========================================
    // Event Bindings
    // ========================================
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

        // URL input - clear error on type
        document.getElementById('url').addEventListener('input', () => {
            document.getElementById('url-error').textContent = '';
        });

        // Query input - clear error on type
        document.getElementById('query').addEventListener('input', () => {
            document.getElementById('query-error').textContent = '';
        });
    },

    // ========================================
    // Navigation
    // ========================================
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

        // Hide state steps
        document.querySelectorAll('.wizard-step[data-state]').forEach(step => {
            step.classList.add('hidden');
        });

        // Show target step
        const targetStep = document.querySelector(`.wizard-step[data-step="${stepNum}"]`);
        if (targetStep) {
            targetStep.classList.remove('hidden');
            // Add animation class
            targetStep.classList.remove('slide-left', 'slide-right');
            if (stepNum > prevStep) {
                targetStep.classList.add('slide-left');
            } else if (stepNum < prevStep) {
                targetStep.classList.add('slide-right');
            }
        }

        // Update dots
        this.updateDots();

        // Update query placeholder based on strategy
        if (stepNum === 4) {
            this.updateQueryPlaceholder();
        }

        // Focus first input in step
        const firstInput = targetStep?.querySelector('input, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    },

    updateDots() {
        document.querySelectorAll('.dot').forEach((dot, index) => {
            const isActive = index < this.state.currentStep;
            dot.classList.toggle('active', isActive);
            dot.setAttribute('aria-current', index === this.state.currentStep - 1 ? 'step' : 'false');
        });
    },

    // ========================================
    // Validation
    // ========================================
    validateCurrentStep() {
        switch (this.state.currentStep) {
            case 1:
                return this.validateUrl();
            case 2:
                return true; // Mode always has a selection
            case 3:
                return true; // Strategy always has a selection
            case 4:
                return this.validateQuery();
            default:
                return true;
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
                errorEl.textContent = 'Por favor, informe uma URL válida (http:// ou https://)';
                return false;
            }
        } catch {
            errorEl.textContent = 'Por favor, informe uma URL válida (http:// ou https://)';
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

    // ========================================
    // Form Data
    // ========================================
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
            xpath: 'Buscar por expressão XPath',
            text: 'Buscar por texto visível na página',
            html_snippet: 'Buscar por trecho de HTML'
        };
        document.getElementById('strategy-description').textContent = descriptions[this.state.strategy];
    },

    updateQueryPlaceholder() {
        const placeholders = {
            css: 'Digite o seletor CSS (ex: .btn-primary)',
            xpath: 'Digite a expressão XPath',
            text: 'Digite o texto do botão, título ou elemento...',
            html_snippet: 'Cole o trecho HTML do elemento'
        };
        document.getElementById('query').placeholder = placeholders[this.state.strategy];
    },

    // ========================================
    // Extraction
    // ========================================
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
                throw new Error('Falha ao iniciar extração');
            }

            const { task_id } = await response.json();
            this.state.taskId = task_id;
            this.connectProgressStream(task_id);

        } catch (error) {
            this.showError('Erro ao iniciar extração. Verifique a conexão.');
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
                this.showError('Conexão perdida durante a extração');
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

        // Update ARIA
        bar.setAttribute('aria-valuenow', pct);
    },

    async fetchResult(taskId) {
        try {
            const response = await fetch(`/api/extract/${taskId}/result`);
            const result = await response.json();
            this.showResult(result);
            this.showToast('Extração concluída!', 'success');
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
                .catch(() => {}); // Ignore errors
        }

        this.state.isExtracting = false;
        this.goToStep(4);
        this.showToast('Extração cancelada', 'error');
    },

    resetExtraction() {
        // Clear query only, keep other fields
        this.state.query = '';
        document.getElementById('query').value = '';

        this.state.isExtracting = false;
        this.state.lastError = null;

        this.goToStep(1);
    },

    // ========================================
    // State Transitions
    // ========================================
    showState(stateName) {
        // Hide all steps
        document.querySelectorAll('.wizard-step').forEach(step => {
            step.classList.add('hidden');
        });

        // Show target state
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

        // Prompt
        document.getElementById('prompt-text').textContent = result.prompt;

        // Screenshot
        const screenshotContainer = document.getElementById('screenshot-container');
        const screenshotImg = document.getElementById('screenshot-img');
        if (result.screenshot_path) {
            screenshotImg.src = `/screenshots/${result.screenshot_path}`;
            screenshotContainer.classList.remove('hidden');
        } else {
            screenshotContainer.classList.add('hidden');
        }

        // JSON
        document.getElementById('json-text').textContent = JSON.stringify(result.full_json, null, 2);

        // Assets
        const assetsList = document.getElementById('assets-list');
        assetsList.innerHTML = result.assets.map(a => `
            <li>${a.type}: ${a.local_path}</li>
        `).join('');

        // Reset tabs
        this.switchTab('prompt');
    },

    // ========================================
    // Tabs
    // ========================================
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

    // ========================================
    // Utilities
    // ========================================
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

    // ========================================
    // Theme
    // ========================================
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

    // ========================================
    // Keyboard Navigation
    // ========================================
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

- [ ] **Step 2: Commit JavaScript changes**

```bash
git add server/static/app.js
git commit -m "feat(ui): implement wizard navigation and state management"
```

---

## Chunk 4: Final Verification

### Task 4: Verify wizard implementation

- [ ] **Step 1: Start the application and verify wizard flow**

```bash
python main.py
```

Expected behavior:
1. Browser opens showing Step 1 (URL input)
2. Enter URL and click "Continuar" → advances to Step 2
3. Select mode and click "Continuar" → advances to Step 3 (or Step 4 if Landing Page)
4. Select strategy and click "Continuar" → advances to Step 4
5. Enter query and click "Extrair" → shows progress state
6. After completion → shows result state
7. Click "Nova Extração" → returns to Step 1 with URL preserved

- [ ] **Step 2: Verify responsive design**

Resize browser to test:
- Desktop (> 1024px): Card centered, 600px max-width
- Tablet (768-1024px): Card 500px, strategy cards 2x2 grid
- Mobile (< 768px): Full-width card, vertical button stack

- [ ] **Step 3: Verify accessibility**

- Tab through all elements
- Enter key advances steps
- Escape cancels extraction
- Screen reader announces step numbers

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat(ui): complete wizard layout implementation

- Full-screen card wizard with 4 steps
- Progress dots and smooth transitions
- Responsive design for desktop/tablet/mobile
- Keyboard navigation and ARIA labels
- Error state and retry functionality"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Restructure HTML for wizard | `index.html` |
| 2 | Add wizard CSS styles | `styles.css` |
| 3 | Implement wizard JS logic | `app.js` |
| 4 | Verify and commit | - |

**Total:** 4 tasks, ~8 steps
