"""LM Studio Configuration Example.

This example shows how to configure PullData to work with LM Studio
for both embeddings and LLM (answer generation).

LM Studio provides a local OpenAI-compatible API server.
"""

from pulldata import PullData
from pulldata.core.config import Config

def main():
    """LM Studio configuration example."""
    print("=" * 60)
    print("LM Studio Configuration Example")
    print("=" * 60)
    
    print("\nPrerequisites:")
    print("1. Download and install LM Studio from https://lmstudio.ai/")
    print("2. Download your preferred embedding model (e.g., bge-small-en-v1.5)")
    print("3. Download your preferred LLM (e.g., Qwen2.5-3B-Instruct)")
    print("4. Start LM Studio local server")
    
    print("\n" + "-" * 60)
    print("SETUP INSTRUCTIONS:")
    print("-" * 60)
    
    print("\nStep 1: Start LM Studio Server")
    print("  - Open LM Studio")
    print("  - Go to 'Local Server' tab")
    print("  - Load your chosen model")
    print("  - Click 'Start Server'")
    print("  - Default URL: http://localhost:1234/v1")
    
    print("\nStep 2: Configure PullData for LM Studio")
    print("  Option A: Use config overrides (shown below)")
    print("  Option B: Modify configs/default.yaml")
    
    print("\n" + "-" * 60)
    print("CONFIGURATION:")
    print("-" * 60)
    
    # Method 1: Direct config overrides
    print("\nMethod 1: Using config overrides in code")
    print("-" * 40)
    
    pd = PullData(
        project="lm_studio_demo",
        # Storage configuration
        storage={"backend": "local"},
        
        # Model configuration
        models={
            # Embedding model - use sentence-transformers locally
            "embedder": {
                "name": "BAAI/bge-small-en-v1.5",
                "dimension": 384,
                "device": "cpu",  # or "cuda" if you have GPU
                "batch_size": 32,
            },
            # LLM configuration - use LM Studio API
            "llm": {
                "provider": "api",  # Use API provider for LM Studio
                "api": {
                    "base_url": "http://localhost:1234/v1",
                    "api_key": "lm-studio",  # LM Studio doesn't need real API key
                    "model": "local-model",  # LM Studio uses this generic name
                    "timeout": 60,
                    "max_retries": 3,
                },
                "generation": {
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            }
        }
    )
    
    print("Configuration:")
    print(f"  - Embedding Model: BAAI/bge-small-en-v1.5 (local)")
    print(f"  - LLM Provider: LM Studio API")
    print(f"  - LM Studio URL: http://localhost:1234/v1")
    print(f"  - Storage: Local (SQLite + FAISS)")
    
    # Method 2: YAML configuration file
    print("\n\nMethod 2: Using YAML configuration file")
    print("-" * 40)
    print("""
Create a file: configs/lm_studio.yaml

storage:
  backend: local

models:
  embedder:
    name: BAAI/bge-small-en-v1.5
    dimension: 384
    device: cpu
    batch_size: 32
    
  llm:
    provider: api  # Use API for LM Studio
    api:
      base_url: http://localhost:1234/v1
      api_key: lm-studio
      model: local-model
      timeout: 60
      max_retries: 3
    generation:
      max_tokens: 2048
      temperature: 0.7
      top_p: 0.9

Then use it:
    pd = PullData(
        project="my_project",
        config_path="configs/lm_studio.yaml"
    )
""")
    
    # Example usage
    print("\n" + "-" * 60)
    print("USAGE EXAMPLE:")
    print("-" * 60)
    
    # Note: Actual usage would require documents and LM Studio running
    print("""
# 1. Ingest documents
stats = pd.ingest("./documents/*.pdf")
print(f"Ingested {stats['processed_files']} documents")

# 2. Query with LM Studio for answer generation
result = pd.query(
    "What are the key findings?",
    generate_answer=True,  # Uses LM Studio LLM
    k=5
)

print(f"Answer: {result.answer}")
print(f"Sources: {len(result.sources)}")
""")
    
    # Tips and troubleshooting
    print("\n" + "-" * 60)
    print("TIPS & TROUBLESHOOTING:")
    print("-" * 60)
    
    print("""
1. Check LM Studio is running:
   - Visit http://localhost:1234/v1/models in your browser
   - Should return JSON with available models

2. Embedding Model:
   - Runs locally using sentence-transformers
   - No LM Studio needed for embeddings
   - Can use CPU or GPU

3. LLM Model (via LM Studio):
   - Must load model in LM Studio first
   - Start the local server
   - Model name is typically "local-model"

4. Performance:
   - First query may be slow (model loading)
   - Subsequent queries faster
   - Adjust max_tokens based on your needs

5. Common Issues:
   - "Connection refused": LM Studio server not running
   - "Model not found": Load a model in LM Studio
   - Slow responses: Normal for large models on CPU
""")
    
    # Alternative: Using different API endpoints
    print("\n" + "-" * 60)
    print("ALTERNATIVE API SERVERS:")
    print("-" * 60)
    
    print("""
LM Studio is compatible with OpenAI API format.
You can also use:

1. Text Generation WebUI (oobabooga):
   base_url: http://localhost:5000/v1
   
2. vLLM:
   base_url: http://localhost:8000/v1

3. Ollama (with OpenAI compatibility):
   base_url: http://localhost:11434/v1

4. OpenAI (cloud):
   base_url: https://api.openai.com/v1
   api_key: <your-openai-key>
   model: gpt-4  # or gpt-3.5-turbo

Just change the base_url and api_key accordingly!
""")
    
    # Clean up
    pd.close()
    
    print("\n" + "=" * 60)
    print("Configuration guide complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
