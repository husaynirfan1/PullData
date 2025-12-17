"""
Embedding generation module for PullData.

Provides text embedding using:
- Local models via sentence-transformers (Embedder)
- API-based via OpenAI-compatible endpoints (APIEmbedder)

Supports both local and API-based embedding generation for flexibility.
"""

from pulldata.embedding.api_embedder import APIEmbedder
from pulldata.embedding.cache import EmbeddingCache, InMemoryCache
from pulldata.embedding.embedder import Embedder, load_embedder

__all__ = [
    "Embedder",
    "APIEmbedder",
    "load_embedder",
    "EmbeddingCache",
    "InMemoryCache",
]
