"""
Output synthesis module for PullData.

Converts structured data into various output formats:
- Excel (.xlsx)
- PowerPoint (.pptx)
- Markdown (.md)
- JSON
- PDF (basic and styled with LLM structuring)
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
    StyledPDFFormatter,
    render_styled_pdf,
)
from pulldata.synthesis.report_models import (
    MetricItem,
    Reference,
    ReportData,
    ReportSection,
    get_structuring_prompt,
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
    "StyledPDFFormatter",
    "render_styled_pdf",
    # Report models
    "ReportData",
    "ReportSection",
    "MetricItem",
    "Reference",
    "get_structuring_prompt",
]
