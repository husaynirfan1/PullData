"""
PDF parsing using PyMuPDF.

Extracts text content from PDF files with page-level granularity.
Handles text extraction, metadata, and page information.
Supports VLM-based OCR for scanned PDFs.
"""

import hashlib
from pathlib import Path
from typing import Optional, Any

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
    Supports VLM-based OCR for scanned PDFs with no text layer.
    """

    def __init__(self, ocr_config: Optional[Any] = None):
        """
        Initialize PDF parser.
        
        Args:
            ocr_config: Optional VLMConfig for OCR support
        """
        self.supported_extensions = {".pdf"}
        self.ocr_config = ocr_config
        self._vlm_client = None
        
        # Initialize VLM client if OCR is enabled
        if ocr_config and ocr_config.enabled:
            try:
                from pulldata.vlm import VLMClient
                self._vlm_client = VLMClient(
                    model_name=ocr_config.model,
                    base_url=ocr_config.base_url,
                    api_key=ocr_config.api_key,
                    timeout=ocr_config.timeout,
                    max_retries=ocr_config.max_retries,
                )
            except ImportError:
                pass  # VLM module not available

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
                
                # Check if OCR is needed (text layer is missing or minimal)
                if self._should_use_ocr(text):
                    text = self._ocr_page(page, page_num + 1)
                
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

    def _should_use_ocr(self, text: str) -> bool:
        """
        Check if OCR should be used for this page.
        
        Args:
            text: Extracted text from page
            
        Returns:
            True if OCR should be used, False otherwise
        """
        if not self._vlm_client or not self.ocr_config:
            return False
            
        if not self.ocr_config.use_for_scanned_pdfs:
            return False
        
        # Check if text is below threshold
        min_threshold = self.ocr_config.min_text_threshold
        return len(text.strip()) < min_threshold

    def _ocr_page(self, page: fitz.Page, page_number: int) -> str:
        """
        Perform OCR on a PDF page using VLM.
        
        Args:
            page: PyMuPDF page object
            page_number: Page number (1-indexed)
            
        Returns:
            OCR-extracted text
        """
        try:
            # Render page as image
            # Use higher resolution for better OCR
            mat = fitz.Matrix(2.0, 2.0)  # 2x scaling
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            from PIL import Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Use VLM for OCR
            text = self._vlm_client.ocr_pdf_page(img, page_number)
            
            return text
            
        except Exception as e:
            # If OCR fails, return empty string
            print(f"Warning: OCR failed for page {page_number}: {e}")
            return ""

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
