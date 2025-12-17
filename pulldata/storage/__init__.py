"""
Storage backends for PullData.

Provides pluggable storage implementations:
- PostgreSQL + pgvector (production)
- SQLite + FAISS (local development)
- ChromaDB (standalone)

All backends support:
- Multi-project isolation
- Differential updates
- LLM output caching
- Advanced metadata filtering
"""

# Will be populated as we implement:
# from pulldata.storage.base import StorageBackend
# from pulldata.storage.postgres_backend import PostgresBackend
# from pulldata.storage.sqlite_backend import SQLiteBackend
# from pulldata.storage.chroma_backend import ChromaBackend
# from pulldata.storage.project_manager import ProjectManager

__all__ = [
    # "StorageBackend",
    # "PostgresBackend",
    # "SQLiteBackend",
    # "ChromaBackend",
    # "ProjectManager",
]
