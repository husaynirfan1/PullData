"""
Retrieval component for RAG pipeline.

Handles document retrieval using vector search and metadata filtering.
"""

from __future__ import annotations

from typing import Any, Optional

from pulldata.core.datatypes import Chunk
from pulldata.embedding.embedder import Embedder
from pulldata.storage.hybrid_search import HybridSearchEngine, SearchResult


class RetrievalResult:
    """
    Represents a retrieval result with chunk and relevance score.
    """

    def __init__(
        self,
        chunk: Chunk,
        score: float,
        rank: int,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize retrieval result.

        Args:
            chunk: Retrieved chunk
            score: Relevance score (lower is better for L2 distance)
            rank: Result ranking (1-indexed)
            metadata: Additional metadata
        """
        self.chunk = chunk
        self.score = score
        self.rank = rank
        self.metadata = metadata or {}

    @classmethod
    def from_search_result(cls, search_result: SearchResult) -> RetrievalResult:
        """
        Create RetrievalResult from SearchResult.

        Args:
            search_result: SearchResult object

        Returns:
            RetrievalResult object
        """
        return cls(
            chunk=search_result.chunk,
            score=search_result.score,
            rank=search_result.rank,
        )

    def __repr__(self) -> str:
        return f"RetrievalResult(rank={self.rank}, score={self.score:.4f}, chunk_id={self.chunk.id})"


class Retriever:
    """
    Handles retrieval of relevant chunks for queries.

    Uses hybrid search (vector + metadata filtering) to find relevant chunks.
    """

    def __init__(
        self,
        search_engine: HybridSearchEngine,
        embedder: Embedder,
        top_k: int = 10,
        score_threshold: Optional[float] = None,
    ):
        """
        Initialize retriever.

        Args:
            search_engine: HybridSearchEngine instance
            embedder: Embedder instance for query encoding
            top_k: Number of results to retrieve
            score_threshold: Optional threshold for filtering results by score
        """
        self.search_engine = search_engine
        self.embedder = embedder
        self.top_k = top_k
        self.score_threshold = score_threshold

    def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Query string
            k: Number of results (defaults to self.top_k)
            filters: Optional metadata filters

        Returns:
            List of RetrievalResult objects
        """
        k = k or self.top_k

        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)

        # Perform search
        search_results = self.search_engine.search(
            query_embedding=query_embedding,
            k=k,
            filters=filters,
        )

        # Convert to RetrievalResults
        results = [
            RetrievalResult.from_search_result(sr)
            for sr in search_results
        ]

        # Apply score threshold if set
        if self.score_threshold is not None:
            results = [r for r in results if r.score <= self.score_threshold]

        return results

    def retrieve_similar(
        self,
        chunk_id: str,
        k: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve chunks similar to a given chunk.

        Args:
            chunk_id: Reference chunk ID
            k: Number of results (defaults to self.top_k)
            filters: Optional metadata filters

        Returns:
            List of RetrievalResult objects
        """
        k = k or self.top_k

        # Search for similar chunks
        search_results = self.search_engine.search_by_chunk_id(
            chunk_id=chunk_id,
            k=k,
            filters=filters,
        )

        # Convert to RetrievalResults
        results = [
            RetrievalResult.from_search_result(sr)
            for sr in search_results
        ]

        # Apply score threshold if set
        if self.score_threshold is not None:
            results = [r for r in results if r.score <= self.score_threshold]

        return results

    def retrieve_with_reranking(
        self,
        query: str,
        k: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
        rerank_multiplier: int = 3,
    ) -> list[RetrievalResult]:
        """
        Retrieve with re-ranking.

        Fetches more results initially, then re-ranks them.

        Args:
            query: Query string
            k: Final number of results (defaults to self.top_k)
            filters: Optional metadata filters
            rerank_multiplier: Fetch k * rerank_multiplier results before re-ranking

        Returns:
            List of RetrievalResult objects
        """
        k = k or self.top_k
        initial_k = k * rerank_multiplier

        # Retrieve initial results
        results = self.retrieve(query=query, k=initial_k, filters=filters)

        # Re-rank based on query relevance (simple lexical overlap for now)
        results = self._rerank_results(query, results)

        # Take top k
        results = results[:k]

        # Update ranks
        for i, result in enumerate(results, start=1):
            result.rank = i

        return results

    def _rerank_results(
        self,
        query: str,
        results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """
        Re-rank results based on query relevance.

        Simple implementation using lexical overlap.

        Args:
            query: Query string
            results: List of initial results

        Returns:
            Re-ranked list of results
        """
        query_tokens = set(query.lower().split())

        # Calculate lexical overlap scores
        for result in results:
            chunk_tokens = set(result.chunk.text.lower().split())
            overlap = len(query_tokens.intersection(chunk_tokens))
            total_tokens = len(query_tokens.union(chunk_tokens))

            # Jaccard similarity
            lexical_score = overlap / total_tokens if total_tokens > 0 else 0

            # Combine with vector score (normalize both to 0-1 range)
            # Lower vector score is better, higher lexical score is better
            combined_score = (1 - lexical_score) * 0.3 + result.score * 0.7

            result.metadata['lexical_score'] = lexical_score
            result.metadata['combined_score'] = combined_score
            result.score = combined_score

        # Sort by combined score (lower is better)
        results.sort(key=lambda r: r.score)

        return results

    def get_context(
        self,
        results: list[RetrievalResult],
        max_tokens: Optional[int] = None,
        separator: str = "\n\n---\n\n",
    ) -> str:
        """
        Assemble context from retrieval results.

        Args:
            results: List of RetrievalResult objects
            max_tokens: Optional maximum context length in tokens
            separator: Separator between chunks

        Returns:
            Assembled context string
        """
        context_parts = []
        total_tokens = 0

        for result in results:
            chunk_text = result.chunk.text
            chunk_tokens = len(chunk_text.split())  # Simple token estimation

            # Check token limit
            if max_tokens is not None and total_tokens + chunk_tokens > max_tokens:
                break

            # Add chunk with metadata
            metadata_str = f"[Document: {result.chunk.document_id}, Page: {result.chunk.start_page or 'N/A'}]"
            context_parts.append(f"{metadata_str}\n{chunk_text}")

            total_tokens += chunk_tokens

        return separator.join(context_parts)
