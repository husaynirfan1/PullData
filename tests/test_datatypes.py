"""Tests for pulldata.core.datatypes."""

from datetime import datetime

import numpy as np
import pytest
from pydantic import ValidationError

from pulldata.core.datatypes import (
    Chunk,
    ChunkType,
    Document,
    DocumentType,
    Embedding,
    LLMResponse,
    OutputFormat,
    Project,
    QueryResult,
    RetrievedChunk,
    Table,
    TableCell,
)


class TestDocument:
    """Tests for Document model."""

    def test_create_document(self):
        """Test creating a valid document."""
        doc = Document(
            source_path="/path/to/doc.pdf",
            filename="doc.pdf",
            doc_type=DocumentType.PDF,
            content_hash="abc123",
            file_size=1024,
            num_pages=10,
        )
        assert doc.filename == "doc.pdf"
        assert doc.doc_type == DocumentType.PDF
        assert doc.num_pages == 10

    def test_document_validation(self):
        """Test document validation."""
        with pytest.raises(ValidationError):
            # Missing required fields
            Document(filename="test.pdf")

        with pytest.raises(ValidationError):
            # Negative file size
            Document(
                source_path="/test.pdf",
                filename="test.pdf",
                content_hash="abc",
                file_size=-100,
            )

    def test_document_metadata(self):
        """Test document custom metadata."""
        doc = Document(
            source_path="/test.pdf",
            filename="test.pdf",
            content_hash="abc",
            file_size=1000,
            metadata={"author": "John Doe", "tags": ["financial", "Q3"]},
        )
        assert doc.metadata["author"] == "John Doe"
        assert "financial" in doc.metadata["tags"]


class TestChunk:
    """Tests for Chunk model."""

    def test_create_chunk(self):
        """Test creating a valid chunk."""
        chunk = Chunk(
            document_id="doc-123",
            chunk_index=0,
            chunk_hash="xyz789",
            text="This is a test chunk.",
            token_count=5,
            page_number=1,
            start_char=0,
            end_char=21,
        )
        assert chunk.text == "This is a test chunk."
        assert chunk.chunk_type == ChunkType.TEXT
        assert chunk.page_number == 1

    def test_chunk_position_validation(self):
        """Test chunk position validation."""
        # Valid positions
        chunk = Chunk(
            document_id="doc-123",
            chunk_index=0,
            chunk_hash="xyz",
            text="Test",
            token_count=1,
            start_char=0,
            end_char=4,
        )
        assert chunk.start_char < chunk.end_char

        # Invalid positions
        with pytest.raises(ValidationError):
            Chunk(
                document_id="doc-123",
                chunk_index=0,
                chunk_hash="xyz",
                text="Test",
                token_count=1,
                start_char=10,
                end_char=5,  # end before start
            )


class TestEmbedding:
    """Tests for Embedding model."""

    def test_create_embedding(self):
        """Test creating a valid embedding."""
        vector = [0.1, 0.2, 0.3, 0.4]
        emb = Embedding(
            chunk_id="chunk-123", vector=vector, dimension=4, model_name="bge-small"
        )
        assert len(emb.vector) == 4
        assert emb.dimension == 4

    def test_embedding_dimension_mismatch(self):
        """Test embedding dimension validation."""
        with pytest.raises(ValidationError):
            # Vector length doesn't match dimension
            Embedding(
                chunk_id="chunk-123",
                vector=[0.1, 0.2, 0.3],
                dimension=5,  # Mismatch!
                model_name="test",
            )

    def test_embedding_to_array(self):
        """Test converting embedding to numpy array."""
        vector = [0.1, 0.2, 0.3, 0.4]
        emb = Embedding(chunk_id="chunk-123", vector=vector, dimension=4, model_name="test")
        arr = emb.vector_array
        assert isinstance(arr, np.ndarray)
        assert arr.shape == (4,)
        assert np.allclose(arr, vector)


class TestTable:
    """Tests for Table model."""

    def test_create_table(self):
        """Test creating a table."""
        table = Table(
            document_id="doc-123",
            table_index=0,
            num_rows=2,
            num_cols=3,
            headers=["Col1", "Col2", "Col3"],
            cells=[
                TableCell(row=0, col=0, value="A"),
                TableCell(row=0, col=1, value="B"),
                TableCell(row=0, col=2, value="C"),
            ],
        )
        assert table.num_rows == 2
        assert table.num_cols == 3
        assert len(table.headers) == 3

    def test_table_get_cell(self):
        """Test getting cell from table."""
        table = Table(
            document_id="doc-123",
            table_index=0,
            num_rows=1,
            num_cols=2,
            cells=[
                TableCell(row=0, col=0, value="A"),
                TableCell(row=0, col=1, value="B"),
            ],
        )
        cell = table.get_cell(0, 1)
        assert cell is not None
        assert cell.value == "B"

        missing_cell = table.get_cell(10, 10)
        assert missing_cell is None

    def test_table_to_dict(self):
        """Test converting table to list of dictionaries."""
        table = Table(
            document_id="doc-123",
            table_index=0,
            num_rows=2,
            num_cols=2,
            headers=["Name", "Age"],
            cells=[
                TableCell(row=0, col=0, value="Alice"),
                TableCell(row=0, col=1, value="30"),
                TableCell(row=1, col=0, value="Bob"),
                TableCell(row=1, col=1, value="25"),
            ],
        )
        result = table.to_dict()
        assert len(result) == 2
        assert result[0] == {"Name": "Alice", "Age": "30"}
        assert result[1] == {"Name": "Bob", "Age": "25"}


class TestLLMResponse:
    """Tests for LLMResponse model."""

    def test_create_llm_response(self):
        """Test creating LLM response."""
        response = LLMResponse(
            text="Generated text",
            model="Qwen2.5-3B",
            provider="local",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        assert response.text == "Generated text"
        assert response.provider == "local"
        assert response.total_tokens == 150
        assert not response.from_cache

    def test_cached_response(self):
        """Test cached LLM response."""
        response = LLMResponse(
            text="Cached text",
            model="gpt-3.5-turbo",
            provider="api",
            from_cache=True,
            cache_key="query_hash_123",
        )
        assert response.from_cache
        assert response.cache_key == "query_hash_123"


class TestQueryResult:
    """Tests for QueryResult model."""

    def test_create_query_result(self):
        """Test creating query result."""
        chunk = Chunk(
            document_id="doc-1",
            chunk_index=0,
            chunk_hash="abc",
            text="Test chunk",
            token_count=2,
        )
        retrieved = RetrievedChunk(chunk=chunk, score=0.95, rank=1)

        result = QueryResult(
            query="What is the revenue?",
            retrieved_chunks=[retrieved],
            output_format=OutputFormat.EXCEL,
        )
        assert result.query == "What is the revenue?"
        assert len(result.retrieved_chunks) == 1
        assert result.retrieved_chunks[0].score == 0.95


class TestProject:
    """Tests for Project model."""

    def test_create_project(self):
        """Test creating a project."""
        project = Project(name="test_project", description="Test project")
        assert project.name == "test_project"
        assert project.num_documents == 0

    def test_project_name_validation(self):
        """Test project name validation."""
        # Valid names
        Project(name="valid_name")
        Project(name="valid-name")
        Project(name="valid123")

        # Invalid names
        with pytest.raises(ValidationError):
            Project(name="")  # Empty

        with pytest.raises(ValidationError):
            Project(name="invalid name")  # Space

        with pytest.raises(ValidationError):
            Project(name="invalid@name")  # Special char
