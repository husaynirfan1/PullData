"""Test script to verify vector store persistence after reload."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pulldata import PullData

def test_reload():
    """Test that vector store persists after reload."""
    project = "test_reload"

    print("=" * 60)
    print("STEP 1: Create new project and ingest document")
    print("=" * 60)

    # Create PullData instance
    pd1 = PullData(project=project)

    # Check initial state
    stats1 = pd1.get_stats()
    print(f"Initial stats: {stats1}")

    # Ingest test document
    test_doc = Path("./testdocs/test.txt")
    if not test_doc.exists():
        print(f"ERROR: Test document not found: {test_doc}")
        print("Please ensure testdocs/test.txt exists")
        return False

    print(f"\nIngesting: {test_doc}")
    ingest_stats = pd1.ingest(str(test_doc))
    print(f"Ingestion stats: {ingest_stats}")

    # Get stats after ingestion
    stats_after_ingest = pd1.get_stats()
    print(f"Stats after ingestion: {stats_after_ingest}")

    # Close (this used to save, but now we auto-save)
    pd1.close()

    print("\n" + "=" * 60)
    print("STEP 2: Reload project (simulate server restart)")
    print("=" * 60)

    # Create new instance (simulates server restart)
    pd2 = PullData(project=project)

    # Get stats - should show documents/chunks from previous session
    stats_after_reload = pd2.get_stats()
    print(f"Stats after reload: {stats_after_reload}")

    print("\n" + "=" * 60)
    print("STEP 3: Test query on reloaded project")
    print("=" * 60)

    # Try a query
    result = pd2.query("What is the content of this document?", k=3, generate_answer=False)

    print(f"Query: {result.query}")
    print(f"Retrieved chunks: {len(result.retrieved_chunks)}")

    if len(result.retrieved_chunks) > 0:
        print("\n[SUCCESS] Query returned results after reload!")
        print("\nTop result:")
        print(f"  Chunk ID: {result.retrieved_chunks[0].chunk.id}")
        print(f"  Score: {result.retrieved_chunks[0].score:.4f}")
        print(f"  Text preview: {result.retrieved_chunks[0].chunk.text[:100]}...")

        # Verify stats match
        chunks_after_ingest = stats_after_ingest.get('metadata_store', {}).get('chunk_count', 0)
        chunks_after_reload = stats_after_reload.get('metadata_store', {}).get('chunk_count', 0)
        if chunks_after_reload == chunks_after_ingest and chunks_after_reload > 0:
            print(f"\n[VERIFIED] Chunk count matches: {chunks_after_reload}")
        else:
            print(f"\n[WARNING] Chunk count mismatch:")
            print(f"   Before: {chunks_after_ingest}")
            print(f"   After:  {chunks_after_reload}")

        pd2.close()
        return True
    else:
        print("\n[FAILED] Query returned 0 results after reload!")
        print("The vector store was not properly loaded.")
        pd2.close()
        return False

if __name__ == "__main__":
    success = test_reload()
    sys.exit(0 if success else 1)
