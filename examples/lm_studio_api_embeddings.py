"""LM Studio with API Embeddings Example.

This example shows how to use LM Studio for BOTH:
- Embeddings (via API)
- LLM (via API)

This is useful if you want all inference to go through LM Studio.
"""

from pulldata import PullData

def main():
    """LM Studio with API embeddings example."""
    print("=" * 60)
    print("LM Studio with API Embeddings Example")
    print("=" * 60)
    
    print("\nPrerequisites:")
    print("1. Install LM Studio from https://lmstudio.ai/")
    print("2. Download an embedding model (e.g., nomic-embed-text-v1.5)")
    print("3. Download an LLM (e.g., Qwen2.5-3B-Instruct)")
    print("4. Load BOTH models in LM Studio")
    print("5. Start the LM Studio server")
    
    print("\n" + "-" * 60)
    print("CONFIGURATION OPTIONS:")
    print("-" * 60)
    
    print("\nOption 1: Use config file")
    print("-" * 40)
    print("""
pd = PullData(
    project="my_project",
    config_path="configs/lm_studio_api_embeddings.yaml"
)
""")
    
    print("\nOption 2: Config overrides in code")
    print("-" * 40)
    
    pd = PullData(
        project="lm_studio_api_demo",
        storage={"backend": "local"},
        models={
            # API Embeddings via LM Studio
            "embedder": {
                "provider": "api",  # Use API
                "dimension": 768,  # Adjust for your model
                "api": {
                    "base_url": "http://localhost:1234/v1",
                    "api_key": "lm-studio",
                    "model": "nomic-embed-text-v1.5",
                    "batch_size": 100,
                }
            },
            # LLM via LM Studio
            "llm": {
                "provider": "api",
                "api": {
                    "base_url": "http://localhost:1234/v1",
                    "api_key": "lm-studio",
                    "model": "local-model",
                }
            }
        }
    )
    
    print("\nConfiguration set:")
    print("  Embeddings: LM Studio API (nomic-embed-text-v1.5)")
    print("  LLM: LM Studio API")
    print("  Storage: Local (SQLite + FAISS)")
    
    print("\n" + "-" * 60)
    print("RECOMMENDED EMBEDDING MODELS FOR LM STUDIO:")
    print("-" * 60)
    
    print("""
1. nomic-embed-text-v1.5 (768D)
   - Good general-purpose embedding
   - Recommended for most use cases
   
2. bge-large-en-v1.5 (1024D)
   - Higher quality, larger dimension
   - Better for complex documents
   
3. e5-mistral-7b-instruct (4096D)
   - Very high quality
   - Requires more resources
""")
    
    print("\n" + "-" * 60)
    print("USAGE EXAMPLE:")
    print("-" * 60)
    
    print("""
# Ingest documents (embeddings via LM Studio API)
stats = pd.ingest("./documents/*.pdf")

# Query (both retrieval and answer via LM Studio)
result = pd.query(
    "What are the key findings?",
    generate_answer=True,
    k=5
)

print(f"Answer: {result.answer}")
print(f"Sources: {len(result.sources)}")
""")
    
    print("\n" + "-" * 60)
    print("LOCAL vs API EMBEDDINGS:")
    print("-" * 60)
    
    print("""
LOCAL Embeddings (sentence-transformers):
  ✓ Free (no API costs)
  ✓ Fast for batch processing
  ✓ No network latency
  ✓ Full privacy
  ✗ Requires local setup

API Embeddings (LM Studio):
  ✓ Easy setup (just load model)
  ✓ Centralized model management
  ✓ Switch models easily in LM Studio UI
  ✗ Slower for large batches (network calls)
  ✗ LM Studio must be running
  
Recommendation: Use LOCAL for embeddings unless you specifically
want all inference through LM Studio or prefer the UI.
""")
    
    print("\n" + "-" * 60)
    print("MIXED CONFIGURATION:")
    print("-" * 60)
    
    print("""
You can also mix local and API:

models:
  embedder:
    provider: local  # Local embeddings
    name: BAAI/bge-small-en-v1.5
    device: cpu
    
  llm:
    provider: api  # LM Studio for LLM
    api:
      base_url: http://localhost:1234/v1
      model: local-model

This gives you the best of both worlds!
""")
    
    pd.close()
    
    print("\n" + "=" * 60)
    print("Configuration guide complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
