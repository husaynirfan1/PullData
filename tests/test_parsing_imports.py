"""Test that all parsing modules can be imported without errors."""

import pytest


def test_import_parsing_module():
    """Test importing parsing module."""
    from pulldata import parsing

    assert hasattr(parsing, "PDFParser")
    assert hasattr(parsing, "DOCXParser")
    assert hasattr(parsing, "TableExtractor")
    assert hasattr(parsing, "TextChunker")


def test_import_parsers():
    """Test importing parser classes."""
    from pulldata.parsing import DOCXParser, PDFParser, TableExtractor

    assert PDFParser is not None
    assert DOCXParser is not None
    assert TableExtractor is not None


def test_import_chunkers():
    """Test importing chunker classes."""
    from pulldata.parsing import FixedSizeChunker, TextChunker, get_chunker

    assert TextChunker is not None
    assert FixedSizeChunker is not None
    assert get_chunker is not None


def test_import_hashing():
    """Test importing hashing functions."""
    from pulldata.parsing import (
        compute_document_fingerprint,
        hash_document_content,
        hash_file,
        hash_text,
    )

    assert hash_text is not None
    assert hash_file is not None
    assert hash_document_content is not None
    assert compute_document_fingerprint is not None


def test_create_pdf_parser():
    """Test creating a PDF parser instance."""
    from pulldata.parsing import PDFParser

    parser = PDFParser()
    assert parser is not None
    assert hasattr(parser, "parse")
    assert hasattr(parser, "is_supported")


def test_create_docx_parser():
    """Test creating a DOCX parser instance."""
    from pulldata.parsing import DOCXParser

    parser = DOCXParser()
    assert parser is not None
    assert hasattr(parser, "parse")
    assert hasattr(parser, "is_supported")


def test_create_table_extractor():
    """Test creating a table extractor instance."""
    from pulldata.parsing import TableExtractor

    extractor = TableExtractor()
    assert extractor is not None
    assert hasattr(extractor, "extract_tables_from_pdf")


def test_create_text_chunker():
    """Test creating a text chunker instance."""
    from pulldata.parsing import TextChunker

    chunker = TextChunker()
    assert chunker is not None
    assert hasattr(chunker, "chunk_text")


def test_get_chunker_factory():
    """Test get_chunker factory function."""
    from pulldata.parsing import get_chunker

    semantic_chunker = get_chunker("semantic")
    assert semantic_chunker is not None

    fixed_chunker = get_chunker("fixed")
    assert fixed_chunker is not None


def test_hash_text_function():
    """Test hash_text function works."""
    from pulldata.parsing import hash_text

    hash_value = hash_text("Test content")
    assert isinstance(hash_value, str)
    assert len(hash_value) == 64  # SHA-256


def test_integration_imports():
    """Test importing multiple components together."""
    from pulldata.core import Chunk, Document
    from pulldata.parsing import (
        PDFParser,
        TextChunker,
        hash_document_content,
    )

    # Should all be importable together
    assert Document is not None
    assert Chunk is not None
    assert PDFParser is not None
    assert TextChunker is not None
    assert hash_document_content is not None
