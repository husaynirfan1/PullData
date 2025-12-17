# PullData Quick Start Guide

This guide will get you up and running with PullData in under 5 minutes.

## Prerequisites

- Python 3.9 or higher
- 8GB RAM minimum (16GB recommended)
- Optional: NVIDIA GPU with CUDA support (Tesla P4 or better)

## Installation

### 1. Clone and Setup

```bash
# Navigate to project directory
cd PullData

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install PullData
pip install -e .
```

### 2. Configure (Optional)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional)
# Default settings work out-of-box for local mode
```

## Basic Usage

### Option 1: Python API (Recommended)

```python
from pulldata import PullData

# Initialize with default local storage
rag = PullData(project="quickstart")

# Ingest documents
rag.ingest("path/to/your/documents/*.pdf")

# Query and generate Excel
result = rag.query(
    query="What are the key financial metrics?",
    output_format="excel"
)

# Save output
result.save("financial_metrics.xlsx")
```

### Option 2: Command Line

```bash
# Initialize a project
pulldata init --project quickstart

# Ingest documents
pulldata ingest --project quickstart --path ./documents/

# Query with Excel output
pulldata query \
  --project quickstart \
  --query "What are the key financial metrics?" \
  --output excel \
  --save financial_metrics.xlsx

# Query with Markdown output
pulldata query \
  --project quickstart \
  --query "Summarize the main findings" \
  --output markdown \
  --save summary.md
```

## Configuration

### LLM Model Selection

Choose between local models or API endpoints:

#### Option A: Local Model (Default)
```yaml
# configs/default.yaml
models:
  llm:
    provider: local
    local:
      name: Qwen/Qwen2.5-3B-Instruct
      quantization: int8
      device: cuda
```

#### Option B: LM Studio (Recommended for No GPU)
```yaml
models:
  llm:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      api_key: sk-dummy
      model: local-model
```

#### Option C: OpenAI or Other Cloud APIs
```yaml
models:
  llm:
    provider: api
    api:
      base_url: https://api.openai.com/v1
      api_key: ${OPENAI_API_KEY}  # Set in .env
      model: gpt-3.5-turbo
```

**See [API Configuration Guide](docs/API_CONFIGURATION.md) for complete setup instructions.**

### Storage Backends

PullData supports three storage backends:

#### Local (Default - Zero Config)
```yaml
# configs/default.yaml
storage:
  backend: local
  local:
    sqlite_path: ./data/pulldata.db
    faiss_index_path: ./data/faiss_indexes
```

#### PostgreSQL (Production)
```yaml
storage:
  backend: postgres
  postgres:
    host: localhost
    port: 5432
    database: pulldata
    user: pulldata_user
    password: ${POSTGRES_PASSWORD}
```

#### ChromaDB (Standalone)
```yaml
storage:
  backend: chromadb
  chromadb:
    persist_directory: ./data/chroma_db
```

### Model Selection

Choose models based on your hardware:

#### Tesla P4 (8GB VRAM) - Default
```yaml
models:
  embedder:
    name: BAAI/bge-small-en-v1.5
  llm:
    name: Qwen/Qwen2.5-3B-Instruct
    quantization: int8
```

#### CPU Only
```yaml
models:
  embedder:
    name: BAAI/bge-small-en-v1.5
    device: cpu
  llm:
    name: Qwen/Qwen2.5-3B-Instruct
    quantization: int8
    device: cpu
```

#### High-End GPU (24GB+)
```yaml
models:
  embedder:
    name: BAAI/bge-large-en-v1.5
  llm:
    name: Qwen/Qwen2.5-7B-Instruct
    quantization: fp16
```

## Output Formats

### Excel
```python
result = rag.query(
    query="Extract revenue by region",
    output_format="excel"
)
result.save("revenue.xlsx")
```

### Markdown
```python
result = rag.query(
    query="Summarize key findings",
    output_format="markdown"
)
result.save("summary.md")
```

### JSON
```python
result = rag.query(
    query="Extract structured data",
    output_format="json"
)
result.save("data.json")
```

### PowerPoint
```python
result = rag.query(
    query="Create presentation slides",
    output_format="pptx"
)
result.save("presentation.pptx")
```

## Advanced Features

### Metadata Filtering

```python
result = rag.query(
    query="Revenue trends",
    filters={
        "doc_type": "financial_report",
        "date_range": ("2024-01-01", "2024-12-31"),
        "tags": ["quarterly", "audited"],
        "page_number": 5
    }
)
```

### Differential Updates

```python
# First ingest (full processing)
rag.ingest("report.pdf")

# Update document (only changed content re-processed)
rag.ingest("report.pdf")  # Much faster!
```

### Multi-Project Management

```python
# Separate projects for different document collections
finance = PullData(project="finance")
legal = PullData(project="legal")

finance.ingest("financial_docs/*.pdf")
legal.ingest("legal_docs/*.pdf")

# Each project has isolated storage
```

### Cache Benefits

```python
# First query (LLM inference ~2s)
result1 = rag.query("What's Q3 revenue?")

# Same query (cache hit ~0.01s)
result2 = rag.query("What's Q3 revenue?")
```

## Troubleshooting

### Out of Memory
```yaml
# Reduce batch size in configs/default.yaml
performance:
  batch_size: 16  # Default: 32
  max_memory_gb: 6  # For P4: 6
```

### Slow Performance
```yaml
# Enable GPU if available
models:
  embedder:
    device: cuda
  llm:
    device: cuda
```

### Table Extraction Issues
```yaml
# Adjust table detection settings
parsing:
  pdf:
    table_settings:
      min_words_vertical: 2  # Lower threshold
      intersection_tolerance: 5  # Higher tolerance
```

## Development Commands

```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test

# Run tests with coverage
make test-cov

# Type checking
make type-check

# Clean build artifacts
make clean
```

## Performance Benchmarks

| Task | Performance | Hardware |
|------|-------------|----------|
| Document ingestion | <5s/page | Tesla P4 |
| Query latency | <2s | Tesla P4 |
| Cache hit latency | <0.05s | Any |
| Table extraction | >90% accuracy | - |

## Next Steps

1. **Read the full documentation**: [README.md](README.md)
2. **Explore configuration options**: [configs/default.yaml](configs/default.yaml)
3. **Check model presets**: [configs/models.yaml](configs/models.yaml)
4. **Review contributing guide**: [CONTRIBUTING.md](CONTRIBUTING.md)

## Support

- **Issues**: https://github.com/pulldata/pulldata/issues
- **Discussions**: https://github.com/pulldata/pulldata/discussions
- **Documentation**: https://pulldata.readthedocs.io

## Examples

See [examples/](examples/) directory for:
- Financial report extraction
- Legal document processing
- Research paper analysis
- Table extraction demos

---

**Version**: 0.1.0
**Status**: Alpha
**Last Updated**: 2025-12-17
