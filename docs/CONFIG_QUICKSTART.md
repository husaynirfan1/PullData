# Configuration Quick Start

**Quick guide for changing embeddings/LLM settings when using PullData Web UI or API**

---

## TL;DR

### For LM Studio API Users:

```bash
# 1. Start LM Studio and load your models
# 2. Edit config before starting server
cp configs/default.yaml configs/lm_studio.yaml
notepad configs/lm_studio.yaml  # Edit as shown below

# 3. Start server
python run_server.py

# 4. In Web UI: Select "lm_studio" from config dropdown
```

### LM Studio Config Template:

```yaml
models:
  embedder:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      model: nomic-embed-text-v1.5  # Must be loaded in LM Studio
      api_key: sk-dummy

  llm:
    provider: api
    api:
      base_url: http://localhost:1234/v1
      model: qwen2.5-3b-instruct  # Must be loaded in LM Studio
      api_key: sk-dummy

storage:
  backend: local
```

---

## How It Works

### Before Starting Server (One-Time Setup):

1. **Create/Edit Config Files** in `configs/` directory
2. **Start Server**: `python run_server.py`
3. **Web UI Auto-Discovers** all `.yaml` files in `configs/`

### When Using Web UI:

1. **During Ingest**: Select config from dropdown (or use default)
2. **During Query**: Optionally override with different config
3. **Server automatically loads** the selected config

---

## Common Scenarios

### Scenario 1: Testing Different LLMs

```bash
# Create configs for each LLM
cp configs/default.yaml configs/gpt4.yaml      # Edit for GPT-4
cp configs/default.yaml configs/claude.yaml    # Edit for Claude
cp configs/default.yaml configs/local.yaml     # Edit for local models

# In Web UI: Select from dropdown to test each
```

### Scenario 2: API vs Local Models

**Development** (use API, no GPU needed):
- Select `lm_studio.yaml` or `openai.yaml`

**Production** (use local models):
- Select `local_gpu.yaml`

### Scenario 3: Different Projects, Different Configs

| Project | Config | Use Case |
|---------|--------|----------|
| `finance_reports` | `openai.yaml` | High quality, paid API |
| `experiments` | `lm_studio.yaml` | Free local testing |
| `production` | `local_gpu.yaml` | Self-hosted, private |

---

## Config Files Location

```
pulldata/
└── configs/
    ├── default.yaml              # Used if no config selected
    ├── lm_studio.yaml            # Your LM Studio API config
    ├── openai.yaml               # Your OpenAI config
    ├── local_gpu.yaml            # Your local model config
    └── ...                       # Add more as needed
```

---

## Environment Variables

For API keys, use `.env` file:

```bash
# .env (don't commit this!)
OPENAI_API_KEY=sk-proj-...
GROQ_API_KEY=gsk_...
LM_STUDIO_BASE_URL=http://localhost:1234/v1
```

Then reference in configs:

```yaml
api:
  api_key: ${OPENAI_API_KEY}  # Loaded from .env
```

---

## Web UI Usage

### Ingest with Config:

1. Select project
2. **Select config** from "Configuration" dropdown
3. Upload files
4. Click "Ingest"

### Query with Config Override:

1. Select project (uses its original config)
2. **Override config** (optional) to test different LLM
3. Enter query
4. Click "Query"

---

## REST API Usage

### With cURL:

```bash
# Ingest with config
curl -X POST "http://localhost:8000/ingest/upload?project=my_project&config_path=configs/lm_studio.yaml" \
  -F "files=@document.pdf"

# Query with config
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "project": "my_project",
    "query": "What are the key points?",
    "config_path": "configs/lm_studio.yaml"
  }'
```

### With Python:

```python
import requests

# Ingest with config
files = [('files', open('doc.pdf', 'rb'))]
response = requests.post(
    "http://localhost:8000/ingest/upload",
    params={
        "project": "my_project",
        "config_path": "configs/lm_studio.yaml"
    },
    files=files
)

# Query with config
response = requests.post(
    "http://localhost:8000/query",
    json={
        "project": "my_project",
        "query": "What are the key points?",
        "config_path": "configs/lm_studio.yaml"
    }
)
```

---

## Troubleshooting

### Config Not Appearing in Web UI Dropdown?

1. Check file is in `configs/` directory
2. Check file has `.yaml` extension
3. Refresh browser page
4. Check browser console for errors

### API Connection Errors?

1. Verify server is running (LM Studio, Ollama, etc.)
2. Check `base_url` is correct
3. Test: `curl http://localhost:1234/v1/models`
4. Check firewall settings

### Environment Variables Not Working?

1. Ensure `.env` file exists in project root
2. Restart server after changing `.env`
3. Don't use quotes in `.env`: `KEY=value` not `KEY="value"`

---

## Examples of Config Files

See `configs/` directory for examples:
- `default.yaml` - Local models (requires GPU)
- `lm_studio_api_embeddings.yaml` - LM Studio API example

Or see full documentation: [docs/CONFIG_GUIDE.md](docs/CONFIG_GUIDE.md)

---

**Need More Help?**
- [Full Configuration Guide](docs/CONFIG_GUIDE.md)
- [Web UI Guide](docs/WEB_UI_GUIDE.md)
- [API Configuration](docs/API_CONFIGURATION.md)
