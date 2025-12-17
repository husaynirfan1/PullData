"""
Hybrid search combining vector similarity and metadata filtering.

Combines FAISS vector search with metadata-based filtering for
powerful and flexible document retrieval.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np

from pulldata.core.datatypes import Chunk, Embedding
from pulldata.core.exceptions import SearchError
from pulldata.storage.metadata_store import MetadataStore
from pulldata.storage.vector_store import VectorStore


class SearchResult:
    """
    Represents a search result with chunk and score.
    """

    def __init__(
        self,
        chunk: Chunk,
        score: float,
        rank: int,
    ):
        """
        Initialize search result.

        Args:
            chunk: Retrieved chunk
            score: Similarity score (lower is better for L2 distance)
            rank: Result ranking (1-indexed)
        """
        self.chunk = chunk
        self.score = score
        self.rank = rank

    def __repr__(self) -> str:
        return f"SearchResult(rank={self.rank}, score={self.score:.4f}, chunk_id={self.chunk.id})"


class HybridSearchEngine:
    """
    Hybrid search engine combining vector and metadata search.

    Performs vector similarity search using FAISS and filters results
    based on metadata criteria.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        metadata_store: MetadataStore,
    ):
        """
        Initialize hybrid search engine.

        Args:
            vector_store: VectorStore instance for similarity search
            metadata_store: MetadataStore instance for metadata retrieval
        """
        self.vector_store = vector_store
        self.metadata_store = metadata_store

    def search(
        self,
        query_embedding: Embedding,
        k: int = 10,
        filters: Optional[dict[str, Any]] = None,
        rerank_multiplier: int = 3,
    ) -> list[SearchResult]:
        """
        Perform hybrid search.

        Args:
            query_embedding: Query embedding
            k: Number of results to return
            filters: Optional metadata filters
                - document_id: Filter by document ID
                - chunk_type: Filter by chunk type
                - min_char_count: Minimum character count
                - max_char_count: Maximum character count
            rerank_multiplier: Fetch this many times k results before filtering

        Returns:
            List of SearchResult objects

        Raises:
            SearchError: If search fails
        """
        try:
            # Fetch more results to account for filtering
            fetch_k = k * rerank_multiplier if filters else k

            # Perform vector search
            chunk_ids, distances = self.vector_store.search(
                query_vector=query_embedding,
                k=fetch_k,
            )

            # Debug logging
            from loguru import logger
            logger.debug(f"HybridSearch: vector search returned {len(chunk_ids)} chunk_ids")

            if not chunk_ids:
                logger.warning("HybridSearch: No chunk_ids returned from vector search!")
                return []

            # Retrieve chunks from metadata store
            chunks = []
            valid_distances = []

            for chunk_id, distance in zip(chunk_ids, distances):
                chunk = self.metadata_store.get_chunk(chunk_id)
                if chunk is not None:
                    chunks.append(chunk)
                    valid_distances.append(distance)
                else:
                    logger.warning(f"HybridSearch: chunk_id '{chunk_id}' not found in metadata store!")

            logger.debug(f"HybridSearch: Retrieved {len(chunks)} chunks from metadata store")

            # Apply filters if provided
            if filters:
                filtered_chunks = []
                filtered_distances = []

                for chunk, distance in zip(chunks, valid_distances):
                    if self._matches_filters(chunk, filters):
                        filtered_chunks.append(chunk)
                        filtered_distances.append(distance)

                chunks = filtered_chunks
                valid_distances = filtered_distances

            # Limit to k results
            chunks = chunks[:k]
            valid_distances = valid_distances[:k]

            # Create search results
            results = []
            for rank, (chunk, score) in enumerate(zip(chunks, valid_distances), start=1):
                results.append(SearchResult(
                    chunk=chunk,
                    score=score,
                    rank=rank,
                ))

            return results

        except Exception as e:
            raise SearchError(f"Search failed: {str(e)}")

    def search_by_text(
        self,
        query_text: str,
        embedder,  # Embedder instance
        k: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        """
        Search using text query (automatically generates embedding).

        Args:
            query_text: Text query
            embedder: Embedder instance to generate query embedding
            k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of SearchResult objects
        """
        # Generate embedding for query
        query_embedding = embedder.embed_text(query_text)

        # Perform search
        return self.search(
            query_embedding=query_embedding,
            k=k,
            filters=filters,
        )

    def search_by_chunk_id(
        self,
        chunk_id: str,
        k: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        """
        Find similar chunks to a given chunk.

        Args:
            chunk_id: ID of the reference chunk
            k: Number of results to return (excluding the query chunk itself)
            filters: Optional metadata filters

        Returns:
            List of SearchResult objects

        Raises:
            SearchError: If chunk not found
        """
        # Get the chunk from metadata store
        chunk = self.metadata_store.get_chunk(chunk_id)
        if chunk is None:
            raise SearchError(f"Chunk not found: {chunk_id}")

        # Find the embedding in vector store
        # Note: This assumes chunk_ids in vector_store match metadata_store
        try:
            idx = self.vector_store.chunk_ids.index(chunk_id)
        except ValueError:
            raise SearchError(f"Chunk embedding not found: {chunk_id}")

        # Get the vector
        vector = self.vector_store.index.reconstruct(idx)

        # Create temporary embedding
        temp_embedding = Embedding(
            chunk_id=chunk_id,
            vector=vector.tolist(),
            dimension=len(vector),
            model_name="",
        )

        # Search (fetch k+1 to exclude the query chunk)
        results = self.search(
            query_embedding=temp_embedding,
            k=k + 1,
            filters=filters,
        )

        # Filter out the query chunk itself
        results = [r for r in results if r.chunk.id != chunk_id][:k]

        # Re-rank
        for i, result in enumerate(results, start=1):
            result.rank = i

        return results

    def _matches_filters(self, chunk: Chunk, filters: dict[str, Any]) -> bool:
        """
        Check if chunk matches filter criteria.

        Args:
            chunk: Chunk to check
            filters: Filter dictionary

        Returns:
            True if chunk matches all filters
        """
        # Document ID filter
        if "document_id" in filters:
            if chunk.document_id != filters["document_id"]:
                return False

        # Chunk type filter
        if "chunk_type" in filters:
            if chunk.chunk_type.value != filters["chunk_type"]:
                return False

        # Character count filters
        if "min_char_count" in filters:
            if chunk.char_count < filters["min_char_count"]:
                return False

        if "max_char_count" in filters:
            if chunk.char_count > filters["max_char_count"]:
                return False

        # Page filters
        if "start_page" in filters and chunk.start_page is not None:
            if chunk.start_page < filters["start_page"]:
                return False

        if "end_page" in filters and chunk.end_page is not None:
            if chunk.end_page > filters["end_page"]:
                return False

        # Custom metadata filters
        if "metadata" in filters:
            for key, value in filters["metadata"].items():
                if chunk.metadata.get(key) != value:
                    return False

        return True

    def get_stats(self) -> dict:
        """
        Get search engine statistics.

        Returns:
            Dictionary with statistics from both stores
        """
        return {
            "vector_store": self.vector_store.get_stats(),
            "metadata_store": self.metadata_store.get_stats(),
        }
