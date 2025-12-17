"""
Content hashing utilities for differential updates.

Provides functions for hashing documents, chunks, and detecting changes.
"""

import hashlib
from pathlib import Path
from typing import Literal

from pulldata.core.datatypes import Chunk, Document


def hash_text(
    text: str,
    algorithm: Literal["sha256", "md5"] = "sha256",
) -> str:
    """
    Hash text content.

    Args:
        text: Text to hash
        algorithm: Hashing algorithm ('sha256' or 'md5')

    Returns:
        Hexadecimal hash string
    """
    if algorithm == "sha256":
        return hashlib.sha256(text.encode()).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(text.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def hash_file(
    file_path: str | Path,
    algorithm: Literal["sha256", "md5"] = "sha256",
    chunk_size: int = 8192,
) -> str:
    """
    Hash file content.

    Args:
        file_path: Path to file
        algorithm: Hashing algorithm ('sha256' or 'md5')
        chunk_size: Size of chunks to read at a time

    Returns:
        Hexadecimal hash string
    """
    file_path = Path(file_path)

    if algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "md5":
        hasher = hashlib.md5()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()


def hash_document_content(
    document_text: str | dict[int, str],
    algorithm: Literal["sha256", "md5"] = "sha256",
) -> str:
    """
    Hash document content.

    Args:
        document_text: Either full text or dict of page_number -> text
        algorithm: Hashing algorithm

    Returns:
        Hexadecimal hash string
    """
    if isinstance(document_text, dict):
        # Combine all pages in order
        sorted_pages = sorted(document_text.items())
        combined = "\n".join(text for _, text in sorted_pages)
        return hash_text(combined, algorithm)
    else:
        return hash_text(document_text, algorithm)


def hash_chunks(chunks: list[Chunk], algorithm: Literal["sha256", "md5"] = "sha256") -> str:
    """
    Hash all chunks together.

    Useful for detecting if chunk boundaries have changed.

    Args:
        chunks: List of Chunk objects
        algorithm: Hashing algorithm

    Returns:
        Hexadecimal hash string
    """
    # Combine all chunk hashes
    combined = "".join(chunk.chunk_hash for chunk in chunks)
    return hash_text(combined, algorithm)


def has_content_changed(
    old_hash: str,
    new_content: str,
    algorithm: Literal["sha256", "md5"] = "sha256",
) -> bool:
    """
    Check if content has changed by comparing hashes.

    Args:
        old_hash: Previous content hash
        new_content: New content to check
        algorithm: Hashing algorithm (should match old_hash algorithm)

    Returns:
        True if content has changed, False if identical
    """
    new_hash = hash_text(new_content, algorithm)
    return old_hash != new_hash


def detect_changed_chunks(
    old_chunks: list[Chunk],
    new_texts: list[str],
    algorithm: Literal["sha256", "md5"] = "sha256",
) -> dict[str, list[int]]:
    """
    Detect which chunks have changed.

    Args:
        old_chunks: Previous chunks
        new_texts: New chunk texts (same order/count as old_chunks)
        algorithm: Hashing algorithm

    Returns:
        Dict with keys:
        - 'changed': Indices of changed chunks
        - 'unchanged': Indices of unchanged chunks
    """
    if len(old_chunks) != len(new_texts):
        # If chunk count changed, consider all changed
        return {
            "changed": list(range(len(new_texts))),
            "unchanged": [],
        }

    changed = []
    unchanged = []

    for idx, (old_chunk, new_text) in enumerate(zip(old_chunks, new_texts)):
        new_hash = hash_text(new_text, algorithm)
        if old_chunk.chunk_hash != new_hash:
            changed.append(idx)
        else:
            unchanged.append(idx)

    return {
        "changed": changed,
        "unchanged": unchanged,
    }


def compute_document_fingerprint(document: Document) -> str:
    """
    Compute a fingerprint for a document including metadata.

    Includes content hash, file size, and modification time if available.

    Args:
        document: Document object

    Returns:
        Combined fingerprint hash
    """
    fingerprint_data = [
        document.content_hash,
        str(document.file_size),
    ]

    if document.modified_at:
        fingerprint_data.append(document.modified_at.isoformat())

    combined = "|".join(fingerprint_data)
    return hash_text(combined, "sha256")
