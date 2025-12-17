"""Embedding cache for storing and retrieving computed embeddings.

This module provides caching functionality to avoid recomputing embeddings
for the same content. Supports both in-memory and disk-based caching.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path
from typing import Optional, Union

import numpy as np

from pulldata.core.datatypes import Embedding
from pulldata.core.exceptions import CacheError


class EmbeddingCache:
    """Cache for storing and retrieving embeddings.

    Supports both in-memory caching (fast) and disk-based caching (persistent).
    Uses content hashing to detect when embeddings need to be regenerated.

    Attributes:
        cache_dir: Directory for disk-based cache
        use_disk: Whether to persist cache to disk
        memory_cache: In-memory cache dictionary

    Example:
        >>> cache = EmbeddingCache(cache_dir="embeddings_cache")
        >>> cache.put("chunk-123", embedding, "This is the text")
        >>> embedding = cache.get("chunk-123", "This is the text")
    """

    def __init__(
        self,
        cache_dir: Optional[str | Path] = None,
        use_disk: bool = True,
        max_memory_size: int = 10000,
    ):
        """Initialize the embedding cache.

        Args:
            cache_dir: Directory for disk cache. Uses '.embeddings_cache' if None.
            use_disk: Whether to persist embeddings to disk
            max_memory_size: Maximum number of embeddings to keep in memory
        """
        self.use_disk = use_disk
        self.max_memory_size = max_memory_size
        self.memory_cache: dict[str, Embedding] = {}

        if cache_dir is None:
            cache_dir = Path(".embeddings_cache")
        self.cache_dir = Path(cache_dir)

        if use_disk:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.metadata_file = self.cache_dir / "cache_metadata.json"
            self._load_metadata()

    def _load_metadata(self) -> None:
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    self.metadata = json.load(f)
            except Exception:
                self.metadata = {}
        else:
            self.metadata = {}

    def _save_metadata(self) -> None:
        """Save cache metadata to disk."""
        if self.use_disk:
            try:
                with open(self.metadata_file, "w") as f:
                    json.dump(self.metadata, f, indent=2)
            except Exception as e:
                raise CacheError(
                    "Failed to save cache metadata",
                    details={"metadata_file": str(self.metadata_file), "error": str(e)},
                ) from e

    def _compute_content_hash(self, text: str) -> str:
        """Compute hash of text content for cache key validation.

        Args:
            text: Text content to hash

        Returns:
            SHA-256 hash of the text
        """
        return hashlib.sha256(text.encode()).hexdigest()

    def _get_cache_path(self, chunk_id: str) -> Path:
        """Get file path for cached embedding.

        Args:
            chunk_id: Chunk identifier

        Returns:
            Path to cache file
        """
        # Use first 2 chars of ID for directory structure (avoid too many files in one dir)
        safe_id = chunk_id.replace("/", "_").replace("\\", "_")
        subdir = self.cache_dir / safe_id[:2] if len(safe_id) >= 2 else self.cache_dir
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir / f"{safe_id}.pkl"

    def get(
        self,
        chunk_id: str,
        text: Optional[str] = None,
        validate_content: bool = True,
    ) -> Optional[Embedding]:
        """Retrieve embedding from cache.

        Args:
            chunk_id: Chunk identifier
            text: Original text (for content validation)
            validate_content: Whether to validate text hasn't changed

        Returns:
            Cached Embedding or None if not found or invalid
        """
        # Check memory cache first
        if chunk_id in self.memory_cache:
            embedding = self.memory_cache[chunk_id]

            # Validate content if text provided
            if validate_content and text is not None:
                content_hash = self._compute_content_hash(text)
                stored_hash = self.metadata.get(chunk_id, {}).get("content_hash")
                if stored_hash != content_hash:
                    # Content changed, invalidate cache
                    self.invalidate(chunk_id)
                    return None

            return embedding

        # Check disk cache
        if self.use_disk:
            cache_path = self._get_cache_path(chunk_id)
            if cache_path.exists():
                try:
                    with open(cache_path, "rb") as f:
                        embedding = pickle.load(f)

                    # Validate content if text provided
                    if validate_content and text is not None:
                        content_hash = self._compute_content_hash(text)
                        stored_hash = self.metadata.get(chunk_id, {}).get("content_hash")
                        if stored_hash != content_hash:
                            # Content changed, invalidate cache
                            self.invalidate(chunk_id)
                            return None

                    # Add to memory cache
                    self._add_to_memory_cache(chunk_id, embedding)
                    return embedding

                except Exception as e:
                    raise CacheError(
                        f"Failed to load embedding from cache",
                        details={
                            "chunk_id": chunk_id,
                            "cache_path": str(cache_path),
                            "error": str(e),
                        },
                    ) from e

        return None

    def put(
        self,
        chunk_id: str,
        embedding: Embedding,
        text: Optional[str] = None,
    ) -> None:
        """Store embedding in cache.

        Args:
            chunk_id: Chunk identifier
            embedding: Embedding to cache
            text: Original text (for content validation later)
        """
        # Store in memory
        self._add_to_memory_cache(chunk_id, embedding)

        # Store to disk
        if self.use_disk:
            cache_path = self._get_cache_path(chunk_id)
            try:
                with open(cache_path, "wb") as f:
                    pickle.dump(embedding, f)

                # Update metadata
                self.metadata[chunk_id] = {
                    "dimension": embedding.dimension,
                    "model_name": embedding.model_name,
                }
                if text is not None:
                    self.metadata[chunk_id]["content_hash"] = self._compute_content_hash(text)

                self._save_metadata()

            except Exception as e:
                raise CacheError(
                    f"Failed to save embedding to cache",
                    details={
                        "chunk_id": chunk_id,
                        "cache_path": str(cache_path),
                        "error": str(e),
                    },
                ) from e

    def _add_to_memory_cache(self, chunk_id: str, embedding: Embedding) -> None:
        """Add embedding to memory cache with size limit."""
        # Remove oldest if at capacity (simple FIFO)
        if len(self.memory_cache) >= self.max_memory_size:
            # Remove first item
            first_key = next(iter(self.memory_cache))
            del self.memory_cache[first_key]

        self.memory_cache[chunk_id] = embedding

    def invalidate(self, chunk_id: str) -> None:
        """Remove embedding from cache.

        Args:
            chunk_id: Chunk identifier to invalidate
        """
        # Remove from memory
        if chunk_id in self.memory_cache:
            del self.memory_cache[chunk_id]

        # Remove from disk
        if self.use_disk:
            cache_path = self._get_cache_path(chunk_id)
            if cache_path.exists():
                cache_path.unlink()

            # Remove from metadata
            if chunk_id in self.metadata:
                del self.metadata[chunk_id]
                self._save_metadata()

    def clear(self) -> None:
        """Clear all cached embeddings."""
        # Clear memory
        self.memory_cache.clear()

        # Clear disk
        if self.use_disk:
            import shutil

            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)

            self.metadata = {}
            self._save_metadata()

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "memory_size": len(self.memory_cache),
            "disk_size": len(self.metadata) if self.use_disk else 0,
            "max_memory_size": self.max_memory_size,
        }

    def has(self, chunk_id: str) -> bool:
        """Check if embedding exists in cache.

        Args:
            chunk_id: Chunk identifier

        Returns:
            True if embedding is cached
        """
        if chunk_id in self.memory_cache:
            return True

        if self.use_disk:
            cache_path = self._get_cache_path(chunk_id)
            return cache_path.exists()

        return False

    def get_cached_ids(self) -> list[str]:
        """Get list of all cached chunk IDs.

        Returns:
            List of chunk IDs in cache
        """
        return list(self.metadata.keys()) if self.use_disk else list(self.memory_cache.keys())


class InMemoryCache:
    """Simple in-memory only embedding cache.

    Faster than EmbeddingCache but doesn't persist across sessions.

    Example:
        >>> cache = InMemoryCache()
        >>> cache.put("chunk-1", embedding)
        >>> embedding = cache.get("chunk-1")
    """

    def __init__(self, max_size: int = 10000):
        """Initialize in-memory cache.

        Args:
            max_size: Maximum number of embeddings to cache
        """
        self.max_size = max_size
        self.cache: dict[str, Embedding] = {}

    def get(self, chunk_id: str) -> Optional[Embedding]:
        """Get embedding from cache.

        Args:
            chunk_id: Chunk identifier

        Returns:
            Cached embedding or None
        """
        return self.cache.get(chunk_id)

    def put(self, chunk_id: str, embedding: Embedding) -> None:
        """Put embedding in cache.

        Args:
            chunk_id: Chunk identifier
            embedding: Embedding to cache
        """
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            first_key = next(iter(self.cache))
            del self.cache[first_key]

        self.cache[chunk_id] = embedding

    def clear(self) -> None:
        """Clear all cached embeddings."""
        self.cache.clear()

    def has(self, chunk_id: str) -> bool:
        """Check if embedding is cached.

        Args:
            chunk_id: Chunk identifier

        Returns:
            True if cached
        """
        return chunk_id in self.cache

    def size(self) -> int:
        """Get number of cached embeddings.

        Returns:
            Number of cached embeddings
        """
        return len(self.cache)
