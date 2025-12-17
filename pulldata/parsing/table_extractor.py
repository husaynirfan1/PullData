"""
Table extraction from PDFs using pdfplumber.

Detects and extracts tabular data from PDF files with structure preservation.
"""

from pathlib import Path
from typing import Optional

import pdfplumber

from pulldata.core.datatypes import Table, TableCell
from pulldata.core.exceptions import (
    DocumentNotFoundError,
    TableExtractionError,
)


class TableExtractor:
    """
    Extract tables from PDF files using pdfplumber.

    Detects tables and extracts their structure, headers, and data.
    """

    def __init__(
        self,
        min_words_vertical: int = 3,
        min_words_horizontal: int = 3,
        intersection_tolerance: int = 3,
    ):
        """
        Initialize table extractor.

        Args:
            min_words_vertical: Minimum words for vertical text (table detection)
            min_words_horizontal: Minimum words for horizontal text
            intersection_tolerance: Tolerance for line intersections
        """
        self.table_settings = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "min_words_vertical": min_words_vertical,
            "min_words_horizontal": min_words_horizontal,
            "intersection_tolerance": intersection_tolerance,
        }

    def extract_tables_from_pdf(
        self,
        file_path: str | Path,
        document_id: str,
        page_numbers: Optional[list[int]] = None,
    ) -> list[Table]:
        """
        Extract all tables from a PDF.

        Args:
            file_path: Path to PDF file
            document_id: ID of parent document
            page_numbers: Specific pages to extract from (1-indexed), None for all

        Returns:
            List of Table objects

        Raises:
            DocumentNotFoundError: If file doesn't exist
            TableExtractionError: If extraction fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise DocumentNotFoundError(
                f"PDF file not found: {file_path}",
                details={"path": str(file_path)},
            )

        try:
            tables = []
            table_index = 0

            with pdfplumber.open(file_path) as pdf:
                pages_to_process = (
                    [pdf.pages[p - 1] for p in page_numbers]
                    if page_numbers
                    else pdf.pages
                )

                for page in pages_to_process:
                    page_number = page.page_number

                    # Extract tables from page
                    page_tables = page.extract_tables(self.table_settings)

                    for raw_table in page_tables:
                        if raw_table and len(raw_table) > 0:
                            table = self._convert_to_table_model(
                                raw_table=raw_table,
                                document_id=document_id,
                                table_index=table_index,
                                page_number=page_number,
                                page_bbox=page.bbox,
                            )
                            tables.append(table)
                            table_index += 1

            return tables

        except Exception as e:
            raise TableExtractionError(
                f"Failed to extract tables: {e}",
                details={"path": str(file_path), "error": str(e), "type": type(e).__name__},
            )

    def extract_tables_from_page(
        self,
        file_path: str | Path,
        page_number: int,
        document_id: str,
        start_table_index: int = 0,
    ) -> list[Table]:
        """
        Extract tables from a specific page.

        Args:
            file_path: Path to PDF file
            page_number: Page number (1-indexed)
            document_id: ID of parent document
            start_table_index: Starting index for table numbering

        Returns:
            List of Table objects from this page

        Raises:
            TableExtractionError: If extraction fails
        """
        file_path = Path(file_path)

        try:
            tables = []
            table_index = start_table_index

            with pdfplumber.open(file_path) as pdf:
                if page_number < 1 or page_number > len(pdf.pages):
                    raise TableExtractionError(
                        f"Page {page_number} out of range (1-{len(pdf.pages)})",
                        details={"page": page_number, "total_pages": len(pdf.pages)},
                    )

                page = pdf.pages[page_number - 1]
                page_tables = page.extract_tables(self.table_settings)

                for raw_table in page_tables:
                    if raw_table and len(raw_table) > 0:
                        table = self._convert_to_table_model(
                            raw_table=raw_table,
                            document_id=document_id,
                            table_index=table_index,
                            page_number=page_number,
                            page_bbox=page.bbox,
                        )
                        tables.append(table)
                        table_index += 1

            return tables

        except Exception as e:
            raise TableExtractionError(
                f"Failed to extract tables from page {page_number}: {e}",
                details={
                    "path": str(file_path),
                    "page": page_number,
                    "error": str(e),
                    "type": type(e).__name__,
                },
            )

    def _convert_to_table_model(
        self,
        raw_table: list[list],
        document_id: str,
        table_index: int,
        page_number: int,
        page_bbox: tuple,
    ) -> Table:
        """
        Convert pdfplumber table format to Table model.

        Args:
            raw_table: Raw table from pdfplumber (list of lists)
            document_id: Parent document ID
            table_index: Table index within document
            page_number: Page number
            page_bbox: Page bounding box

        Returns:
            Table object
        """
        if not raw_table or len(raw_table) == 0:
            raise TableExtractionError("Empty table data")

        # First row is headers
        headers = [str(cell) if cell is not None else "" for cell in raw_table[0]]

        # Remaining rows are data
        data_rows = raw_table[1:]

        # Get dimensions
        num_cols = len(headers)
        num_rows = len(data_rows)

        # Convert to TableCell objects
        cells = []
        for row_idx, row in enumerate(data_rows):
            for col_idx in range(num_cols):
                # Get cell value (handle rows with fewer columns)
                value = ""
                if col_idx < len(row):
                    cell_value = row[col_idx]
                    value = str(cell_value) if cell_value is not None else ""

                cell = TableCell(
                    row=row_idx,
                    col=col_idx,
                    value=value,
                    cell_type="data",
                )
                cells.append(cell)

        # Create Table
        table = Table(
            document_id=document_id,
            table_index=table_index,
            page_number=page_number,
            bbox=None,  # pdfplumber doesn't provide individual table bbox easily
            num_rows=num_rows,
            num_cols=num_cols,
            headers=headers,
            cells=cells,
        )

        return table

    def count_tables(self, file_path: str | Path) -> dict[int, int]:
        """
        Count tables per page without full extraction.

        Args:
            file_path: Path to PDF file

        Returns:
            Dict mapping page_number -> table_count

        Raises:
            TableExtractionError: If counting fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise DocumentNotFoundError(
                f"PDF file not found: {file_path}",
                details={"path": str(file_path)},
            )

        try:
            table_counts = {}

            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_number = page.page_number
                    tables = page.extract_tables(self.table_settings)
                    # Count non-empty tables
                    count = sum(1 for t in tables if t and len(t) > 0)
                    table_counts[page_number] = count

            return table_counts

        except Exception as e:
            raise TableExtractionError(
                f"Failed to count tables: {e}",
                details={"path": str(file_path), "error": str(e)},
            )

    def has_tables(self, file_path: str | Path) -> bool:
        """
        Check if PDF contains any tables.

        Args:
            file_path: Path to PDF file

        Returns:
            True if PDF contains tables, False otherwise
        """
        try:
            counts = self.count_tables(file_path)
            return sum(counts.values()) > 0
        except Exception:
            return False
