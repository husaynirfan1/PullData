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

Embeddings are used to convert text into vector representations for similarity search. PullData supports **local embedding models only** (via sentence-transformers), as this is more efficient and doesn't require API calls for every chunk.

###  Configuration

```yaml
# configs/default.yaml
models:
  embedder:
    name: BAAI/bge-small-en-v1.5  # Model from HuggingFace
    dimension: 384                 # Embedding dimension
    device: cpu                    # or 'cuda' for GPU
    batch_size: 32                 # Chunks per batch
    normalize_embeddings: true     # L2 normalization
    cache_dir: ./models/embeddings # Download location
```

### Recommended Embedding Models

| Model | Dimension | Size | Quality | Speed |
|-------|-----------|------|---------|-------|
| `BAAI/bge-small-en-v1.5` | 384 | ~130MB | Good | Fast |
| `BAAI/bge-base-en-v1.5` | 768 | ~440MB | Better | Medium |
| `BAAI/bge-large-en-v1.5` | 1024 | ~1.3GB | Best | Slow |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | ~90MB | Good | Very Fast |
| `intfloat/e5-small-v2` | 384 | ~130MB | Good | Fast |

###Using GPU for Embeddings

```yaml
models:
  embedder:
    name: BAAI/bge-small-en-v1.5
    device: cuda  # Use GPU (10x faster)
    batch_size: 128  # Increase batch size with GPU
```

### Performance Tips

1. **Use GPU if available**: 10x faster than CPU
2. **Match dimensions**: Vector store dimension must match embedding dimension
3. **Batch size**: Larger = faster,  but uses more memory
4. **Model size**: Smaller models = faster, less accurate; Larger = slower, more accurate

### LM Studio Note

**LM Studio is ONLY for the LLM (answer generation), NOT for embeddings.**

Embeddings always run locally using sentence-transformers. This is intentional because:
- Embedding thousands of chunks would be expensive via API
- Local embedding models are fast and efficient
- No network latency for vector generation

**Typical Setup with LM Studio:**
```yaml
models:
  # Embeddings:  Local (sentence-transformers)
  embedder:
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
