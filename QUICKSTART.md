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
pd = PullData(project="quickstart")

# Ingest documents
stats = pd.ingest("path/to/your/documents/*.pdf")
print(f"Processed {stats['new_chunks']} chunks")

# Query with automatic Excel generation
result = pd.query(
    query="What are the key financial metrics?",
    output_format="excel"  # File automatically saved to ./output/
)

print(f"Answer: {result.llm_response.text}")
print(f"Report saved to: {result.output_path}")
print(f"Sources: {len(result.retrieved_chunks)}")

# Cleanup
pd.close()
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

PullData automatically generates deliverable files in multiple formats!

### Excel (.xlsx)
```python
result = pd.query(
    query="Extract revenue by region",
    output_format="excel"  # Automatically saved to ./output/
)
print(f"Excel report: {result.output_path}")
```

### Markdown (.md)
```python
result = pd.query(
    query="Summarize key findings",
    output_format="markdown"
)
print(f"Markdown summary: {result.output_path}")
```

### JSON (.json)
```python
result = pd.query(
    query="Extract structured data",
    output_format="json"
)
print(f"JSON data: {result.output_path}")
```

### PowerPoint (.pptx)
```python
result = pd.query(
    query="Create presentation slides",
    output_format="powerpoint"
)
print(f"PowerPoint: {result.output_path}")
```

### PDF (.pdf)
```python
result = pd.query(
    query="Generate report",
    output_format="pdf"
)
print(f"PDF report: {result.output_path}")
```

**Note:** Files are automatically saved to `./output/{project}_query_{timestamp}.{format}` with the full path available in `result.output_path`.

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
pd.ingest("report.pdf")

# Update document (only changed content re-processed)
stats = pd.ingest("report.pdf")
print(f"Skipped {stats['skipped_chunks']} unchanged chunks")  # Much faster!
```

### Multi-Project Management

```python
# Separate projects for different document collections
finance = PullData(project="finance")
legal = PullData(project="legal")

finance.ingest("financial_docs/*.pdf")
legal.ingest("legal_docs/*.pdf")

# Each project has isolated storage
finance_result = finance.query("What's Q3 revenue?", output_format="excel")
legal_result = legal.query("What are the terms?", output_format="pdf")

finance.close()
legal.close()
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

See [examples/](examples/) directory for complete working examples:

- **[basic_usage.py](examples/basic_usage.py)** - Simple RAG query workflow
- **[lm_studio_api_embeddings.py](examples/lm_studio_api_embeddings.py)** - Using LM Studio for embeddings and LLM
- **[query_with_output_formats.py](examples/query_with_output_formats.py)** - End-to-end with all output formats
- **[output_formats_example.py](examples/output_formats_example.py)** - Standalone formatter usage
- **[pdf_ingestion_example.py](examples/pdf_ingestion_example.py)** - PDF processing and ingestion

### Complete Working Example

```python
from pathlib import Path
from pulldata import PullData

# Initialize
pd = PullData(
    project="financial_analysis",
    config_path="configs/lm_studio_api_embeddings.yaml"
)

# Ingest documents
stats = pd.ingest("financial_reports/*.pdf")
print(f"Ingested {stats['new_chunks']} chunks from {stats['processed_files']} files")

# Query with Excel output
result = pd.query(
    query="What was the total revenue in Q3 2024?",
    output_format="excel"
)

print(f"\nAnswer: {result.llm_response.text}")
print(f"Sources: {len(result.retrieved_chunks)}")
print(f"Excel report saved to: {result.output_path}")

# Query with PowerPoint output
presentation = pd.query(
    query="Create a summary of key financial metrics",
    output_format="powerpoint"
)
print(f"PowerPoint saved to: {presentation.output_path}")

pd.close()
```

---

**Version**: 0.1.0
**Status**: Alpha
**Last Updated**: 2024-12-18
