// PullData Web UI JavaScript (NotebookLM Style)

const API_URL = 'http://localhost:8000';

// State
let currentProject = null;
let projects = [];
let configs = [];

// DOM Elements object
let elements = {};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('App initializing...');

    // Populate elements map
    elements = {
        projectsList: document.getElementById('projectsList'),
        projectName: document.getElementById('projectName'),
        createProjectBtn: document.getElementById('createProjectBtn'),
        refreshProjectsBtn: document.getElementById('refreshProjectsBtn'),

        // Ingest Modal & Form
        ingestModal: document.getElementById('ingestModal'),
        openIngestModalBtn: document.getElementById('openIngestModalBtn'),
        closeIngestModal: document.getElementById('closeIngestModal'),
        ingestProject: document.getElementById('ingestProject'),
        ingestConfig: document.getElementById('ingestConfig'),
        fileUpload: document.getElementById('fileUpload'),
        ingestBtn: document.getElementById('ingestBtn'),
        ingestStatus: document.getElementById('ingestStatus'),

        // Main Area
        currentProjectTitle: document.getElementById('currentProjectTitle'),
        activeProjectStats: document.getElementById('activeProjectStats'),
        statsDisplay: document.getElementById('statsDisplay'),
        notebookArea: document.getElementById('notebookArea'),
        emptyState: document.getElementById('emptyState'),

        // Query / Chat
        queryProject: document.getElementById('queryProject'),
        queryConfig: document.getElementById('queryConfig'),
        queryText: document.getElementById('queryText'),
        outputFormat: document.getElementById('outputFormat'),
        pdfStyleGroup: document.getElementById('pdfStyleGroup'), // For display toggle
        generateAnswer: document.getElementById('generateAnswer'),
        queryBtn: document.getElementById('queryBtn'),
        queryStatus: document.getElementById('queryStatus'),

        // Results
        resultsCard: document.getElementById('resultsCard'),
        answerText: document.getElementById('answerText'),
        sourcesCount: document.getElementById('sourcesCount'),
        sourcesList: document.getElementById('sourcesList'),
        outputFileSection: document.getElementById('outputFileSection'),
        outputFileLink: document.getElementById('outputFileLink'),

        // Theme
        themeCheckbox: document.getElementById('checkbox'),
        themeToggle: document.getElementById('themeToggle'),

        // Misc
        pdfStyle: document.getElementById('pdfStyle'),
        sidebarSourcesList: document.getElementById('sidebarSourcesList'),
        documentsModal: document.getElementById('documentsModal')
    };

    initTheme();
    checkHealth();
    loadProjects();
    loadConfigs();
    setupEventListeners();
    setupModals();
});

// Theme Functions
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    let theme = 'light';
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        theme = 'dark';
    }
    setTheme(theme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    const icon = theme === 'dark' ? 'light_mode' : 'dark_mode';
    if (elements.themeToggle) {
        elements.themeToggle.innerHTML = `<span class="material-symbols-outlined">${icon}</span>`;
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    setTheme(current === 'dark' ? 'light' : 'dark');
}

// Event Listeners
function setupEventListeners() {
    if (elements.themeToggle) {
        elements.themeToggle.addEventListener('click', toggleTheme);
    }

    elements.createProjectBtn.addEventListener('click', createProject);
    elements.refreshProjectsBtn.addEventListener('click', loadProjects);
    elements.ingestBtn.addEventListener('click', ingestDocuments);
    elements.queryBtn.addEventListener('click', queryDocuments);

    // Auto-resize textarea and proper Enter handling
    elements.queryText.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') this.style.height = 'auto';
    });

    elements.queryText.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            queryDocuments();
        }
    });

    // Documents Modal Logic Removed (View Documents button replaced by list)
    const closeModalBtn = elements.documentsModal.querySelector('.close');
    closeModalBtn.addEventListener('click', () => {
        elements.documentsModal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target === elements.documentsModal) elements.documentsModal.style.display = 'none';
        if (event.target === elements.ingestModal) elements.ingestModal.style.display = 'none';
    });

    // Show/hide PDF style selector
    elements.outputFormat.addEventListener('change', function () {
        if (this.value === 'styled_pdf') {
            elements.pdfStyleGroup.style.display = 'flex';
        } else {
            elements.pdfStyleGroup.style.display = 'none';
        }
    });
}

function setupModals() {
    // Ingest Modal
    elements.openIngestModalBtn.addEventListener('click', () => {
        elements.ingestModal.style.display = 'block';
    });

    elements.closeIngestModal.addEventListener('click', () => {
        elements.ingestModal.style.display = 'none';
    });
}

// API Functions
async function checkHealth() {
    try {
        await fetch(`${API_URL}/health`);
    } catch (error) {
        console.error('API Health check failed:', error);
    }
}

async function loadProjects() {
    try {
        const response = await fetch(`${API_URL}/projects`);
        const data = await response.json();
        projects = data.projects;
        updateProjectsUI();

        // Auto-select first project if exists and none selected
        if (!currentProject && projects.length > 0) {
            selectProject(projects[0]);
        }
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
    const configOptions = configs.map(config =>
        `<option value="${config.path}">${config.name}</option>`
    ).join('');

    elements.ingestConfig.innerHTML = `<option value="">Default (configs/default.yaml)</option>${configOptions}`;
    elements.queryConfig.innerHTML = `<option value="">Default Config</option>${configOptions}`;
}

function selectProject(projectName) {
    currentProject = projectName;
    updateProjectsUI();
    loadProjectStats(currentProject);
    loadSidebarSources(currentProject);

    // Reset Main Area
    elements.currentProjectTitle.textContent = currentProject;
    elements.resultsCard.style.display = 'none';
    elements.emptyState.style.display = 'block';
    elements.activeProjectStats.style.display = 'block';
}

function updateProjectsUI() {
    // Update sidebar list
    if (projects.length === 0) {
        elements.projectsList.innerHTML = '<p class="nav-item" style="cursor:default">No projects yet</p>';
    } else {
        elements.projectsList.innerHTML = projects.map(project => `
            <div class="nav-item ${project === currentProject ? 'active' : ''}"
                 onclick="selectProject('${project}')">
                <span class="material-symbols-outlined" style="margin-right:12px; font-size:1.2rem">
                    ${project === currentProject ? 'folder_open' : 'folder'}
                </span>
                ${project}
            </div>
        `).join('');
    }

    // Explicitly expose selectProject to window scope to use in onclick string above
    window.selectProject = selectProject;

    // Update hidden dropdowns for forms
    const projectOptions = projects.map(p =>
        `<option value="${p}" ${p === currentProject ? 'selected' : ''}>${p}</option>`
    ).join('');

    elements.ingestProject.innerHTML = projectOptions;
    elements.queryProject.innerHTML = projectOptions;

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

        // Show in sidebar
        elements.statsDisplay.textContent = `${stats.metadata_store?.document_count || 0} Sources • ${stats.metadata_store?.chunk_count || 0} Chunks`;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function loadSidebarSources(project) {
    const list = elements.sidebarSourcesList;
    list.innerHTML = '<div class="source-pill" style="justify-content:center; color:gray">Loading...</div>';

    try {
        const response = await fetch(`${API_URL}/projects/${project}/documents`);
        const data = await response.json();

        if (response.ok) {
            const docs = data.documents || [];
            if (docs.length === 0) {
                list.innerHTML = '<div style="padding:12px; text-align:center; color:gray; font-size:0.8rem">No sources yet</div>';
            } else {
                list.innerHTML = docs.map(doc => {
                    const fileName = doc.source.split(/[/\\]/).pop();
                    return `
                    <div class="source-pill" title="${escapeHtml(doc.title || fileName)}">
                        <span class="material-symbols-outlined" style="font-size:1rem; color: #1a73e8;">description</span>
                        <div style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:0.85rem;">
                            ${escapeHtml(fileName)}
                        </div>
                    </div>`;
                }).join('');
            }
        } else {
            list.innerHTML = `<div style="color:red; font-size:0.8rem">Error loading sources</div>`;
        }
    } catch (error) {
        list.innerHTML = `<div style="color:red; font-size:0.8rem">Failed to load</div>`;
        console.error(error);
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
    projects.push(projectName);
    selectProject(projectName);
    elements.projectName.value = '';
    // Hide form
    document.getElementById('newProjectForm').classList.add('hidden');
}

async function ingestDocuments() {
    const project = elements.ingestProject.value || currentProject;
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

    showStatus(elements.ingestStatus, `Uploading ${files.length} file(s)...`, 'info');
    elements.ingestBtn.disabled = true;

    try {
        const formData = new FormData();
        for (let file of files) {
            formData.append('files', file);
        }

        let url = `${API_URL}/ingest/upload?project=${project}`;
        if (configPath) url += `&config_path=${encodeURIComponent(configPath)}`;

        const response = await fetch(url, { method: 'POST', body: formData });
        const data = await response.json();

        if (response.ok) {
            showStatus(elements.ingestStatus, `Success! Processed ${data.stats.processed_files} files`, 'success');
            elements.fileUpload.value = '';

            // Reload stats and projects
            if (!projects.includes(project)) await loadProjects();
            loadProjectStats(project);
            loadSidebarSources(project);

            // Close modal after 1.5s
            setTimeout(() => {
                elements.ingestModal.style.display = 'none';
                elements.ingestStatus.style.display = 'none';
            }, 1500);

        } else {
            showStatus(elements.ingestStatus, `Error: ${data.detail}`, 'error');
        }
    } catch (error) {
        showStatus(elements.ingestStatus, `Failed: ${error.message}`, 'error');
    } finally {
        elements.ingestBtn.disabled = false;
    }
}

async function queryDocuments() {
    const project = elements.queryProject.value || currentProject;
    const configPath = elements.queryConfig.value;
    const query = elements.queryText.value.trim();
    const outputFormat = elements.outputFormat.value || null;
    const generateAnswer = elements.generateAnswer.checked;
    const pdfStyle = elements.pdfStyle.value;

    if (!project) {
        alert('Please select a project first');
        return;
    }
    if (!query) return;

    // UI Updates for Loading
    elements.emptyState.style.display = 'none';
    elements.resultsCard.style.display = 'block';

    // Clear previous results or show loading state
    elements.answerText.innerHTML = '<div class="typing-indicator">Thinking...</div>';
    elements.sourcesList.innerHTML = '';

    // Scroll to bottom
    elements.notebookArea.scrollTo(0, elements.notebookArea.scrollHeight);

    elements.queryBtn.disabled = true;

    try {
        const requestBody = {
            project,
            query,
            k: 5,
            generate_answer: generateAnswer,
            output_format: outputFormat,
        };

        if (outputFormat === 'styled_pdf') requestBody.pdf_style = pdfStyle;
        if (configPath) requestBody.config_path = configPath;

        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
        });

        const data = await response.json();

        if (response.ok) {
            displayResults(data);
            // Clear input
            elements.queryText.value = '';
            elements.queryText.style.height = 'auto';
        } else {
            elements.answerText.textContent = `Error: ${data.detail}`;
        }
    } catch (error) {
        elements.answerText.textContent = `Failed to query: ${error.message}`;
    } finally {
        elements.queryBtn.disabled = false;
    }
}

function displayResults(data) {
    elements.resultsCard.style.display = 'block';

    // Display Answer
    if (data.answer) {
        elements.answerText.innerHTML = marked.parse(data.answer);
    } else {
        elements.answerText.textContent = 'No text answer generated.';
        elements.answerText.style.fontStyle = 'italic';
    }

    // Display File Link
    if (data.output_path) {
        elements.outputFileSection.style.display = 'block';
        const filename = data.output_path.split(/[/\\]/).pop();
        elements.outputFileLink.href = `${API_URL}/output/${data.project || 'unknown'}/${filename}`;
        elements.outputFileLink.innerHTML = `<span class="material-symbols-outlined">download</span> Download ${filename}`;
    } else {
        elements.outputFileSection.style.display = 'none';
    }

    // Display Sources
    elements.sourcesCount.textContent = data.sources.length;

    if (data.sources.length === 0) {
        elements.sourcesList.innerHTML = '<p style="color:var(--md-sys-color-secondary)">No relevant sources found.</p>';
    } else {
        elements.sourcesList.innerHTML = data.sources.map((source, index) => `
            <div class="citation-card">
                 <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em;">
                    <span>Source ${index + 1} ${source.page_number ? ` • Page ${source.page_number}` : ''}</span>
                    <span style="color:var(--md-sys-color-primary)">${(source.score * 100).toFixed(0)}% Match</span>
                 </div>
                 <div class="citation-text" style="line-height:1.5;">${escapeHtml(source.text)}</div>
            </div>
        `).join('');
    }

    // Scroll to new content
    setTimeout(() => {
        elements.notebookArea.scrollTo({ top: elements.notebookArea.scrollHeight, behavior: 'smooth' });
    }, 100);
}

// document modal logic
async function openDocumentsModal(project) {
    const container = document.getElementById('documentsListContainer');
    elements.documentsModal.style.display = 'block';
    container.innerHTML = '<p>Loading...</p>';

    try {
        const response = await fetch(`${API_URL}/projects/${project}/documents`);
        const data = await response.json();
        if (response.ok) {
            if (!data.documents || data.documents.length === 0) {
                container.innerHTML = '<p>No documents found.</p>';
                return;
            }
            container.innerHTML = data.documents.map(doc => {
                const fileName = doc.source.split(/[/\\]/).pop();
                return `
                    <div style="padding:12px; border-bottom:1px solid var(--md-sys-color-outline-variant); display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:500;">${escapeHtml(doc.title || fileName)}</div>
                            <div style="font-size:0.85rem; color:var(--md-sys-color-secondary);">
                                ${fileName} • ${doc.page_count || 0} Pages • ${new Date(doc.ingested_at).toLocaleDateString()}
                            </div>
                        </div>
                        <span class="material-symbols-outlined" style="color:var(--md-sys-color-secondary)">description</span>
                    </div>
                 `;
            }).join('');
        } else {
            container.innerHTML = `<p style="color:red">Error: ${data.detail}</p>`;
        }
    } catch (error) {
        container.innerHTML = `<p style="color:red">Failed: ${error.message}</p>`;
    }
}

// Utilities
function showStatus(element, message, type) {
    element.style.display = 'block';
    element.textContent = message;
    element.className = `status-message ${type}`;
}

function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
