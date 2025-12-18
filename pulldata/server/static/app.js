// PullData Web UI JavaScript

const API_URL = 'http://localhost:8000';

// State
let currentProject = null;
let projects = [];

// DOM Elements
const elements = {
    projectsList: document.getElementById('projectsList'),
    projectName: document.getElementById('projectName'),
    createProjectBtn: document.getElementById('createProjectBtn'),
    refreshProjectsBtn: document.getElementById('refreshProjectsBtn'),
    ingestProject: document.getElementById('ingestProject'),
    queryProject: document.getElementById('queryProject'),
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
    statsDisplay: document.getElementById('statsDisplay'),
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadProjects();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    elements.createProjectBtn.addEventListener('click', createProject);
    elements.refreshProjectsBtn.addEventListener('click', loadProjects);
    elements.ingestBtn.addEventListener('click', ingestDocuments);
    elements.queryBtn.addEventListener('click', queryDocuments);
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

        const response = await fetch(`${API_URL}/ingest/upload?project=${project}`, {
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
    const query = elements.queryText.value.trim();
    const outputFormat = elements.outputFormat.value || null;
    const generateAnswer = elements.generateAnswer.checked;

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
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project,
                query,
                k: 5,
                generate_answer: generateAnswer,
                output_format: outputFormat,
            }),
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
