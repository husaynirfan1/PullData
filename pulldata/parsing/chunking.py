"""
Text chunking strategies for PullData.

Provides different strategies for breaking text into chunks:
- Semantic chunking (default)
- Fixed-size chunking
- Sentence-based chunking
"""

import hashlib
import re
from typing import Literal, Optional

from pulldata.core.datatypes import Chunk, ChunkType
from pulldata.core.exceptions import ChunkingError


class TextChunker:
    """
    Base class for text chunking.

    Chunks text content with overlap and boundary respect.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
        respect_sentence_boundary: bool = True,
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target chunk size in tokens (approximate)
            chunk_overlap: Number of tokens to overlap between chunks
            min_chunk_size: Minimum chunk size in tokens
            respect_sentence_boundary: Try to break at sentence boundaries
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.respect_sentence_boundary = respect_sentence_boundary

    def chunk_text(
        self,
        text: str,
        document_id: str,
        page_number: Optional[int] = None,
        start_char_offset: int = 0,
    ) -> list[Chunk]:
        """
        Chunk text into Chunk objects.

        Args:
            text: Text to chunk
            document_id: ID of parent document
            page_number: Page number (optional)
            start_char_offset: Starting character offset in document

        Returns:
            List of Chunk objects

        Raises:
            ChunkingError: If chunking fails
        """
        if not text or not text.strip():
            return []

        try:
            # Split into sentences for boundary respect
            sentences = self._split_into_sentences(text) if self.respect_sentence_boundary else [text]

            chunks = []
            current_chunk_text = []
            current_token_count = 0
            current_start_char = start_char_offset
            chunk_index = 0

            for sentence in sentences:
                sentence_tokens = self._estimate_tokens(sentence)

                # If adding this sentence exceeds chunk size, create a chunk
                if current_token_count + sentence_tokens > self.chunk_size and current_chunk_text:
                    chunk = self._create_chunk(
                        text="".join(current_chunk_text),
                        document_id=document_id,
                        chunk_index=chunk_index,
                        page_number=page_number,
                        start_char=current_start_char,
                        offset_in_original=start_char_offset,
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                    # Handle overlap
                    if self.chunk_overlap > 0:
                        # Keep last few sentences for overlap
                        overlap_text, overlap_tokens = self._get_overlap_text(
                            current_chunk_text, self.chunk_overlap
                        )
                        current_chunk_text = [overlap_text]
                        current_token_count = overlap_tokens
                        # Adjust start_char for overlap
                        overlap_length = len(overlap_text)
                        current_start_char = current_start_char + len("".join(current_chunk_text)) - overlap_length
                    else:
                        current_chunk_text = []
                        current_token_count = 0
                        current_start_char += len("".join(current_chunk_text))

                # Add sentence to current chunk
                current_chunk_text.append(sentence)
                current_token_count += sentence_tokens

            # Create final chunk if there's remaining text
            if current_chunk_text:
                final_text = "".join(current_chunk_text)
                final_tokens = self._estimate_tokens(final_text)

                # Only create chunk if it meets minimum size
                if final_tokens >= self.min_chunk_size or len(chunks) == 0:
                    chunk = self._create_chunk(
                        text=final_text,
                        document_id=document_id,
                        chunk_index=chunk_index,
                        page_number=page_number,
                        start_char=current_start_char,
                        offset_in_original=start_char_offset,
                    )
                    chunks.append(chunk)

            return chunks

        except Exception as e:
            raise ChunkingError(
                f"Failed to chunk text: {e}",
                details={"document_id": document_id, "error": str(e), "type": type(e).__name__},
            )

    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with NLP libraries)
        # Split on periods, question marks, exclamation marks followed by space
        pattern = r'(?<=[.!?])\s+'
        sentences = re.split(pattern, text)

        # Clean up and keep delimiters
        result = []
        for sentence in sentences:
            if sentence.strip():
                # Add back space if not at end
                result.append(sentence if sentence.endswith(('.', '!', '?')) else sentence + ' ')

        return result if result else [text]

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses simple heuristic: ~4 characters per token.
        For production, use actual tokenizer from the LLM.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Simple approximation: 1 token ≈ 4 characters
        # This is a rough estimate; real tokenizer would be better
        return len(text) // 4

    def _get_overlap_text(self, chunk_parts: list[str], overlap_tokens: int) -> tuple[str, int]:
        """
        Get overlap text from end of chunk.

        Args:
            chunk_parts: List of text parts in chunk
            overlap_tokens: Target overlap in tokens

        Returns:
            Tuple of (overlap_text, actual_token_count)
        """
        if not chunk_parts:
            return "", 0

        # Work backwards through chunk parts
        overlap_parts = []
        token_count = 0

        for part in reversed(chunk_parts):
            part_tokens = self._estimate_tokens(part)
            if token_count + part_tokens <= overlap_tokens:
                overlap_parts.insert(0, part)
                token_count += part_tokens
            else:
                # Take partial part if needed
                remaining_tokens = overlap_tokens - token_count
                if remaining_tokens > 0:
                    chars_needed = remaining_tokens * 4  # Rough estimate
                    partial = part[-chars_needed:] if chars_needed < len(part) else part
                    overlap_parts.insert(0, partial)
                    token_count += self._estimate_tokens(partial)
                break

        return "".join(overlap_parts), token_count

    def _create_chunk(
        self,
        text: str,
        document_id: str,
        chunk_index: int,
        page_number: Optional[int],
        start_char: int,
        offset_in_original: int,
    ) -> Chunk:
        """
        Create a Chunk object.

        Args:
            text: Chunk text
            document_id: Parent document ID
            chunk_index: Index of chunk
            page_number: Page number (optional)
            start_char: Start character position
            offset_in_original: Offset in original document

        Returns:
            Chunk object
        """
        # Calculate actual positions
        actual_start = start_char
        actual_end = start_char + len(text)

        # Hash chunk content
        chunk_hash = hashlib.sha256(text.encode()).hexdigest()

        # Estimate tokens
        token_count = self._estimate_tokens(text)

        return Chunk(
            document_id=document_id,
            chunk_index=chunk_index,
            chunk_hash=chunk_hash,
            text=text,
            chunk_type=ChunkType.TEXT,
            char_count=len(text),
            page_number=page_number,
            start_char=actual_start,
            end_char=actual_end,
            token_count=token_count,
        )


class FixedSizeChunker(TextChunker):
    """
    Fixed-size chunker that splits text at exact token boundaries.

    Simpler than semantic chunker, doesn't respect sentence boundaries.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        """Initialize fixed-size chunker."""
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_size=0,  # No minimum for fixed size
            respect_sentence_boundary=False,
        )

    def chunk_text(
        self,
        text: str,
        document_id: str,
        page_number: Optional[int] = None,
        start_char_offset: int = 0,
    ) -> list[Chunk]:
        """Chunk text at fixed token boundaries."""
        if not text or not text.strip():
            return []

        chunks = []
        chunk_index = 0
        pos = 0

        while pos < len(text):
            # Calculate chunk size in characters (approximate)
            chunk_chars = self.chunk_size * 4  # ~4 chars per token

            # Extract chunk
            end_pos = min(pos + chunk_chars, len(text))
            chunk_text = text[pos:end_pos]

            # Create chunk
            chunk = self._create_chunk(
                text=chunk_text,
                document_id=document_id,
                chunk_index=chunk_index,
                page_number=page_number,
                start_char=start_char_offset + pos,
                offset_in_original=start_char_offset,
            )
            chunks.append(chunk)

            # Move position (with overlap)
            overlap_chars = self.chunk_overlap * 4
            pos += chunk_chars - overlap_chars
            chunk_index += 1

        return chunks


def get_chunker(
    strategy: Literal["semantic", "fixed", "sentence"] = "semantic",
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    **kwargs,
) -> TextChunker:
    """
    Factory function to get appropriate chunker.

    Args:
        strategy: Chunking strategy ('semantic', 'fixed', 'sentence')
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap size in tokens
        **kwargs: Additional arguments for specific chunkers

    Returns:
        TextChunker instance

    Raises:
        ChunkingError: If strategy is invalid
    """
    if strategy == "semantic":
        return TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            respect_sentence_boundary=True,
            **kwargs,
        )
    elif strategy == "fixed":
        return FixedSizeChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    elif strategy == "sentence":
        # Sentence-based is semantic with stricter boundaries
        return TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            respect_sentence_boundary=True,
            min_chunk_size=1,  # Allow single sentences
            **kwargs,
        )
    else:
        raise ChunkingError(
            f"Unknown chunking strategy: {strategy}",
            details={"strategy": strategy, "valid_strategies": ["semantic", "fixed", "sentence"]},
        )
