"""API-based embedding generation using OpenAI-compatible endpoints.

Supports embedding generation via:
- OpenAI API (text-embedding-3-small, text-embedding-ada-002)
- LM Studio (with embedding models loaded)
- Ollama
- Any OpenAI-compatible embedding API

This is an alternative to local embeddings for users who prefer API-based solutions.
"""

from __future__ import annotations

import time
from typing import Any, Optional

import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from pulldata.core.datatypes import Chunk, Embedding
from pulldata.core.exceptions import EmbeddingError, EmbeddingGenerationError


class APIEmbedder:
    """API-based embedder using OpenAI-compatible endpoints.
    
    Supports any OpenAI-compatible embedding API including:
    - OpenAI (text-embedding-3-small, ada-002)
    - LM Studio (local embedding models)
    - Ollama
    - Cohere, Voyage AI, etc.
    
    Example:
        >>> # OpenAI
        >>> embedder = APIEmbedder(
        ...     base_url="https://api.openai.com/v1",
        ...     api_key=os.getenv("OPENAI_API_KEY"),
        ...     model="text-embedding-3-small"
        ... )
        
        >>> # LM Studio
        >>> embedder = APIEmbedder(
        ...     base_url="http://localhost:1234/v1",
        ...     api_key="lm-studio",
        ...     model="nomic-embed-text-v1.5"
        ... )
    """
    
    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "text-embedding-3-small",
        timeout: int = 60,
        max_retries: int = 3,
        batch_size: int = 100,
        dimension: Optional[int] = None,
    ):
        """Initialize API embedder.
        
        Args:
            base_url: API base URL
            api_key: API key (use "lm-studio" for LM Studio)
            model: Model name/identifier
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            batch_size: Maximum texts per API call
            dimension: Embedding dimension (auto-detected if None)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.batch_size = batch_size
        self._dimension = dimension
        
        # Test connection and get dimension
        if self._dimension is None:
            self._dimension = self._detect_dimension()
        
        logger.info(f"Initialized APIEmbedder: {model} ({self._dimension}D)")
    
    @property
    def model_name(self) -> str:
        """Get model name."""
        return self.model
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension
    
    def _detect_dimension(self) -> int:
        """Detect embedding dimension by making a test call."""
        try:
            embedding = self.embed_text("test", show_progress_bar=False)
            return embedding.dimension
        except Exception as e:
            logger.warning(f"Could not detect dimension: {e}, using default 1536")
            return 1536  # OpenAI default
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_api(self, texts: list[str]) -> list[list[float]]:
        """Call embedding API.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingGenerationError: If API call fails
        """
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "input": texts,
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract embeddings from response
            embeddings = []
            for item in data["data"]:
                embeddings.append(item["embedding"])
            
            return embeddings
            
        except requests.exceptions.Timeout as e:
            raise EmbeddingGenerationError(
                f"API request timeout after {self.timeout}s",
                details={"url": url, "timeout": self.timeout},
            ) from e
        except requests.exceptions.RequestException as e:
            raise EmbeddingGenerationError(
                f"API request failed: {e}",
                details={"url": url, "status_code": getattr(e.response, "status_code", None)},
            ) from e
        except (KeyError, ValueError) as e:
            raise EmbeddingGenerationError(
                f"Invalid API response format: {e}",
                details={"url": url},
            ) from e
    
    def embed_text(
        self,
        text: str,
        chunk_id: Optional[str] = None,
        show_progress_bar: bool = False,
    ) -> Embedding:
        """Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            chunk_id: Optional chunk ID
            show_progress_bar: Ignored (for compatibility)
            
        Returns:
            Embedding object
        """
        vectors = self._call_api([text])
        
        return Embedding(
            chunk_id=chunk_id or "",
            vector=vectors[0],
            dimension=len(vectors[0]),
            model_name=self.model,
        )
    
    def embed_texts(
        self,
        texts: list[str],
        chunk_ids: Optional[list[str]] = None,
        show_progress_bar: bool = True,
    ) -> list[Embedding]:
        """Generate embeddings for multiple texts (batched).
        
        Args:
            texts: List of input texts
            chunk_ids: Optional list of chunk IDs
            show_progress_bar: Whether to show progress (logged instead)
            
        Returns:
            List of Embedding objects
        """
        if chunk_ids is not None and len(chunk_ids) != len(texts):
            raise ValueError(
                f"chunk_ids length ({len(chunk_ids)}) must match texts length ({len(texts)})"
            )
        
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_ids = chunk_ids[i:i + self.batch_size] if chunk_ids else None
            
            if show_progress_bar:
                logger.info(f"Processing batch {i // self.batch_size + 1}/{(len(texts) - 1) // self.batch_size + 1}")
            
            # Call API
            vectors = self._call_api(batch_texts)
            
            # Create Embedding objects
            for j, vector in enumerate(vectors):
                chunk_id = batch_ids[j] if batch_ids else f"chunk-{i + j}"
                embeddings.append(
                    Embedding(
                        chunk_id=chunk_id,
                        vector=vector,
                        dimension=len(vector),
                        model_name=self.model,
                    )
                )
            
            # Small delay to avoid rate limiting
            if i + self.batch_size < len(texts):
                time.sleep(0.1)
        
        return embeddings
    
    def embed_chunks(
        self,
        chunks: list[Chunk],
        show_progress_bar: bool = True,
    ) -> list[Embedding]:
        """Generate embeddings for a list of Chunk objects.
        
        Args:
            chunks: List of Chunk objects to embed
            show_progress_bar: Whether to show progress
            
        Returns:
            List of Embedding objects with chunk IDs
        """
        texts = [chunk.text for chunk in chunks]
        chunk_ids = [chunk.id or f"chunk-{chunk.chunk_index}" for chunk in chunks]
        
        return self.embed_texts(
            texts=texts,
            chunk_ids=chunk_ids,
            show_progress_bar=show_progress_bar,
        )
    
    def get_model_info(self) -> dict[str, Any]:
        """Get information about the embedding model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model,
            "dimension": self.dimension,
            "provider": "api",
            "base_url": self.base_url,
            "batch_size": self.batch_size,
            "max_retries": self.max_retries,
        }
