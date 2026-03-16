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
