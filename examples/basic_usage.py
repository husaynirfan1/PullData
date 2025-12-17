"""Basic PullData Usage Example.

This example demonstrates the most basic usage of PullData:
1. Initialize a project
2. Ingest a document
3. Query the system
"""

from pathlib import Path
from pulldata import PullData

def main():
    """Basic usage example."""
    print("=" * 60)
    print("PullData Basic Usage Example")
    print("=" * 60)
    
    # Step 1: Initialize PullData with a project name
    print("\n1. Initializing PullData...")
    pd = PullData(project="basic_example")
    print(f"✓ Initialized project: basic_example")
    
    # Step 2: Ingest a document (assuming you have a PDF in the current directory)
    print("\n2. Ingesting documents...")
    
    # Option A: Ingest a single file
    # stats = pd.ingest("path/to/your/document.pdf")
    
    # Option B: Ingest all PDFs in a directory
    # stats = pd.ingest("./sample_docs/")
    
    # Option C: Ingest using glob pattern
    # stats = pd.ingest("./sample_docs/*.pdf")
    
    # For this example, let's create a simple text-based demo
    # In practice, you would point to real PDF files
    print("   Note: In this example, you should replace the path with your actual documents")
    print("   Example: pd.ingest('./documents/*.pdf')")
    
    # Stats will contain:
    # {
    #     "total_files": 5,
    #     "processed_files": 5,
    #     "failed_files": 0,
    #     "total_chunks": 150,
    #     "new_chunks": 150,
    #     "updated_chunks": 0,
    #     "skipped_chunks": 0,
    # }
    
    # Step 3: Query the system
    print("\n3. Querying the system...")
    
    # Basic query (retrieval only, no answer generation)
    # result = pd.query("What are the main topics?", generate_answer=False)
    
    # Query with answer generation (requires LLM)
    # result = pd.query("What are the main topics?", generate_answer=True)
    
    # Advanced query with filters
    # result = pd.query(
    #     "What are the financial results?",
    #     k=10,  # Retrieve top 10 chunks
    #     filters={"page_number": {"$gte": 1, "$lte": 10}},  # Only pages 1-10
    #     generate_answer=True,
    # )
    
    print("   Example query: pd.query('What are the main topics?')")
    
    # Step 4: Access results
    print("\n4. Accessing results...")
    print("   result.query      - Original query")
    print("   result.answer     - Generated answer (if LLM enabled)")
    print("   result.sources    - List of source chunks with scores")
    print("   result.metadata   - Additional metadata")
    
    # Step 5: Get statistics
    print("\n5. Getting system statistics...")
    stats = pd.get_stats()
    print(f"   Project: {stats['project']}")
    
    # Step 6: Clean up
    print("\n6. Closing PullData...")
    pd.close()
    print("✓ Resources cleaned up")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
