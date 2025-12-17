"""Test that all core modules can be imported without errors."""

import pytest


def test_import_exceptions():
    """Test importing exceptions module."""
    from pulldata.core import exceptions

    assert hasattr(exceptions, "PullDataError")
    assert hasattr(exceptions, "ConfigError")
    assert hasattr(exceptions, "StorageError")


def test_import_datatypes():
    """Test importing datatypes module."""
    from pulldata.core import datatypes

    assert hasattr(datatypes, "Document")
    assert hasattr(datatypes, "Chunk")
    assert hasattr(datatypes, "Embedding")
    assert hasattr(datatypes, "Table")


def test_import_config():
    """Test importing config module."""
    from pulldata.core import config

    assert hasattr(config, "Config")
    assert hasattr(config, "load_config")
    assert hasattr(config, "save_config")


def test_import_core_module():
    """Test importing from core __init__."""
    from pulldata.core import (
        Chunk,
        Config,
        ConfigError,
        Document,
        Embedding,
        LLMResponse,
        Project,
        PullDataError,
        QueryResult,
        StorageError,
        Table,
        load_config,
    )

    # Just check they're not None
    assert Document is not None
    assert Chunk is not None
    assert Embedding is not None
    assert Table is not None
    assert QueryResult is not None
    assert LLMResponse is not None
    assert Project is not None
    assert Config is not None
    assert load_config is not None
    assert PullDataError is not None
    assert ConfigError is not None
    assert StorageError is not None


def test_create_simple_document():
    """Test creating a simple document to verify functionality."""
    from pulldata.core import Document, DocumentType

    doc = Document(
        source_path="/test/doc.pdf",
        filename="doc.pdf",
        doc_type=DocumentType.PDF,
        content_hash="abc123",
        file_size=1024,
    )
    assert doc.filename == "doc.pdf"
    assert doc.doc_type == DocumentType.PDF


def test_create_simple_config():
    """Test creating a simple config to verify functionality."""
    from pulldata.core import Config

    config = Config()
    assert config.storage.backend == "local"
    assert config.models.llm.provider == "local"
