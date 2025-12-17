# API Configuration Guide

PullData supports both **local models** (via transformers) and **OpenAI-compatible API endpoints**. This gives you maximum flexibility to use:

- Local models on your own hardware
- LM Studio or Ollama for easy local inference
- Cloud APIs like OpenAI, Groq, or Together AI
- Self-hosted inference servers (vLLM, Text Generation WebUI)

## Quick Start

### Option 1: Local Models (Default)

```yaml
# configs/default.yaml
models:
  llm:
    provider: local
    local:
      name: Qwen/Qwen2.5-3B-Instruct
      quantization: int8
      device: cuda
```

### Option 2: LM Studio

```yaml
# configs/default.yaml
models:
  llm:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      api_key: sk-dummy
      model: local-model
```

### Option 3: OpenAI

```yaml
# configs/default.yaml
models:
  llm:
    provider: api
    api:
      base_url: https://api.openai.com/v1
      api_key: ${OPENAI_API_KEY}
      model: gpt-3.5-turbo
```

## Supported API Providers

### 1. LM Studio (Recommended for Local)

**What is it?** Desktop app for running LLMs locally with a beautiful UI and OpenAI-compatible API.

**Setup:**
1. Download from [https://lmstudio.ai](https://lmstudio.ai)
2. Install and launch LM Studio
3. Download a model (e.g., Llama 3.2 3B, Qwen 2.5 3B)
4. Start the local server (Server tab)
5. Configure PullData:

```yaml
# configs/default.yaml
models:
  llm:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      api_key: sk-dummy  # LM Studio doesn't require a real key
      model: local-model  # Or the specific model name
```

```bash
# .env
LM_STUDIO_API_KEY=sk-dummy
LM_STUDIO_BASE_URL=http://localhost:1234/v1
```

**Use Preset:**
```yaml
# Use the pre-configured preset
preset: lm_studio_preset  # From configs/models.yaml
```

---

### 2. OpenAI

**What is it?** Official OpenAI API (GPT-3.5, GPT-4, GPT-4 Turbo).

**Setup:**
1. Get API key at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Set in `.env`:

```bash
OPENAI_API_KEY=sk-proj-your_actual_key_here
```

3. Configure:

```yaml
# configs/default.yaml
models:
  llm:
    provider: api
    api:
      base_url: https://api.openai.com/v1
      api_key: ${OPENAI_API_KEY}
      model: gpt-3.5-turbo  # or gpt-4, gpt-4-turbo, gpt-4o
```

**Popular Models:**
- `gpt-3.5-turbo` - Fast, affordable
- `gpt-4` - High quality
- `gpt-4-turbo` - Faster GPT-4
- `gpt-4o` - Latest, multimodal

---

### 3. Groq

**What is it?** Ultra-fast inference API with open-source models.

**Setup:**
1. Get API key at [https://console.groq.com/keys](https://console.groq.com/keys)
2. Set in `.env`:

```bash
GROQ_API_KEY=gsk_your_actual_key_here
```

3. Configure:

```yaml
models:
  llm:
    provider: api
    api:
      base_url: https://api.groq.com/openai/v1
      api_key: ${GROQ_API_KEY}
      model: llama-3.2-3b-instruct  # or mixtral-8x7b, llama-70b
```

**Popular Models:**
- `llama-3.2-3b-instruct` - Fast, efficient
- `llama-3.1-70b-versatile` - High quality
- `mixtral-8x7b-32768` - Good balance

---

### 4. Together AI

**What is it?** Fast inference API for open-source models.

**Setup:**
1. Get API key at [https://api.together.xyz/settings/api-keys](https://api.together.xyz/settings/api-keys)
2. Set in `.env`:

```bash
TOGETHER_API_KEY=your_actual_key_here
```

3. Configure:

```yaml
models:
  llm:
    provider: api
    api:
      base_url: https://api.together.xyz/v1
      api_key: ${TOGETHER_API_KEY}
      model: meta-llama/Llama-3.2-3B-Instruct
```

---

### 5. Ollama

**What is it?** Easy-to-use local LLM runner.

**Setup:**
1. Install Ollama from [https://ollama.ai](https://ollama.ai)
2. Pull a model: `ollama pull llama3.2:3b`
3. Ollama automatically starts an API server
4. Configure:

```yaml
models:
  llm:
    provider: api
    api:
      base_url: http://localhost:11434/v1
      api_key: sk-dummy
      model: llama3.2:3b
```

**Use Preset:**
```yaml
preset: ollama_preset
```

---

### 6. vLLM

**What is it?** High-throughput, self-hosted inference server.

**Setup:**
1. Install vLLM:
```bash
pip install vllm
```

2. Start server:
```bash
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-3B-Instruct \
  --port 8000
```

3. Configure:

```yaml
models:
  llm:
    provider: api
    api:
      base_url: http://localhost:8000/v1
      api_key: sk-dummy
      model: Qwen/Qwen2.5-3B-Instruct
```

**Use Preset:**
```yaml
preset: vllm_preset
```

---

### 7. Text Generation WebUI (Oobabooga)

**What is it?** Feature-rich web UI for running LLMs.

**Setup:**
1. Install from [https://github.com/oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui)
2. Enable OpenAI API extension
3. Start with `--api` flag
4. Configure:

```yaml
models:
  llm:
    provider: api
    api:
      base_url: http://localhost:5000/v1
      api_key: sk-dummy
      model: default
```

**Use Preset:**
```yaml
preset: text_gen_webui_preset
```

---

## Embedding Models Configuration

Embeddings are used to convert text into vector representations for similarity search. PullData supports **both local and API-based embeddings**.

### Local Embeddings (Default - Recommended)

```yaml
# configs/default.yaml
models:
  embedder:
    provider: local  # or omit (local is default)
    name: BAAI/bge-small-en-v1.5
    dimension: 384
    device: cpu  # or 'cuda' for GPU
    batch_size: 32
    normalize_embeddings: true
```

**Advantages:**
- ✅ Free (no API costs)
- ✅ Fast batch processing
- ✅  No network latency
- ✅ Full privacy
- ✅ Offline capable

### API Embeddings (New!)

```yaml
# configs/default.yaml
models:
  embedder:
    provider: api  # Use API for embeddings
    dimension: 768  # Match your model's dimension
    
    api:
      base_url: http://localhost:1234/v1  # LM Studio
      api_key: lm-studio
      model: nomic-embed-text-v1.5
      batch_size: 100
      timeout: 60
      max_retries: 3
```

**Advantages:**
- ✅ Easy setup (no local model downloads)
- ✅ Centralized management (LM Studio UI)
- ✅ Easy model switching
- ✅ Works on any machine

**Disadvantages:**
- ❌ Slower for large batches (network calls)
- ❌ Requires API server running
- ❌ Costs money if using cloud APIs

### Recommended Embedding Models

**Local Models:**
| Model | Dimension | Size | Quality | Speed |
|-------|-----------|------|---------|-------|
| `BAAI/bge-small-en-v1.5` | 384 | ~130MB | Good | Fast |
| `BAAI/bge-base-en-v1.5` | 768 | ~440MB | Better | Medium |
| `BAAI/bge-large-en-v1.5` | 1024 | ~1.3GB | Best | Slow |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | ~90MB | Good | Very Fast |

**API Models (via LM Studio):**
| Model | Dimension | Quality | Notes |
|-------|-----------|---------|-------|
| `nomic-embed-text-v1.5` | 768 | Excellent | Recommended |
| `bge-large-en-v1.5` | 1024 | Best | Slower |
| `e5-mistral-7b-instruct` | 4096 | Top-tier | Resource intensive |

### LM Studio Embedding Setup

**Option 1: Local Embeddings + LM Studio LLM (Recommended)**
```yaml
models:
  embedder:
    provider: local  # Fast, free local embeddings
    name: BAAI/bge-small-en-v1.5
    device: cpu
  
  llm:
    provider: api  # LM Studio for answer generation
    api:
      base_url: http://localhost:1234/v1
      model: local-model
```

**Option 2: LM Studio for Everything**
```yaml
models:
  embedder:
    provider: api  # LM Studio for embeddings
    api:
      base_url: http://localhost:1234/v1
      model: nomic-embed-text-v1.5
  
  llm:
    provider: api  # LM Studio for LLM
    api:
      base_url: http://localhost:1234/v1
      model: local-model
```

**Which to choose?**
- Use Option 1 for best performance (local embeddings are faster)
- Use Option 2 if you want all inference in LM Studio UI

### Performance Tips

1. **Use GPU if available**: 10x faster than CPU
2. **Match dimensions**: Vector store dimension must match embedding dimension
3. **Batch size**: Larger = faster,  but uses more memory
4. **Model size**: Smaller models = faster, less accurate; Larger = slower, more accurate

### LM Studio Note

**LM Studio can now be used for BOTH LLM and embeddings** (as of latest release).

You can choose between:
- **Local embeddings** (recommended for performance): Fast, free, no API calls
- **API embeddings** (via LM Studio): Centralized management, easy model switching

**Recommended Setup (Best Performance):**
```yaml
models:
  # Embeddings: Local (sentence-transformers) - Fast & Free
  embedder:
    provider: local
    name: BAAI/bge-small-en-v1.5
    device: cpu  # or cuda

  # LLM: LM Studio API
  llm:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      api_key: sk-dummy
      model: local-model
```

**Alternative (All-in-LM Studio):**
```yaml
models:
  # Both embeddings and LLM via LM Studio
  embedder:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      model: nomic-embed-text-v1.5

  llm:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      model: local-model
```

---

## Configuration Examples

### Example 1: Switch from Local to LM Studio

**Before (Local):**
```yaml
models:
  llm:
    provider: local
    local:
      name: Qwen/Qwen2.5-3B-Instruct
      quantization: int8
      device: cuda
```

**After (LM Studio):**
```yaml
models:
  llm:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      api_key: sk-dummy
      model: local-model
```

### Example 2: Use OpenAI for LLM, Local for Embeddings

```yaml
models:
  # Embeddings still run locally
  embedder:
    name: BAAI/bge-small-en-v1.5
    device: cpu  # or cuda

  # LLM via OpenAI API
  llm:
    provider: api
    api:
      base_url: https://api.openai.com/v1
      api_key: ${OPENAI_API_KEY}
      model: gpt-3.5-turbo
```

### Example 3: Load Preset

```yaml
# In your config, reference a preset from configs/models.yaml
preset: lm_studio_preset  # Loads all settings from preset
```

Or override specific values:

```yaml
preset: lm_studio_preset
models:
  llm:
    api:
      model: my-custom-model  # Override just the model
```

## Environment Variables

All sensitive values should be in `.env`:

```bash
# .env
OPENAI_API_KEY=sk-proj-your_key_here
GROQ_API_KEY=gsk_your_key_here
TOGETHER_API_KEY=your_key_here

# Local servers usually don't need real keys
LM_STUDIO_API_KEY=sk-dummy
OLLAMA_API_KEY=sk-dummy
VLLM_API_KEY=sk-dummy
```

Reference in YAML with `${VARIABLE_NAME}`:

```yaml
api:
  api_key: ${OPENAI_API_KEY}
```

## Generation Parameters

These apply to both local and API models:

```yaml
models:
  llm:
    generation:
      max_tokens: 2048          # Maximum response length
      temperature: 0.7          # Randomness (0.0-2.0)
      top_p: 0.9               # Nucleus sampling
      top_k: 50                # Top-k sampling (not all APIs support)
      frequency_penalty: 0.0   # Penalize repeated tokens
      presence_penalty: 0.0    # Penalize new topics
```

## API vs Local: When to Use What?

### Use Local Models When:
- You have a GPU (even modest ones like P4)
- You need maximum privacy/offline capability
- You want zero API costs
- You need full control over model behavior

### Use API Endpoints When:
- No GPU available or GPU not powerful enough
- Need faster responses (Groq is ultra-fast)
- Want to use state-of-the-art models (GPT-4)
- Don't want to manage model downloads

### Use LM Studio/Ollama When:
- Want easy local setup
- Need a UI for model management
- Want OpenAI-compatible API locally
- Transitioning from cloud to local

## Ingestion Statistics

When you ingest documents, PullData returns statistics about the operation:

```python
stats = pd.ingest(str(sample_file))
print(f"Processed: {stats.get('processed_files', 0)} files")
print(f"New chunks: {stats.get('new_chunks', 0)}")
print(f"Total chunks: {stats.get('total_chunks', 0)}")
print(f"Skipped chunks: {stats.get('skipped_chunks', 0)}")
```

**Available Statistics:**
- `processed_files`: Number of files successfully ingested
- `failed_files`: Number of files that failed to ingest
- `total_files`: Total files attempted
- `new_chunks`: Number of newly created chunks (added to vector store)
- `total_chunks`: Total chunks parsed from all documents
- `updated_chunks`: Number of chunks updated (when using differential updates)
- `skipped_chunks`: Number of unchanged chunks (when differential updates enabled)

**Note:** When differential updates are enabled (default), existing unchanged chunks are skipped to avoid re-embedding the same content.

---

## Troubleshooting

### Connection Refused
```
Error: Connection refused to http://localhost:1234/v1
```

**Solution:** Make sure the API server is running:
- LM Studio: Check "Server" tab is started
- Ollama: Run `ollama serve`
- vLLM: Start the API server first

### Invalid API Key
```
Error: Invalid API key
```

**Solution:**
1. Check `.env` file has the correct key
2. Reload environment: `source .env` or restart terminal
3. For local servers, try `sk-dummy` as the key

### Model Not Found
```
Error: Model 'xyz' not found
```

**Solution:**
1. Check model name matches what's loaded in your API server
2. For LM Studio: Use `local-model` or the exact model name shown
3. For Ollama: Use format like `llama3.2:3b`

### Timeout Errors
```
Error: Request timeout after 60s
```

**Solution:**
Increase timeout in config:
```yaml
api:
  timeout: 120  # Increase to 120 seconds
```

### Retrieval Returns 0 Sources
```
Query: What is machine learning?
Answer: No answer generated
Sources: 0
```

**Possible Causes & Solutions:**

1. **Dimension Mismatch**
   - Symptom: `ValueError: Embedding dimension X does not match store dimension Y`
   - Solution: Ensure `embedder.dimension` matches your model's actual output
   ```yaml
   embedder:
     dimension: 768  # Must match your embedding model's dimension
   ```

2. **Empty Vector Store**
   - Check: Vector store may not have any chunks
   - Solution: Re-run ingestion and check for errors
   ```python
   # Debug: Check vector store status
   vec_size = pd._vector_store.index.ntotal
   print(f"Vector store size: {vec_size}")
   ```

3. **Chunk ID Mismatch** (Fixed in v0.1.0+)
   - Symptom: Logs show "chunk_id 'X' not found in metadata store"
   - Solution: Update to latest version - chunk IDs are now synchronized

4. **Database Schema Outdated**
   - Symptom: `ValidationError: chunk_hash/token_count field required`
   - Solution: Delete old database and re-ingest
   ```bash
   rm -rf ./data/your_project/
   ```

### FAISS Warnings (Normal Behavior)
```
Invalid index -1 returned by FAISS
```

**This is normal!** When you request k=5 results but only have 1 chunk in the index, FAISS returns:
- Index 0 (valid chunk)
- Index -1, -1, -1, -1 (sentinels for missing results)

The code automatically filters these out. These warnings only appear in debug mode.

## Python API Usage

```python
from pulldata import PullData

# Using local model
rag = PullData(
    project="my_project",
    config="configs/default.yaml"  # provider=local
)

# Using LM Studio
rag = PullData(
    project="my_project",
    llm_provider="api",
    api_base_url="http://localhost:1234/v1",
    api_key="sk-dummy"
)

# Using OpenAI
rag = PullData(
    project="my_project",
    llm_provider="api",
    api_base_url="https://api.openai.com/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    api_model="gpt-3.5-turbo"
)
```

## Performance Comparison

| Provider | Latency | Cost | Quality | Privacy |
|----------|---------|------|---------|---------|
| Local (P4) | ~2s | $0 | Good | 100% |
| LM Studio | ~2s | $0 | Good | 100% |
| Ollama | ~2s | $0 | Good | 100% |
| Groq | ~0.5s | $$ | Excellent | Cloud |
| OpenAI GPT-4 | ~3s | $$$$ | Best | Cloud |
| OpenAI GPT-3.5 | ~1s | $ | Good | Cloud |
| Together AI | ~1s | $$ | Good | Cloud |

## Cost Estimates

For a 30-page PDF → Excel workflow:

| Provider | Cost per Document | Notes |
|----------|------------------|-------|
| Local | $0 | Only electricity |
| LM Studio | $0 | Only electricity |
| OpenAI GPT-3.5 | ~$0.02 | ~10K tokens |
| OpenAI GPT-4 | ~$0.30 | ~10K tokens |
| Groq | ~$0.01 | Very fast |
| Together AI | ~$0.02 | Good balance |

---

**Need Help?**
- Check [QUICKSTART.md](../QUICKSTART.md) for basic setup
- See [README.md](../README.md) for full documentation
- Report issues at [GitHub Issues](https://github.com/pulldata/pulldata/issues)
