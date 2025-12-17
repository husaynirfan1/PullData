# PullData Examples

This directory contains practical examples demonstrating how to use PullData.

## Available Examples

### 1. Basic Usage (`basic_usage.py`)
The simplest example showing core PullData functionality:
- Initialize a project
- Ingest documents
- Query the system
- Access results

**Run:**
```bash
python examples/basic_usage.py
```

### 2. PDF Ingestion (`pdf_ingestion_example.py`)
Demonstrates PDF document processing:
- Ingest multiple PDFs
- Add custom metadata
- Query with filters
- Different retrieval modes

**Setup:**
1. Create `./data/reports/` directory
2. Add PDF files
3. Run the example

**Run:**
```bash
python examples/pdf_ingestion_example.py
```

### 3. Output Formats (`output_formats_example.py`)
Shows how to export results to various formats:
- Excel (.xlsx)
- Markdown (.md)
- JSON (.json)
- PowerPoint (.pptx)
- PDF (.pdf)

**Run:**
```bash
python examples/output_formats_example.py
```

This example generates sample outputs in `./output_examples/` directory.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the output formats example** (works without data):
   ```bash
   python examples/output_formats_example.py
   ```

3. **For PDF examples**, add your PDFs to `./data/reports/` and run:
   ```bash
   python examples/pdf_ingestion_example.py
   ```

## Common Patterns

### Initialize PullData
```python
from pulldata import PullData

pd = PullData(project="my_project")
```

### Ingest Documents
```python
# Single file
pd.ingest("document.pdf")

# Directory
pd.ingest("./documents/")

# Glob pattern
pd.ingest("./documents/*.pdf")

# With metadata
pd.ingest("./reports/", department="Finance", year=2024)
```

### Query
```python
# Simple query
result = pd.query("What are the key points?")

# With answer generation
result = pd.query("Summarize the findings", generate_answer=True)

# With filters
result = pd.query(
    "What is the revenue?",
    filters={"year": 2024},
    k=10
)

# Retrieval only (no LLM)
result = pd.query("search term", generate_answer=False)
```

### Export Results
```python
from pulldata.synthesis import ExcelFormatter

formatter = ExcelFormatter()
formatter.save(result, "output.xlsx")

# Or use the integrated method
pd.format_and_save(
    result=result,
    formatter=formatter,
    output_path="output.xlsx"
)
```

## Environment Setup

For LLM-based answer generation, you need to configure:

**Local LLM:**
- Set `models.llm.provider = "local"` in config
- Ensure you have GPU/CPU resources

**API LLM:**
- Set `models.llm.provider = "api"` in config
- Configure API endpoint and key

See `configs/default.yaml` for full configuration options.

## Troubleshooting

**Import errors:**
- Make sure you're in the PullData root directory
- Verify installation: `pip install -e .`

**No documents ingested:**
- Check file paths are correct
- Ensure PDFs are readable
- Check logs in `./logs/pulldata.log`

**Out of memory:**
- Reduce batch size in config
- Use smaller embedding models
- Process fewer documents at once

## Need Help?

- Check the main [README.md](../README.md)
- Review [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)
- See configuration docs in `configs/`
