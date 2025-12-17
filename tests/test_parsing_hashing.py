"""Tests for pulldata.parsing.hashing."""

import tempfile
from pathlib import Path

import pytest

from pulldata.core.datatypes import Chunk, Document, DocumentType
from pulldata.parsing.hashing import (
    compute_document_fingerprint,
    detect_changed_chunks,
    hash_chunks,
    hash_document_content,
    hash_file,
    hash_text,
    has_content_changed,
)


class TestHashText:
    """Tests for hash_text function."""

    def test_hash_simple_text(self):
        """Test hashing simple text."""
        text = "Hello, World!"
        hash_value = hash_text(text)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 produces 64 hex characters

    def test_hash_same_text_same_hash(self):
        """Test same text produces same hash."""
        text = "Test content"
        hash1 = hash_text(text)
        hash2 = hash_text(text)
        assert hash1 == hash2

    def test_hash_different_text_different_hash(self):
        """Test different text produces different hash."""
        text1 = "First text"
        text2 = "Second text"
        hash1 = hash_text(text1)
        hash2 = hash_text(text2)
        assert hash1 != hash2

    def test_hash_with_md5(self):
        """Test hashing with MD5 algorithm."""
        text = "Test"
        hash_value = hash_text(text, algorithm="md5")
        assert len(hash_value) == 32  # MD5 produces 32 hex characters

    def test_hash_invalid_algorithm(self):
        """Test invalid hashing algorithm."""
        with pytest.raises(ValueError):
            hash_text("Test", algorithm="invalid")


class TestHashFile:
    """Tests for hash_file function."""

    def test_hash_file(self):
        """Test hashing a file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("File content for hashing")
            temp_path = f.name

        try:
            hash_value = hash_file(temp_path)
            assert isinstance(hash_value, str)
            assert len(hash_value) == 64
        finally:
            Path(temp_path).unlink()

    def test_hash_same_file_same_hash(self):
        """Test same file content produces same hash."""
        content = "Test file content"

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            hash1 = hash_file(temp_path)
            hash2 = hash_file(temp_path)
            assert hash1 == hash2
        finally:
            Path(temp_path).unlink()


class TestHashDocumentContent:
    """Tests for hash_document_content function."""

    def test_hash_string_content(self):
        """Test hashing string document content."""
        content = "Document text content"
        hash_value = hash_document_content(content)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_hash_dict_content(self):
        """Test hashing dict document content (pages)."""
        content = {
            1: "Page 1 text",
            2: "Page 2 text",
            3: "Page 3 text",
        }
        hash_value = hash_document_content(content)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64

    def test_hash_dict_order_matters(self):
        """Test dict content hash is consistent regardless of input order."""
        content1 = {1: "Page 1", 2: "Page 2"}
        content2 = {2: "Page 2", 1: "Page 1"}

        hash1 = hash_document_content(content1)
        hash2 = hash_document_content(content2)

        # Should be same because we sort by page number
        assert hash1 == hash2


class TestHashChunks:
    """Tests for hash_chunks function."""

    def test_hash_empty_chunks(self):
        """Test hashing empty chunk list."""
        hash_value = hash_chunks([])
        assert isinstance(hash_value, str)

    def test_hash_multiple_chunks(self):
        """Test hashing multiple chunks."""
        chunks = [
            Chunk(
                document_id="doc-1",
                chunk_index=0,
                chunk_hash="hash1",
                text="Chunk 1",
                token_count=2,
            ),
            Chunk(
                document_id="doc-1",
                chunk_index=1,
                chunk_hash="hash2",
                text="Chunk 2",
                token_count=2,
            ),
        ]
        hash_value = hash_chunks(chunks)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64


class TestHasContentChanged:
    """Tests for has_content_changed function."""

    def test_unchanged_content(self):
        """Test detecting unchanged content."""
        content = "Same content"
        old_hash = hash_text(content)
        assert not has_content_changed(old_hash, content)

    def test_changed_content(self):
        """Test detecting changed content."""
        old_content = "Old content"
        new_content = "New content"
        old_hash = hash_text(old_content)
        assert has_content_changed(old_hash, new_content)


class TestDetectChangedChunks:
    """Tests for detect_changed_chunks function."""

    def test_no_changes(self):
        """Test detecting no changes."""
        old_chunks = [
            Chunk(
                document_id="doc-1",
                chunk_index=0,
                chunk_hash=hash_text("Text 1"),
                text="Text 1",
                token_count=2,
            ),
            Chunk(
                document_id="doc-1",
                chunk_index=1,
                chunk_hash=hash_text("Text 2"),
                text="Text 2",
                token_count=2,
            ),
        ]
        new_texts = ["Text 1", "Text 2"]

        result = detect_changed_chunks(old_chunks, new_texts)

        assert len(result["changed"]) == 0
        assert len(result["unchanged"]) == 2
        assert result["unchanged"] == [0, 1]

    def test_some_changes(self):
        """Test detecting some changes."""
        old_chunks = [
            Chunk(
                document_id="doc-1",
                chunk_index=0,
                chunk_hash=hash_text("Text 1"),
                text="Text 1",
                token_count=2,
            ),
            Chunk(
                document_id="doc-1",
                chunk_index=1,
                chunk_hash=hash_text("Text 2"),
                text="Text 2",
                token_count=2,
            ),
        ]
        new_texts = ["Text 1", "Modified Text 2"]  # Second chunk changed

        result = detect_changed_chunks(old_chunks, new_texts)

        assert len(result["changed"]) == 1
        assert len(result["unchanged"]) == 1
        assert 1 in result["changed"]
        assert 0 in result["unchanged"]

    def test_different_chunk_count(self):
        """Test when chunk count changes."""
        old_chunks = [
            Chunk(
                document_id="doc-1",
                chunk_index=0,
                chunk_hash=hash_text("Text 1"),
                text="Text 1",
                token_count=2,
            ),
        ]
        new_texts = ["Text 1", "Text 2"]  # Added a chunk

        result = detect_changed_chunks(old_chunks, new_texts)

        # All considered changed when count differs
        assert len(result["changed"]) == 2
        assert len(result["unchanged"]) == 0


class TestComputeDocumentFingerprint:
    """Tests for compute_document_fingerprint function."""

    def test_compute_fingerprint(self):
        """Test computing document fingerprint."""
        doc = Document(
            source_path="/test/doc.pdf",
            filename="doc.pdf",
            doc_type=DocumentType.PDF,
            content_hash="abc123",
            file_size=1000,
        )

        fingerprint = compute_document_fingerprint(doc)

        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 64

    def test_different_docs_different_fingerprints(self):
        """Test different documents have different fingerprints."""
        doc1 = Document(
            source_path="/test/doc1.pdf",
            filename="doc1.pdf",
            doc_type=DocumentType.PDF,
            content_hash="hash1",
            file_size=1000,
        )

        doc2 = Document(
            source_path="/test/doc2.pdf",
            filename="doc2.pdf",
            doc_type=DocumentType.PDF,
            content_hash="hash2",
            file_size=2000,
        )

        fp1 = compute_document_fingerprint(doc1)
        fp2 = compute_document_fingerprint(doc2)

        assert fp1 != fp2
