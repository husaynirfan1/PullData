"""High-level pipeline orchestrator for PullData.

Provides the main user-facing API that integrates all components:
parsing, embedding, storage, retrieval, generation, and formatting.
"""

from __future__ import annotations

import warnings
import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

from pulldata.core.config import Config, load_config
from pulldata.core.datatypes import Document, QueryResult
from pulldata.core.exceptions import (
    ConfigError,
    EmbeddingError,
    ParsingError,
    StorageError,
)
from pulldata.embedding.cache import EmbeddingCache
from pulldata.embedding.embedder import Embedder
from pulldata.parsing.chunking import get_chunker
from pulldata.parsing.pdf_parser import PDFParser
from pulldata.rag.pipeline import RAGPipeline
from pulldata.rag.query_processor import QueryProcessor
from pulldata.rag.retriever import Retriever
from pulldata.storage.hybrid_search import HybridSearchEngine
from pulldata.storage.metadata_store import MetadataStore
from pulldata.storage.vector_store import VectorStore
from pulldata.synthesis import OutputData, OutputFormatter, strip_reasoning_tags
from pulldata.synthesis.formatters import (
    ExcelFormatter,
    MarkdownFormatter,
    JSONFormatter,
    PowerPointFormatter,
    PDFFormatter,
)

# Optional imports
try:
    from pulldata.llm.api_llm import APILLM
    from pulldata.llm.local_llm import LocalLLM
    from pulldata.llm.prompts import PromptManager

    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    warnings.warn("LLM modules not available. Query with answer generation will not work.")


class PullData:
    """Main PullData orchestrator class.
    
    Provides a simple, high-level API for document ingestion and querying
    with automatic initialization of all required components.
    
    Example:
        >>> pd = PullData(project="financial_reports")
        >>> pd.ingest("./documents/*.pdf")
        >>> result = pd.query("What is the Q3 revenue?", output_format="excel")
        >>> result.save("report.xlsx")
    """

    def __init__(
        self,
        project: str = "default",
        config_path: Optional[Union[str, Path]] = None,
        config: Optional[Config] = None,
        **config_overrides,
    ):
        """Initialize PullData.
        
        Args:
            project: Project name for isolation
            config_path: Path to config file (uses default if None)
            config: Pre-loaded Config object (takes precedence)
            **config_overrides: Override specific configuration values
        """
        logger.info(f"Initializing PullData for project: {project}")
        
        self.project = project
        
        # Load or use provided configuration
        if config is not None:
            self.config = config
        else:
            self.config = load_config(config_path=config_path, **config_overrides)
        
        # Update project name in config
        self.config.project.name = project
        
        # Component placeholders
        self._embedder: Optional[Embedder] = None
        self._embedding_cache: Optional[EmbeddingCache] = None
        self._vector_store: Optional[VectorStore] = None
        self._metadata_store: Optional[MetadataStore] = None
        self._search_engine: Optional[HybridSearchEngine] = None
        self._query_processor: Optional[QueryProcessor] = None
        self._retriever: Optional[Retriever] = None
        self._rag_pipeline: Optional[RAGPipeline] = None
        self._llm = None
        self._prompt_manager = None
        
        # Initialize core components
        self._initialize_components()
        
        logger.info(f"PullData initialized successfully for project '{project}'")

    def _initialize_components(self) -> None:
        """Initialize all required components."""
        logger.debug("Initializing components...")
        
        # Embedder
        self._embedder = self._create_embedder()
        
        # Embedding cache
        if self.config.cache.embedding.enabled:
            cache_dir = Path(f"./cache/embeddings/{self.project}")
            cache_dir.mkdir(parents=True, exist_ok=True)
            self._embedding_cache = EmbeddingCache(
                cache_dir=str(cache_dir),
                max_memory_size=self.config.cache.embedding.max_entries,
            )
        
        # Storage components
        self._vector_store = self._create_vector_store()
        self._metadata_store = self._create_metadata_store()
        self._search_engine = HybridSearchEngine(
            vector_store=self._vector_store,
            metadata_store=self._metadata_store,
        )
        
        # RAG components
        self._query_processor = QueryProcessor()
        self._retriever = Retriever(
            search_engine=self._search_engine,
            embedder=self._embedder,
            top_k=self.config.retrieval.vector_search.top_k,
        )
        
        # LLM components (optional)
        if LLM_AVAILABLE:
            self._llm = self._create_llm()
            self._prompt_manager = PromptManager()
        
        # RAG Pipeline
        self._rag_pipeline = RAGPipeline(
            search_engine=self._search_engine,
            embedder=self._embedder,
            query_processor=self._query_processor,
            retriever=self._retriever,
            llm=self._llm,
            prompt_manager=self._prompt_manager,
            top_k=self.config.retrieval.vector_search.top_k,
            max_context_tokens=self.config.models.llm.generation.max_tokens,
        )

    def _create_embedder(self):
        """Create embedder from configuration (local or API)."""
        # Check if API embedder is configured
        provider = getattr(self.config.models.embedder, 'provider', 'local')
        
        if provider == 'api':
            # Use API embedder
            logger.debug(f"Creating API embedder: {self.config.models.embedder.api.model}")
            from pulldata.embedding.api_embedder import APIEmbedder
            
            return APIEmbedder(
                base_url=self.config.models.embedder.api.base_url,
                api_key=self.config.models.embedder.api.api_key,
                model=self.config.models.embedder.api.model,
                timeout=getattr(self.config.models.embedder.api, 'timeout', 60),
                max_retries=getattr(self.config.models.embedder.api, 'max_retries', 3),
                batch_size=getattr(self.config.models.embedder.api, 'batch_size', 100),
                dimension=getattr(self.config.models.embedder, 'dimension', None),
            )
        else:
            # Use local embedder (default)
            logger.debug(f"Creating local embedder: {self.config.models.embedder.name}")
            return Embedder(
                model_name=self.config.models.embedder.name,
                device=self.config.models.embedder.device,
                batch_size=self.config.models.embedder.batch_size,
                normalize_embeddings=self.config.models.embedder.normalize_embeddings,
            )

    def _create_vector_store(self) -> VectorStore:
        """Create vector store from configuration."""
        logger.debug("Creating vector store...")

        # Check if existing index exists
        index_path = Path(f"./data/{self.project}/faiss_index")
        if index_path.exists() and (index_path / "index.faiss").exists():
            logger.info(f"Loading existing FAISS index from {index_path}")
            try:
                return VectorStore.load(index_path)
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}. Creating new index.")

        # Map metric from config to FAISS format
        metric = self.config.retrieval.vector_search.metric
        if metric.lower() == "cosine":
            faiss_metric = "IP"  # Inner product for normalized vectors = cosine similarity
        elif metric.lower() in ["l2", "euclidean"]:
            faiss_metric = "L2"
        else:
            faiss_metric = metric

        # Normalize index type to proper case
        index_type = self.config.retrieval.vector_search.index_type
        if index_type.lower() == "flat":
            index_type = "Flat"
        elif index_type.lower() == "ivf":
            index_type = "IVF"
        elif index_type.lower() == "hnsw":
            index_type = "HNSW"

        logger.info("Creating new FAISS index")
        return VectorStore(
            dimension=self.config.models.embedder.dimension,
            index_type=index_type,
            metric=faiss_metric,
        )

    def _create_metadata_store(self) -> MetadataStore:
        """Create metadata store from configuration."""
        logger.debug("Creating metadata store...")
        db_path = Path(f"./data/{self.project}/metadata.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        return MetadataStore(db_path=str(db_path))

    def _create_llm(self):
        """Create LLM from configuration."""
        if not LLM_AVAILABLE:
            logger.warning("LLM modules not available")
            return None
        
        if self.config.models.llm.provider == "local":
            logger.debug(f"Creating local LLM: {self.config.models.llm.local.name}")
            return LocalLLM(
                model_name=self.config.models.llm.local.name,
                device=self.config.models.llm.local.device,
                quantization=self.config.models.llm.local.quantization,
                generation_config=self.config.models.llm.generation.model_dump(),
            )
        else:  # api
            logger.debug(f"Creating API LLM: {self.config.models.llm.api.model}")
            return APILLM(
                base_url=self.config.models.llm.api.base_url,
                api_key=self.config.models.llm.api.api_key,
                model_name=self.config.models.llm.api.model,
                timeout=self.config.models.llm.api.timeout,
                max_retries=self.config.models.llm.api.max_retries,
                generation_config=self.config.models.llm.generation.model_dump(),
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def ingest(
        self,
        source: Union[str, Path, List[Union[str, Path]]],
        **metadata,
    ) -> Dict[str, Any]:
        """Ingest documents into the system.
        
        Args:
            source: Path to document(s) or glob pattern
            **metadata: Additional metadata for all documents
            
        Returns:
            Dictionary with ingestion statistics
            
        Raises:
            ParsingError: If document parsing fails
            EmbeddingError: If embedding generation fails
            StorageError: If storage operations fail
        """
        logger.info(f"Starting ingestion from: {source}")
        
        # Handle glob patterns and lists
        if isinstance(source, (str, Path)):
            source_path = Path(source)
            if "*" in str(source):
                # Glob pattern
                files = list(source_path.parent.glob(source_path.name))
            elif source_path.is_dir():
                # Directory
                files = list(source_path.rglob("*.pdf"))  # Add more extensions as needed
            else:
                # Single file
                files = [source_path]
        else:
            # List of files
            files = [Path(f) for f in source]
        
        logger.info(f"Found {len(files)} document(s) to ingest")
        
        stats = {
            "total_files": len(files),
            "processed_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "new_chunks": 0,
            "updated_chunks": 0,
            "skipped_chunks": 0,
        }
        
        # Process each document with progress bar
        progress_bar = tqdm(files, desc="Ingesting documents", disable=not self.config.performance.show_progress)
        
        for file_path in progress_bar:
            try:
                progress_bar.set_description(f"Processing {file_path.name}")
                result = self._ingest_document(file_path, metadata)
                
                stats["processed_files"] += 1
                stats["total_chunks"] += result["total_chunks"]
                stats["new_chunks"] += result["new_chunks"]
                stats["updated_chunks"] += result["updated_chunks"]
                stats["skipped_chunks"] += result["skipped_chunks"]
                
            except Exception as e:
                logger.error(f"Failed to ingest {file_path}: {e}")
                stats["failed_files"] += 1
        
        logger.info(f"Ingestion complete. Processed {stats['processed_files']}/{stats['total_files']} files")
        return stats

    def _ingest_document(
        self,
        file_path: Path,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Ingest a single document.
        
        Args:
            file_path: Path to document
            metadata: Document metadata
            
        Returns:
            Dictionary with document ingestion stats
        """
        # Step 1: Parse document
        logger.debug(f"Parsing {file_path}")
        
        if file_path.suffix.lower() == ".pdf":
            parser = PDFParser()
            document, page_texts = parser.parse(file_path)
        elif file_path.suffix.lower() in [".txt", ".md"]:
            # Simple text file handling
            import hashlib
            from pulldata.core.datatypes import Document
            
            text_content = file_path.read_text(encoding='utf-8')
            document_id = f"doc_{file_path.stem}_{int(time.time())}"
            
            # Calculate content hash
            content_hash = hashlib.sha256(text_content.encode()).hexdigest()
            
            document = Document(
                id=document_id,
                source=str(file_path),
                source_path=str(file_path),
                filename=file_path.name,
                content_hash=content_hash,
                file_size=len(text_content.encode('utf-8')),
                metadata={"file_name": file_path.name, "file_type": file_path.suffix}
            )
            page_texts = {1: text_content}  # Treat as single page
        else:
            raise ParsingError(
                f"Unsupported file format: {file_path.suffix}",
                details={"path": str(file_path)}
            )
        
        # Add user metadata
        document.metadata.update(metadata)
        
        # Step 2: Chunk document
        logger.debug(f"Chunking document: {document.id}")
        
        # Create chunker instance
        chunker = get_chunker(
            strategy=self.config.parsing.chunking.strategy,
            chunk_size=self.config.parsing.chunking.chunk_size,
            chunk_overlap=self.config.parsing.chunking.chunk_overlap,
            min_chunk_size=self.config.parsing.chunking.min_chunk_size,
        )
        
        # Chunk all page texts
        chunks = []
        for page_num, page_text in page_texts.items():
            page_chunks = chunker.chunk_text(
                text=page_text,
                document_id=document.id,
                page_number=page_num,
            )
            # Set start_page and end_page from page_number
            for chunk in page_chunks:
                chunk.start_page = page_num
                chunk.end_page = page_num
            chunks.extend(page_chunks)

        
        stats = {
            "total_chunks": len(chunks),
            "new_chunks": 0,
            "updated_chunks": 0,
            "skipped_chunks": 0,
        }
        
        # Step 3: Check for existing chunks (differential updates)
        if self.config.features.differential_updates:
            # Filter out unchanged chunks by comparing hashes
            existing_hashes = self._metadata_store.get_chunk_hashes(document.id)
            chunks_to_process = [
                chunk for chunk in chunks
                if chunk.chunk_hash not in existing_hashes
            ]
            stats["skipped_chunks"] = len(chunks) - len(chunks_to_process)
            logger.debug(f"Skipped {stats['skipped_chunks']} unchanged chunks")
        else:
            chunks_to_process = chunks
        
        if not chunks_to_process:
            logger.info(f"No new/updated chunks for {document.id}")
            return stats

        # Step 4: Assign chunk IDs (must be done BEFORE embedding)
        # This ensures VectorStore and MetadataStore use the same IDs
        for chunk in chunks_to_process:
            if chunk.id is None:
                chunk.id = f"chunk-{document.id}-{chunk.chunk_index}"

        # Step 5: Generate embeddings
        logger.debug(f"Generating embeddings for {len(chunks_to_process)} chunks")
        embeddings = self._embedder.embed_chunks(
            chunks_to_process,
            show_progress_bar=False,
        )

        # Step 6: Store in vector store and metadata store
        logger.debug(f"Storing {len(chunks_to_process)} chunks")

        # Store metadata
        self._metadata_store.add_document(document)
        for chunk in chunks_to_process:
            self._metadata_store.add_chunk(chunk)

        # Store vectors
        self._vector_store.add(embeddings)

        # Auto-save vector store to disk for persistence
        index_path = Path(f"./data/{self.project}/faiss_index")
        self._vector_store.save(index_path)
        logger.debug(f"Saved vector store to {index_path}")

        stats["new_chunks"] = len(chunks_to_process)

        logger.debug(f"Successfully ingested {document.id}")
        return stats

    def query(
        self,
        query: str,
        k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        generate_answer: bool = True,
        output_format: Optional[Literal["excel", "markdown", "json", "powerpoint", "pdf", "styled_pdf"]] = None,
        pdf_style: Optional[Literal["executive", "modernist", "academic"]] = "executive",
        **llm_kwargs,
    ) -> Union[QueryResult, OutputData]:
        """Query the system and optionally generate formatted output.

        Args:
            query: Query string
            k: Number of chunks to retrieve (uses config default if None)
            filters: Optional metadata filters
            generate_answer: Whether to generate an answer with LLM
            output_format: Optional output format for results
            pdf_style: PDF style for styled_pdf format (executive, modernist, academic)
            **llm_kwargs: Additional LLM generation parameters

        Returns:
            QueryResult object (or OutputData if output_format specified)
        """
        logger.info(f"Processing query: {query[:100]}...")
        
        # Execute RAG pipeline
        if generate_answer and self._llm is not None:
            rag_response = self._rag_pipeline.query_with_answer(
                query=query,
                k=k,
                filters=filters,
                **llm_kwargs,
            )
        else:
            rag_response = self._rag_pipeline.query(
                query=query,
                k=k,
                filters=filters,
            )
        
        # Convert to QueryResult
        from pulldata.core.datatypes import RetrievedChunk, LLMResponse

        result = QueryResult(
            query=query,
            retrieved_chunks=[
                RetrievedChunk(
                    chunk=r.chunk,
                    score=r.score,
                    rank=r.rank,
                )
                for r in rag_response.retrieved_chunks
            ],
            llm_response=LLMResponse(
                text=rag_response.answer or "",
                model=rag_response.metadata.get("llm_response", {}).get("model", "unknown"),
                provider="api" if self.config.models.llm.provider == "api" else "local",
                prompt_tokens=rag_response.metadata.get("llm_response", {}).get("prompt_tokens"),
                completion_tokens=rag_response.metadata.get("llm_response", {}).get("completion_tokens"),
                total_tokens=rag_response.metadata.get("llm_response", {}).get("tokens_used"),
            ) if rag_response.answer else None,
        )
        
        # If output format specified, format and save to file
        if output_format:
            output_data = self._convert_to_output_data(result)
            formatter = self._get_formatter(output_format, pdf_style=pdf_style)

            # Create output directory if it doesn't exist
            output_dir = Path("./output")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            timestamp = int(time.time())
            output_path = output_dir / f"{self.project}_query_{timestamp}.{formatter.file_extension.lstrip('.')}"

            # Save formatted output
            saved_path = self.format_and_save(output_data, formatter, output_path)
            logger.info(f"Query results saved to {saved_path}")

            # Update result with output path
            result.output_path = str(saved_path)
            return result

        return result

    def _convert_to_output_data(self, result: QueryResult) -> OutputData:
        """Convert QueryResult to OutputData for formatting.

        Args:
            result: QueryResult object

        Returns:
            OutputData object ready for formatting
        """
        answer_text = result.llm_response.text if result.llm_response else "No answer generated"

        # Strip reasoning tags from LLM output (e.g., <think>, <thinking>, etc.)
        answer_text = strip_reasoning_tags(answer_text)

        sources = [
            {
                "document_id": r.chunk.document_id,
                "chunk_id": r.chunk.id,
                "page_number": r.chunk.metadata.get("page_number"),
                "score": r.score,
                "text": r.chunk.text,
            }
            for r in result.retrieved_chunks
        ]

        return OutputData(
            title=f"Query: {result.query}",
            content=answer_text,
            sources=sources,
            metadata={},
        )

    def _get_formatter(
        self,
        format_type: str,
        pdf_style: Optional[str] = "executive",
    ) -> OutputFormatter:
        """Get formatter instance for the specified format.

        Args:
            format_type: Format type ('excel', 'markdown', 'json', 'powerpoint', 'pdf', 'styled_pdf')
            pdf_style: PDF style for styled_pdf format (executive, modernist, academic)

        Returns:
            OutputFormatter instance

        Raises:
            ValueError: If format_type is not supported
        """
        # Handle styled_pdf format specially
        if format_type == "styled_pdf":
            from pulldata.synthesis.formatters.styled_pdf import StyledPDFFormatter
            return StyledPDFFormatter(style=pdf_style, llm=self._llm)

        formatters = {
            "excel": ExcelFormatter,
            "markdown": MarkdownFormatter,
            "json": JSONFormatter,
            "powerpoint": PowerPointFormatter,
            "pdf": PDFFormatter,
        }

        if format_type not in formatters:
            raise ValueError(
                f"Unsupported format: {format_type}. "
                f"Supported formats: {', '.join(list(formatters.keys()) + ['styled_pdf'])}"
            )

        return formatters[format_type]()

    def format_and_save(
        self,
        result: Union[QueryResult, OutputData],
        formatter: OutputFormatter,
        output_path: Union[str, Path],
    ) -> Path:
        """Format and save query results.
        
        Args:
            result: QueryResult or OutputData object
            formatter: OutputFormatter instance
            output_path: Path to save output
            
        Returns:
            Path to saved file
        """
        # Convert QueryResult to OutputData if needed
        if isinstance(result, QueryResult):
            output_data = self._convert_to_output_data(result)
        else:
            output_data = result
        
        # Format and save
        return formatter.save(output_data, output_path)

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics.
        
        Returns:
            Dictionary with system stats
        """
        return {
            "project": self.project,
            "vector_store": self._vector_store.get_stats(),
            "metadata_store": self._metadata_store.get_stats(),
            "search_engine": self._search_engine.get_stats(),
        }


    def close(self) -> None:
        """Clean up resources."""
        logger.info("Closing PullData")
        if self._vector_store:
            index_path = Path(f"./data/{self.project}/faiss_index")
            self._vector_store.save(index_path)
        if self._metadata_store:
            self._metadata_store.close()
