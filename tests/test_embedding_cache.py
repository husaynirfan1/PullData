"""Tests for pulldata.embedding.cache."""

import tempfile
from pathlib import Path

import pytest

from pulldata.core.datatypes import Embedding
from pulldata.embedding.cache import EmbeddingCache, InMemoryCache


class TestInMemoryCache:
    """Tests for InMemoryCache."""

    def test_create_cache(self):
        """Test creating an in-memory cache."""
        cache = InMemoryCache(max_size=100)
        assert cache.size() == 0
        assert cache.max_size == 100

    def test_put_and_get(self):
        """Test storing and retrieving embeddings."""
        cache = InMemoryCache()
        embedding = Embedding(
            chunk_id="chunk-1",
            vector=[0.1, 0.2, 0.3],
            dimension=3,
            model_name="test-model",
        )

        cache.put("chunk-1", embedding)
        retrieved = cache.get("chunk-1")

        assert retrieved is not None
        assert retrieved.chunk_id == "chunk-1"
        assert retrieved.vector == [0.1, 0.2, 0.3]
        assert retrieved.dimension == 3

    def test_get_nonexistent(self):
        """Test getting non-existent embedding returns None."""
        cache = InMemoryCache()
        assert cache.get("nonexistent") is None

    def test_has(self):
        """Test checking if embedding exists."""
        cache = InMemoryCache()
        embedding = Embedding(
            chunk_id="chunk-1",
            vector=[0.1, 0.2],
            dimension=2,
            model_name="test",
        )

        assert not cache.has("chunk-1")
        cache.put("chunk-1", embedding)
        assert cache.has("chunk-1")

    def test_clear(self):
        """Test clearing cache."""
        cache = InMemoryCache()
        embedding = Embedding(
            chunk_id="chunk-1",
            vector=[0.1],
            dimension=1,
            model_name="test",
        )

        cache.put("chunk-1", embedding)
        assert cache.size() == 1

        cache.clear()
        assert cache.size() == 0
        assert not cache.has("chunk-1")

    def test_max_size_limit(self):
        """Test that cache respects max size limit."""
        cache = InMemoryCache(max_size=3)

        # Add 4 embeddings
        for i in range(4):
            embedding = Embedding(
                chunk_id=f"chunk-{i}",
                vector=[float(i)],
                dimension=1,
                model_name="test",
            )
            cache.put(f"chunk-{i}", embedding)

        # Should only have 3 (oldest removed)
        assert cache.size() == 3
        assert not cache.has("chunk-0")  # First one removed
        assert cache.has("chunk-1")
        assert cache.has("chunk-2")
        assert cache.has("chunk-3")


class TestEmbeddingCache:
    """Tests for EmbeddingCache (disk-backed)."""

    def test_create_cache_with_dir(self):
        """Test creating cache with specified directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(cache_dir=tmpdir, use_disk=True)
            assert cache.cache_dir == Path(tmpdir)
            assert cache.cache_dir.exists()

    def test_create_cache_without_dir(self):
        """Test creating cache without specified directory."""
        cache = EmbeddingCache(use_disk=False)
        assert cache.cache_dir == Path(".embeddings_cache")

    def test_put_and_get_memory_only(self):
        """Test caching with memory only (no disk)."""
        cache = EmbeddingCache(use_disk=False)
        embedding = Embedding(
            chunk_id="chunk-1",
            vector=[0.1, 0.2, 0.3],
            dimension=3,
            model_name="test-model",
        )

        cache.put("chunk-1", embedding)
        retrieved = cache.get("chunk-1")

        assert retrieved is not None
        assert retrieved.chunk_id == "chunk-1"
        assert retrieved.vector == [0.1, 0.2, 0.3]

    def test_put_and_get_with_disk(self):
        """Test caching with disk persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(cache_dir=tmpdir, use_disk=True)
            embedding = Embedding(
                chunk_id="chunk-1",
                vector=[0.1, 0.2, 0.3, 0.4],
                dimension=4,
                model_name="test-model",
            )

            # Store embedding
            cache.put("chunk-1", embedding, text="Test text")

            # Clear memory to force disk read
            cache.memory_cache.clear()

            # Retrieve from disk
            retrieved = cache.get("chunk-1", text="Test text")
            assert retrieved is not None
            assert retrieved.chunk_id == "chunk-1"
            assert len(retrieved.vector) == 4

    def test_content_validation(self):
        """Test that cache validates content hasn't changed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(cache_dir=tmpdir, use_disk=True)
            embedding = Embedding(
                chunk_id="chunk-1",
                vector=[0.1, 0.2],
                dimension=2,
                model_name="test",
            )

            # Store with original text
            cache.put("chunk-1", embedding, text="Original text")

            # Try to retrieve with different text
            cache.memory_cache.clear()  # Force disk read
            retrieved = cache.get("chunk-1", text="Different text", validate_content=True)

            # Should return None because content changed
            assert retrieved is None
            assert not cache.has("chunk-1")  # Should be invalidated

    def test_content_validation_disabled(self):
        """Test retrieving without content validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(cache_dir=tmpdir, use_disk=True)
            embedding = Embedding(
                chunk_id="chunk-1",
                vector=[0.1, 0.2],
                dimension=2,
                model_name="test",
            )

            cache.put("chunk-1", embedding, text="Original text")
            cache.memory_cache.clear()

            # Retrieve without validation
            retrieved = cache.get("chunk-1", text="Different text", validate_content=False)
            assert retrieved is not None

    def test_invalidate(self):
        """Test invalidating cached embedding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(cache_dir=tmpdir, use_disk=True)
            embedding = Embedding(
                chunk_id="chunk-1",
                vector=[0.1],
                dimension=1,
                model_name="test",
            )

            cache.put("chunk-1", embedding)
            assert cache.has("chunk-1")

            cache.invalidate("chunk-1")
            assert not cache.has("chunk-1")
            assert cache.get("chunk-1") is None

    def test_clear_all(self):
        """Test clearing entire cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(cache_dir=tmpdir, use_disk=True)

            # Add multiple embeddings
            for i in range(3):
                embedding = Embedding(
                    chunk_id=f"chunk-{i}",
                    vector=[float(i)],
                    dimension=1,
                    model_name="test",
                )
                cache.put(f"chunk-{i}", embedding)

            stats = cache.get_stats()
            assert stats["memory_size"] == 3
            assert stats["disk_size"] == 3

            cache.clear()

            stats = cache.get_stats()
            assert stats["memory_size"] == 0
            assert stats["disk_size"] == 0

    def test_get_stats(self):
        """Test getting cache statistics."""
        cache = EmbeddingCache(use_disk=False, max_memory_size=100)
        stats = cache.get_stats()

        assert "memory_size" in stats
        assert "disk_size" in stats
        assert "max_memory_size" in stats
        assert stats["max_memory_size"] == 100
        assert stats["memory_size"] == 0

    def test_get_cached_ids(self):
        """Test getting list of cached IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(cache_dir=tmpdir, use_disk=True)

            # Add embeddings
            for i in range(3):
                embedding = Embedding(
                    chunk_id=f"chunk-{i}",
                    vector=[float(i)],
                    dimension=1,
                    model_name="test",
                )
                cache.put(f"chunk-{i}", embedding)

            cached_ids = cache.get_cached_ids()
            assert len(cached_ids) == 3
            assert "chunk-0" in cached_ids
            assert "chunk-1" in cached_ids
            assert "chunk-2" in cached_ids

    def test_memory_size_limit(self):
        """Test that memory cache respects size limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(cache_dir=tmpdir, use_disk=True, max_memory_size=2)

            # Add 3 embeddings
            for i in range(3):
                embedding = Embedding(
                    chunk_id=f"chunk-{i}",
                    vector=[float(i)],
                    dimension=1,
                    model_name="test",
                )
                cache.put(f"chunk-{i}", embedding)

            # Memory should only have 2
            stats = cache.get_stats()
            assert stats["memory_size"] == 2
            # But disk should have all 3
            assert stats["disk_size"] == 3

    def test_subdirectory_structure(self):
        """Test that cache creates subdirectories for organization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = EmbeddingCache(cache_dir=tmpdir, use_disk=True)
            embedding = Embedding(
                chunk_id="ab-chunk-1",
                vector=[0.1],
                dimension=1,
                model_name="test",
            )

            cache.put("ab-chunk-1", embedding)

            # Should create subdirectory based on first 2 chars
            subdir = Path(tmpdir) / "ab"
            assert subdir.exists()
            cache_file = subdir / "ab-chunk-1.pkl"
            assert cache_file.exists()
