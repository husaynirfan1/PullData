"""
Embedding generation module for PullData.

Provides text embedding using transformer models:
- BGE embeddings (default: bge-small-en-v1.5)
- Embedding caching for performance
- Batch processing support
"""

from pulldata.embedding.cache import EmbeddingCache, InMemoryCache
from pulldata.embedding.embedder import Embedder, load_embedder

__all__ = [
    "Embedder",
    "load_embedder",
    "EmbeddingCache",
    "InMemoryCache",
]
