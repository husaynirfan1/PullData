"""Tests for pulldata.parsing.chunking."""

import pytest

from pulldata.core.datatypes import Chunk, ChunkType
from pulldata.core.exceptions import ChunkingError
from pulldata.parsing.chunking import (
    FixedSizeChunker,
    TextChunker,
    get_chunker,
)


class TestTextChunker:
    """Tests for TextChunker (semantic)."""

    def test_create_chunker(self):
        """Test creating a text chunker."""
        chunker = TextChunker(
            chunk_size=100,
            chunk_overlap=10,
            min_chunk_size=50,
        )
        assert chunker.chunk_size == 100
        assert chunker.chunk_overlap == 10
        assert chunker.min_chunk_size == 50

    def test_chunk_simple_text(self):
        """Test chunking simple text."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "This is a test. " * 100  # Long text

        chunks = chunker.chunk_text(text, document_id="doc-1")

        assert len(chunks) > 0
        for chunk in chunks:
            assert isinstance(chunk, Chunk)
            assert chunk.document_id == "doc-1"
            assert chunk.text
            assert chunk.token_count > 0

    def test_chunk_with_page_number(self):
        """Test chunking with page number."""
        chunker = TextChunker(chunk_size=50)
        text = "Sample text for testing chunking with page numbers."

        chunks = chunker.chunk_text(text, document_id="doc-1", page_number=5)

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.page_number == 5

    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("", document_id="doc-1")
        assert len(chunks) == 0

        chunks = chunker.chunk_text("   ", document_id="doc-1")
        assert len(chunks) == 0

    def test_chunk_indices(self):
        """Test chunk indices are sequential."""
        chunker = TextChunker(chunk_size=50)
        text = "This is sentence one. " * 50

        chunks = chunker.chunk_text(text, document_id="doc-1")

        for idx, chunk in enumerate(chunks):
            assert chunk.chunk_index == idx

    def test_chunk_hashes_unique(self):
        """Test chunk hashes are unique for different content."""
        chunker = TextChunker(chunk_size=20)
        text1 = "This is the first chunk of text."
        text2 = "This is the second chunk of text."

        chunks1 = chunker.chunk_text(text1, document_id="doc-1")
        chunks2 = chunker.chunk_text(text2, document_id="doc-2")

        # Different text should have different hashes
        assert chunks1[0].chunk_hash != chunks2[0].chunk_hash

    def test_estimate_tokens(self):
        """Test token estimation."""
        chunker = TextChunker()

        # ~4 characters per token
        text1 = "word"  # 4 chars = ~1 token
        assert chunker._estimate_tokens(text1) == 1

        text2 = "word " * 100  # 500 chars = ~125 tokens
        tokens = chunker._estimate_tokens(text2)
        assert 100 < tokens < 150  # Rough estimate


class TestFixedSizeChunker:
    """Tests for FixedSizeChunker."""

    def test_create_fixed_chunker(self):
        """Test creating fixed-size chunker."""
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)
        assert chunker.chunk_size == 100
        assert chunker.chunk_overlap == 20

    def test_fixed_chunking(self):
        """Test fixed-size chunking."""
        chunker = FixedSizeChunker(chunk_size=50, chunk_overlap=10)
        text = "A" * 1000  # Long uniform text

        chunks = chunker.chunk_text(text, document_id="doc-1")

        assert len(chunks) > 0
        for chunk in chunks:
            assert isinstance(chunk, Chunk)
            assert chunk.document_id == "doc-1"


class TestGetChunker:
    """Tests for get_chunker factory function."""

    def test_get_semantic_chunker(self):
        """Test getting semantic chunker."""
        chunker = get_chunker("semantic", chunk_size=100)
        assert isinstance(chunker, TextChunker)
        assert chunker.respect_sentence_boundary is True

    def test_get_fixed_chunker(self):
        """Test getting fixed-size chunker."""
        chunker = get_chunker("fixed", chunk_size=100)
        assert isinstance(chunker, FixedSizeChunker)

    def test_get_sentence_chunker(self):
        """Test getting sentence-based chunker."""
        chunker = get_chunker("sentence", chunk_size=100)
        assert isinstance(chunker, TextChunker)
        assert chunker.respect_sentence_boundary is True

    def test_invalid_strategy(self):
        """Test invalid chunking strategy."""
        with pytest.raises(ChunkingError):
            get_chunker("invalid_strategy")


class TestChunkingIntegration:
    """Integration tests for chunking."""

    def test_chunk_long_document(self):
        """Test chunking a long document."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)

        # Simulate long document
        paragraphs = [
            "This is the first paragraph. It contains multiple sentences. " * 10,
            "This is the second paragraph. More text here. " * 10,
            "This is the third paragraph. Final section. " * 10,
        ]
        text = "\n\n".join(paragraphs)

        chunks = chunker.chunk_text(text, document_id="doc-1", page_number=1)

        # Verify basic properties
        assert len(chunks) > 3  # Should create multiple chunks
        assert all(c.page_number == 1 for c in chunks)
        assert all(c.document_id == "doc-1" for c in chunks)

        # Verify positions make sense
        for i in range(len(chunks) - 1):
            assert chunks[i].end_char <= chunks[i + 1].end_char

    def test_chunk_with_special_characters(self):
        """Test chunking text with special characters."""
        chunker = TextChunker(chunk_size=50)
        text = "Hello! How are you? I'm fine. Let's test: special (chars) & symbols."

        chunks = chunker.chunk_text(text, document_id="doc-1")

        assert len(chunks) > 0
        # Text should be preserved
        combined = "".join(c.text for c in chunks)
        # Should contain the original content (possibly with overlap)
        assert "Hello!" in combined
        assert "special" in combined
