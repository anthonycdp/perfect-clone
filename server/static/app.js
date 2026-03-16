// Component Extractor Web UI - JavaScript Application

// State
let taskId = null;
let isExtracting = false;
let eventSource = null;

// DOM Elements
const urlInput = document.getElementById('url');
const queryInput = document.getElementById('query');
const extractBtn = document.getElementById('extract-btn');
const progressContainer = document.querySelector('.progress-container');
const progressFill = document.querySelector('.progress-fill');
const progressText = document.querySelector('.progress-text');
const resultPanel = document.querySelector('.result-panel');
const promptText = document.getElementById('prompt-text');
const jsonText = document.getElementById('json-text');
const assetsList = document.getElementById('assets-list');
const screenshotImg = document.getElementById('screenshot-img');
const screenshotPreview = document.querySelector('.screenshot-preview');
const statusText = document.getElementById('status');
const themeToggle = document.getElementById('theme-toggle');
const tabs = document.querySelectorAll('.tab');
const copyButtons = document.querySelectorAll('.btn-copy');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadTheme();
    bindEvents();
});

// Bind Events
function bindEvents() {
    extractBtn.addEventListener('click', startExtraction);
    themeToggle.addEventListener('click', toggleTheme);

    tabs.forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    copyButtons.forEach(btn => {
        btn.addEventListener('click', () => copyToClipboard(btn.dataset.copy));
    });

    // Update query placeholder based on strategy
    document.querySelectorAll('input[name="strategy"]').forEach(radio => {
        radio.addEventListener('change', updateQueryPlaceholder);
    });

    updateQueryPlaceholder();
}

// Update Query Placeholder
function updateQueryPlaceholder() {
    const strategy = document.querySelector('input[name="strategy"]:checked').value;
    const placeholders = {
        css: '.class-name or #id',
        xpath: '//div[@class="example"]',
        text: 'Text to search...',
        html_snippet: '<div class="example">...</div>'
    };
    queryInput.placeholder = placeholders[strategy] || 'Enter query...';
}

// Start Extraction
async function startExtraction() {
    const url = urlInput.value.trim();
    if (!url) {
        showToast('Please enter a URL', 'error');
        urlInput.focus();
        return;
    }

    const mode = document.querySelector('input[name="mode"]:checked').value;
    const strategy = document.querySelector('input[name="strategy"]:checked').value;
    const query = queryInput.value.trim();

    if (!query && strategy !== 'html_snippet') {
        showToast('Please enter a selector or query', 'error');
        queryInput.focus();
        return;
    }

    setExtractingState(true);
    showProgress();
    updateProgress({ progress: 0, message: 'Starting extraction...' });

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
    }
}

// Connect Progress Stream (SSE)
function connectProgressStream(taskId) {
    if (eventSource) {
        eventSource.close();
    }

    eventSource = new EventSource(`/api/progress/${taskId}`);

    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateProgress(data);

        if (data.status === 'completed') {
            eventSource.close();
            fetchResult(taskId);
        } else if (data.status === 'failed') {
            eventSource.close();
            showToast(data.message || 'Extraction failed', 'error');
            setExtractingState(false);
            hideProgress();
            updateStatus('Failed');
        }
    };

    eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        eventSource.close();
        showToast('Connection lost', 'error');
        setExtractingState(false);
        hideProgress();
        updateStatus('Error');
    };
}

// Update Progress
function updateProgress(data) {
    const progress = data.progress || 0;
    const message = data.message || 'Processing...';

    progressFill.style.width = `${progress}%`;
    progressText.textContent = message;
    updateStatus(message);
}

// Fetch Result
async function fetchResult(taskId) {
    try {
        updateProgress({ progress: 95, message: 'Fetching results...' });

        const response = await fetch(`/api/result/${taskId}`);

        if (!response.ok) {
            throw new Error('Failed to fetch result');
        }

        const result = await response.json();
        showResult(result);

        updateProgress({ progress: 100, message: 'Complete!' });
        setExtractingState(false);
        updateStatus('Ready');
        showToast('Extraction complete!', 'success');

    } catch (error) {
        showToast(error.message, 'error');
        setExtractingState(false);
        hideProgress();
        updateStatus('Error');
    }
}

// Show Result
function showResult(result) {
    resultPanel.classList.remove('hidden');

    // Show prompt
    if (result.prompt) {
        promptText.textContent = result.prompt;
    }

    // Show screenshot
    if (result.screenshot_base64) {
        screenshotImg.src = `data:image/png;base64,${result.screenshot_base64}`;
        screenshotPreview.classList.remove('hidden');
    } else {
        screenshotPreview.classList.add('hidden');
    }

    // Show JSON
    if (result.component_data) {
        jsonText.textContent = JSON.stringify(result.component_data, null, 2);
    }

    // Show assets
    if (result.assets && result.assets.length > 0) {
        assetsList.innerHTML = result.assets.map(asset => `
            <li>
                <span>${asset.type}: ${asset.filename}</span>
                <a href="${asset.path}" target="_blank">View</a>
            </li>
        `).join('');
    } else {
        assetsList.innerHTML = '<li>No assets extracted</li>';
    }

    // Switch to prompt tab
    switchTab('prompt');
}

// Set Extracting State
function setExtractingState(extracting) {
    isExtracting = extracting;
    extractBtn.disabled = extracting;
    extractBtn.textContent = extracting ? 'Extracting...' : 'Extract';
}

// Show/Hide Progress
function showProgress() {
    progressContainer.classList.remove('hidden');
}

function hideProgress() {
    progressContainer.classList.add('hidden');
    progressFill.style.width = '0%';
}

// Switch Tab
function switchTab(tabName) {
    tabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.dataset.content === tabName);
    });
}

// Copy to Clipboard
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
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('Copied to clipboard!', 'success');
    }
}

// Show Toast
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            container.removeChild(toast);
        }, 300);
    }, 3000);
}

// Update Status
function updateStatus(message) {
    statusText.textContent = message;
}

// Toggle Theme
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Load Theme
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
}
