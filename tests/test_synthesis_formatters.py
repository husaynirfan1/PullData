"""Tests for synthesis output formatters.

Tests all formatters: Excel, Markdown, JSON, PowerPoint, PDF.
"""

import json
from pathlib import Path

import pytest

from pulldata.synthesis import (
    ExcelFormatter,
    FormatConfig,
    JSONFormatter,
    MarkdownFormatter,
    OutputData,
    PDFFormatter,
    PowerPointFormatter,
)

# Check availability of optional dependencies
try:
    import openpyxl

    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import xlsxwriter

    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False

try:
    from pptx import Presentation

    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

try:
    from reportlab.platypus import SimpleDocTemplate

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


@pytest.fixture
def sample_data():
    """Sample data for testing formatters."""
    return OutputData(
        title="Test Report",
        content="This is a test report with sample content.\n\nIt has multiple paragraphs.",
        sections=[
            {"title": "Introduction", "content": "This is the introduction section."},
            {"title": "Analysis", "content": "This is the analysis section."},
        ],
        tables=[
            {
                "name": "Sales Data",
                "headers": ["Region", "Q1", "Q2", "Q3", "Q4"],
                "rows": [
                    ["North", 100, 120, 130, 140],
                    ["South", 90, 95, 100, 105],
                    ["East", 110, 115, 120, 125],
                    ["West", 95, 100, 105, 110],
                ],
            }
        ],
        metadata={"author": "Test Author", "date": "2025-12-18", "version": "1.0"},
        sources=[
            {"document_id": "doc1", "page_number": 1, "chunk_id": "chunk1", "score": 0.95},
            {"document_id": "doc2", "page_number": 2, "chunk_id": "chunk2", "score": 0.88},
        ],
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for output files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


class TestExcelFormatter:
    """Tests for Excel formatter."""

    @pytest.mark.skipif(not (OPENPYXL_AVAILABLE or XLSXWRITER_AVAILABLE), reason="No Excel backend available")
    def test_format_basic(self, sample_data):
        """Test basic Excel formatting."""
        formatter = ExcelFormatter()
        result = formatter.format(sample_data)

        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.skipif(not (OPENPYXL_AVAILABLE or XLSXWRITER_AVAILABLE), reason="No Excel backend available")
    def test_save_file(self, sample_data, temp_output_dir):
        """Test saving Excel file."""
        formatter = ExcelFormatter()
        output_path = temp_output_dir / "test.xlsx"

        result_path = formatter.save(sample_data, output_path)

        assert result_path.exists()
        assert result_path.suffix == ".xlsx"
        assert result_path.stat().st_size > 0

    @pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not available")
    def test_openpyxl_backend(self, sample_data):
        """Test openpyxl backend specifically."""
        formatter = ExcelFormatter(backend="openpyxl")
        result = formatter.format(sample_data)

        assert isinstance(result, bytes)

    @pytest.mark.skipif(not XLSXWRITER_AVAILABLE, reason="xlsxwriter not available")
    def test_xlsxwriter_backend(self, sample_data):
        """Test xlsxwriter backend specifically."""
        formatter = ExcelFormatter(backend="xlsxwriter")
        result = formatter.format(sample_data)

        assert isinstance(result, bytes)

    @pytest.mark.skipif(not (OPENPYXL_AVAILABLE or XLSXWRITER_AVAILABLE), reason="No Excel backend available")
    def test_auto_add_extension(self, sample_data, temp_output_dir):
        """Test that .xlsx extension is added automatically."""
        formatter = ExcelFormatter()
        output_path = temp_output_dir / "test"  # No extension

        result_path = formatter.save(sample_data, output_path)

        assert result_path.suffix == ".xlsx"

    @pytest.mark.skipif(not (OPENPYXL_AVAILABLE or XLSXWRITER_AVAILABLE), reason="No Excel backend available")
    def test_format_config(self, sample_data, temp_output_dir):
        """Test formatter with custom config."""
        config = FormatConfig(
            output_path=temp_output_dir / "configured.xlsx",
            include_metadata=False,
            include_sources=False,
        )
        formatter = ExcelFormatter(config=config)
        result = formatter.format(sample_data)

        assert isinstance(result, bytes)


class TestMarkdownFormatter:
    """Tests for Markdown formatter."""

    def test_format_basic(self, sample_data):
        """Test basic Markdown formatting."""
        formatter = MarkdownFormatter()
        result = formatter.format(sample_data)

        assert isinstance(result, bytes)
        markdown_str = result.decode("utf-8")
        assert "# Test Report" in markdown_str
        assert sample_data.content in markdown_str

    def test_save_file(self, sample_data, temp_output_dir):
        """Test saving Markdown file."""
        formatter = MarkdownFormatter()
        output_path = temp_output_dir / "test.md"

        result_path = formatter.save(sample_data, output_path)

        assert result_path.exists()
        assert result_path.suffix == ".md"
        content = result_path.read_text(encoding="utf-8")
        assert "# Test Report" in content

    def test_table_of_contents(self, sample_data):
        """Test TOC generation."""
        formatter = MarkdownFormatter(include_toc=True)
        result = formatter.format(sample_data).decode("utf-8")

        assert "## Table of Contents" in result
        assert "[Introduction]" in result
        assert "[Analysis]" in result

    def test_no_toc(self, sample_data):
        """Test disabling TOC."""
        formatter = MarkdownFormatter(include_toc=False)
        result = formatter.format(sample_data).decode("utf-8")

        assert "Table of Contents" not in result

    def test_gfm_tables(self, sample_data):
        """Test GitHub-Flavored Markdown tables."""
        formatter = MarkdownFormatter()
        result = formatter.format(sample_data).decode("utf-8")

        # Check for table structure
        assert "| Region | Q1 | Q2 | Q3 | Q4 |" in result
        assert "| --- |" in result  # Table separator
        assert "| North | 100 | 120 | 130 | 140 |" in result

    def test_heading_level(self, sample_data):
        """Test custom heading level."""
        formatter = MarkdownFormatter(heading_level=2)
        result = formatter.format(sample_data).decode("utf-8")

        assert "## Test Report" in result  # H2 instead of H1


class TestJSONFormatter:
    """Tests for JSON formatter."""

    def test_format_basic(self, sample_data):
        """Test basic JSON formatting."""
        formatter = JSONFormatter()
        result = formatter.format(sample_data)

        assert isinstance(result, bytes)

        # Verify it's valid JSON
        data = json.loads(result.decode("utf-8"))
        assert data["title"] == "Test Report"
        assert data["content"] == sample_data.content

    def test_save_file(self, sample_data, temp_output_dir):
        """Test saving JSON file."""
        formatter = JSONFormatter()
        output_path = temp_output_dir / "test.json"

        result_path = formatter.save(sample_data, output_path)

        assert result_path.exists()
        assert result_path.suffix == ".json"

        # Verify content
        with open(result_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["title"] == "Test Report"

    def test_pretty_print(self, sample_data):
        """Test pretty-printing with indentation."""
        formatter = JSONFormatter(indent=2)
        result = formatter.format(sample_data).decode("utf-8")

        # Check for indentation
        assert "  \"title\"" in result or "  " in result

    def test_compact_json(self, sample_data):
        """Test compact JSON (no indentation)."""
        formatter = JSONFormatter(indent=None)
        result = formatter.format(sample_data).decode("utf-8")

        # Should not have excessive whitespace
        assert "\n  " not in result

    def test_sort_keys(self, sample_data):
        """Test sorting dictionary keys."""
        formatter = JSONFormatter(sort_keys=True)
        result = formatter.format(sample_data).decode("utf-8")

        # Verify it's valid JSON
        data = json.loads(result)
        assert "title" in data

    def test_exclude_metadata(self, sample_data):
        """Test excluding metadata."""
        config = FormatConfig(include_metadata=False)
        formatter = JSONFormatter(config=config)
        result = formatter.format(sample_data).decode("utf-8")

        data = json.loads(result)
        assert "metadata" not in data

    def test_exclude_sources(self, sample_data):
        """Test excluding sources."""
        config = FormatConfig(include_sources=False)
        formatter = JSONFormatter(config=config)
        result = formatter.format(sample_data).decode("utf-8")

        data = json.loads(result)
        assert "sources" not in data


class TestPowerPointFormatter:
    """Tests for PowerPoint formatter."""

    @pytest.mark.skipif(not PPTX_AVAILABLE, reason="python-pptx not available")
    def test_format_basic(self, sample_data):
        """Test basic PowerPoint formatting."""
        formatter = PowerPointFormatter()
        result = formatter.format(sample_data)

        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.skipif(not PPTX_AVAILABLE, reason="python-pptx not available")
    def test_save_file(self, sample_data, temp_output_dir):
        """Test saving PowerPoint file."""
        formatter = PowerPointFormatter()
        output_path = temp_output_dir / "test.pptx"

        result_path = formatter.save(sample_data, output_path)

        assert result_path.exists()
        assert result_path.suffix == ".pptx"
        assert result_path.stat().st_size > 0

    @pytest.mark.skipif(not PPTX_AVAILABLE, reason="python-pptx not available")
    def test_auto_add_extension(self, sample_data, temp_output_dir):
        """Test that .pptx extension is added automatically."""
        formatter = PowerPointFormatter()
        output_path = temp_output_dir / "test"  # No extension

        result_path = formatter.save(sample_data, output_path)

        assert result_path.suffix == ".pptx"


class TestPDFFormatter:
    """Tests for PDF formatter."""

    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not available")
    def test_format_basic(self, sample_data):
        """Test basic PDF formatting."""
        formatter = PDFFormatter()
        result = formatter.format(sample_data)

        assert isinstance(result, bytes)
        assert len(result) > 0
        # PDF files start with %PDF
        assert result[:4] == b"%PDF"

    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not available")
    def test_save_file(self, sample_data, temp_output_dir):
        """Test saving PDF file."""
        formatter = PDFFormatter()
        output_path = temp_output_dir / "test.pdf"

        result_path = formatter.save(sample_data, output_path)

        assert result_path.exists()
        assert result_path.suffix == ".pdf"
        assert result_path.stat().st_size > 0

    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not available")
    def test_auto_add_extension(self, sample_data, temp_output_dir):
        """Test that .pdf extension is added automatically."""
        formatter = PDFFormatter()
        output_path = temp_output_dir / "test"  # No extension

        result_path = formatter.save(sample_data, output_path)

        assert result_path.suffix == ".pdf"


class TestFormatterErrors:
    """Tests for formatter error handling."""

    @pytest.mark.skipif(not (OPENPYXL_AVAILABLE or XLSXWRITER_AVAILABLE), reason="No Excel backend available")
    def test_wrong_extension_error(self, sample_data, temp_output_dir):
        """Test that wrong file extension raises error."""
        formatter = ExcelFormatter()
        output_path = temp_output_dir / "test.pdf"  # Wrong extension

        with pytest.raises(Exception):  # FormatterError
            formatter.save(sample_data, output_path)

    def test_no_output_path_error(self, sample_data):
        """Test that missing output path raises error."""
        formatter = JSONFormatter()  # No config with output_path

        with pytest.raises(Exception):  # FormatterError
            formatter.save(sample_data)  # No output_path argument
