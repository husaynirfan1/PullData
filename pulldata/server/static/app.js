// PullData Web UI JavaScript

const API_URL = 'http://localhost:8000';

// State
let currentProject = null;
let projects = [];
let configs = [];

// DOM Elements object (populated on init)
let elements = {};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('App initializing...');

    // Populate elements
    elements = {
        projectsList: document.getElementById('projectsList'),
        projectName: document.getElementById('projectName'),
        createProjectBtn: document.getElementById('createProjectBtn'),
        refreshProjectsBtn: document.getElementById('refreshProjectsBtn'),
        ingestProject: document.getElementById('ingestProject'),
        ingestConfig: document.getElementById('ingestConfig'),
        queryProject: document.getElementById('queryProject'),
        queryConfig: document.getElementById('queryConfig'),
        fileUpload: document.getElementById('fileUpload'),
        ingestBtn: document.getElementById('ingestBtn'),
        ingestStatus: document.getElementById('ingestStatus'),
        queryText: document.getElementById('queryText'),
        outputFormat: document.getElementById('outputFormat'),
        generateAnswer: document.getElementById('generateAnswer'),
        queryBtn: document.getElementById('queryBtn'),
        queryStatus: document.getElementById('queryStatus'),
        resultsCard: document.getElementById('resultsCard'),
        answerText: document.getElementById('answerText'),
        sourcesCount: document.getElementById('sourcesCount'),
        sourcesList: document.getElementById('sourcesList'),
        outputFileSection: document.getElementById('outputFileSection'),
        outputFileLink: document.getElementById('outputFileLink'),
        themeCheckbox: document.getElementById('checkbox'),
    };

    console.log('Elements loaded. Checkbox found:', !!elements.themeCheckbox);

    initTheme();
    checkHealth();
    loadProjects();
    loadConfigs();
    setupEventListeners();
});

// Theme Functions
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    // Default to light if no preference
    let theme = 'light';
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        theme = 'dark';
    }

    setTheme(theme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    // Update checkbox state
    if (elements.themeCheckbox) {
        elements.themeCheckbox.checked = (theme === 'dark');
    }
    console.log(`Theme set to: ${theme}`);
}

function toggleTheme(e) {
    if (e.target.checked) {
        setTheme('dark');
    } else {
        setTheme('light');
    }
}

// Event Listeners
function setupEventListeners() {
    if (elements.themeCheckbox) {
        elements.themeCheckbox.addEventListener('change', toggleTheme);
    }

    elements.createProjectBtn.addEventListener('click', createProject);
    elements.refreshProjectsBtn.addEventListener('click', loadProjects);
    elements.ingestBtn.addEventListener('click', ingestDocuments);
    elements.queryBtn.addEventListener('click', queryDocuments);

    // Show/hide PDF style selector based on output format
    elements.outputFormat.addEventListener('change', function() {
        const pdfStyleGroup = document.getElementById('pdfStyleGroup');
        if (this.value === 'styled_pdf') {
            pdfStyleGroup.style.display = 'block';
        } else {
            pdfStyleGroup.style.display = 'none';
        }
    });
}

// API Functions
async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        console.log('API Health:', data);
    } catch (error) {
        showStatus(elements.queryStatus, 'Cannot connect to API server', 'error');
        console.error('API Health check failed:', error);
    }
}

async function loadProjects() {
    try {
        const response = await fetch(`${API_URL}/projects`);
        const data = await response.json();
        projects = data.projects;
        updateProjectsUI();
    } catch (error) {
        console.error('Failed to load projects:', error);
    }
}

async function loadConfigs() {
    try {
        const response = await fetch(`${API_URL}/configs`);
        const data = await response.json();
        configs = data.configs;
        updateConfigsUI();
    } catch (error) {
        console.error('Failed to load configs:', error);
    }
}

function updateConfigsUI() {
    // Build config options
    const configOptions = configs.map(config =>
        `<option value="${config.path}">${config.name}</option>`
    ).join('');

    // Update ingest config dropdown
    elements.ingestConfig.innerHTML = `
        <option value="">Default (configs/default.yaml)</option>
        ${configOptions}
    `;

    // Update query config dropdown
    elements.queryConfig.innerHTML = `
        <option value="">Use project default</option>
        ${configOptions}
    `;
}

function updateProjectsUI() {
    // Update sidebar list
    if (projects.length === 0) {
        elements.projectsList.innerHTML = '<p class="placeholder">No projects yet</p>';
    } else {
        elements.projectsList.innerHTML = projects.map(project => `
            <div class="project-item ${project === currentProject ? 'active' : ''}"
                 data-project="${project}">
                ${project}
            </div>
        `).join('');

        // Add click handlers
        document.querySelectorAll('.project-item').forEach(item => {
            item.addEventListener('click', () => {
                currentProject = item.dataset.project;
                updateProjectsUI();
                loadProjectStats(currentProject);
            });
        });
    }

    // Update dropdowns
    const projectOptions = projects.map(p =>
        `<option value="${p}" ${p === currentProject ? 'selected' : ''}>${p}</option>`
    ).join('');

    elements.ingestProject.innerHTML = `<option value="">Select project...</option>${projectOptions}`;
    elements.queryProject.innerHTML = `<option value="">Select project...</option>${projectOptions}`;

    if (currentProject) {
        elements.ingestProject.value = currentProject;
        elements.queryProject.value = currentProject;
    }
}

async function loadProjectStats(project) {
    try {
        const response = await fetch(`${API_URL}/projects/${project}/stats`);
        const data = await response.json();

        const stats = data.stats;
        elements.statsDisplay.innerHTML = `
            <strong>${project}</strong><br>
            Docs: ${stats.metadata_store?.document_count || 0}<br>
            Chunks: ${stats.metadata_store?.chunk_count || 0}
        `;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

function createProject() {
    const projectName = elements.projectName.value.trim();
    if (!projectName) {
        alert('Please enter a project name');
        return;
    }

    if (projects.includes(projectName)) {
        alert('Project already exists');
        return;
    }

    // Just add to UI - it will be created on first ingest/query
    projects.push(projectName);
    currentProject = projectName;
    elements.projectName.value = '';
    updateProjectsUI();
}

async function ingestDocuments() {
    const project = elements.ingestProject.value;
    const configPath = elements.ingestConfig.value;
    const files = elements.fileUpload.files;

    if (!project) {
        showStatus(elements.ingestStatus, 'Please select a project', 'error');
        return;
    }

    if (files.length === 0) {
        showStatus(elements.ingestStatus, 'Please select files to upload', 'error');
        return;
    }

    showStatus(elements.ingestStatus, `Uploading and ingesting ${files.length} file(s)...`, 'info');
    elements.ingestBtn.disabled = true;

    try {
        const formData = new FormData();
        for (let file of files) {
            formData.append('files', file);
        }

        // Build URL with optional config_path
        let url = `${API_URL}/ingest/upload?project=${project}`;
        if (configPath) {
            url += `&config_path=${encodeURIComponent(configPath)}`;
        }

        const response = await fetch(url, {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(
                elements.ingestStatus,
                `Success! Processed ${data.stats.processed_files} files, created ${data.stats.new_chunks} chunks`,
                'success'
            );
            elements.fileUpload.value = '';

            // Refresh projects if new
            if (!projects.includes(project)) {
                await loadProjects();
            } else if (project === currentProject) {
                loadProjectStats(project);
            }
        } else {
            showStatus(elements.ingestStatus, `Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showStatus(elements.ingestStatus, `Failed to ingest: ${error.message}`, 'error');
    } finally {
        elements.ingestBtn.disabled = false;
    }
}

async function queryDocuments() {
    const project = elements.queryProject.value;
    const configPath = elements.queryConfig.value;
    const query = elements.queryText.value.trim();
    const outputFormat = elements.outputFormat.value || null;
    const generateAnswer = elements.generateAnswer.checked;
    const pdfStyle = document.getElementById('pdfStyle').value;

    if (!project) {
        showStatus(elements.queryStatus, 'Please select a project', 'error');
        return;
    }

    if (!query) {
        showStatus(elements.queryStatus, 'Please enter a query', 'error');
        return;
    }

    showStatus(elements.queryStatus, 'Querying...', 'info');
    elements.queryBtn.disabled = true;
    elements.resultsCard.style.display = 'none';

    try {
        const requestBody = {
            project,
            query,
            k: 5,
            generate_answer: generateAnswer,
            output_format: outputFormat,
        };

        // Add pdf_style if styled_pdf format is selected
        if (outputFormat === 'styled_pdf') {
            requestBody.pdf_style = pdfStyle;
        }

        // Add config_path if specified
        if (configPath) {
            requestBody.config_path = configPath;
        }

        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(elements.queryStatus, 'Query successful!', 'success');
            displayResults(data);
        } else {
            showStatus(elements.queryStatus, `Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showStatus(elements.queryStatus, `Failed to query: ${error.message}`, 'error');
    } finally {
        elements.queryBtn.disabled = false;
    }
}

function displayResults(data) {
    // Show results card
    elements.resultsCard.style.display = 'block';

    // Display answer
    if (data.answer) {
        elements.answerText.textContent = data.answer;
    } else {
        elements.answerText.textContent = 'No answer generated';
        elements.answerText.style.fontStyle = 'italic';
        elements.answerText.style.color = '#999';
    }

    // Display output file link
    if (data.output_path) {
        elements.outputFileSection.style.display = 'block';
        const filename = data.output_path.split(/[/\\]/).pop();
        elements.outputFileLink.href = `${API_URL}/output/${data.project || 'unknown'}/${filename}`;
        elements.outputFileLink.textContent = `📄 Download ${filename}`;
    } else {
        elements.outputFileSection.style.display = 'none';
    }

    // Display sources
    elements.sourcesCount.textContent = data.sources.length;

    if (data.sources.length === 0) {
        elements.sourcesList.innerHTML = '<p class="placeholder">No sources found</p>';
    } else {
        elements.sourcesList.innerHTML = data.sources.map((source, index) => `
            <div class="source-item">
                <div class="source-header">
                    <span>
                        <strong>Source ${index + 1}</strong>
                        ${source.page_number ? ` • Page ${source.page_number}` : ''}
                    </span>
                    <span class="source-score">${(source.score * 100).toFixed(1)}%</span>
                </div>
                <div class="source-text">${escapeHtml(source.text)}</div>
            </div>
        `).join('');
    }

    // Scroll to results
    elements.resultsCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Utility Functions
function showStatus(element, message, type) {
    element.textContent = message;
    element.className = `status-message ${type}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
