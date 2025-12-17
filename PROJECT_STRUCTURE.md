# PullData Project Structure

Generated: 2025-12-17

```
PullData/
│
├── configs/                          # Configuration files
│   ├── default.yaml                  # Main configuration
│   ├── models.yaml                   # Model presets
│   └── templates/                    # Output templates
│
├── pulldata/                         # Main package
│   ├── __init__.py                   # Package initialization
│   ├── py.typed                      # Type checking marker
│   │
│   ├── core/                         # Core data structures
│   │   └── __init__.py
│   │   # TODO: datatypes.py         - Document, Chunk, Embedding classes
│   │   # TODO: config.py            - Configuration management
│   │   # TODO: exceptions.py        - Custom exceptions
│   │
│   ├── parsing/                      # Document parsing
│   │   └── __init__.py
│   │   # TODO: pdf_parser.py        - PDF parsing with PyMuPDF
│   │   # TODO: table_extractor.py   - Table extraction
│   │   # TODO: chunking.py          - Semantic chunking
│   │
│   ├── embedding/                    # Embedding generation
│   │   └── __init__.py
│   │   # TODO: embedder.py          - BGE embedding wrapper
│   │   # TODO: cache.py             - Embedding cache
│   │
│   ├── storage/                      # Storage backends
│   │   └── __init__.py
│   │   # TODO: base.py              - Abstract StorageBackend
│   │   # TODO: postgres_backend.py  - PostgreSQL + pgvector
│   │   # TODO: sqlite_backend.py    - SQLite + FAISS
│   │   # TODO: chroma_backend.py    - ChromaDB
│   │   # TODO: project_manager.py   - Project isolation
│   │
│   ├── retrieval/                    # Vector search
│   │   └── __init__.py
│   │   # TODO: vector_store.py      - FAISS wrapper
│   │   # TODO: retriever.py         - Search + filtering
│   │   # TODO: reranker.py          - Optional reranking
│   │
│   ├── generation/                   # LLM generation
│   │   └── __init__.py
│   │   # TODO: llm.py               - Qwen wrapper
│   │   # TODO: prompts.py           - Prompt templates
│   │   # TODO: extractor.py         - Structured extraction
│   │
│   ├── synthesis/                    # Output synthesis
│   │   ├── __init__.py
│   │   └── formatters/              # Format generators
│   │       └── __init__.py
│   │       # TODO: excel.py         - Excel generation
│   │       # TODO: markdown.py      - Markdown output
│   │       # TODO: json.py          - JSON output
│   │       # TODO: pptx.py          - PowerPoint
│   │       # TODO: latex.py         - LaTeX output
│   │
│   ├── pipeline/                     # Orchestration
│   │   └── __init__.py
│   │   # TODO: orchestrator.py      - End-to-end pipeline
│   │
│   └── cli/                          # CLI interface
│       └── __init__.py
│       # TODO: main.py              - Typer CLI commands
│
├── tests/                            # Tests
│   # TODO: Unit tests
│   # TODO: Integration tests
│   # TODO: Fixtures
│
├── benchmarks/                       # Performance benchmarks
│   # TODO: Ingestion benchmarks
│   # TODO: Query benchmarks
│   # TODO: Memory profiling
│
├── examples/                         # Usage examples
│   # TODO: Financial report example
│   # TODO: Legal document example
│   # TODO: Table extraction demo
│
├── docs/                             # Documentation
│   # TODO: API reference
│   # TODO: Architecture guide
│   # TODO: Tutorial notebooks
│
├── data/                             # Data directory (gitignored)
│   # Created at runtime for local storage
│
├── .env.example                      # Environment template
├── .gitignore                        # Git ignore rules
├── .pre-commit-config.yaml           # Pre-commit hooks
├── CONTRIBUTING.md                   # Contribution guide
├── LICENSE                           # MIT License
├── Makefile                          # Development commands
├── PROJECT_STRUCTURE.md              # This file
├── QUICKSTART.md                     # Quick start guide
├── README.md                         # Main documentation
├── SETUP_COMPLETE.md                 # Setup completion summary
├── pyproject.toml                    # Project configuration
├── requirements.txt                  # Pip requirements
├── setup.py                          # Backward compat setup
└── verify_setup.py                   # Setup verification script

```

## Module Overview

### Core Modules (Phase 1-2)
- **core**: Data structures, configuration, exceptions
- **parsing**: PDF/DOCX parsing, table extraction, chunking

### ML Modules (Phase 2-3)
- **embedding**: Text embedding generation and caching
- **generation**: LLM inference and structured extraction

### Storage Modules (Phase 3)
- **storage**: Pluggable backends (Postgres, SQLite, Chroma)
- **retrieval**: Vector search and metadata filtering

### Output Modules (Phase 3)
- **synthesis**: Output format generation (Excel, MD, JSON, etc.)
- **pipeline**: End-to-end orchestration

### Interface Modules (Phase 4)
- **cli**: Command-line interface

## File Count

### Current Status
- **Configuration files**: 3
- **Documentation files**: 6
- **Python modules**: 10 (with `__init__.py`)
- **Development files**: 6
- **Total files**: 39

### Target (Post-MVP)
- **Python files**: ~30-40
- **Test files**: ~25-30
- **Example files**: ~10
- **Documentation files**: ~15
- **Total files**: ~100+

## Storage Layout (Runtime)

### Local Mode (SQLite)
```
data/
├── pulldata.db                       # SQLite database
└── faiss_indexes/
    ├── project_default.index         # FAISS index per project
    └── project_finance.index
```

### PostgreSQL Mode
```
PostgreSQL Database: pulldata
├── Schema: project_default
│   ├── documents
│   ├── chunks
│   ├── embeddings (pgvector)
│   ├── extracted_tables
│   ├── table_headers
│   ├── table_cells
│   ├── llm_cache
│   └── document_versions
└── Schema: project_finance
    └── (same structure)

data/
└── faiss_indexes/
    └── project_default.index         # In-memory FAISS backup
```

### ChromaDB Mode
```
data/
└── chroma_db/
    ├── collection_default/           # One collection per project
    └── collection_finance/
```

## Key Design Patterns

### 1. Pluggable Architecture
All storage backends implement the same `StorageBackend` interface, making them interchangeable.

### 2. Multi-Project Isolation
- PostgreSQL: Separate schemas
- SQLite: Separate database files
- ChromaDB: Separate collections

### 3. Hybrid Storage
- Text data: SQL databases (queryable)
- Vectors: FAISS (fast search) + persistent backup
- Tables: Relational format (normalized)

### 4. Caching Layers
- Embedding cache: Avoid re-computing embeddings
- LLM output cache: Instant repeated queries
- FAISS in-memory: Fast vector search

### 5. Differential Updates
- Content hashing: Detect changes
- Chunk-level updates: Only re-process modified content
- Version tracking: Enable rollback

## Development Phases

### Phase 1: Foundation (Weeks 1-2) ✓ Step 1 Complete
- [x] Project setup
- [ ] Core data structures
- [ ] Document parsing
- [ ] Embedding layer

### Phase 2: Storage (Weeks 3-4)
- [ ] Storage abstraction
- [ ] PostgreSQL backend
- [ ] SQLite backend
- [ ] ChromaDB backend (optional)

### Phase 3: Generation (Weeks 5-6)
- [ ] Retrieval engine
- [ ] LLM generation
- [ ] Output synthesis (Excel, Markdown)

### Phase 4: Integration (Weeks 7-8)
- [ ] Pipeline orchestration
- [ ] CLI interface
- [ ] Testing & benchmarks
- [ ] Documentation

## Quick Reference

### Import Structure (Future)
```python
# Main API
from pulldata import PullData

# Core types
from pulldata.core import Document, Chunk, Embedding, Config

# Parsing
from pulldata.parsing import PDFParser, TableExtractor

# Storage
from pulldata.storage import PostgresBackend, SQLiteBackend

# Output
from pulldata.synthesis.formatters import ExcelFormatter
```

### Configuration Files
```yaml
# Storage: configs/default.yaml
storage:
  backend: local | postgres | chromadb

# Models: configs/models.yaml
models:
  embedder:
    name: BAAI/bge-small-en-v1.5
  llm:
    name: Qwen/Qwen2.5-3B-Instruct
```

---

**Structure Snapshot**: 2025-12-17
**Phase**: 1 - Foundation
**Step**: 1 Complete, Moving to Step 2
