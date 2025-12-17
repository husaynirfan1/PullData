"""
Document parsing module for PullData.

Handles extraction of text and tables from various document formats:
- PDF (via PyMuPDF and pdfplumber)
- DOCX (via python-docx)

Also provides text chunking strategies and content hashing.
"""

# PDF parsing
from pulldata.parsing.pdf_parser import PDFParser

# Table extraction
from pulldata.parsing.table_extractor import TableExtractor

# Text chunking
from pulldata.parsing.chunking import (
    FixedSizeChunker,
    TextChunker,
    get_chunker,
)

# DOCX parsing
from pulldata.parsing.docx_parser import DOCXParser

# Content hashing
from pulldata.parsing.hashing import (
    compute_document_fingerprint,
    detect_changed_chunks,
    hash_chunks,
    hash_document_content,
    hash_file,
    hash_text,
    has_content_changed,
)

__all__ = [
    # Parsers
    "PDFParser",
    "DOCXParser",
    "TableExtractor",
    # Chunkers
    "TextChunker",
    "FixedSizeChunker",
    "get_chunker",
    # Hashing
    "hash_text",
    "hash_file",
    "hash_document_content",
    "hash_chunks",
    "has_content_changed",
    "detect_changed_chunks",
    "compute_document_fingerprint",
]
