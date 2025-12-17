"""
Vector storage using FAISS for efficient similarity search.

This module provides a wrapper around FAISS (Facebook AI Similarity Search)
for storing and querying vector embeddings.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Optional, Union

import faiss
import numpy as np

from pulldata.core.datatypes import Embedding
from pulldata.core.exceptions import VectorStoreError


class VectorStore:
    """
    FAISS-based vector storage for embeddings.

    Provides efficient similarity search using FAISS indices with support
    for different index types (Flat, IVF, HNSW).
    """

    def __init__(
        self,
        dimension: int,
        index_type: str = "Flat",
        metric: str = "L2",
        nlist: int = 100,
    ):
        """
        Initialize vector store.

        Args:
            dimension: Dimensionality of vectors
            index_type: FAISS index type ("Flat", "IVF", "HNSW")
            metric: Distance metric ("L2" or "IP" for inner product)
            nlist: Number of clusters for IVF index
        """
        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        self.nlist = nlist

        # Create FAISS index
        self.index = self._create_index()

        # Track chunk IDs corresponding to vectors
        self.chunk_ids: list[str] = []

    def _create_index(self) -> faiss.Index:
        """Create FAISS index based on configuration."""
        if self.metric == "L2":
            measure = faiss.METRIC_L2
        elif self.metric == "IP":
            measure = faiss.METRIC_INNER_PRODUCT
        else:
            raise VectorStoreError(f"Unsupported metric: {self.metric}")

        if self.index_type == "Flat":
            # Exact search (brute force)
            index = faiss.IndexFlatL2(self.dimension) if self.metric == "L2" else faiss.IndexFlatIP(self.dimension)
        elif self.index_type == "IVF":
            # Inverted file index (faster but approximate)
            quantizer = faiss.IndexFlatL2(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist, measure)
        elif self.index_type == "HNSW":
            # Hierarchical Navigable Small World (fast approximate search)
            index = faiss.IndexHNSWFlat(self.dimension, 32, measure)
        else:
            raise VectorStoreError(f"Unsupported index type: {self.index_type}")

        return index

    def add(self, embeddings: list[Embedding]) -> None:
        """
        Add embeddings to the index.

        Args:
            embeddings: List of Embedding objects to add

        Raises:
            VectorStoreError: If embeddings have wrong dimension
        """
        if not embeddings:
            return

        # Validate dimensions
        for emb in embeddings:
            if emb.dimension != self.dimension:
                raise VectorStoreError(
                    f"Embedding dimension {emb.dimension} does not match store dimension {self.dimension}"
                )

        # Convert to numpy array
        vectors = np.array([emb.vector for emb in embeddings], dtype=np.float32)

        # Train index if needed (for IVF)
        if self.index_type == "IVF" and not self.index.is_trained:
            self.index.train(vectors)

        # Add vectors
        self.index.add(vectors)

        # Track chunk IDs
        self.chunk_ids.extend([emb.chunk_id for emb in embeddings])

    def add_single(self, embedding: Embedding) -> None:
        """
        Add a single embedding to the index.

        Args:
            embedding: Embedding object to add
        """
        self.add([embedding])

    def search(
        self,
        query_vector: Union[list[float], np.ndarray, Embedding],
        k: int = 10,
        nprobe: int = 10,
    ) -> tuple[list[str], list[float]]:
        """
        Search for k nearest neighbors.

        Args:
            query_vector: Query vector (list, numpy array, or Embedding)
            k: Number of results to return
            nprobe: Number of clusters to search (for IVF index)

        Returns:
            Tuple of (chunk_ids, distances)

        Raises:
            VectorStoreError: If index is empty or query has wrong dimension
        """
        if self.size == 0:
            raise VectorStoreError("Cannot search empty index")

        # Convert query to numpy array
        if isinstance(query_vector, Embedding):
            query = np.array([query_vector.vector], dtype=np.float32)
        elif isinstance(query_vector, list):
            query = np.array([query_vector], dtype=np.float32)
        else:
            query = query_vector.reshape(1, -1).astype(np.float32)

        # Validate dimension
        if query.shape[1] != self.dimension:
            raise VectorStoreError(
                f"Query dimension {query.shape[1]} does not match store dimension {self.dimension}"
            )

        # Set nprobe for IVF index
        if self.index_type == "IVF":
            self.index.nprobe = nprobe

        # Search
        distances, indices = self.index.search(query, k)

        # Convert to lists and filter out invalid indices
        distances = distances[0].tolist()
        indices = indices[0].tolist()

        # Get chunk IDs for valid indices
        chunk_ids = []
        valid_distances = []
        for idx, dist in zip(indices, distances):
            if 0 <= idx < len(self.chunk_ids):
                chunk_ids.append(self.chunk_ids[idx])
                valid_distances.append(dist)

        return chunk_ids, valid_distances

    def remove(self, chunk_ids: list[str]) -> int:
        """
        Remove vectors by chunk IDs.

        Note: This rebuilds the index, which can be slow for large indices.

        Args:
            chunk_ids: List of chunk IDs to remove

        Returns:
            Number of vectors removed
        """
        # Find indices to keep
        indices_to_keep = [
            i for i, cid in enumerate(self.chunk_ids)
            if cid not in chunk_ids
        ]

        if len(indices_to_keep) == len(self.chunk_ids):
            return 0  # Nothing to remove

        # Reconstruct vectors for indices to keep
        vectors_to_keep = np.zeros((len(indices_to_keep), self.dimension), dtype=np.float32)
        for new_idx, old_idx in enumerate(indices_to_keep):
            vectors_to_keep[new_idx] = self.index.reconstruct(old_idx)

        # Create new index
        old_size = self.size
        self.index = self._create_index()
        self.chunk_ids = [self.chunk_ids[i] for i in indices_to_keep]

        # Re-add vectors
        if len(vectors_to_keep) > 0:
            if self.index_type == "IVF":
                self.index.train(vectors_to_keep)
            self.index.add(vectors_to_keep)

        return old_size - self.size

    def save(self, path: Union[str, Path]) -> None:
        """
        Save index to disk.

        Args:
            path: Directory path to save index
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_path = path / "index.faiss"
        faiss.write_index(self.index, str(index_path))

        # Save metadata
        metadata = {
            "dimension": self.dimension,
            "index_type": self.index_type,
            "metric": self.metric,
            "nlist": self.nlist,
            "chunk_ids": self.chunk_ids,
        }
        metadata_path = path / "metadata.pkl"
        with open(metadata_path, "wb") as f:
            pickle.dump(metadata, f)

    @classmethod
    def load(cls, path: Union[str, Path]) -> VectorStore:
        """
        Load index from disk.

        Args:
            path: Directory path containing saved index

        Returns:
            Loaded VectorStore instance
        """
        path = Path(path)

        # Load metadata
        metadata_path = path / "metadata.pkl"
        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)

        # Create instance
        store = cls(
            dimension=metadata["dimension"],
            index_type=metadata["index_type"],
            metric=metadata["metric"],
            nlist=metadata["nlist"],
        )

        # Load FAISS index
        index_path = path / "index.faiss"
        store.index = faiss.read_index(str(index_path))
        store.chunk_ids = metadata["chunk_ids"]

        return store

    @property
    def size(self) -> int:
        """Return number of vectors in the index."""
        return self.index.ntotal

    def clear(self) -> None:
        """Clear all vectors from the index."""
        self.index = self._create_index()
        self.chunk_ids = []

    def get_stats(self) -> dict:
        """
        Get index statistics.

        Returns:
            Dictionary with index statistics
        """
        return {
            "size": self.size,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "metric": self.metric,
            "is_trained": self.index.is_trained if hasattr(self.index, "is_trained") else True,
        }
