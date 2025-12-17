"""Embedding generation using sentence-transformers (BGE models).

This module provides a wrapper around sentence-transformers for generating
embeddings from text chunks. Supports batch processing and caching.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from pulldata.core.datatypes import Chunk, Embedding
from pulldata.core.exceptions import (
    EmbedderLoadError,
    EmbeddingGenerationError,
)


class Embedder:
    """Wrapper for sentence-transformers embedding models.

    Supports BGE and other sentence-transformer models. Handles model loading,
    batch processing, and embedding generation.

    Attributes:
        model_name: Name of the sentence-transformers model
        device: Device to run model on ('cuda', 'cpu', or 'mps')
        normalize_embeddings: Whether to normalize embeddings to unit length
        batch_size: Batch size for processing multiple texts
        model: The loaded sentence-transformers model

    Example:
        >>> embedder = Embedder(model_name="BAAI/bge-small-en-v1.5")
        >>> embedding = embedder.embed_text("Hello world")
        >>> print(embedding.dimension)  # 384
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        device: Optional[str] = None,
        normalize_embeddings: bool = True,
        batch_size: int = 32,
        cache_folder: Optional[str | Path] = None,
    ):
        """Initialize the embedder.

        Args:
            model_name: HuggingFace model name or local path
            device: Device to use ('cuda', 'cpu', 'mps'). Auto-detected if None.
            normalize_embeddings: Whether to L2-normalize embeddings
            batch_size: Batch size for encoding
            cache_folder: Where to cache downloaded models

        Raises:
            EmbedderLoadError: If model fails to load
        """
        self.model_name = model_name
        self.normalize_embeddings = normalize_embeddings
        self.batch_size = batch_size

        # Auto-detect device
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        self.device = device

        # Load model
        try:
            self.model = SentenceTransformer(
                model_name,
                device=device,
                cache_folder=str(cache_folder) if cache_folder else None,
            )
            self._dimension = self.model.get_sentence_embedding_dimension()
        except Exception as e:
            raise EmbedderLoadError(
                f"Failed to load embedding model '{model_name}'",
                details={
                    "model_name": model_name,
                    "device": device,
                    "error": str(e),
                },
            ) from e

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension

    def embed_text(
        self,
        text: str,
        chunk_id: Optional[str] = None,
        show_progress_bar: bool = False,
    ) -> Embedding:
        """Generate embedding for a single text.

        Args:
            text: Input text to embed
            chunk_id: Optional chunk ID for the embedding
            show_progress_bar: Whether to show progress bar

        Returns:
            Embedding object with vector and metadata

        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        try:
            vector = self.model.encode(
                text,
                normalize_embeddings=self.normalize_embeddings,
                show_progress_bar=show_progress_bar,
                convert_to_numpy=True,
            )

            return Embedding(
                chunk_id=chunk_id or "",
                vector=vector.tolist(),
                dimension=len(vector),
                model_name=self.model_name,
            )
        except Exception as e:
            raise EmbeddingGenerationError(
                f"Failed to generate embedding for text",
                details={
                    "text_length": len(text),
                    "model": self.model_name,
                    "error": str(e),
                },
            ) from e

    def embed_texts(
        self,
        texts: list[str],
        chunk_ids: Optional[list[str]] = None,
        show_progress_bar: bool = True,
    ) -> list[Embedding]:
        """Generate embeddings for multiple texts (batched).

        Args:
            texts: List of input texts
            chunk_ids: Optional list of chunk IDs (must match texts length)
            show_progress_bar: Whether to show progress bar

        Returns:
            List of Embedding objects

        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        if chunk_ids is not None and len(chunk_ids) != len(texts):
            raise ValueError(
                f"chunk_ids length ({len(chunk_ids)}) must match texts length ({len(texts)})"
            )

        try:
            vectors = self.model.encode(
                texts,
                batch_size=self.batch_size,
                normalize_embeddings=self.normalize_embeddings,
                show_progress_bar=show_progress_bar,
                convert_to_numpy=True,
            )

            embeddings = []
            for i, vector in enumerate(vectors):
                chunk_id = chunk_ids[i] if chunk_ids else f"chunk-{i}"
                embeddings.append(
                    Embedding(
                        chunk_id=chunk_id,
                        vector=vector.tolist(),
                        dimension=len(vector),
                        model_name=self.model_name,
                    )
                )

            return embeddings
        except Exception as e:
            raise EmbeddingGenerationError(
                f"Failed to generate embeddings for {len(texts)} texts",
                details={
                    "num_texts": len(texts),
                    "batch_size": self.batch_size,
                    "model": self.model_name,
                    "error": str(e),
                },
            ) from e

    def embed_chunks(
        self,
        chunks: list[Chunk],
        show_progress_bar: bool = True,
    ) -> list[Embedding]:
        """Generate embeddings for a list of Chunk objects.

        Args:
            chunks: List of Chunk objects to embed
            show_progress_bar: Whether to show progress bar

        Returns:
            List of Embedding objects with chunk IDs

        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        texts = [chunk.text for chunk in chunks]
        chunk_ids = [chunk.id or f"chunk-{chunk.chunk_index}" for chunk in chunks]

        return self.embed_texts(
            texts=texts,
            chunk_ids=chunk_ids,
            show_progress_bar=show_progress_bar,
        )

    def compute_similarity(
        self,
        embedding1: Embedding | np.ndarray | list[float],
        embedding2: Embedding | np.ndarray | list[float],
    ) -> float:
        """Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding (Embedding object, numpy array, or list)
            embedding2: Second embedding (Embedding object, numpy array, or list)

        Returns:
            Cosine similarity score (0 to 1 if normalized, -1 to 1 otherwise)
        """
        # Convert to numpy arrays
        if isinstance(embedding1, Embedding):
            vec1 = embedding1.vector_array
        elif isinstance(embedding1, list):
            vec1 = np.array(embedding1)
        else:
            vec1 = embedding1

        if isinstance(embedding2, Embedding):
            vec2 = embedding2.vector_array
        elif isinstance(embedding2, list):
            vec2 = np.array(embedding2)
        else:
            vec2 = embedding2

        # Compute cosine similarity
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "device": self.device,
            "normalize_embeddings": self.normalize_embeddings,
            "batch_size": self.batch_size,
            "max_seq_length": self.model.max_seq_length,
        }


def load_embedder(
    model_name: str = "BAAI/bge-small-en-v1.5",
    device: Optional[str] = None,
    **kwargs,
) -> Embedder:
    """Load an embedder with the specified model.

    Convenience function for creating an Embedder instance.

    Args:
        model_name: HuggingFace model name or local path
        device: Device to use ('cuda', 'cpu', 'mps')
        **kwargs: Additional arguments passed to Embedder

    Returns:
        Initialized Embedder instance

    Example:
        >>> embedder = load_embedder("BAAI/bge-base-en-v1.5", device="cuda")
        >>> embedding = embedder.embed_text("Hello world")
    """
    return Embedder(model_name=model_name, device=device, **kwargs)
