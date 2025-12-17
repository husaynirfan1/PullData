"""
PDF parsing using PyMuPDF.

Extracts text content from PDF files with page-level granularity.
Handles text extraction, metadata, and page information.
"""

import hashlib
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from pulldata.core.datatypes import Document, DocumentType
from pulldata.core.exceptions import (
    DocumentNotFoundError,
    PDFParsingError,
    UnsupportedFormatError,
)


class PDFParser:
    """
    PDF parser using PyMuPDF (fitz).

    Extracts text content, metadata, and page information from PDF files.
    """

    def __init__(self):
        """Initialize PDF parser."""
        self.supported_extensions = {".pdf"}

    def is_supported(self, file_path: str | Path) -> bool:
        """
        Check if file is a supported PDF.

        Args:
            file_path: Path to file

        Returns:
            True if file is a PDF, False otherwise
        """
        path = Path(file_path)
        return path.suffix.lower() in self.supported_extensions

    def parse(
        self,
        file_path: str | Path,
        extract_metadata: bool = True,
    ) -> tuple[Document, dict[int, str]]:
        """
        Parse a PDF file.

        Args:
            file_path: Path to PDF file
            extract_metadata: Whether to extract document metadata

        Returns:
            Tuple of (Document, page_texts)
            - Document: Document metadata
            - page_texts: Dict mapping page_number -> text content

        Raises:
            DocumentNotFoundError: If file doesn't exist
            UnsupportedFormatError: If file is not a PDF
            PDFParsingError: If parsing fails
        """
        file_path = Path(file_path)

        # Validate file exists
        if not file_path.exists():
            raise DocumentNotFoundError(
                f"PDF file not found: {file_path}",
                details={"path": str(file_path)},
            )

        # Validate file type
        if not self.is_supported(file_path):
            raise UnsupportedFormatError(
                f"File is not a PDF: {file_path}",
                details={"path": str(file_path), "extension": file_path.suffix},
            )

        try:
            # Open PDF
            pdf_doc = fitz.open(file_path)

            # Extract page texts
            page_texts = {}
            full_text = []

            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                text = page.get_text()
                page_texts[page_num + 1] = text  # 1-indexed pages
                full_text.append(text)

            # Combine all text for hashing
            combined_text = "\n".join(full_text)
            content_hash = hashlib.sha256(combined_text.encode()).hexdigest()

            # Get file size
            file_size = file_path.stat().st_size

            # Extract metadata
            metadata = {}
            if extract_metadata:
                pdf_metadata = pdf_doc.metadata
                if pdf_metadata:
                    # Clean metadata (remove None values)
                    metadata = {
                        k: v
                        for k, v in pdf_metadata.items()
                        if v is not None and v != ""
                    }

            # Create Document
            document = Document(
                source_path=str(file_path),
                filename=file_path.name,
                doc_type=DocumentType.PDF,
                content_hash=content_hash,
                file_size=file_size,
                num_pages=len(pdf_doc),
                metadata=metadata,
            )

            pdf_doc.close()

            return document, page_texts

        except fitz.FitzError as e:
            raise PDFParsingError(
                f"Failed to parse PDF: {e}",
                details={"path": str(file_path), "error": str(e)},
            )
        except Exception as e:
            raise PDFParsingError(
                f"Unexpected error parsing PDF: {e}",
                details={"path": str(file_path), "error": str(e), "type": type(e).__name__},
            )

    def extract_page_text(self, file_path: str | Path, page_number: int) -> str:
        """
        Extract text from a specific page.

        Args:
            file_path: Path to PDF file
            page_number: Page number (1-indexed)

        Returns:
            Text content of the page

        Raises:
            PDFParsingError: If page extraction fails
        """
        file_path = Path(file_path)

        try:
            pdf_doc = fitz.open(file_path)

            # Convert to 0-indexed
            page_index = page_number - 1

            if page_index < 0 or page_index >= len(pdf_doc):
                raise PDFParsingError(
                    f"Page {page_number} out of range (1-{len(pdf_doc)})",
                    details={"page": page_number, "total_pages": len(pdf_doc)},
                )

            page = pdf_doc[page_index]
            text = page.get_text()
            pdf_doc.close()

            return text

        except fitz.FitzError as e:
            raise PDFParsingError(
                f"Failed to extract page {page_number}: {e}",
                details={"path": str(file_path), "page": page_number, "error": str(e)},
            )

    def get_page_count(self, file_path: str | Path) -> int:
        """
        Get number of pages in PDF.

        Args:
            file_path: Path to PDF file

        Returns:
            Number of pages

        Raises:
            PDFParsingError: If reading fails
        """
        file_path = Path(file_path)

        try:
            pdf_doc = fitz.open(file_path)
            page_count = len(pdf_doc)
            pdf_doc.close()
            return page_count

        except fitz.FitzError as e:
            raise PDFParsingError(
                f"Failed to get page count: {e}",
                details={"path": str(file_path), "error": str(e)},
            )

    def extract_text_with_positions(
        self, file_path: str | Path, page_number: int
    ) -> list[dict]:
        """
        Extract text with position information (for advanced use cases).

        Args:
            file_path: Path to PDF file
            page_number: Page number (1-indexed)

        Returns:
            List of text blocks with position info

        Raises:
            PDFParsingError: If extraction fails
        """
        file_path = Path(file_path)

        try:
            pdf_doc = fitz.open(file_path)
            page_index = page_number - 1

            if page_index < 0 or page_index >= len(pdf_doc):
                raise PDFParsingError(
                    f"Page {page_number} out of range",
                    details={"page": page_number, "total_pages": len(pdf_doc)},
                )

            page = pdf_doc[page_index]

            # Get text blocks with positions
            blocks = page.get_text("dict")["blocks"]

            result = []
            for block in blocks:
                if "lines" in block:  # Text block
                    for line in block["lines"]:
                        for span in line["spans"]:
                            result.append(
                                {
                                    "text": span["text"],
                                    "bbox": span["bbox"],  # (x0, y0, x1, y1)
                                    "font": span["font"],
                                    "size": span["size"],
                                }
                            )

            pdf_doc.close()
            return result

        except fitz.FitzError as e:
            raise PDFParsingError(
                f"Failed to extract positioned text: {e}",
                details={"path": str(file_path), "page": page_number, "error": str(e)},
            )
