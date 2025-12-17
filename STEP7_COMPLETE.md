# Step 7: LLM Integration - COMPLETE ✅

## Overview

Step 7 implements LLM (Large Language Model) integration for PullData, enabling answer generation on top of the RAG pipeline. The implementation supports both local models (via Hugging Face transformers) and API-based models (OpenAI-compatible endpoints).

## Components Implemented

### 1. BaseLLM (`pulldata/llm/base.py`)

Abstract base class defining the LLM interface:

```python
from pulldata.llm import BaseLLM, LLMResponse

class MyCustomLLM(BaseLLM):
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        # Implementation
        pass

    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        # Implementation
        pass

    def count_tokens(self, text: str) -> int:
        # Implementation
        pass
```

**Features:**
- Unified interface for all LLM implementations
- Support for standard and streaming generation
- Token counting capabilities
- Configuration management

### 2. LocalLLM (`pulldata/llm/local_llm.py`)

Local LLM using Hugging Face transformers:

```python
from pulldata.llm import LocalLLM

# Initialize with quantization for efficiency
llm = LocalLLM(
    model_name="Qwen/Qwen2.5-3B-Instruct",
    device="cuda",
    quantization="int8",  # Options: none, int8, int4, fp16
    max_tokens=2048,
    temperature=0.7,
)

# Generate answer
response = llm.generate(
    prompt="What is machine learning?",
    max_tokens=512,
    temperature=0.7,
)

print(response.text)
print(f"Tokens used: {response.tokens_used}")
```

**Features:**
- Automatic quantization (int8, int4, fp16)
- GPU acceleration with CUDA
- Streaming support
- Memory-efficient inference
- Supports any Hugging Face causal LM

### 3. APILLM (`pulldata/llm/api_llm.py`)

API-based LLM for OpenAI-compatible endpoints:

```python
from pulldata.llm import APILLM

# For OpenAI API
llm = APILLM(
    model_name="gpt-3.5-turbo",
    base_url="https://api.openai.com/v1",
    api_key="sk-your-key-here",
)

# For local servers (LM Studio, Ollama, etc.)
llm = APILLM(
    model_name="local-model",
    base_url="http://localhost:1234/v1",
    api_key="sk-dummy",  # Dummy key for local servers
)

# Generate answer
response = llm.generate(
    prompt="Explain neural networks",
    max_tokens=512,
)

print(response.text)
```

**Features:**
- OpenAI API compatibility
- Local server support (LM Studio, Ollama)
- Automatic retries with exponential backoff
- Streaming support
- Connection testing

### 4. PromptTemplate System (`pulldata/llm/prompts.py`)

Flexible prompt templates with variable substitution:

```python
from pulldata.llm import PromptTemplate, PromptManager

# Create custom template
template = PromptTemplate(
    name="custom_qa",
    template="""Answer the question: {query}

Context: {context}

Answer:""",
)

# Format with variables
prompt = template.format(
    query="What is deep learning?",
    context="Deep learning is a subset of machine learning...",
)

# Use PromptManager for pre-built templates
manager = PromptManager()
print(manager.list_templates())
# ['basic_qa', 'detailed_qa', 'extractive_qa', 'summarize', 'multi_doc_qa', 'conversational']

# Format using manager
prompt = manager.format_prompt(
    name="detailed_qa",
    query="What is RAG?",
    context="RAG stands for Retrieval-Augmented Generation...",
)
```

**Pre-built Templates:**
- `basic_qa`: Simple question-answering
- `detailed_qa`: Detailed answers with fallback handling
- `extractive_qa`: Quote-based answers from context
- `summarize`: Content summarization
- `multi_doc_qa`: Multi-document Q&A with citations
- `conversational`: Friendly conversational assistant

### 5. RAG Pipeline Integration

The RAG pipeline now supports end-to-end question answering:

```python
from pulldata.storage import VectorStore, MetadataStore, HybridSearchEngine
from pulldata.embedding import Embedder
from pulldata.rag import RAGPipeline
from pulldata.llm import LocalLLM

# Initialize components
vector_store = VectorStore(dimension=384)
metadata_store = MetadataStore(db_type="sqlite")
search_engine = HybridSearchEngine(vector_store, metadata_store)
embedder = Embedder()

# Initialize LLM
llm = LocalLLM(
    model_name="Qwen/Qwen2.5-3B-Instruct",
    quantization="int8",
)

# Create RAG pipeline with LLM
pipeline = RAGPipeline(
    search_engine=search_engine,
    embedder=embedder,
    llm=llm,
    top_k=5,
    max_context_tokens=2000,
)

# Query with answer generation
response = pipeline.query_with_answer(
    query="What are neural networks?",
    use_reranking=True,
)

print(f"Question: {response.query}")
print(f"Answer: {response.answer}")
print(f"Retrieved {len(response.retrieved_chunks)} chunks")
print(f"Tokens used: {response.metadata['llm_response']['tokens_used']}")
```

## Complete Usage Example

```python
from pathlib import Path
from pulldata.storage import VectorStore, MetadataStore, HybridSearchEngine
from pulldata.embedding import Embedder
from pulldata.rag import RAGPipeline
from pulldata.llm import LocalLLM, APILLM, PromptManager
from pulldata.core.datatypes import Document, Chunk

# Step 1: Set up storage and search
vector_store = VectorStore(dimension=384, index_type="Flat")
metadata_store = MetadataStore(db_type="sqlite", db_path="data.db")
search_engine = HybridSearchEngine(vector_store, metadata_store)

# Step 2: Initialize embedder
embedder = Embedder(model_name="BAAI/bge-small-en-v1.5")

# Step 3: Add documents and chunks (from previous steps)
doc = Document(
    id="doc-1",
    source_path="ml_paper.pdf",
    filename="ml_paper.pdf",
    content_hash="abc123",
    file_size=1024,
)
metadata_store.add_document(doc)

chunks = [
    Chunk(
        id="chunk-1",
        document_id="doc-1",
        text="Neural networks are computational models inspired by biological neural networks...",
        chunk_index=0,
        chunk_type="text",
        char_count=85,
    ),
    # ... more chunks
]

for chunk in chunks:
    metadata_store.add_chunk(chunk)

embeddings = embedder.embed_chunks(chunks)
vector_store.add(embeddings)

# Step 4: Initialize LLM (choose one)

# Option A: Local LLM
llm = LocalLLM(
    model_name="Qwen/Qwen2.5-3B-Instruct",
    device="cuda",
    quantization="int8",
    max_tokens=2048,
)

# Option B: API-based LLM
llm = APILLM(
    model_name="gpt-3.5-turbo",
    base_url="https://api.openai.com/v1",
    api_key="sk-your-api-key",
)

# Option C: Local server (LM Studio)
llm = APILLM(
    model_name="local-model",
    base_url="http://localhost:1234/v1",
    api_key="sk-dummy",
)

# Step 5: Create RAG pipeline with LLM
pipeline = RAGPipeline(
    search_engine=search_engine,
    embedder=embedder,
    llm=llm,
    top_k=5,
    max_context_tokens=2000,
    default_prompt_template="detailed_qa",
)

# Step 6: Query with full answer generation
response = pipeline.query_with_answer(
    query="What are the key components of a neural network?",
    use_reranking=True,
    temperature=0.7,  # LLM parameter
)

# Step 7: Display results
print(f"Question: {response.query}")
print(f"\nAnswer:\n{response.answer}")
print(f"\nRetrieved {len(response.retrieved_chunks)} relevant chunks:")
for result in response.retrieved_chunks[:3]:
    print(f"  - [{result.chunk.document_id}] Score: {result.score:.4f}")
    print(f"    {result.chunk.text[:100]}...")

print(f"\nLLM Stats:")
print(f"  Model: {response.metadata['llm_response']['model']}")
print(f"  Total tokens: {response.metadata['llm_response']['tokens_used']}")
```

## Advanced Features

### 1. Custom Prompt Templates

```python
from pulldata.llm import PromptManager

# Create manager and add custom template
manager = PromptManager()
manager.add_template(
    name="technical_qa",
    template="""You are a technical documentation assistant.
Provide a precise, technical answer to the question based on the context.
Include code examples if relevant.

Context:
{context}

Technical Question: {query}

Technical Answer:""",
    description="Technical documentation Q&A",
)

# Use in pipeline
pipeline = RAGPipeline(
    search_engine=search_engine,
    embedder=embedder,
    llm=llm,
    prompt_manager=manager,
    default_prompt_template="technical_qa",
)
```

### 2. Streaming Responses

```python
# For local LLM streaming
response = pipeline.query_with_answer(
    query="Explain transformers in detail",
    stream=True,  # Enable streaming
)

# Note: Current implementation collects all chunks
# In production, you'd yield chunks for real-time display
```

### 3. Separate Answer Generation

```python
# First, retrieve without generating answer
response = pipeline.query(
    query="What is backpropagation?",
    use_reranking=True,
)

# Inspect retrieved chunks
print(f"Found {len(response.retrieved_chunks)} chunks")

# Generate answer separately
answer = pipeline.generate_answer(
    response=response,
    prompt_template="extractive_qa",
    temperature=0.5,
)

response.answer = answer
print(answer)
```

### 4. Multiple LLMs for Different Tasks

```python
# Use different LLMs for different purposes
fast_llm = APILLM(model_name="gpt-3.5-turbo", ...)  # Fast, for quick queries
powerful_llm = APILLM(model_name="gpt-4", ...)      # Powerful, for complex queries

# Create multiple pipelines
quick_pipeline = RAGPipeline(..., llm=fast_llm)
detailed_pipeline = RAGPipeline(..., llm=powerful_llm)

# Use based on query complexity
if is_simple_query(query):
    response = quick_pipeline.query_with_answer(query)
else:
    response = detailed_pipeline.query_with_answer(query)
```

### 5. Model Quantization Strategies

```python
# For small models (< 3B parameters)
llm = LocalLLM(
    model_name="Qwen/Qwen2.5-3B-Instruct",
    quantization="int8",  # Good balance
)

# For medium models (3B-7B parameters)
llm = LocalLLM(
    model_name="meta-llama/Llama-2-7b-chat-hf",
    quantization="int4",  # More aggressive
)

# For large models (> 7B parameters)
llm = LocalLLM(
    model_name="meta-llama/Llama-2-13b-chat-hf",
    quantization="int4",  # Necessary for consumer GPUs
)

# For production/no quantization
llm = LocalLLM(
    model_name="Qwen/Qwen2.5-3B-Instruct",
    quantization="none",  # Full precision
    torch_dtype="fp16",   # Still use fp16 for efficiency
)
```

## Data Models

### LLMResponse

```python
@dataclass
class LLMResponse:
    text: str                      # Generated text
    prompt: str                    # Input prompt
    model: str                     # Model name
    tokens_used: Optional[int]     # Total tokens
    prompt_tokens: Optional[int]   # Prompt tokens
    completion_tokens: Optional[int]  # Completion tokens
    finish_reason: Optional[str]   # Completion reason
    metadata: dict[str, Any]       # Additional metadata
```

### RAGResponse (Extended)

```python
@dataclass
class RAGResponse:
    query: str                              # Original query
    processed_query: ProcessedQuery         # Processed query
    retrieved_chunks: list[RetrievalResult] # Retrieved chunks
    context: str                            # Assembled context
    answer: Optional[str]                   # Generated answer (NEW)
    metadata: dict[str, Any]                # Response metadata
```

## Configuration

### From Config File

```yaml
# config.yaml
models:
  llm:
    provider: local  # or 'api'

    local:
      name: "Qwen/Qwen2.5-3B-Instruct"
      quantization: int8
      device: cuda
      cache_dir: ./models/llm

    api:
      base_url: "http://localhost:1234/v1"
      api_key: "sk-dummy"
      model: "local-model"
      timeout: 60

    generation:
      max_tokens: 2048
      temperature: 0.7
      top_p: 0.9
```

### From Code

```python
from pulldata.core.config import load_config

# Load configuration
config = load_config("config.yaml")

# Create LLM from config
if config.models.llm.provider == "local":
    llm = LocalLLM(
        model_name=config.models.llm.local.name,
        device=config.models.llm.local.device,
        quantization=config.models.llm.local.quantization,
        max_tokens=config.models.llm.generation.max_tokens,
        temperature=config.models.llm.generation.temperature,
    )
else:  # api
    llm = APILLM(
        model_name=config.models.llm.api.model,
        base_url=config.models.llm.api.base_url,
        api_key=config.models.llm.api.api_key,
        max_tokens=config.models.llm.generation.max_tokens,
        temperature=config.models.llm.generation.temperature,
    )
```

## Performance Considerations

### 1. Model Selection

```python
# For CPU-only systems
llm = LocalLLM(
    model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",  # Small model
    device="cpu",
    quantization="int8",
)

# For systems with GPU (8GB+ VRAM)
llm = LocalLLM(
    model_name="Qwen/Qwen2.5-3B-Instruct",
    device="cuda",
    quantization="int8",
)

# For high-end GPUs (24GB+ VRAM)
llm = LocalLLM(
    model_name="meta-llama/Llama-2-13b-chat-hf",
    device="cuda",
    quantization="int4",
)
```

### 2. Context Length Management

```python
# Estimate context size
def estimate_tokens(text: str) -> int:
    return len(text) // 4  # Rough estimate

# Limit context to fit model window
max_model_tokens = 4096
max_completion_tokens = 512
max_context_tokens = max_model_tokens - max_completion_tokens - 100  # Buffer

pipeline = RAGPipeline(
    ...,
    max_context_tokens=max_context_tokens,
)
```

### 3. Batch Processing

```python
# Process multiple queries efficiently
queries = [
    "What is machine learning?",
    "Explain neural networks",
    "What are transformers?",
]

responses = []
for query in queries:
    response = pipeline.query_with_answer(query)
    responses.append(response)
```

### 4. Caching LLM Responses

```python
import hashlib
import json

class LLMCache:
    def __init__(self):
        self.cache = {}

    def get_cache_key(self, prompt: str, **kwargs) -> str:
        key_data = {"prompt": prompt, **kwargs}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, prompt: str, **kwargs) -> Optional[str]:
        key = self.get_cache_key(prompt, **kwargs)
        return self.cache.get(key)

    def set(self, prompt: str, answer: str, **kwargs) -> None:
        key = self.get_cache_key(prompt, **kwargs)
        self.cache[key] = answer

# Use cache
cache = LLMCache()

def cached_generate(pipeline, query, **kwargs):
    # Check cache
    cached_answer = cache.get(query, **kwargs)
    if cached_answer:
        return cached_answer

    # Generate if not cached
    response = pipeline.query_with_answer(query, **kwargs)
    cache.set(query, response.answer, **kwargs)
    return response.answer
```

## Error Handling

```python
from pulldata.core.exceptions import LLMError, LLMLoadError, GenerationError

try:
    # Initialize LLM
    llm = LocalLLM(model_name="Qwen/Qwen2.5-3B-Instruct")

    # Create pipeline
    pipeline = RAGPipeline(..., llm=llm)

    # Generate answer
    response = pipeline.query_with_answer("What is AI?")

except LLMLoadError as e:
    print(f"Failed to load LLM: {e}")
    print(f"Details: {e.details}")

except GenerationError as e:
    print(f"Answer generation failed: {e}")

except LLMError as e:
    print(f"LLM error: {e}")
```

## Integration Examples

### With Document Parsing

```python
from pulldata.parsing import PDFParser, TextChunker

# Parse PDF
parser = PDFParser()
parsed_doc = parser.parse("document.pdf")

# Chunk text
chunker = TextChunker(chunk_size=512, chunk_overlap=50)
chunks = chunker.chunk_document(parsed_doc)

# Store and index
for chunk in chunks:
    metadata_store.add_chunk(chunk)

embeddings = embedder.embed_chunks(chunks)
vector_store.add(embeddings)

# Query with LLM
response = pipeline.query_with_answer(
    "Summarize the main findings from the document"
)
```

### With Multiple Documents

```python
# Add multiple documents
documents = ["paper1.pdf", "paper2.pdf", "paper3.pdf"]

for doc_path in documents:
    # Parse and chunk
    parsed = parser.parse(doc_path)
    chunks = chunker.chunk_document(parsed)

    # Store
    for chunk in chunks:
        metadata_store.add_chunk(chunk)

    embeddings = embedder.embed_chunks(chunks)
    vector_store.add(embeddings)

# Query across all documents
response = pipeline.query_with_answer(
    "Compare the methodologies across all papers",
    prompt_template="multi_doc_qa",
)
```

## Design Decisions

### 1. Abstract Base Class

Using `BaseLLM` provides:
- Unified interface for all LLM implementations
- Easy to add new providers
- Consistent API across local and API-based models

### 2. Optional LLM Integration

RAG pipeline works with or without LLM:
- Without LLM: Retrieval only (existing behavior)
- With LLM: Full RAG with answer generation
- Backwards compatible with Step 6

### 3. Flexible Prompt System

PromptManager allows:
- Pre-built templates for common tasks
- Easy customization
- Variable substitution
- Template reuse

### 4. Quantization Support

Enables running large models on consumer hardware:
- int8: 2x memory reduction
- int4: 4x memory reduction
- Minimal accuracy loss for most tasks

## Next Steps

With Step 7 complete, the core PullData RAG system is fully functional. Potential enhancements:

1. **Advanced Re-ranking**: Cross-encoder models for better retrieval
2. **Multi-turn Conversations**: Chat history and context
3. **Citation Extraction**: Link answers to specific chunks
4. **Answer Validation**: Confidence scoring and hallucination detection
5. **Fine-tuning Support**: Adapt models to specific domains
6. **Distributed Inference**: Load balancing across multiple GPUs/nodes

## Files Created

- `pulldata/llm/__init__.py` - Module exports
- `pulldata/llm/base.py` - Base LLM interface (176 lines)
- `pulldata/llm/local_llm.py` - Local LLM implementation (341 lines)
- `pulldata/llm/api_llm.py` - API LLM implementation (315 lines)
- `pulldata/llm/prompts.py` - Prompt template system (218 lines)
- `pulldata/rag/pipeline.py` - Updated with LLM integration (132 new lines)
- `pulldata/core/exceptions.py` - Added LLMError

## Summary

**Step 7: LLM Integration** is complete! ✅

The implementation provides:
- ✅ Flexible LLM interface supporting local and API models
- ✅ Quantization support for efficient inference
- ✅ Streaming generation capabilities
- ✅ Rich prompt template system
- ✅ Seamless integration with RAG pipeline
- ✅ Support for major LLM providers
- ✅ Error handling and retries

Total code: **~1,180 lines** of production-ready LLM integration.

**PullData now has a complete RAG system with answer generation!** 🎉
