"""Tests for pulldata.core.exceptions."""

import pytest

from pulldata.core.exceptions import (
    APIAuthenticationError,
    ConfigError,
    EmbeddingError,
    GenerationError,
    ParsingError,
    PullDataError,
    StorageError,
)


def test_base_exception():
    """Test base PullDataError."""
    error = PullDataError("Test error")
    assert str(error) == "Test error"
    assert error.message == "Test error"
    assert error.details == {}


def test_exception_with_details():
    """Test exception with details dictionary."""
    details = {"file": "test.pdf", "line": 42}
    error = PullDataError("Test error", details=details)
    assert error.details == details
    assert "file=test.pdf" in str(error)
    assert "line=42" in str(error)


def test_config_error_inheritance():
    """Test ConfigError inherits from PullDataError."""
    error = ConfigError("Config failed")
    assert isinstance(error, PullDataError)
    assert isinstance(error, ConfigError)


def test_storage_error_inheritance():
    """Test StorageError inherits from PullDataError."""
    error = StorageError("Storage failed")
    assert isinstance(error, PullDataError)
    assert isinstance(error, StorageError)


def test_parsing_error_inheritance():
    """Test ParsingError inherits from PullDataError."""
    error = ParsingError("Parsing failed")
    assert isinstance(error, PullDataError)
    assert isinstance(error, ParsingError)


def test_embedding_error_inheritance():
    """Test EmbeddingError inherits from PullDataError."""
    error = EmbeddingError("Embedding failed")
    assert isinstance(error, PullDataError)
    assert isinstance(error, EmbeddingError)


def test_generation_error_inheritance():
    """Test GenerationError inherits from PullDataError."""
    error = GenerationError("Generation failed")
    assert isinstance(error, PullDataError)
    assert isinstance(error, GenerationError)


def test_api_authentication_error():
    """Test API authentication error."""
    error = APIAuthenticationError(
        "Authentication failed", details={"api_key": "sk-***", "endpoint": "https://api.example.com"}
    )
    assert isinstance(error, GenerationError)
    assert "Authentication failed" in str(error)
    assert error.details["endpoint"] == "https://api.example.com"
