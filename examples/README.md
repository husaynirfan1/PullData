# PullData Examples

This directory contains working examples demonstrating PullData's features.

## Available Examples

### 1. **basic_usage.py** - Getting Started
Basic PullData usage showing core workflow and output formats.
```bash
python examples/basic_usage.py
```

**Shows:**
- Project initialization
- Document ingestion
- Query with/without LLM
- Output format generation

---

### 2. **query_with_output_formats.py** - Full Demo ⭐
**Complete working example!** Ingests a document and generates all 5 output formats.
```bash
python examples/query_with_output_formats.py
```

**Output:** Creates 5 files in `./output/` directory:
- Excel (.xlsx)
- Markdown (.md)
- JSON (.json)
- PowerPoint (.pptx)
- PDF (.pdf)

---

### 3. **lm_studio_api_embeddings.py** - LM Studio Integration
Real-world example using LM Studio for both embeddings and LLM.
```bash
# Start LM Studio server first
python examples/lm_studio_api_embeddings.py
```

**Requirements:**
- LM Studio running on http://localhost:1234
- Embedding model loaded (nomic-embed-text-v1.5)
- LLM model loaded (qwen3-1.7b)

---

### 4. **output_formats_example.py** - Standalone Formatters
**Works immediately** - No database or documents required!
```bash
python examples/output_formats_example.py
```

**Perfect for:**
- Testing output formatters
- Custom data pipelines
- Quick prototyping

---

### 5. **pdf_ingestion_example.py** - PDF Processing
Ingest and query PDF documents with metadata filtering.
```bash
python examples/pdf_ingestion_example.py
```

**Shows:**
- PDF ingestion
- Metadata filtering
- Retrieval strategies
- Output format generation

---

### 6. **lm_studio_config.py** - Configuration Guide
LM Studio configuration examples and patterns.
```bash
python examples/lm_studio_config.py
```

---

## Quick Start

### Test Output Formats (No Setup Required)
```bash
python examples/output_formats_example.py
```

### Full Pipeline with All Formats
```bash
python examples/query_with_output_formats.py
```

### LM Studio Integration
```bash
# 1. Start LM Studio server
# 2. Load models
python examples/lm_studio_api_embeddings.py
```

---

## Common Patterns

### Initialize PullData
```python
from pulldata import PullData

# Local (default)
pd = PullData(project="my_project")

# With LM Studio
pd = PullData(
    project="my_project",
    config_path="configs/lm_studio_api_embeddings.yaml"
)
```

### Ingest Documents
```python
stats = pd.ingest("./documents/*.pdf")
print(f"Processed: {stats['processed_files']} files")
print(f"New chunks: {stats['new_chunks']}")
```

### Query with Output Format
```python
result = pd.query(
    "What are the key findings?",
    output_format="excel"  # Automatically saved to ./output/
)

print(f"Answer: {result.llm_response.text}")
print(f"Report: {result.output_path}")
```

### All Available Formats
```python
# Excel spreadsheet
result = pd.query("...", output_format="excel")

# Markdown document
result = pd.query("...", output_format="markdown")

# JSON structured data
result = pd.query("...", output_format="json")

# PowerPoint presentation
result = pd.query("...", output_format="powerpoint")

# PDF report
result = pd.query("...", output_format="pdf")
```

---

## Configuration Files

Ready-to-use config files in `configs/`:
- **configs/default.yaml** - Default local configuration
- **configs/lm_studio_api_embeddings.yaml** - LM Studio API setup

**Example:**
```python
pd = PullData(
    project="my_project",
    config_path="configs/lm_studio_api_embeddings.yaml"
)
```

---

## Troubleshooting

### "Module not found: pulldata"
```bash
pip install -e .
```

### "Connection refused" (LM Studio)
1. Open LM Studio
2. Go to "Server" tab
3. Click "Start Server"
4. Verify port is 1234

### "File not found: testdocs/test.txt"
```bash
mkdir testdocs
echo "Sample text for testing" > testdocs/test.txt
```

---

## What to Run First?

**Complete beginner?**
→ [basic_usage.py](basic_usage.py)

**Want to see output formats?**
→ [query_with_output_formats.py](query_with_output_formats.py)

**Using LM Studio?**
→ [lm_studio_api_embeddings.py](lm_studio_api_embeddings.py)

**Just testing formatters?**
→ [output_formats_example.py](output_formats_example.py) (no database!)

---

## See Also

- **[QUICKSTART.md](../QUICKSTART.md)** - Detailed quick start guide
- **[docs/API_CONFIGURATION.md](../docs/API_CONFIGURATION.md)** - API configuration
- **[docs/FEATURES_STATUS.md](../docs/FEATURES_STATUS.md)** - Feature overview
- **[README.md](../README.md)** - Full documentation

---

**Last Updated:** 2024-12-18
