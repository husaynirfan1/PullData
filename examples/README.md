# Examples Directory - Quick Reference

This directory contains practical examples for using PullData.

## Available Examples

### 1. **basic_usage.py** - Getting Started
Basic PullData usage without complex setup.
```bash
python examples/basic_usage.py
```

### 2. **pdf_ingestion_example.py** - PDF Processing
Ingest and query PDF documents with metadata filtering.
**Requires**: PDFs in `./data/reports/`
```bash
python examples/pdf_ingestion_example.py
```

### 3. **output_formats_example.py** - Export Examples ⭐
**Works immediately** - No database or PDFs required!
Generates sample outputs in all 5 formats.
```bash
python examples/output_formats_example.py
```

### 4. **lm_studio_config.py** - LM Studio Setup ⭐
Complete guide for configuring LM Studio with PullData.
```bash
python examples/lm_studio_config.py
```

## Quick Start

**Test formatters immediately (no setup):**
```bash
python examples/output_formats_example.py
```

**See LM Studio configuration:**
```bash
python examples/lm_studio_config.py
```

## Configuration Files

Ready-to-use config files in `configs/`:
- `configs/lm_studio.yaml` - LM Studio configuration
- `configs/default.yaml` - Default local configuration

**Use with:**
```python
from pulldata import PullData

pd = PullData(
    project="my_project",
    config_path="configs/lm_studio.yaml"
)
```

## Common Patterns

### Initialize PullData
```python
from pulldata import PullData

# Local (default)
pd = PullData(project="my_project")

# With LM Studio
pd = PullData(
    project="my_project",
    config_path="configs/lm_studio.yaml"
)
```

### Ingest Documents
```python
stats = pd.ingest("./documents/*.pdf")
print(f"Processed: {stats['processed_files']} files")
```

### Query
```python
result = pd.query("What are the key findings?")
print(result.answer)
```

### Export Results
```python
from pulldata.synthesis import ExcelFormatter

formatter = ExcelFormatter()
formatter.save(result, "output.xlsx")
```

## See Also

- **README.md** - Full PullData documentation
- **docs/API_CONFIGURATION.md** - API configuration guide
- **QUICKSTART.md** - Quick start guide
