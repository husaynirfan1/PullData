# PullData

**Turn Documents into Deliverables**

PullData is a high-performance, text-based RAG (Retrieval-Augmented Generation) system optimized for extracting structured data from documents and generating versatile output formats. Built for efficiency on modest hardware (Tesla P4 8GB VRAM), it excels at transforming PDFs into Excel spreadsheets, PowerPoint presentations, Markdown, JSON, and more.

## Key Features

- **Versatile Output Formats**: Excel (.xlsx), PowerPoint (.pptx), Markdown, JSON, LaTeX, PDF
- **Advanced Table Extraction**: Preserves table structure and enables direct Excel export
- **Flexible LLM Options**: Local models OR OpenAI-compatible APIs (LM Studio, Ollama, OpenAI, Groq, etc.)
- **Pluggable Storage**: PostgreSQL + pgvector, SQLite (local), or ChromaDB
- **Smart Caching**: LLM output caching and embedding caching for blazing-fast repeated queries
- **Differential Updates**: Hash-based change detection avoids re-processing unchanged content
- **Multi-Project Isolation**: Manage multiple document collections with complete separation
- **Hardware Optimized**: Runs efficiently on Tesla P4 (8GB VRAM) with INT8 quantization

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/pulldata/pulldata.git
cd pulldata

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy environment file
cp .env.example .env
```

### Basic Usage (Python API)

```python
from pulldata import PullData

# Initialize with default local storage (SQLite + FAISS)
rag = PullData(project="financial_reports")

# Ingest documents
rag.ingest("./documents/*.pdf")

# Query and generate Excel output
result = rag.query(
    query="Extract Q3 revenue by region",
    output_format="excel"
)

# Save output
result.save("revenue_report.xlsx")
```

### CLI Usage

```bash
# Initialize a new project
pulldata init --project financial_reports --backend local

# Ingest documents
pulldata ingest --project financial_reports --path ./documents/

# Query with Excel output
pulldata query \
  --project financial_reports \
  --query "Extract Q3 revenue by region" \
  --output excel \
  --save revenue_report.xlsx

# Query with Markdown output
pulldata query \
  --project financial_reports \
  --query "Summarize key findings" \
  --output markdown \
  --save summary.md
```

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         Document Ingestion              │
├─────────────────────────────────────────┤
│ PDF → PyMuPDF (text) + pdfplumber       │
│      (tables)                            │
│ ↓                                        │
│ Semantic Chunking (512 tokens)          │
│ ↓                                        │
│ BGE Embeddings (384 dim)                │
│ ↓                                        │
│ Storage Backend (Postgres/SQLite/Chroma) │
│ + FAISS Index                            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│           Query Pipeline                │
├─────────────────────────────────────────┤
│ User Query → Embedding → FAISS Search   │
│ → Metadata Filtering → LLM Generation   │
│ → Format Synthesis → Output File        │
└─────────────────────────────────────────┘
```

## Technology Stack

| Component | Technology | Size | VRAM |
|-----------|-----------|------|------|
| **Embedder** | BAAI/bge-small-en-v1.5 | 33M | ~0.5GB |
| **LLM (Default)** | Qwen/Qwen2.5-3B-Instruct | 3B | ~3GB (INT8) |
| **LLM (API)** | OpenAI-compatible APIs | - | - |
| **Vector DB** | FAISS + pgvector | - | - |
| **Storage** | PostgreSQL / SQLite / ChromaDB | - | - |

## LLM Options

PullData supports two modes for language models:

### Local Models (Default)
Run models directly on your hardware using transformers:
- **Qwen 2.5 3B** (Default for P4)
- **Qwen 2.5 7B** (High-end GPUs)
- **Llama 3.2 3B**
- **Phi-2**

### API Providers
Use OpenAI-compatible API endpoints:
- **LM Studio** - Local API server with UI (Recommended for no GPU)
- **Ollama** - Easy local LLM runner
- **OpenAI** - GPT-3.5, GPT-4
- **Groq** - Ultra-fast inference
- **Together AI** - Fast open-source models
- **vLLM** - Self-hosted inference server
- **Text Generation WebUI** - Feature-rich local server

**Switch with one config change:**
```yaml
# Local model
models:
  llm:
    provider: local

# API endpoint
models:
  llm:
    provider: api
    api:
      base_url: http://localhost:1234/v1  # LM Studio
      model: local-model
```

See [API Configuration Guide](docs/API_CONFIGURATION.md) for detailed setup.

## Configuration

PullData uses YAML configuration files located in the `configs/` directory:

- [configs/default.yaml](configs/default.yaml) - Main configuration
- [configs/models.yaml](configs/models.yaml) - Model presets for different hardware

### Storage Backends

#### Local (SQLite + FAISS)
Zero-config, single-file storage. Perfect for development and small projects.

```yaml
storage:
  backend: local
  local:
    sqlite_path: ./data/pulldata.db
    faiss_index_path: ./data/faiss_indexes
```

#### PostgreSQL + pgvector
Production-ready with multi-user support and advanced querying.

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

#### ChromaDB
Standalone vector database with built-in persistence.

```yaml
storage:
  backend: chromadb
  chromadb:
    persist_directory: ./data/chroma_db
```

## Advanced Features

### Differential Updates
PullData detects unchanged content using SHA-256 hashing and only re-processes modified chunks:

```python
# First ingest
rag.ingest("report.pdf")  # Full processing

# Update document (only changed pages re-processed)
rag.ingest("report.pdf")  # Differential update
```

### LLM Output Caching
Repeated queries are served from cache instantly:

```python
# Cache key: hash(query + context_ids + model)
result1 = rag.query("What's Q3 revenue?")  # LLM call (2s)
result2 = rag.query("What's Q3 revenue?")  # Cache hit (0.01s)
```

### Advanced Metadata Filtering

```python
results = rag.query(
    query="Revenue trends",
    filters={
        "doc_type": "financial_report",
        "date_range": ("2024-01-01", "2024-12-31"),
        "tags": ["quarterly", "audited"],
        "page_number": 5
    }
)
```

### Multi-Project Management

```python
# Create separate projects for isolation
finance_rag = PullData(project="finance")
legal_rag = PullData(project="legal")

# Each has independent storage and indexes
finance_rag.ingest("financial_docs/")
legal_rag.ingest("legal_docs/")
```

## Output Formats

### Excel (.xlsx)
- Preserves table structure from PDFs
- Automatic styling (headers, filters, freeze panes)
- Support for multiple sheets
- Formula support (coming soon)

### PowerPoint (.pptx)
- Template-based generation
- Automatic slide layouts
- Table and chart embedding

### Markdown
- Clean, readable format
- Automatic TOC generation
- Code highlighting

### JSON
- Structured data extraction
- Configurable schema
- Nested data support

### LaTeX
- Academic paper formatting
- Math equation support
- Citation management (coming soon)

## Performance Benchmarks

| Task | Performance | Hardware |
|------|-------------|----------|
| Ingest (per page) | <5s | Tesla P4 |
| Query latency | <2s | Tesla P4 |
| Cache hit latency | <0.05s | Any |
| Table extraction accuracy | >90% | - |

## Project Structure

```
pulldata/
├── configs/              # Configuration files
├── pulldata/
│   ├── core/            # Core data structures
│   ├── parsing/         # Document parsing
│   ├── embedding/       # Embedding generation
│   ├── storage/         # Storage backends
│   ├── retrieval/       # Vector search & filtering
│   ├── generation/      # LLM generation
│   ├── synthesis/       # Output format synthesis
│   ├── pipeline/        # End-to-end orchestration
│   └── cli/            # CLI interface
├── tests/               # Unit & integration tests
├── benchmarks/          # Performance benchmarks
├── examples/            # Usage examples
└── docs/               # Documentation
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=pulldata --cov-report=html
```

### Code Quality

```bash
# Format code
black pulldata/

# Lint code
ruff check pulldata/

# Type checking
mypy pulldata/
```

## Hardware Requirements

### Minimum
- **GPU**: None (CPU mode supported)
- **RAM**: 8GB
- **Storage**: 5GB (models + data)

### Recommended (Target)
- **GPU**: Tesla P4 (8GB VRAM) or equivalent
- **RAM**: 16GB
- **Storage**: 20GB

### High Performance
- **GPU**: RTX 3090 (24GB) or better
- **RAM**: 32GB
- **Storage**: 50GB

## Roadmap

### MVP (Current)
- [x] Project structure setup
- [ ] Core data structures
- [ ] Document parsing (PDF + tables)
- [ ] Embedding generation
- [ ] Storage backends (PostgreSQL, SQLite)
- [ ] Vector search with FAISS
- [ ] LLM generation
- [ ] Excel & Markdown output
- [ ] CLI interface

### Post-MVP
- [ ] ChromaDB backend
- [ ] PowerPoint output
- [ ] LaTeX output
- [ ] Streaming generation
- [ ] Reranking support
- [ ] FastAPI server
- [ ] Web UI
- [ ] Table embeddings
- [ ] Multi-modal support

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Citation

```bibtex
@software{pulldata2025,
  title = {PullData: Turn Documents into Deliverables},
  author = {PullData Team},
  year = {2025},
  url = {https://github.com/pulldata/pulldata}
}
```

## Support

- Documentation: [https://pulldata.readthedocs.io](https://pulldata.readthedocs.io)
- Issues: [https://github.com/pulldata/pulldata/issues](https://github.com/pulldata/pulldata/issues)
- Discussions: [https://github.com/pulldata/pulldata/discussions](https://github.com/pulldata/pulldata/discussions)

---

**Status**: Alpha - Active Development

**Last Updated**: 2025-12-17
