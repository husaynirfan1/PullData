"""
Custom exceptions for PullData.

Provides a hierarchy of exceptions for different error scenarios throughout the system.
All exceptions inherit from the base PullDataError.
"""

from typing import Any, Optional


class PullDataError(Exception):
    """Base exception for all PullData errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


# Configuration Errors
class ConfigError(PullDataError):
    """Raised when there's an error in configuration loading or validation."""

    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""

    pass


class ConfigFileNotFoundError(ConfigError):
    """Raised when a configuration file is not found."""

    pass


# Storage Errors
class StorageError(PullDataError):
    """Base exception for storage-related errors."""

    pass


class StorageConnectionError(StorageError):
    """Raised when unable to connect to storage backend."""

    pass


class StorageInitializationError(StorageError):
    """Raised when storage backend initialization fails."""

    pass


class StorageQueryError(StorageError):
    """Raised when a storage query fails."""

    pass


class StorageIntegrityError(StorageError):
    """Raised when data integrity checks fail."""

    pass


class ProjectNotFoundError(StorageError):
    """Raised when a requested project doesn't exist."""

    pass


# Document Parsing Errors
class ParsingError(PullDataError):
    """Base exception for document parsing errors."""

    pass


class DocumentNotFoundError(ParsingError):
    """Raised when a document file is not found."""

    pass


class UnsupportedFormatError(ParsingError):
    """Raised when trying to parse an unsupported file format."""

    pass


class PDFParsingError(ParsingError):
    """Raised when PDF parsing fails."""

    pass


class TableExtractionError(ParsingError):
    """Raised when table extraction fails."""

    pass


class ChunkingError(ParsingError):
    """Raised when text chunking fails."""

    pass


# Embedding Errors
class EmbeddingError(PullDataError):
    """Base exception for embedding-related errors."""

    pass


class EmbedderLoadError(EmbeddingError):
    """Raised when embedding model fails to load."""

    pass


class EmbeddingGenerationError(EmbeddingError):
    """Raised when embedding generation fails."""

    pass


class EmbeddingDimensionMismatchError(EmbeddingError):
    """Raised when embedding dimensions don't match expected size."""

    pass


# Retrieval Errors
class RetrievalError(PullDataError):
    """Base exception for retrieval-related errors."""

    pass


class VectorIndexError(RetrievalError):
    """Raised when vector index operations fail."""

    pass


class SearchError(RetrievalError):
    """Raised when search operation fails."""

    pass


class RerankerError(RetrievalError):
    """Raised when reranking fails."""

    pass


# LLM Generation Errors
class LLMError(PullDataError):
    """Base exception for all LLM-related errors."""

    pass


class GenerationError(LLMError):
    """Base exception for LLM generation errors."""

    pass


class LLMLoadError(GenerationError):
    """Raised when LLM model fails to load."""

    pass


class LLMInferenceError(GenerationError):
    """Raised when LLM inference fails."""

    pass


class LLMTimeoutError(GenerationError):
    """Raised when LLM inference times out."""

    pass


class APIConnectionError(GenerationError):
    """Raised when API endpoint connection fails."""

    pass


class APIAuthenticationError(GenerationError):
    """Raised when API authentication fails."""

    pass


class APIRateLimitError(GenerationError):
    """Raised when API rate limit is exceeded."""

    pass


class PromptTooLongError(GenerationError):
    """Raised when prompt exceeds model's context length."""

    pass


# Output Synthesis Errors
class SynthesisError(PullDataError):
    """Base exception for output synthesis errors."""

    pass


class FormatterNotFoundError(SynthesisError):
    """Raised when requested output formatter is not available."""

    pass


class FormattingError(SynthesisError):
    """Raised when output formatting fails."""

    pass


class TemplateError(SynthesisError):
    """Raised when template loading or rendering fails."""

    pass


# Validation Errors
class ValidationError(PullDataError):
    """Base exception for data validation errors."""

    pass


class SchemaValidationError(ValidationError):
    """Raised when data doesn't match expected schema."""

    pass


class FileValidationError(ValidationError):
    """Raised when file validation fails (size, type, etc.)."""

    pass


# Cache Errors
class CacheError(PullDataError):
    """Base exception for caching-related errors."""

    pass


class CacheReadError(CacheError):
    """Raised when reading from cache fails."""

    pass


class CacheWriteError(CacheError):
    """Raised when writing to cache fails."""

    pass


# Vector Store Errors
class VectorStoreError(PullDataError):
    """Base exception for vector store operations."""

    pass


class MetadataStoreError(PullDataError):
    """Base exception for metadata store operations."""

    pass
