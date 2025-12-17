"""Debug script to isolate retrieval issue."""

from pathlib import Path
from pulldata import PullData

# Initialize
print("Initializing PullData...")
pd = PullData(
    project="debug_test",
    config_path="configs/lm_studio_api_embeddings.yaml"
)

# Create sample text
sample_dir = Path("./sample_data")
sample_dir.mkdir(exist_ok=True)
sample_file = sample_dir / "test.txt"
sample_file.write_text("Machine learning is awesome. Deep learning is a subset of machine learning.", encoding='utf-8')

# Ingest
print("\nIngesting...")
stats = pd.ingest(str(sample_file))
print(f"Ingestion stats: {stats}")

# Check vector store state
print("\nChecking vector store...")
print(f"Vector store size (property): {pd._vector_store.size}")
print(f"Vector store ntotal (direct): {pd._vector_store.index.ntotal}")
print(f"Chunk IDs in vector store: {pd._vector_store.chunk_ids}")
print(f"Metadata chunks: {pd._metadata_store.get_stats()['chunk_count']}")

# Try to retrieve WITHOUT generating answer
print("\nAttempting retrieval (no LLM)...")
try:
    results = pd._rag_pipeline.retrieve_only(
        query="What is machine learning?",
        k=5
    )
    print(f"Retrieved {len(results)} chunks")
    for r in results:
        print(f"  - Chunk {r.chunk.id}: score={r.score:.4f}")
except Exception as e:
    print(f"Retrieval failed: {e}")
    import traceback
    traceback.print_exc()

# Check vector store again
print("\nChecking vector store again after query...")
print(f"Vector store size: {pd._vector_store.size}")
print(f"Vector store ntotal: {pd._vector_store.index.ntotal}")

pd.close()
print("\nDone!")
