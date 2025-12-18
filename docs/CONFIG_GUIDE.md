# PullData Configuration Guide

Complete guide for configuring PullData for different use cases, especially when using the Web UI or REST API.

---

## Quick Start

### Option 1: Edit Default Config (Easiest)

Before starting the server, edit `configs/default.yaml`:

```bash
# Open and edit the config
notepad configs/default.yaml  # Windows
nano configs/default.yaml     # Linux/Mac

# Then start the server
python run_server.py
```

All projects will use this config by default.

### Option 2: Create Project-Specific Configs

Create separate config files for different setups:

```bash
# Copy default config
cp configs/default.yaml configs/lm_studio.yaml

# Edit for LM Studio API
notepad configs/lm_studio.yaml

# Select it in the Web UI when creating project
```

### Option 3: Use Environment Variables

Set environment variables in `.env`:

```bash
# LM Studio
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=sk-dummy
```

Then reference in your config with `${LM_STUDIO_BASE_URL}`.

---

## Configuration via Web UI

The Web UI (http://localhost:8000/ui/) now supports config selection:

### During Ingest:
1. Select your project
2. **Choose Configuration** from dropdown (or leave as "Default")
3. Upload files
4. Click "Ingest Documents"

### During Query:
1. Select your project
2. **Choose Configuration** to override (optional)
3. Enter query
4. Click "Query"

The Web UI automatically discovers all `.yaml` files in the `configs/` directory.

---

## Configuration via REST API

### List Available Configs

```bash
curl http://localhost:8000/configs
```

Response:
```json
{
  "configs": [
    {
      "name": "default",
      "path": "configs/default.yaml",
      "filename": "default.yaml"
    },
    {
      "name": "lm_studio",
      "path": "configs/lm_studio.yaml",
      "filename": "lm_studio.yaml"
    }
  ],
  "count": 2
}
```

### Ingest with Config

```bash
curl -X POST "http://localhost:8000/ingest/upload?project=my_project&config_path=configs/lm_studio.yaml" \
  -F "files=@document.pdf"
```

### Query with Config

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "project": "my_project",
    "query": "What are the key findings?",
    "config_path": "configs/lm_studio.yaml",
    "output_format": "excel"
  }'
```

---

## Common Configuration Scenarios

### 1. LM Studio API (Recommended for No GPU)

Create `configs/lm_studio.yaml`:

```yaml
models:
  embedder:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      model: nomic-embed-text-v1.5
      api_key: sk-dummy

  llm:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      model: qwen2.5-3b-instruct
      api_key: sk-dummy
      temperature: 0.7

storage:
  backend: local
  local:
    sqlite_path: ./data/pulldata.db
    faiss_index_path: ./data/faiss_indexes
```

**Steps:**
1. Install and start LM Studio
2. Load models in LM Studio
3. Start LM Studio server
4. Select this config in Web UI

### 2. OpenAI API

Create `configs/openai.yaml`:

```yaml
models:
  embedder:
    provider: api
    api:
      base_url: https://api.openai.com/v1
      model: text-embedding-3-small
      api_key: ${OPENAI_API_KEY}  # From .env file

  llm:
    provider: api
    api:
      base_url: https://api.openai.com/v1
      model: gpt-3.5-turbo
      api_key: ${OPENAI_API_KEY}
      temperature: 0.7

storage:
  backend: local
  local:
    sqlite_path: ./data/pulldata.db
    faiss_index_path: ./data/faiss_indexes
```

**Prerequisites:**
1. Add `OPENAI_API_KEY` to `.env`
2. Select this config in Web UI

### 3. Local Models (GPU Required)

Create `configs/local_gpu.yaml`:

```yaml
models:
  embedder:
    provider: local
    local:
      model_name: BAAI/bge-small-en-v1.5
      device: cuda

  llm:
    provider: local
    local:
      model_name: Qwen/Qwen2.5-3B-Instruct
      device: cuda
      load_in_8bit: true
      max_new_tokens: 512
      temperature: 0.7

storage:
  backend: local
  local:
    sqlite_path: ./data/pulldata.db
    faiss_index_path: ./data/faiss_indexes
```

### 4. Ollama

Create `configs/ollama.yaml`:

```yaml
models:
  embedder:
    provider: api
    api:
      base_url: http://localhost:11434/v1
      model: nomic-embed-text
      api_key: sk-dummy

  llm:
    provider: api
    api:
      base_url: http://localhost:11434/v1
      model: llama3.2
      api_key: sk-dummy

storage:
  backend: local
```

**Prerequisites:**
1. Install Ollama: https://ollama.ai
2. Pull models: `ollama pull nomic-embed-text` and `ollama pull llama3.2`
3. Ollama runs automatically on port 11434

### 5. Groq (Fast Cloud Inference)

Create `configs/groq.yaml`:

```yaml
models:
  embedder:
    provider: api
    api:
      base_url: https://api.openai.com/v1  # Use OpenAI for embeddings
      model: text-embedding-3-small
      api_key: ${OPENAI_API_KEY}

  llm:
    provider: api
    api:
      base_url: https://api.groq.com/openai/v1
      model: llama-3.1-8b-instant
      api_key: ${GROQ_API_KEY}
      temperature: 0.5

storage:
  backend: local
```

**Prerequisites:**
1. Get API keys from https://console.groq.com
2. Add to `.env`: `GROQ_API_KEY=gsk_your_key`

---

## Configuration Structure

### Complete Config Template

```yaml
# Embedding & LLM Models
models:
  embedder:
    provider: api  # or 'local'
    api:
      base_url: http://localhost:1234/v1
      model: nomic-embed-text-v1.5
      api_key: sk-dummy
      timeout: 30
      max_retries: 3
    local:
      model_name: BAAI/bge-small-en-v1.5
      device: cuda
      batch_size: 32

  llm:
    provider: api  # or 'local'
    api:
      base_url: http://localhost:1234/v1
      model: qwen2.5-3b-instruct
      api_key: sk-dummy
      temperature: 0.7
      max_tokens: 512
      timeout: 60
    local:
      model_name: Qwen/Qwen2.5-3B-Instruct
      device: cuda
      load_in_8bit: true
      max_new_tokens: 512
      temperature: 0.7

# Storage Backend
storage:
  backend: local  # or 'postgres', 'chromadb'

  local:
    sqlite_path: ./data/pulldata.db
    faiss_index_path: ./data/faiss_indexes

  postgres:
    host: localhost
    port: 5432
    database: pulldata
    user: pulldata_user
    password: ${POSTGRES_PASSWORD}

  chromadb:
    persist_directory: ./data/chroma_db

# Document Processing
parsing:
  chunk_size: 512
  chunk_overlap: 50
  min_chunk_size: 100

# Retrieval
retrieval:
  top_k: 5
  similarity_threshold: 0.0
  use_reranking: false

# Output Formats
output:
  excel:
    auto_format: true
    freeze_panes: true

  markdown:
    include_toc: true

  pdf:
    page_size: A4

# Caching
cache:
  enabled: true
  llm_cache_enabled: true
  embedding_cache_enabled: true
  cache_dir: ./data/cache

# Performance
performance:
  max_workers: 4
  batch_size: 32
  enable_gpu: true
```

---

## Python API with Config

```python
from pulldata import PullData

# Option 1: Specify config path
pd = PullData(
    project="my_project",
    config_path="configs/lm_studio.yaml"
)

# Option 2: Use default config
pd = PullData(project="my_project")

# Option 3: Override specific settings
from pulldata.core.config import PullDataConfig

config = PullDataConfig.from_yaml("configs/default.yaml")
config.models.llm.api.temperature = 0.9

pd = PullData(project="my_project", config=config)
```

---

## Troubleshooting

### Config Not Found

**Error:** `Config file not found: configs/my_config.yaml`

**Solution:**
1. Check file exists: `ls configs/`
2. Use correct path (relative to project root)
3. File must have `.yaml` extension

### API Connection Errors

**Error:** `Connection refused to http://localhost:1234/v1`

**Solution:**
1. Verify server is running (LM Studio, Ollama, etc.)
2. Check port number is correct
3. Check firewall settings
4. Try: `curl http://localhost:1234/v1/models`

### Model Not Loaded

**Error:** `Model 'my-model' not found`

**Solution:**
1. For LM Studio: Load model in LM Studio UI first
2. For Ollama: Run `ollama pull model-name`
3. For local: Model will auto-download from Hugging Face

### Environment Variables Not Working

**Error:** `${OPENAI_API_KEY}` appears literally in error

**Solution:**
1. Check `.env` file exists in project root
2. Add variable: `OPENAI_API_KEY=sk-your-key`
3. Restart server after changing `.env`
4. Don't use quotes: `OPENAI_API_KEY=sk-key` (not `"sk-key"`)

---

## Best Practices

### 1. Separate Configs for Different Use Cases

```
configs/
├── default.yaml              # Local models (development)
├── lm_studio.yaml            # LM Studio API
├── production.yaml           # Production settings
├── openai.yaml               # OpenAI API
└── experiments/              # Experimental configs
    ├── high_temp.yaml
    └── long_context.yaml
```

### 2. Use Environment Variables for Secrets

**Never commit API keys to git!**

```yaml
# ✅ Good - uses .env
api_key: ${OPENAI_API_KEY}

# ❌ Bad - hardcoded key
api_key: sk-proj-abc123...
```

### 3. Document Your Configs

Add comments to explain choices:

```yaml
models:
  llm:
    api:
      temperature: 0.3  # Lower for factual extraction
      max_tokens: 1024  # Enough for detailed answers
```

### 4. Version Control Configs

```bash
git add configs/
git commit -m "Add LM Studio config for API usage"
```

### 5. Test Configs Before Deploying

```bash
# Test with verify_install.py
python verify_install.py

# Test config loading
python -c "from pulldata.core.config import PullDataConfig; PullDataConfig.from_yaml('configs/my_config.yaml')"
```

---

## See Also

- [Web UI Guide](WEB_UI_GUIDE.md) - Using the Web interface
- [API Configuration](API_CONFIGURATION.md) - API provider details
- [Features Status](FEATURES_STATUS.md) - What's implemented

---

**Last Updated:** 2024-12-18
