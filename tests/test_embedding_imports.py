"""Test that all embedding modules can be imported without errors."""

import pytest


def test_import_embedder():
    """Test importing embedder module."""
    from pulldata.embedding import embedder

    assert hasattr(embedder, "Embedder")
    assert hasattr(embedder, "load_embedder")


def test_import_cache():
    """Test importing cache module."""
    from pulldata.embedding import cache

    assert hasattr(cache, "EmbeddingCache")
    assert hasattr(cache, "InMemoryCache")


def test_import_from_embedding():
    """Test importing from embedding __init__."""
    from pulldata.embedding import Embedder, EmbeddingCache, InMemoryCache, load_embedder

    # Just check they're not None
    assert Embedder is not None
    assert load_embedder is not None
    assert EmbeddingCache is not None
    assert InMemoryCache is not None


def test_create_in_memory_cache():
    """Test creating InMemoryCache to verify basic functionality."""
    from pulldata.embedding import InMemoryCache

    cache = InMemoryCache(max_size=100)
    assert cache.size() == 0
    assert cache.max_size == 100


def test_create_embedding_cache():
    """Test creating EmbeddingCache to verify basic functionality."""
    from pulldata.embedding import EmbeddingCache

    cache = EmbeddingCache(use_disk=False)
    stats = cache.get_stats()
    assert "memory_size" in stats
    assert stats["memory_size"] == 0
