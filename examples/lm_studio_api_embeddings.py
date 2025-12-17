"""LM Studio API Embeddings - Full Demo

Demonstrates LM Studio API embeddings with document ingestion and querying.

Prerequisites:
1. Install LM Studio from https://lmstudio.ai
2. Load an embedding model (e.g., nomic-embed-text-v1.5)
3. Load an LLM model (e.g., Qwen2.5-3B-Instruct)
4. Start LM Studio server
"""

from pathlib import Path
from pulldata import PullData


def create_sample_document():
    """Create a sample text document."""
    sample_dir = Path("./sample_data")
    sample_dir.mkdir(exist_ok=True)
    
    sample_file = sample_dir / "ml_intro.txt"
    sample_file.write_text("""Machine Learning Overview

Machine learning is a branch of artificial intelligence that enables computers to learn from data.

Key Types:
1. Supervised Learning - Learning from labeled examples
2. Unsupervised Learning - Finding patterns in unlabeled data  
3. Reinforcement Learning - Learning through trial and error

Applications include image recognition, natural language processing, and recommendation systems.
""", encoding='utf-8')
    return sample_file


def main():
    print("=" * 60)
    print("LM Studio API Embeddings - Full Demo")
    print("=" * 60)
    
    # Create sample document
    print("\n[1/4] Creating sample document...")
    sample_file = create_sample_document()
    print(f"      Created: {sample_file}")
    
    # Initialize
    print("\n[2/4] Initializing PullData...")
    config_path = Path(__file__).parent.parent / "configs" / "lm_studio_api_embeddings.yaml"
    
    try:
        pd = PullData(
            project="lm_studio_demo",
            config_path=str(config_path)
        )
        print(f"      API Embedder: {pd.config.models.embedder.api.model}")
        print(f"      LLM: {pd.config.models.llm.api.model}")
        
    except Exception as e:
        print(f"      [FAILED] {e}")
        return
    
    # Ingest
    print("\n[3/4] Ingesting document...")
    try:
        stats = pd.ingest(str(sample_file))
        print(f"      Processed: {stats.get('processed_files', 0)} files")
        print(f"      Chunks: {stats.get('new_chunks', 0)}")
    except Exception as e:
        print(f"      [FAILED] {e}")
        pd.close()
        return
    
    # Query  
    print("\n[4/4] Querying...")
    
    # Debug: Check vector store
    vec_size = pd._vector_store.index.ntotal if hasattr(pd._vector_store.index, 'ntotal') else 0
    print(f"      Debug: Vector store size = {vec_size}")
    print(f"      Debug: Metadata chunks = {pd._metadata_store.get_stats()['chunk_count']}")
    
    try:
        result = pd.query("What are the types of machine learning?", generate_answer=True)
        answer = result.llm_response.text if result.llm_response else "No answer generated"
        print(f"      Answer: {answer}")
        print(f"      Sources: {len(result.retrieved_chunks)}")
    except Exception as e:
        print(f"      [FAILED] {e}")
    
    pd.close()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
