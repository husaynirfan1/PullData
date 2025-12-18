"""
Output synthesis module for PullData.

Converts structured data into various output formats:
- Excel (.xlsx)
- PowerPoint (.pptx)
- Markdown (.md)
- JSON
- PDF
"""

from pulldata.synthesis.base import (
    FormatConfig,
    FormatterError,
    OutputData,
    OutputFormatter,
    strip_reasoning_tags,
)
from pulldata.synthesis.formatters import (
    ExcelFormatter,
    JSONFormatter,
    MarkdownFormatter,
    PDFFormatter,
    PowerPointFormatter,
)

__all__ = [
    # Base classes
    "OutputFormatter",
    "OutputData",
    "FormatConfig",
    "FormatterError",
    "strip_reasoning_tags",
    # Formatters
    "ExcelFormatter",
    "MarkdownFormatter",
    "JSONFormatter",
    "PowerPointFormatter",
    "PDFFormatter",
]
