"""
RAG Pipeline for PullData.

Orchestrates query processing, retrieval, context assembly, and response generation.
"""

from __future__ import annotations

from typing import Any, Optional

from pulldata.core.datatypes import Chunk
from pulldata.core.exceptions import SearchError, LLMError
from pulldata.embedding.embedder import Embedder
from pulldata.rag.query_processor import ProcessedQuery, QueryProcessor
from pulldata.rag.retriever import Retriever, RetrievalResult
from pulldata.storage.hybrid_search import HybridSearchEngine

# Optional LLM imports
try:
    from pulldata.llm.base import BaseLLM, LLMResponse
    from pulldata.llm.prompts import PromptManager
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    BaseLLM = None
    LLMResponse = None
    PromptManager = None


class RAGResponse:
    """
    Represents a complete RAG pipeline response.
    """

    def __init__(
        self,
        query: str,
        processed_query: ProcessedQuery,
        retrieved_chunks: list[RetrievalResult],
        context: str,
        answer: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize RAG response.

        Args:
            query: Original query
            processed_query: Processed query object
            retrieved_chunks: List of retrieved chunks
            context: Assembled context
            answer: Optional generated answer
            metadata: Additional response metadata
        """
        self.query = query
        self.processed_query = processed_query
        self.retrieved_chunks = retrieved_chunks
        self.context = context
        self.answer = answer
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"RAGResponse(query='{self.query[:50]}...', num_chunks={len(self.retrieved_chunks)})"


class RAGPipeline:
    """
    Complete RAG pipeline.

    Handles the full retrieval-augmented generation workflow:
    1. Query processing
    2. Document retrieval
    3. Context assembly
    4. Response generation (optional)
    """

    def __init__(
        self,
        search_engine: HybridSearchEngine,
        embedder: Embedder,
        query_processor: Optional[QueryProcessor] = None,
        retriever: Optional[Retriever] = None,
        llm: Optional[BaseLLM] = None,
        prompt_manager: Optional[PromptManager] = None,
        top_k: int = 5,
        max_context_tokens: int = 2000,
        default_prompt_template: str = "detailed_qa",
    ):
        """
        Initialize RAG pipeline.

        Args:
            search_engine: HybridSearchEngine for retrieval
            embedder: Embedder for query encoding
            query_processor: Optional custom QueryProcessor
            retriever: Optional custom Retriever
            llm: Optional LLM for answer generation
            prompt_manager: Optional PromptManager for prompt templates
            top_k: Number of chunks to retrieve
            max_context_tokens: Maximum context length
            default_prompt_template: Default prompt template name
        """
        self.search_engine = search_engine
        self.embedder = embedder
        self.top_k = top_k
        self.max_context_tokens = max_context_tokens
        self.default_prompt_template = default_prompt_template

        # Initialize components
        self.query_processor = query_processor or QueryProcessor()
        self.retriever = retriever or Retriever(
            search_engine=search_engine,
            embedder=embedder,
            top_k=top_k,
        )

        # LLM components (optional)
        self.llm = llm
        if prompt_manager is not None:
            self.prompt_manager = prompt_manager
        elif LLM_AVAILABLE and PromptManager is not None:
            self.prompt_manager = PromptManager()
        else:
            self.prompt_manager = None

    def query(
        self,
        query: str,
        k: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
        use_reranking: bool = False,
    ) -> RAGResponse:
        """
        Execute RAG pipeline for a query.

        Args:
            query: User query
            k: Number of results (defaults to pipeline's top_k)
            filters: Optional metadata filters
            use_reranking: Whether to use re-ranking

        Returns:
            RAGResponse object

        Raises:
            SearchError: If retrieval fails
        """
        k = k or self.top_k

        # Step 1: Process query
        processed_query = self.query_processor.process(query)

        # Extract filters from query if not provided
        if filters is None:
            clean_query, extracted_filters = self.query_processor.extract_filters(
                processed_query.processed_query
            )
            if extracted_filters:
                processed_query.processed_query = clean_query
                filters = extracted_filters

        # Step 2: Retrieve relevant chunks
        try:
            if use_reranking:
                retrieved_chunks = self.retriever.retrieve_with_reranking(
                    query=processed_query.processed_query,
                    k=k,
                    filters=filters,
                )
            else:
                retrieved_chunks = self.retriever.retrieve(
                    query=processed_query.processed_query,
                    k=k,
                    filters=filters,
                )
        except Exception as e:
            raise SearchError(f"Retrieval failed: {str(e)}")

        # Step 3: Assemble context
        context = self.retriever.get_context(
            results=retrieved_chunks,
            max_tokens=self.max_context_tokens,
        )

        # Step 4: Create response (generation handled separately)
        response = RAGResponse(
            query=query,
            processed_query=processed_query,
            retrieved_chunks=retrieved_chunks,
            context=context,
            metadata={
                'num_retrieved': len(retrieved_chunks),
                'used_reranking': use_reranking,
                'filters': filters or {},
            },
        )

        return response

    def query_with_answer(
        self,
        query: str,
        k: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
        use_reranking: bool = False,
        prompt_template: Optional[str] = None,
        stream: bool = False,
        **llm_kwargs,
    ) -> RAGResponse:
        """
        Execute RAG pipeline with answer generation.

        Args:
            query: User query
            k: Number of results (defaults to pipeline's top_k)
            filters: Optional metadata filters
            use_reranking: Whether to use re-ranking
            prompt_template: Prompt template name (uses default if None)
            stream: Whether to stream the response
            **llm_kwargs: Additional LLM generation parameters

        Returns:
            RAGResponse object with generated answer

        Raises:
            LLMError: If LLM is not configured or generation fails
        """
        if self.llm is None:
            raise LLMError(
                "LLM not configured. Provide llm parameter during initialization.",
                details={"method": "query_with_answer"}
            )

        # Step 1-3: Execute standard RAG query
        response = self.query(
            query=query,
            k=k,
            filters=filters,
            use_reranking=use_reranking,
        )

        # Step 4: Generate answer
        response.answer = self.generate_answer(
            response=response,
            prompt_template=prompt_template,
            stream=stream,
            **llm_kwargs,
        )

        return response

    def generate_answer(
        self,
        response: RAGResponse,
        prompt_template: Optional[str] = None,
        stream: bool = False,
        **llm_kwargs,
    ) -> str:
        """
        Generate answer for an existing RAGResponse.

        Args:
            response: RAGResponse object
            prompt_template: Prompt template name (uses default if None)
            stream: Whether to stream the response
            **llm_kwargs: Additional LLM generation parameters

        Returns:
            Generated answer string

        Raises:
            LLMError: If LLM is not configured or generation fails
        """
        if self.llm is None:
            raise LLMError(
                "LLM not configured. Provide llm parameter during initialization.",
                details={"method": "generate_answer"}
            )

        # Select prompt template
        template_name = prompt_template or self.default_prompt_template

        # Format prompt
        if self.prompt_manager:
            prompt = self.prompt_manager.format_prompt(
                name=template_name,
                context=response.context,
                query=response.query,
            )
        else:
            # Fallback: basic template
            prompt = f"""Answer the following question based on the provided context.

Context:
{response.context}

Question: {response.query}

Answer:"""

        # Generate answer
        try:
            if stream:
                # Streaming generation
                answer_parts = []
                for chunk in self.llm.generate_stream(prompt, **llm_kwargs):
                    answer_parts.append(chunk)
                    # Note: In a real application, you'd yield these chunks
                answer = "".join(answer_parts)
            else:
                # Standard generation
                llm_response = self.llm.generate(prompt, **llm_kwargs)
                answer = llm_response.text

                # Store LLM metadata
                response.metadata["llm_response"] = {
                    "model": llm_response.model,
                    "tokens_used": llm_response.tokens_used,
                    "prompt_tokens": llm_response.prompt_tokens,
                    "completion_tokens": llm_response.completion_tokens,
                }

            return answer

        except Exception as e:
            raise LLMError(
                f"Answer generation failed: {str(e)}",
                details={"query": response.query, "error": str(e)}
            )

    def retrieve_only(
        self,
        query: str,
        k: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant chunks without generating a response.

        Args:
            query: User query
            k: Number of results
            filters: Optional metadata filters

        Returns:
            List of RetrievalResult objects
        """
        k = k or self.top_k

        # Process query
        processed_query = self.query_processor.process(query)

        # Extract filters if needed
        if filters is None:
            clean_query, extracted_filters = self.query_processor.extract_filters(
                processed_query.processed_query
            )
            if extracted_filters:
                processed_query.processed_query = clean_query
                filters = extracted_filters

        # Retrieve
        return self.retriever.retrieve(
            query=processed_query.processed_query,
            k=k,
            filters=filters,
        )

    def get_similar_chunks(
        self,
        chunk_id: str,
        k: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[RetrievalResult]:
        """
        Find chunks similar to a given chunk.

        Args:
            chunk_id: Reference chunk ID
            k: Number of results
            filters: Optional metadata filters

        Returns:
            List of RetrievalResult objects
        """
        k = k or self.top_k

        return self.retriever.retrieve_similar(
            chunk_id=chunk_id,
            k=k,
            filters=filters,
        )

    def batch_query(
        self,
        queries: list[str],
        k: Optional[int] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[RAGResponse]:
        """
        Process multiple queries in batch.

        Args:
            queries: List of query strings
            k: Number of results per query
            filters: Optional metadata filters

        Returns:
            List of RAGResponse objects
        """
        responses = []

        for query in queries:
            response = self.query(query=query, k=k, filters=filters)
            responses.append(response)

        return responses

    def update_config(
        self,
        top_k: Optional[int] = None,
        max_context_tokens: Optional[int] = None,
    ) -> None:
        """
        Update pipeline configuration.

        Args:
            top_k: New top_k value
            max_context_tokens: New max_context_tokens value
        """
        if top_k is not None:
            self.top_k = top_k
            self.retriever.top_k = top_k

        if max_context_tokens is not None:
            self.max_context_tokens = max_context_tokens

    def get_stats(self) -> dict[str, Any]:
        """
        Get pipeline statistics.

        Returns:
            Dictionary with pipeline stats
        """
        return {
            'top_k': self.top_k,
            'max_context_tokens': self.max_context_tokens,
            'search_engine_stats': self.search_engine.get_stats(),
        }
