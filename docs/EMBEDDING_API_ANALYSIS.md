# Embedding API Support Analysis

## Current Implementation
- **Local only**: sentence-transformers models (BAAI/bge, e5, all-MiniLM)
- **No API support**: Cannot use OpenAI embeddings, Cohere, etc.

## Should We Add API Embedding Support?

### PRO: Add API Embedding Support
1. **OpenAI embeddings** (text-embedding-3-small, ada-002) are very good
2. **Cohere embeddings** optimized for search
3. **No local GPU needed** - works on any machine
4. **Less local setup** - no model downloads
5. **Consistent with LLM** - both can use APIs

### CON: Keep Local Only
1. **Cost**: Embedding 1000 chunks = ~$0.20 with OpenAI (adds up quickly)
2. **Latency**: API calls slower than local (especially in batch)
3. **Privacy**: Sending all document content to third party
4. **Dependency**: Requires internet and API access
5. **Our design**: We chose local-first architecture

## Cost Comparison

For a 100-page PDF (~500 chunks):
- **Local**: $0 (just electricity)
- **OpenAI API**: ~$0.10 per document
- **For 1000 documents**: $100 vs $0

## Recommendation

**Add API embedding support as OPTIONAL** with clear warnings:
- Default: Local (current behavior)
- Optional: API for users who prefer it
- Configuration: Similar to LLM provider choice

This gives users flexibility while maintaining our local-first design.

## Implementation Plan

1. Create `APIEmbedder` class (mirrors `APILLM`)
2. Support OpenAI, Cohere, Voyage AI embedding APIs
3. Update config to allow `embedder.provider: "local"` or `"api"`
4. Add cost warnings in documentation
5. Keep local as default

## Example Configuration

```yaml
models:
  embedder:
    provider: api  # NEW: 'local' or 'api'
    api:  # NEW section
      base_url: https://api.openai.com/v1
      api_key: ${OPENAI_API_KEY}
      model: text-embedding-3-small
      batch_size: 100
    local:  # Existing
      name: BAAI/bge-small-en-v1.5
      device: cpu
```
