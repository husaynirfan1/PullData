"""
Core data structures for PullData.

Defines Pydantic models for documents, chunks, embeddings, tables, and results.
All models use strict validation and provide serialization capabilities.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import numpy as np
from pydantic import BaseModel, Field, field_validator, model_validator


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    UNKNOWN = "unknown"


class ChunkType(str, Enum):
    """Type of text chunk."""

    TEXT = "text"  # Regular text chunk
    TABLE = "table"  # Table content
    HEADER = "header"  # Header/title
    FOOTER = "footer"  # Footer
    CAPTION = "caption"  # Image/table caption


class OutputFormat(str, Enum):
    """Supported output formats."""

    EXCEL = "excel"
    MARKDOWN = "markdown"
    JSON = "json"
    PPTX = "pptx"
    LATEX = "latex"
    PDF = "pdf"


# ============================================================
# Document and Content Models
# ============================================================


class Document(BaseModel):
    """
    Represents a source document.

    Stores metadata and content hash for a document that has been ingested
    into the system.
    """

    id: Optional[str] = None  # Assigned by storage backend
    source_path: str = Field(..., description="Original file path")
    filename: str = Field(..., description="File name")
    doc_type: DocumentType = Field(default=DocumentType.UNKNOWN)
    content_hash: str = Field(..., description="SHA-256 hash of content")

    # Metadata
    file_size: int = Field(..., gt=0, description="File size in bytes")
    num_pages: Optional[int] = Field(None, ge=1, description="Number of pages (for PDFs)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: Optional[datetime] = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    # Custom metadata (tags, categories, etc.)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    @field_validator("source_path", "filename")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @property
    def source_path_obj(self) -> Path:
        """Return source_path as a Path object."""
        return Path(self.source_path)


class Chunk(BaseModel):
    """
    Represents a text chunk extracted from a document.

    Chunks are the primary unit for retrieval and processing.
    """

    id: Optional[str] = None  # Assigned by storage backend
    document_id: str = Field(..., description="Parent document ID")
    chunk_index: int = Field(..., ge=0, description="Index within document")
    chunk_hash: str = Field(..., description="SHA-256 hash of chunk content")

    # Content
    text: str = Field(..., min_length=1, description="Chunk text content")
    chunk_type: ChunkType = Field(default=ChunkType.TEXT)

    # Position information
    page_number: Optional[int] = Field(None, ge=1, description="Page number (for PDFs)")
    start_char: Optional[int] = Field(None, ge=0, description="Start char position in document")
    end_char: Optional[int] = Field(None, ge=0, description="End char position in document")

    # Token information
    token_count: int = Field(..., gt=0, description="Number of tokens")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_positions(self) -> "Chunk":
        """Validate that start_char < end_char if both are set."""
        if (
            self.start_char is not None
            and self.end_char is not None
            and self.start_char >= self.end_char
        ):
            raise ValueError("start_char must be less than end_char")
        return self


class Embedding(BaseModel):
    """
    Represents a vector embedding for a chunk.

    Stores the dense vector representation along with metadata.
    """

    id: Optional[str] = None
    chunk_id: str = Field(..., description="Associated chunk ID")
    vector: list[float] = Field(..., description="Embedding vector")
    dimension: int = Field(..., gt=0, description="Vector dimension")
    model_name: str = Field(..., description="Embedding model used")

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    @field_validator("vector")
    @classmethod
    def validate_vector_dimension(cls, v: list[float], info) -> list[float]:
        """Ensure vector length matches dimension if dimension is set."""
        if not v:
            raise ValueError("Vector cannot be empty")
        return v

    @model_validator(mode="after")
    def validate_dimension_matches(self) -> "Embedding":
        """Validate vector length matches dimension field."""
        if len(self.vector) != self.dimension:
            raise ValueError(
                f"Vector length {len(self.vector)} doesn't match dimension {self.dimension}"
            )
        return self

    @property
    def vector_array(self) -> np.ndarray:
        """Return vector as numpy array."""
        return np.array(self.vector, dtype=np.float32)


# ============================================================
# Table Models
# ============================================================


class TableCell(BaseModel):
    """Represents a single cell in a table."""

    row: int = Field(..., ge=0)
    col: int = Field(..., ge=0)
    value: str = Field(default="")
    cell_type: str = Field(default="data")  # 'header', 'data', 'footer'

    # Span information
    rowspan: int = Field(default=1, ge=1)
    colspan: int = Field(default=1, ge=1)


class Table(BaseModel):
    """
    Represents an extracted table from a document.

    Stores table structure, headers, and cell data.
    """

    id: Optional[str] = None
    document_id: str = Field(..., description="Parent document ID")
    table_index: int = Field(..., ge=0, description="Index within document")

    # Position information
    page_number: Optional[int] = Field(None, ge=1)
    bbox: Optional[tuple[float, float, float, float]] = Field(
        None, description="Bounding box (x0, y0, x1, y1)"
    )

    # Structure
    num_rows: int = Field(..., gt=0)
    num_cols: int = Field(..., gt=0)
    headers: list[str] = Field(default_factory=list)
    cells: list[TableCell] = Field(default_factory=list)

    # Metadata
    caption: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_cell(self, row: int, col: int) -> Optional[TableCell]:
        """Get cell at specified row and column."""
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None

    def to_dict(self) -> list[dict[str, str]]:
        """
        Convert table to list of dictionaries (one per row).

        Returns:
            List where each dict maps header -> cell value
        """
        if not self.headers or not self.cells:
            return []

        # Group cells by row
        rows_dict: dict[int, dict[int, str]] = {}
        for cell in self.cells:
            if cell.row not in rows_dict:
                rows_dict[cell.row] = {}
            rows_dict[cell.row][cell.col] = cell.value

        # Convert to list of dicts
        result = []
        for row_idx in sorted(rows_dict.keys()):
            row_data = {}
            for col_idx, header in enumerate(self.headers):
                row_data[header] = rows_dict[row_idx].get(col_idx, "")
            result.append(row_data)

        return result


# ============================================================
# Query and Response Models
# ============================================================


class RetrievedChunk(BaseModel):
    """A chunk retrieved during search with relevance score."""

    chunk: Chunk
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    rank: int = Field(..., ge=1, description="Rank in results")


class LLMResponse(BaseModel):
    """
    Response from LLM generation.

    Wraps the generated text along with metadata about the generation.
    """

    text: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used for generation")
    provider: str = Field(..., description="Provider type (local or api)")

    # Token usage
    prompt_tokens: Optional[int] = Field(None, ge=0)
    completion_tokens: Optional[int] = Field(None, ge=0)
    total_tokens: Optional[int] = Field(None, ge=0)

    # Generation metadata
    finish_reason: Optional[str] = None
    generation_time: Optional[float] = Field(None, ge=0.0, description="Time in seconds")

    # Cache information
    from_cache: bool = Field(default=False)
    cache_key: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class QueryResult(BaseModel):
    """
    Complete result from a query operation.

    Includes retrieved chunks, LLM response, and synthesized output.
    """

    query: str = Field(..., description="Original query")
    output_format: Optional[OutputFormat] = None

    # Retrieval results
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    retrieved_tables: list[Table] = Field(default_factory=list)

    # LLM response
    llm_response: Optional[LLMResponse] = None

    # Synthesized output
    output_data: Optional[dict[str, Any]] = Field(
        None, description="Structured output data"
    )
    output_path: Optional[str] = Field(None, description="Path to output file if saved")

    # Metadata
    total_time: Optional[float] = Field(None, ge=0.0, description="Total query time in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def save(self, path: str) -> None:
        """
        Save the query result to a file.

        This is a placeholder - actual implementation will depend on output_format.
        """
        # Will be implemented in synthesis module
        raise NotImplementedError("save() will be implemented in synthesis module")


# ============================================================
# Project Model
# ============================================================


class Project(BaseModel):
    """
    Represents a PullData project.

    Projects provide isolation for different document collections.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: str = Field(default="", description="Project description")

    # Statistics
    num_documents: int = Field(default=0, ge=0)
    num_chunks: int = Field(default=0, ge=0)
    num_tables: int = Field(default=0, ge=0)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    @field_validator("name")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        """Validate project name (alphanumeric, underscore, hyphen only)."""
        v = v.strip()
        if not v:
            raise ValueError("Project name cannot be empty")

        # Allow alphanumeric, underscore, hyphen
        if not all(c.isalnum() or c in ("_", "-") for c in v):
            raise ValueError(
                "Project name can only contain letters, numbers, underscores, and hyphens"
            )

        return v
