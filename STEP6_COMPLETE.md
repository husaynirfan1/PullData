# Step 6: RAG Pipeline - COMPLETE ✅

## Overview

Step 6 implements the complete Retrieval-Augmented Generation (RAG) pipeline for PullData. The pipeline orchestrates query processing, document retrieval, context assembly, and provides the foundation for response generation.

## Components Implemented

### 1. QueryProcessor (`pulldata/rag/query_processor.py`)

Handles query preprocessing and understanding:

```python
from pulldata.rag import QueryProcessor

processor = QueryProcessor(
    lowercase=True,
    remove_punctuation=False,
    expand_queries=False,
)

# Process a query
processed = processor.process("What is machine learning?")
print(processed.original_query)    # "What is machine learning?"
print(processed.processed_query)   # "what is machine learning?"

# Extract filters from query
query, filters = processor.extract_filters(
    "machine learning document:ml_paper.pdf page:5"
)
# query: "machine learning"
# filters: {'document_id': 'ml_paper.pdf', 'start_page': 5, 'end_page': 5}
```

**Features:**
- Query cleaning and normalization
- Automatic filter extraction (document:, type:, page:)
- Query expansion (optional)
- Configurable preprocessing

### 2. Retriever (`pulldata/rag/retriever.py`)

Handles document retrieval with hybrid search:

```python
from pulldata.rag import Retriever
from pulldata.storage import HybridSearchEngine
from pulldata.embedding import Embedder

# Create retriever
retriever = Retriever(
    search_engine=search_engine,
    embedder=embedder,
    top_k=10,
    score_threshold=0.5,  # Optional
)

# Retrieve relevant chunks
results = retriever.retrieve(
    query="What is deep learning?",
    k=5,
    filters={'chunk_type': 'text'},
)

for result in results:
    print(f"Rank {result.rank}: {result.chunk.text[:100]}")
    print(f"Score: {result.score:.4f}\n")
```

**Features:**
- Vector similarity search
- Metadata filtering
- Re-ranking with lexical overlap
- Score thresholds
- Context assembly

### 3. RAGPipeline (`pulldata/rag/pipeline.py`)

Complete RAG pipeline orchestration:

```python
from pulldata.rag import RAGPipeline
from pulldata.storage import HybridSearchEngine, VectorStore, MetadataStore
from pulldata.embedding import Embedder

# Initialize components
vector_store = VectorStore(dimension=384)
metadata_store = MetadataStore(db_type="sqlite")
search_engine = HybridSearchEngine(vector_store, metadata_store)
embedder = Embedder()

# Create pipeline
pipeline = RAGPipeline(
    search_engine=search_engine,
    embedder=embedder,
    top_k=5,
    max_context_tokens=2000,
)

# Query the pipeline
response = pipeline.query(
    query="Explain neural networks",
    use_reranking=True,
)

print(f"Query: {response.query}")
print(f"Retrieved {len(response.retrieved_chunks)} chunks")
print(f"\nContext:\n{response.context}")
```

**Features:**
- End-to-end RAG workflow
- Automatic query processing
- Flexible retrieval options
- Context assembly
- Batch query processing

## Complete Usage Example

```python
from pulldata.storage import VectorStore, MetadataStore, HybridSearchEngine
from pulldata.embedding import Embedder
from pulldata.rag import RAGPipeline
from pulldata.core.datatypes import Document, Chunk, Embedding

# Step 1: Initialize storage
vector_store = VectorStore(dimension=384, index_type="Flat")
metadata_store = MetadataStore(db_type="sqlite", db_path="my_data.db")
search_engine = HybridSearchEngine(vector_store, metadata_store)

# Step 2: Initialize embedder
embedder = Embedder(model_name="BAAI/bge-small-en-v1.5")

# Step 3: Add documents
doc = Document(
    id="doc-1",
    source_path="example.pdf",
    filename="example.pdf",
    content_hash="abc123",
    file_size=1024,
)
metadata_store.add_document(doc)

# Step 4: Add chunks and embeddings
chunks = [
    Chunk(
        id="chunk-1",
        document_id="doc-1",
        text="Neural networks are computational models...",
        chunk_index=0,
        chunk_type="text",
        char_count=45,
    ),
    Chunk(
        id="chunk-2",
        document_id="doc-1",
        text="Deep learning uses multiple layers...",
        chunk_index=1,
        chunk_type="text",
        char_count=38,
    ),
]

for chunk in chunks:
    metadata_store.add_chunk(chunk)

# Generate and store embeddings
embeddings = embedder.embed_chunks(chunks)
vector_store.add(embeddings)

# Step 5: Create RAG pipeline
pipeline = RAGPipeline(
    search_engine=search_engine,
    embedder=embedder,
    top_k=5,
    max_context_tokens=1500,
)

# Step 6: Query
response = pipeline.query(
    query="What are neural networks?",
    use_reranking=True,
)

# Step 7: Use results
print(f"Found {len(response.retrieved_chunks)} relevant chunks:")
for result in response.retrieved_chunks:
    print(f"\n[Rank {result.rank}, Score: {result.score:.4f}]")
    print(result.chunk.text[:200])

print(f"\n\nAssembled Context:\n{response.context}")
```

## Advanced Features

### 1. Query with Filters

```python
# Filter by document
response = pipeline.query(
    query="machine learning",
    filters={'document_id': 'doc-1'}
)

# Filter by chunk type
response = pipeline.query(
    query="algorithms",
    filters={'chunk_type': 'table'}
)

# Filter by page range
response = pipeline.query(
    query="introduction",
    filters={'start_page': 1, 'end_page': 5}
)
```

### 2. Retrieve Similar Chunks

```python
# Find chunks similar to a specific chunk
similar = pipeline.get_similar_chunks(
    chunk_id="chunk-1",
    k=10,
)
```

### 3. Batch Processing

```python
# Process multiple queries
queries = [
    "What is deep learning?",
    "Explain backpropagation",
    "What are CNNs?",
]

responses = pipeline.batch_query(queries, k=3)

for response in responses:
    print(f"Query: {response.query}")
    print(f"Top result: {response.retrieved_chunks[0].chunk.text[:100]}\n")
```

### 4. Re-ranking

```python
# Use re-ranking for better results
response = pipeline.query(
    query="neural network architecture",
    use_reranking=True,
)

# Re-ranking combines vector similarity with lexical overlap
for result in response.retrieved_chunks:
    lexical_score = result.metadata.get('lexical_score', 0)
    print(f"Combined score: {result.score:.4f}, Lexical: {lexical_score:.4f}")
```

### 5. Context Assembly

```python
# Get only retrieval results
results = pipeline.retrieve_only(
    query="transformers",
    k=10,
)

# Manually assemble context with custom settings
from pulldata.rag import Retriever

retriever = Retriever(search_engine, embedder)
context = retriever.get_context(
    results=results,
    max_tokens=1000,
    separator="\n\n========\n\n",
)
```

## Data Models

### ProcessedQuery

```python
@dataclass
class ProcessedQuery:
    original_query: str          # Original user query
    processed_query: str         # Cleaned/normalized query
    expanded_queries: list[str]  # Query variations
    metadata: dict[str, Any]     # Additional metadata
```

### RetrievalResult

```python
@dataclass
class RetrievalResult:
    chunk: Chunk               # Retrieved chunk
    score: float              # Relevance score (lower = better for L2)
    rank: int                 # Result ranking (1-indexed)
    metadata: dict[str, Any]  # Additional metadata (lexical_score, etc.)
```

### RAGResponse

```python
@dataclass
class RAGResponse:
    query: str                              # Original query
    processed_query: ProcessedQuery         # Processed query
    retrieved_chunks: list[RetrievalResult] # Retrieved chunks
    context: str                            # Assembled context
    answer: Optional[str]                   # Generated answer (future)
    metadata: dict[str, Any]                # Response metadata
```

## Configuration

```python
# Update pipeline config
pipeline.update_config(
    top_k=10,
    max_context_tokens=3000,
)

# Get pipeline stats
stats = pipeline.get_stats()
print(stats)
# {
#     'top_k': 10,
#     'max_context_tokens': 3000,
#     'search_engine_stats': {
#         'vector_store': {...},
#         'metadata_store': {...}
#     }
# }
```

## Performance Considerations

### 1. Index Type Selection

```python
# For small datasets (<10K chunks): Use Flat index
vector_store = VectorStore(dimension=384, index_type="Flat")

# For medium datasets (10K-100K chunks): Use IVF
vector_store = VectorStore(
    dimension=384,
    index_type="IVF",
    nlist=100,  # Adjust based on dataset size
)

# For large datasets (>100K chunks): Use HNSW
vector_store = VectorStore(
    dimension=384,
    index_type="HNSW",
)
```

### 2. Re-ranking Strategy

```python
# Re-ranking improves quality but adds latency
# Use selectively for important queries

# Standard retrieval (fast)
results = pipeline.retrieve_only(query="...", k=5)

# With re-ranking (slower but better quality)
response = pipeline.query(
    query="...",
    k=5,
    use_reranking=True,
)
```

### 3. Context Length Management

```python
# Limit context to fit model's context window
pipeline = RAGPipeline(
    search_engine=search_engine,
    embedder=embedder,
    top_k=10,
    max_context_tokens=2000,  # Adjust based on your LLM
)
```

## Design Decisions

### 1. Modular Architecture

The pipeline is split into independent components:
- **QueryProcessor**: Query understanding
- **Retriever**: Document retrieval
- **RAGPipeline**: Orchestration

This allows easy customization and testing.

### 2. Hybrid Search

Combines vector similarity with metadata filtering for precise results:
- Vector search: Semantic similarity
- Metadata filters: Exact matching on document, page, type, etc.

### 3. Score Normalization

- Lower scores are better (L2 distance)
- Re-ranking produces combined scores (0-1 range)
- Customizable score thresholds for filtering

### 4. Extensibility

Easy to extend with:
- Custom query processors
- Advanced re-ranking models
- External LLM integration for answer generation

## Integration with Other Modules

```python
# Works seamlessly with embedding layer
from pulldata.embedding import Embedder, EmbeddingCache

cache = EmbeddingCache()
embedder = Embedder(model_name="...")

# Works with all storage backends
from pulldata.storage import VectorStore, MetadataStore

vector_store = VectorStore(...)
metadata_store = MetadataStore(db_type="postgres", ...)

# Integrates with parsing layer
from pulldata.parsing import TextChunker

chunker = TextChunker(chunk_size=512)
chunks = chunker.chunk_text(text, document_id="doc-1")

embeddings = embedder.embed_chunks(chunks)
for chunk in chunks:
    metadata_store.add_chunk(chunk)
vector_store.add(embeddings)
```

## Error Handling

```python
from pulldata.core.exceptions import SearchError

try:
    response = pipeline.query("...")
except SearchError as e:
    print(f"Search failed: {e}")
    print(f"Details: {e.details}")
except ValueError as e:
    print(f"Invalid query: {e}")
```

## Next Steps

The RAG pipeline is now complete and ready for:

1. **LLM Integration** (Step 7): Add response generation using local or API-based LLMs
2. **Testing**: Comprehensive tests for all RAG components
3. **Optimization**: Performance tuning and caching
4. **Advanced Features**:
   - Multi-query retrieval
   - Parent document retrieval
   - Hybrid re-ranking with cross-encoders
   - Query routing

## Files Created

- `pulldata/rag/__init__.py` - Module exports
- `pulldata/rag/query_processor.py` - Query processing (163 lines)
- `pulldata/rag/retriever.py` - Retrieval logic (251 lines)
- `pulldata/rag/pipeline.py` - Main RAG pipeline (243 lines)

## Summary

**Step 6: RAG Pipeline** is complete! ✅

The implementation provides:
- ✅ Flexible query processing with filter extraction
- ✅ Hybrid search combining vectors and metadata
- ✅ Re-ranking for improved result quality
- ✅ Context assembly with token limits
- ✅ Batch processing support
- ✅ Clean, extensible architecture

Total code: **~650 lines** of production-ready RAG pipeline.

Ready for **Step 7: LLM Integration** to add answer generation capabilities!
