"""
Metadata storage using PostgreSQL or SQLite.

Stores document and chunk metadata in a relational database for
efficient querying and filtering.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from pulldata.core.datatypes import Chunk, Document
from pulldata.core.exceptions import MetadataStoreError


class MetadataStore:
    """
    Metadata storage for documents and chunks.

    Supports both SQLite (for local/development) and PostgreSQL (for production).
    """

    def __init__(
        self,
        db_type: str = "sqlite",
        db_path: Optional[Union[str, Path]] = None,
        connection_string: Optional[str] = None,
    ):
        """
        Initialize metadata store.

        Args:
            db_type: Database type ("sqlite" or "postgres")
            db_path: Path to SQLite database file
            connection_string: PostgreSQL connection string (e.g., "postgresql://user:pass@host/db")
        """
        self.db_type = db_type.lower()

        if self.db_type == "sqlite":
            if db_path is None:
                db_path = ".pulldata_metadata.db"
            self.db_path = Path(db_path)
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        elif self.db_type == "postgres":
            if not PSYCOPG2_AVAILABLE:
                raise MetadataStoreError("psycopg2 not installed. Install with: pip install psycopg2-binary")
            if connection_string is None:
                raise MetadataStoreError("connection_string required for PostgreSQL")
            self.connection_string = connection_string
            self.conn = psycopg2.connect(connection_string)
        else:
            raise MetadataStoreError(f"Unsupported database type: {db_type}")

        self._create_tables()

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        if self.db_type == "sqlite":
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    num_pages INTEGER,
                    created_at TIMESTAMP,
                    modified_at TIMESTAMP,
                    ingested_at TIMESTAMP NOT NULL,
                    metadata TEXT
                )
            """)

            # Chunks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_hash TEXT NOT NULL,
                    chunk_type TEXT NOT NULL,
                    start_page INTEGER,
                    end_page INTEGER,
                    char_count INTEGER NOT NULL,
                    token_count INTEGER NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)

            # Create indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_chunk_type ON chunks(chunk_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename)")

        else:  # PostgreSQL
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    num_pages INTEGER,
                    created_at TIMESTAMP,
                    modified_at TIMESTAMP,
                    ingested_at TIMESTAMP NOT NULL,
                    metadata JSONB
                )
            """)

            # Chunks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_hash TEXT NOT NULL,
                    chunk_type TEXT NOT NULL,
                    start_page INTEGER,
                    end_page INTEGER,
                    char_count INTEGER NOT NULL,
                    token_count INTEGER NOT NULL,
                    metadata JSONB,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)

            # Create indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_chunk_type ON chunks(chunk_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename)")

        self.conn.commit()
        cursor.close()

    def add_document(self, document: Document) -> str:
        """
        Add a document to the metadata store.

        Args:
            document: Document object to store

        Returns:
            Document ID
        """
        cursor = self.conn.cursor()

        # Serialize metadata
        if self.db_type == "sqlite":
            metadata_str = json.dumps(document.metadata)
        else:
            metadata_str = json.dumps(document.metadata)  # PostgreSQL will handle JSONB

        cursor.execute("""
            INSERT INTO documents (
                id, source_path, filename, doc_type, content_hash,
                file_size, num_pages, created_at, modified_at, ingested_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """ if self.db_type == "sqlite" else """
            INSERT INTO documents (
                id, source_path, filename, doc_type, content_hash,
                file_size, num_pages, created_at, modified_at, ingested_at, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            document.id,
            document.source_path,
            document.filename,
            document.doc_type.value,
            document.content_hash,
            document.file_size,
            document.num_pages,
            document.created_at,
            document.modified_at,
            document.ingested_at,
            metadata_str,
        ))

        self.conn.commit()
        cursor.close()
        return document.id

    def add_chunk(self, chunk: Chunk) -> str:
        """
        Add a chunk to the metadata store.

        Args:
            chunk: Chunk object to store

        Returns:
            Chunk ID
        """
        cursor = self.conn.cursor()

        # Serialize metadata
        if self.db_type == "sqlite":
            metadata_str = json.dumps(chunk.metadata)
        else:
            metadata_str = json.dumps(chunk.metadata)

        cursor.execute("""
            INSERT INTO chunks (
                id, document_id, text, chunk_index, chunk_hash, chunk_type,
                start_page, end_page, char_count, token_count, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """ if self.db_type == "sqlite" else """
            INSERT INTO chunks (
                id, document_id, text, chunk_index, chunk_hash, chunk_type,
                start_page, end_page, char_count, token_count, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            chunk.id,
            chunk.document_id,
            chunk.text,
            chunk.chunk_index,
            chunk.chunk_hash,
            chunk.chunk_type.value,
            chunk.start_page,
            chunk.end_page,
            chunk.char_count,
            chunk.token_count,
            metadata_str,
        ))

        self.conn.commit()
        cursor.close()
        return chunk.id

    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document object or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE id = ?" if self.db_type == "sqlite" else
            "SELECT * FROM documents WHERE id = %s",
            (document_id,)
        )
        row = cursor.fetchone()
        cursor.close()

        if row is None:
            return None

        return self._row_to_document(row)

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """
        Get a chunk by ID.

        Args:
            chunk_id: Chunk ID

        Returns:
            Chunk object or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM chunks WHERE id = ?" if self.db_type == "sqlite" else
            "SELECT * FROM chunks WHERE id = %s",
            (chunk_id,)
        )
        row = cursor.fetchone()
        cursor.close()

        if row is None:
            return None

        return self._row_to_chunk(row)

    def get_chunks_by_document(self, document_id: str) -> list[Chunk]:
        """
        Get all chunks for a document.

        Args:
            document_id: Document ID

        Returns:
            List of Chunk objects
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index" if self.db_type == "sqlite" else
            "SELECT * FROM chunks WHERE document_id = %s ORDER BY chunk_index",
            (document_id,)
        )
        rows = cursor.fetchall()
        cursor.close()


        return [self._row_to_chunk(row) for row in rows]

    def get_chunk_hashes(self, document_id: str) -> set[str]:
        """
        Get chunk hashes for a document (for differential updates).

        Args:
            document_id: Document ID

        Returns:
            Set of chunk hashes
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT chunk_hash FROM chunks WHERE document_id = ?" if self.db_type == "sqlite" else
                "SELECT chunk_hash FROM chunks WHERE document_id = %s",
                (document_id,)
            )
            rows = cursor.fetchall()
            cursor.close()
            return {row[0] for row in rows if row[0]}
        except Exception as e:
            # If chunk_hash column doesn't exist, return empty set
            return set()

    def search_chunks(
        self,
        query: str = "",
        chunk_type: Optional[str] = None,
        document_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Chunk]:
        """
        Search chunks with filters.

        Args:
            query: Text search query (searches in chunk text)
            chunk_type: Filter by chunk type
            document_id: Filter by document ID
            limit: Maximum number of results

        Returns:
            List of matching Chunk objects
        """
        cursor = self.conn.cursor()

        where_clauses = []
        params = []

        if query:
            where_clauses.append("text LIKE ?" if self.db_type == "sqlite" else "text LIKE %s")
            params.append(f"%{query}%")

        if chunk_type:
            where_clauses.append("chunk_type = ?" if self.db_type == "sqlite" else "chunk_type = %s")
            params.append(chunk_type)

        if document_id:
            where_clauses.append("document_id = ?" if self.db_type == "sqlite" else "document_id = %s")
            params.append(document_id)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        params.append(limit)

        cursor.execute(
            f"SELECT * FROM chunks WHERE {where_sql} LIMIT ?" if self.db_type == "sqlite" else
            f"SELECT * FROM chunks WHERE {where_sql} LIMIT %s",
            tuple(params)
        )
        rows = cursor.fetchall()
        cursor.close()

        return [self._row_to_chunk(row) for row in rows]

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its chunks.

        Args:
            document_id: Document ID

        Returns:
            True if document was deleted, False if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM documents WHERE id = ?" if self.db_type == "sqlite" else
            "DELETE FROM documents WHERE id = %s",
            (document_id,)
        )
        deleted = cursor.rowcount > 0
        self.conn.commit()
        cursor.close()
        return deleted

    def delete_chunk(self, chunk_id: str) -> bool:
        """
        Delete a chunk.

        Args:
            chunk_id: Chunk ID

        Returns:
            True if chunk was deleted, False if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM chunks WHERE id = ?" if self.db_type == "sqlite" else
            "DELETE FROM chunks WHERE id = %s",
            (chunk_id,)
        )
        deleted = cursor.rowcount > 0
        self.conn.commit()
        cursor.close()
        return deleted

    def _row_to_document(self, row) -> Document:
        """Convert database row to Document object."""
        if self.db_type == "sqlite":
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        else:
            metadata = row[10] if isinstance(row[10], dict) else json.loads(row[10] or "{}")

        return Document(
            id=row[0],
            source_path=row[1],
            filename=row[2],
            doc_type=row[3],
            content_hash=row[4],
            file_size=row[5],
            num_pages=row[6],
            created_at=row[7],
            modified_at=row[8],
            ingested_at=row[9],
            metadata=metadata,
        )

    def _row_to_chunk(self, row) -> Chunk:
        """Convert database row to Chunk object."""
        if self.db_type == "sqlite":
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        else:
            metadata = row[10] if isinstance(row[10], dict) else json.loads(row[10] or "{}")

        return Chunk(
            id=row[0],
            document_id=row[1],
            text=row[2],
            chunk_index=row[3],
            chunk_hash=row[4],
            chunk_type=row[5],
            start_page=row[6],
            end_page=row[7],
            char_count=row[8],
            token_count=row[9],
            metadata=metadata,
        )

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def get_stats(self) -> dict:
        """
        Get metadata store statistics.

        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chunks")
        chunk_count = cursor.fetchone()[0]

        cursor.close()

        return {
            "database_type": self.db_type,
            "document_count": doc_count,
            "chunk_count": chunk_count,
        }

    def list_documents(self, limit: Optional[int] = None, offset: int = 0) -> list[Document]:
        """
        List all documents in the store.

        Args:
            limit: Maximum number of documents to return (None for all)
            offset: Number of documents to skip

        Returns:
            List of Document objects
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM documents ORDER BY ingested_at DESC"
        if limit is not None:
            query += f" LIMIT {limit} OFFSET {offset}"

        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()

        return [self._row_to_document(row) for row in rows]
