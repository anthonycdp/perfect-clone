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
