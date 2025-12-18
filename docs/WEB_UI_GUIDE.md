# PullData Web UI & API Guide

Complete guide for using PullData's Web UI and REST API.

## Quick Start

### Start the Server

```bash
# Activate virtual environment
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Start server
python run_server.py
```

Server will start on **http://localhost:8000**

### Access Points

- **Web UI**: http://localhost:8000/ui/
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Web UI

### Features

The Web UI provides a modern, elegant interface with:
- ✨ **Gemini-inspired design** with Playfair Display and Roboto fonts
- 🌓 **Dark/Light theme toggle** (respects system preferences, persists across sessions)
- ✅ Creating and managing projects with real-time statistics
- ⚙️ **Configuration selection** for embeddings and LLM settings
- ✅ Uploading and ingesting documents (PDF, TXT, MD)
- ✅ **Viewing ingested documents** with metadata (NEW!)
- ✅ Querying documents with LLM
- ✅ Generating deliverable outputs (Excel, PDF, PowerPoint, Markdown, JSON)
- ✅ Real-time results display with source citations
- ✅ Downloading generated files
- 📱 Responsive design that works on all screen sizes

### Using the Web UI

#### 1. Create a Project

1. Enter a project name in the sidebar
2. Click "Create"
3. The project appears in the projects list

#### 2. Ingest Documents

1. Select your project from the dropdown
2. **(Optional)** Choose a configuration file for embeddings/LLM settings
   - Default: uses `configs/default.yaml`
   - Custom: select from available configs (e.g., `lm_studio`, `openai`)
3. Click "Choose Files" and select PDF/TXT/MD files
4. Click "Ingest Documents"
5. Wait for processing (progress shown in status message)

#### 3. Query Documents

1. Select your project
2. **(Optional)** Choose a configuration to override project defaults
   - Useful for testing different LLMs or settings
3. Enter your query (e.g., "What are the key findings?")
4. Choose an output format (optional):
   - Excel (.xlsx) - Spreadsheet format
   - Markdown (.md) - Document format
   - JSON (.json) - Structured data
   - PowerPoint (.pptx) - Presentation
   - PDF (.pdf) - Basic report format
   - **Styled PDF (.pdf) ✨** - Professional styled report (NEW!)
     - Automatically structures content using LLM
     - Three visual styles available:
       - **Executive**: Clean & minimal (perfect for executives)
       - **Modernist**: Bold & impactful (great for presentations)
       - **Academic**: Traditional & formal (ideal for research)
5. Toggle "Generate LLM Answer" if needed
6. Click "Query"

#### 4. View Results

Results display:
- **Answer**: LLM-generated response
- **Generated File**: Download link (if output format selected)
- **Sources**: Retrieved chunks with similarity scores

---

## Styled PDF Reports

### Overview

The **Styled PDF** feature uses AI to transform raw query results into professional, well-structured reports with three distinct visual styles.

### How It Works

1. **Query documents** as normal
2. **Select "Styled PDF"** as output format
3. **Choose a style**:
   - **Executive**: Clean, minimalist design with blue/grey palette
   - **Modernist**: Bold typography with high-contrast dark accents
   - **Academic**: Traditional serif fonts with two-column layout
4. **Submit query**
5. **LLM automatically structures** the content into:
   - Title and summary
   - Key metrics (if present in data)
   - Organized sections with headings
   - Source citations

### Visual Style Comparison

| Feature | Executive | Modernist | Academic |
|---------|-----------|-----------|----------|
| **Font** | Sans-serif (clean) | Sans-serif (bold) | Serif (traditional) |
| **Layout** | Single column | Asymmetric | Two-column |
| **Best For** | Board meetings | Marketing | Research papers |
| **Tone** | Professional | Impactful | Scholarly |

### Example Workflow

```
1. Select project: "financial_reports"
2. Enter query: "What were Q3 2024 results?"
3. Output format: "Styled PDF"
4. PDF Style: "Executive"
5. Click "Query"
6. Download professional report with:
   - Executive summary
   - Key metrics (Revenue, Growth, etc.)
   - Organized findings
   - Source references
```

### Tips

- **Executive style**: Best for time-sensitive reports to leadership
- **Modernist style**: Use when you want to make a strong visual impression
- **Academic style**: Ideal for detailed technical or research documentation
- **LLM requirement**: Styled PDFs require an LLM to be configured (works with OpenAI, LM Studio, Ollama, etc.)

---

## REST API

### Base URL

```
http://localhost:8000
```

### Authentication

Currently no authentication required (development mode).

---

### Endpoints

#### 1. List Available Configs

**GET** `/configs`

List all configuration files in the `configs/` directory.

**Response:**
```json
{
  "configs": [
    {
      "name": "default",
      "path": "configs/default.yaml",
      "filename": "default.yaml"
    },
    {
      "name": "lm_studio",
      "path": "configs/lm_studio.yaml",
      "filename": "lm_studio.yaml"
    }
  ],
  "count": 2
}
```

---

#### 2. Health Check

**GET** `/health`

Check API server status.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

#### 3. List Projects

**GET** `/projects`

List all active projects.

**Response:**
```json
{
  "projects": ["project1", "project2"],
  "count": 2
}
```

---

#### 4. Get Project Statistics

**GET** `/projects/{project}/stats`

Get statistics for a specific project.

**Response:**
```json
{
  "project": "my_project",
  "stats": {
    "metadata_store": {
      "document_count": 5,
      "chunk_count": 127
    },
    "vector_store": {
      "total_vectors": 127
    }
  }
}
```

---

#### 5. Ingest Documents

**POST** `/ingest`

Ingest documents from a file path.

**Request Body:**
```json
{
  "project": "my_project",
  "source_path": "/path/to/documents/*.pdf",
  "config_path": "configs/lm_studio.yaml",
  "metadata": {
    "department": "Finance",
    "year": 2024
  }
}
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "processed_files": 3,
    "new_chunks": 45,
    "total_chunks": 45,
    "skipped_chunks": 0
  },
  "message": "Successfully ingested 3 files"
}
```

---

#### 6. Upload and Ingest

**POST** `/ingest/upload?project={project_name}&config_path={config_path}`

Upload and ingest files directly.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: files (multiple file upload)

**cURL Example:**
```bash
# Without config (uses default)
curl -X POST "http://localhost:8000/ingest/upload?project=my_project" \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf"

# With config
curl -X POST "http://localhost:8000/ingest/upload?project=my_project&config_path=configs/lm_studio.yaml" \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf"
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_files": 2,
    "processed_files": 2,
    "new_chunks": 32
  },
  "message": "Successfully ingested 2 files"
}
```

---

#### 7. Query Documents

**POST** `/query`

Query documents and optionally generate formatted output.

**Request Body:**
```json
{
  "project": "my_project",
  "query": "What are the Q3 revenue figures?",
  "k": 5,
  "generate_answer": true,
  "output_format": "styled_pdf",
  "pdf_style": "executive",
  "config_path": "configs/lm_studio.yaml",
  "filters": {
    "department": "Finance"
  }
}
```

**Parameters:**
- `project` (required): Project name
- `query` (required): Query text
- `k` (optional): Number of results to retrieve (default: 5)
- `generate_answer` (optional): Generate LLM answer (default: true)
- `output_format` (optional): Output format (`excel`, `markdown`, `json`, `powerpoint`, `pdf`, `styled_pdf`)
- `pdf_style` (optional): PDF style for `styled_pdf` format - `executive`, `modernist`, or `academic` (default: `executive`)
- `config_path` (optional): Path to config YAML file (overrides project default)
- `filters` (optional): Metadata filters

**Styled PDF Example:**
```json
{
  "project": "financial_reports",
  "query": "Summarize Q3 2024 performance",
  "output_format": "styled_pdf",
  "pdf_style": "executive"
}
```

**Response:**
```json
{
  "query": "What are the Q3 revenue figures?",
  "answer": "According to the Q3 financial report, total revenue was $10.5M...",
  "sources": [
    {
      "document_id": "doc_report_2024",
      "chunk_id": "chunk-doc-0",
      "text": "Q3 2024 Revenue: $10.5M representing a 15% increase...",
      "score": 0.89,
      "page_number": 3
    }
  ],
  "output_path": "./output/my_project_query_1234567890.xlsx",
  "metadata": {}
}
```

---

#### 8. List Project Documents

**GET** `/projects/{project}/documents`

List all documents ingested into a project.

**Query Parameters:**
- `limit` (optional): Maximum number of documents to return
- `offset` (optional): Number of documents to skip (default: 0)

**Response:**
```json
{
  "project": "my_project",
  "documents": [
    {
      "id": "doc_financial_report_2024",
      "source": "/path/to/financial_report_2024.pdf",
      "title": "Annual Financial Report 2024",
      "file_type": "pdf",
      "ingested_at": "2024-12-18T12:30:45",
      "page_count": 45,
      "metadata": {}
    }
  ],
  "count": 1
}
```

---

#### 9. Download Output File

**GET** `/output/{project}/{filename}`

Download a generated output file.

**Example:**
```
GET http://localhost:8000/output/my_project/my_project_query_1234567890.xlsx
```

**Response:** File download

---

#### 10. Delete Project

**DELETE** `/projects/{project}`

Close and remove a project from memory.

**Response:**
```json
{
  "success": true,
  "message": "Project 'my_project' closed and removed"
}
```

---

## Python Client Example

```python
import requests

API_URL = "http://localhost:8000"

# 1. Upload and ingest documents
files = [
    ('files', open('report1.pdf', 'rb')),
    ('files', open('report2.pdf', 'rb'))
]
response = requests.post(
    f"{API_URL}/ingest/upload?project=financial_reports",
    files=files
)
print(response.json())

# 2. Query with Excel output
response = requests.post(
    f"{API_URL}/query",
    json={
        "project": "financial_reports",
        "query": "What was the Q3 revenue?",
        "output_format": "excel"
    }
)
result = response.json()

print(f"Answer: {result['answer']}")
print(f"Excel file: {result['output_path']}")

# 3. Download the Excel file
filename = result['output_path'].split('/')[-1]
file_response = requests.get(
    f"{API_URL}/output/financial_reports/{filename}"
)
with open('downloaded_report.xlsx', 'wb') as f:
    f.write(file_response.content)
```

---

## JavaScript/Fetch Example

```javascript
const API_URL = 'http://localhost:8000';

// Upload and ingest
async function uploadDocuments(project, files) {
    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }

    const response = await fetch(
        `${API_URL}/ingest/upload?project=${project}`,
        {
            method: 'POST',
            body: formData
        }
    );

    return await response.json();
}

// Query
async function queryDocuments(project, query, outputFormat) {
    const response = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            project,
            query,
            output_format: outputFormat
        })
    });

    return await response.json();
}

// Usage
const result = await queryDocuments(
    'my_project',
    'What is the revenue?',
    'excel'
);
console.log('Answer:', result.answer);
console.log('File:', result.output_path);
```

---

## Changing Embeddings/LLM Settings

Before starting the server, you can configure which embedding and LLM models to use:

### Option 1: Edit Default Config

```bash
# Edit configs/default.yaml before starting server
notepad configs/default.yaml  # Windows
nano configs/default.yaml     # Linux/Mac

# Then start server
python run_server.py
```

### Option 2: Create Custom Configs

```bash
# Copy and edit for different setups
cp configs/default.yaml configs/lm_studio.yaml
notepad configs/lm_studio.yaml

# Select in Web UI dropdown when ingesting/querying
```

### Example: LM Studio API Config

Edit `configs/lm_studio.yaml`:

```yaml
models:
  embedder:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      model: nomic-embed-text-v1.5
      api_key: sk-dummy

  llm:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      model: qwen2.5-3b-instruct
      api_key: sk-dummy
```

See [Configuration Guide](CONFIG_GUIDE.md) for detailed config options.

---

## Server Configuration

### Change Server Port

Edit `run_server.py`:

```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=9000,  # Change port here
    log_level="info",
)
```

### Enable HTTPS

For production, use a reverse proxy (nginx, Apache) with SSL certificates.

---

## Troubleshooting

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### CORS Errors

If accessing from a different domain, update CORS settings in `pulldata/server/api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specify origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Module Not Found

```bash
# Ensure dependencies are installed
pip install fastapi uvicorn python-multipart

# Or install all dependencies
pip install -r requirements.txt
```

---

## Production Deployment

### Using Gunicorn (Linux)

```bash
pip install gunicorn

gunicorn pulldata.server.api:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.9

WORKDIR /app
COPY . /app

RUN pip install -e .

EXPOSE 8000

CMD ["python", "run_server.py"]
```

Build and run:

```bash
docker build -t pulldata-server .
docker run -p 8000:8000 pulldata-server
```

---

## Security Considerations

⚠️ **Important for Production:**

1. **Add Authentication**: Implement API key or JWT authentication
2. **Rate Limiting**: Prevent abuse with rate limiting
3. **Input Validation**: Validate all user inputs
4. **HTTPS Only**: Use HTTPS in production
5. **CORS**: Restrict to known origins
6. **File Upload Limits**: Set maximum file sizes
7. **Sandboxing**: Isolate file processing

---

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

Features:
- Test endpoints directly in browser
- View request/response schemas
- Copy cURL commands

---

## See Also

- **[Configuration Guide](CONFIG_GUIDE.md)** - Detailed config examples for LM Studio, OpenAI, Ollama, etc.
- **[API Configuration](API_CONFIGURATION.md)** - API provider setup details
- **[Features Status](FEATURES_STATUS.md)** - Current feature status

---

**Last Updated:** 2024-12-18
**Version:** 0.1.0
