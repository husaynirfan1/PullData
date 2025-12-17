"""
Query processing for RAG pipeline.

Handles query preprocessing, expansion, and understanding.
"""

from __future__ import annotations

import re
from typing import Any, Optional


class ProcessedQuery:
    """
    Represents a processed query with metadata.
    """

    def __init__(
        self,
        original_query: str,
        processed_query: str,
        expanded_queries: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize processed query.

        Args:
            original_query: Original user query
            processed_query: Cleaned/normalized query
            expanded_queries: Optional list of expanded query variations
            metadata: Additional query metadata
        """
        self.original_query = original_query
        self.processed_query = processed_query
        self.expanded_queries = expanded_queries or []
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"ProcessedQuery(original='{self.original_query[:50]}...', processed='{self.processed_query[:50]}...')"


class QueryProcessor:
    """
    Processes queries for RAG pipeline.

    Handles query cleaning, normalization, and optional expansion.
    """

    def __init__(
        self,
        lowercase: bool = True,
        remove_punctuation: bool = False,
        expand_queries: bool = False,
        max_query_length: int = 1000,
    ):
        """
        Initialize query processor.

        Args:
            lowercase: Convert query to lowercase
            remove_punctuation: Remove punctuation from query
            expand_queries: Generate query variations
            max_query_length: Maximum allowed query length
        """
        self.lowercase = lowercase
        self.remove_punctuation = remove_punctuation
        self.expand_queries = expand_queries
        self.max_query_length = max_query_length

    def process(self, query: str, **metadata) -> ProcessedQuery:
        """
        Process a query.

        Args:
            query: User query string
            **metadata: Additional metadata to attach to the query

        Returns:
            ProcessedQuery object

        Raises:
            ValueError: If query is empty or too long
        """
        # Validate query
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        query = query.strip()

        if len(query) > self.max_query_length:
            raise ValueError(
                f"Query too long: {len(query)} characters (max: {self.max_query_length})"
            )

        # Store original
        original_query = query

        # Clean query
        processed_query = self._clean_query(query)

        # Generate expansions if enabled
        expanded_queries = []
        if self.expand_queries:
            expanded_queries = self._expand_query(processed_query)

        return ProcessedQuery(
            original_query=original_query,
            processed_query=processed_query,
            expanded_queries=expanded_queries,
            metadata=metadata,
        )

    def _clean_query(self, query: str) -> str:
        """
        Clean and normalize query.

        Args:
            query: Raw query string

        Returns:
            Cleaned query string
        """
        # Normalize whitespace
        query = " ".join(query.split())

        # Lowercase if enabled
        if self.lowercase:
            query = query.lower()

        # Remove punctuation if enabled
        if self.remove_punctuation:
            query = re.sub(r'[^\w\s]', ' ', query)
            query = " ".join(query.split())

        return query

    def _expand_query(self, query: str) -> list[str]:
        """
        Generate query variations.

        Args:
            query: Processed query

        Returns:
            List of query variations
        """
        expansions = []

        # Simple expansion: add question variations
        if not query.endswith('?'):
            expansions.append(f"{query}?")

        # Add "what is" variation if not present
        if not query.lower().startswith(('what', 'how', 'why', 'when', 'where', 'who')):
            expansions.append(f"what is {query}")

        return expansions

    def extract_filters(self, query: str) -> tuple[str, dict[str, Any]]:
        """
        Extract metadata filters from query.

        Recognizes patterns like:
        - "document:filename.pdf"
        - "type:table"
        - "page:5"

        Args:
            query: Query string with potential filters

        Returns:
            Tuple of (cleaned_query, filters_dict)
        """
        filters = {}
        cleaned_query = query

        # Extract document filter
        doc_match = re.search(r'document:(\S+)', query)
        if doc_match:
            filters['document_id'] = doc_match.group(1)
            cleaned_query = cleaned_query.replace(doc_match.group(0), '').strip()

        # Extract chunk type filter
        type_match = re.search(r'type:(\w+)', query)
        if type_match:
            filters['chunk_type'] = type_match.group(1)
            cleaned_query = cleaned_query.replace(type_match.group(0), '').strip()

        # Extract page filter
        page_match = re.search(r'page:(\d+)', query)
        if page_match:
            filters['start_page'] = int(page_match.group(1))
            filters['end_page'] = int(page_match.group(1))
            cleaned_query = cleaned_query.replace(page_match.group(0), '').strip()

        # Clean up extra whitespace
        cleaned_query = " ".join(cleaned_query.split())

        return cleaned_query, filters
