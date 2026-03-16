// Component Extractor Web UI - JavaScript Application
// Premium Dark UI Implementation

// ========================================
// State
// ========================================
let taskId = null;
let isExtracting = false;
let eventSource = null;

// ========================================
// DOM Elements
// ========================================
const elements = {
    // Inputs
    urlInput: document.getElementById('url'),
    queryInput: document.getElementById('query'),
    extractBtn: document.getElementById('extract-btn'),

    // Progress
    progressSection: document.getElementById('progress-section'),
    progressFill: document.querySelector('.progress-fill'),
    progressPercentage: document.querySelector('.progress-percentage'),
    progressText: document.querySelector('.progress-text'),

    // Results
    emptyState: document.getElementById('empty-state'),
    resultPanel: document.getElementById('result-panel'),
    promptText: document.getElementById('prompt-text'),
    jsonText: document.getElementById('json-text'),
    assetsList: document.getElementById('assets-list'),

    // Preview
    screenshotImg: document.getElementById('screenshot-img'),
    screenshotPreview: document.getElementById('screenshot-preview'),
    noPreview: document.getElementById('no-preview'),
    resultActions: document.getElementById('result-actions'),
    downloadPackageLink: document.getElementById('download-package'),
    packageExpiry: document.getElementById('package-expiry'),

    // Status & Theme
    statusText: document.getElementById('status'),
    statusIndicator: document.getElementById('status-indicator'),
    themeToggle: document.getElementById('theme-toggle'),

    // Navigation
    tabs: document.querySelectorAll('.tab'),
    copyButtons: document.querySelectorAll('.btn-copy'),
    querySection: document.getElementById('query-section')
};

// ========================================
// Initialize
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    loadTheme();
    bindEvents();
    initializeModeVisibility();
});

// ========================================
// Event Bindings
// ========================================
function bindEvents() {
    // Main actions
    elements.extractBtn.addEventListener('click', startExtraction);
    elements.themeToggle.addEventListener('click', toggleTheme);

    // Tabs
    elements.tabs.forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // Copy buttons
    elements.copyButtons.forEach(btn => {
        btn.addEventListener('click', () => copyToClipboard(btn.dataset.copy));
    });

    // Strategy changes
    document.querySelectorAll('input[name="strategy"]').forEach(radio => {
        radio.addEventListener('change', updateQueryPlaceholder);
    });

    // Mode changes
    document.querySelectorAll('input[name="mode"]').forEach(radio => {
        radio.addEventListener('change', handleModeChange);
    });

    // Update query placeholder initially
    updateQueryPlaceholder();

    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

// ========================================
// Mode & Strategy Handlers
// ========================================
function initializeModeVisibility() {
    const mode = document.querySelector('input[name="mode"]:checked').value;
    updateQuerySectionVisibility(mode === 'component');
}

function handleModeChange(event) {
    const isComponentMode = event.target.value === 'component';
    updateQuerySectionVisibility(isComponentMode);
}

function updateQuerySectionVisibility(visible) {
    if (elements.querySection) {
        elements.querySection.style.display = visible ? 'block' : 'none';
    }
}

function updateQueryPlaceholder() {
    const strategy = document.querySelector('input[name="strategy"]:checked').value;
    const placeholders = {
        css: '.class-name or #id',
        xpath: '//div[@class="example"]',
        text: 'Text to search...',
        html_snippet: '<div class="example">...</div>'
    };
    elements.queryInput.placeholder = placeholders[strategy] || 'Enter query...';
}

// ========================================
// Extraction Flow
// ========================================
async function startExtraction() {
    const url = elements.urlInput.value.trim();
    if (!url) {
        showToast('Please enter a URL', 'error');
        elements.urlInput.focus();
        return;
    }

    const mode = document.querySelector('input[name="mode"]:checked').value;
    const strategy = document.querySelector('input[name="strategy"]:checked').value;
    const query = elements.queryInput.value.trim();

    if (mode !== 'full_page' && !query) {
        showToast('Please enter a selector or query', 'error');
        elements.queryInput.focus();
        return;
    }

    // Update UI state
    setExtractingState(true);
    showProgress();
    updateProgress({ progress: 0, message: 'Starting extraction...' });

    // Hide previous results and show progress
    elements.resultPanel.classList.add('hidden');
    elements.emptyState.classList.add('hidden');

    try {
        const response = await fetch('/api/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url,
                mode,
                strategy,
                query
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Extraction failed');
        }

        const data = await response.json();
        taskId = data.task_id;

        updateStatus(`Task created: ${taskId}`);
        connectProgressStream(taskId);

    } catch (error) {
        showToast(error.message, 'error');
        setExtractingState(false);
        hideProgress();
        updateStatus('Error');
        elements.emptyState.classList.remove('hidden');
    }
}

// ========================================
// Progress Stream (SSE)
// ========================================
function connectProgressStream(taskId) {
    if (eventSource) {
        eventSource.close();
    }

    eventSource = new EventSource(`/api/extract/${taskId}/progress`);

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateProgress(data);

        if (data.done && data.step_name === 'error') {
            eventSource.close();
            showToast(data.message || 'Extraction failed', 'error');
            setExtractingState(false);
            hideProgress();
            updateStatus('Failed');
            setStatusError(true);
        } else if (data.done) {
            eventSource.close();
            fetchResult(taskId);
        }
    };

    eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        eventSource.close();
        showToast('Connection lost', 'error');
        setExtractingState(false);
        hideProgress();
        updateStatus('Error');
        setStatusError(true);
    };
}

function updateProgress(data) {
    const totalSteps = data.total_steps || 12;
    const progress = typeof data.progress === 'number'
        ? data.progress
        : Math.min(100, Math.round(((data.step || 0) / totalSteps) * 100));
    const message = data.message || 'Processing...';

    elements.progressFill.style.width = `${progress}%`;
    elements.progressPercentage.textContent = `${progress}%`;
    elements.progressText.textContent = message;
    updateStatus(message);
}

// ========================================
// Result Handling
// ========================================
async function fetchResult(taskId) {
    try {
        updateProgress({ progress: 95, message: 'Fetching results...' });

        const response = await fetch(`/api/extract/${taskId}/result`);

        if (!response.ok) {
            throw new Error('Failed to fetch result');
        }

        const result = await response.json();
        showResult(result);

        updateProgress({ progress: 100, message: 'Complete!' });
        setExtractingState(false);
        updateStatus('Ready');
        setStatusSuccess(true);
        showToast('Extraction complete!', 'success');

        // Hide progress after a delay
        setTimeout(() => {
            hideProgress();
        }, 1000);

    } catch (error) {
        showToast(error.message, 'error');
        setExtractingState(false);
        hideProgress();
        updateStatus('Error');
        setStatusError(true);
    }
}

function showResult(result) {
    // Show result panel
    elements.emptyState.classList.add('hidden');
    elements.resultPanel.classList.remove('hidden');

    // Show prompt
    if (result.prompt) {
        elements.promptText.textContent = result.prompt;
    }

    // Show screenshot
    if (result.screenshot_url) {
        elements.screenshotImg.src = result.screenshot_url;
        elements.screenshotPreview.classList.remove('hidden');
        elements.noPreview.classList.add('hidden');
    } else {
        elements.screenshotImg.removeAttribute('src');
        elements.screenshotPreview.classList.add('hidden');
        elements.noPreview.classList.remove('hidden');
    }

    // Show download
    if (result.download_url) {
        elements.downloadPackageLink.href = result.download_url;
        elements.downloadPackageLink.setAttribute(
            'download',
            result.download_filename || 'component-extractor-package.zip'
        );
        elements.resultActions.classList.remove('hidden');
    } else {
        elements.downloadPackageLink.removeAttribute('href');
        elements.resultActions.classList.add('hidden');
    }

    // Show expiry
    if (result.expires_at) {
        elements.packageExpiry.textContent = `Expires ${formatExpiry(result.expires_at)}`;
    } else {
        elements.packageExpiry.textContent = '';
    }

    // Show JSON
    if (result.full_json) {
        elements.jsonText.textContent = JSON.stringify(result.full_json, null, 2);
    }

    // Show assets
    if (result.assets && result.assets.length > 0) {
        elements.assetsList.innerHTML = result.assets.map(asset => `
            <li>
                <span>
                    <strong>${asset.type}</strong>: ${asset.filename}
                </span>
                ${asset.url ? `<a href="${asset.url}" target="_blank" rel="noopener noreferrer">View</a>` : ''}
            </li>
        `).join('');
    } else {
        elements.assetsList.innerHTML = '<li class="no-assets">No assets extracted</li>';
    }

    // Switch to prompt tab
    switchTab('prompt');
}

// ========================================
// UI State Management
// ========================================
function setExtractingState(extracting) {
    isExtracting = extracting;
    elements.extractBtn.disabled = extracting;

    const btnSpan = elements.extractBtn.querySelector('span');
    if (btnSpan) {
        btnSpan.textContent = extracting ? 'Extracting...' : 'Extract Component';
    }

    // Add loading class for animation
    if (extracting) {
        elements.extractBtn.classList.add('loading');
    } else {
        elements.extractBtn.classList.remove('loading');
    }
}

function showProgress() {
    elements.progressSection.classList.remove('hidden');
}

function hideProgress() {
    elements.progressSection.classList.add('hidden');
    elements.progressFill.style.width = '0%';
}

function updateStatus(message) {
    elements.statusText.textContent = message;
}

function setStatusSuccess(success) {
    const dot = elements.statusIndicator.querySelector('.status-dot');
    if (success) {
        dot.style.background = 'var(--color-success)';
    }
}

function setStatusError(error) {
    const dot = elements.statusIndicator.querySelector('.status-dot');
    if (error) {
        dot.style.background = 'var(--color-error)';
        setTimeout(() => {
            dot.style.background = 'var(--color-success)';
        }, 3000);
    }
}

// ========================================
// Tab Navigation
// ========================================
function switchTab(tabName) {
    elements.tabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.dataset.content === tabName);
    });
}

// ========================================
// Clipboard
// ========================================
async function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;

    try {
        await navigator.clipboard.writeText(text);
        showToast('Copied to clipboard!', 'success');
    } catch (error) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('Copied to clipboard!', 'success');
    }
}

// ========================================
// Toast Notifications
// ========================================
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastSlideOut 0.3s ease forwards';
        setTimeout(() => {
            if (toast.parentNode) {
                container.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// ========================================
// Theme Management
// ========================================
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

// ========================================
// Utilities
// ========================================
function formatExpiry(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString(undefined, {
        dateStyle: 'short',
        timeStyle: 'short'
    });
}

function handleKeyboardShortcuts(event) {
    // Ctrl/Cmd + Enter to extract
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        if (!isExtracting) {
            startExtraction();
        }
    }

    // Escape to cancel (if we implement cancellation)
    if (event.key === 'Escape' && isExtracting) {
        // Could implement cancellation here
    }
}

// ========================================
// Animations & Micro-interactions
// ========================================

// Add ripple effect to buttons
document.addEventListener('click', function(e) {
    const button = e.target.closest('.cta-button, .download-button');
    if (!button) return;

    const ripple = document.createElement('span');
    ripple.style.cssText = `
        position: absolute;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
    `;

    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
    ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';

    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);

    setTimeout(() => ripple.remove(), 600);
});

// Add ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
