"""PDF Ingestion and Query Example.

This example demonstrates:
1. Ingesting multiple PDF documents
2. Querying with different strategies
3. Accessing retrieved chunks and metadata
"""

from pathlib import Path
from pulldata import PullData

def main():
    """PDF ingestion and query example."""
    print("=" * 60)
    print("PDF Ingestion and Query Example")
    print("=" * 60)
    
    # Initialize PullData
    print("\n1. Initializing PullData for 'financial_reports' project...")
    pd = PullData(
        project="financial_reports",
        # Optional: provide custom config
        # config_path="./configs/custom.yaml"
    )
    print("✓ Initialized")
    
    # Ingest documents with custom metadata
    print("\n2. Ingesting PDF documents...")
    
    # Example: Ingest financial reports
    # Assuming you have PDFs in ./data/reports/
    sample_path = "./data/reports/"
    
    print(f"   Looking for PDFs in: {sample_path}")
    print("   (Create this directory and add PDFs for a real test)")
    
    # Ingest with metadata
    # stats = pd.ingest(
    #     source=sample_path,
    #     department="Finance",
    #     year=2024,
    #     quarter="Q3",
    # )
    
    # The metadata will be attached to all ingested documents
    # and can be used for filtering during queries
    
    # Print ingestion statistics
    # print(f"\n   Ingestion Results:")
    # print(f"   - Total files: {stats['total_files']}")
    # print(f"   - Processed: {stats['processed_files']}")
    # print(f"   - Failed: {stats['failed_files']}")
    # print(f"   - Total chunks: {stats['total_chunks']}")
    # print(f"   - New chunks: {stats['new_chunks']}")
    # print(f"   - Skipped (unchanged): {stats['skipped_chunks']}")
    
    # Query examples
    print("\n3. Query Examples:")
    
    # Example 1: Simple query
    print("\n   Example 1: Simple query")
    query1 = "What was the total revenue in Q3?"
    print(f"   Query: {query1}")
    # result1 = pd.query(query1)
    # print(f"   Answer: {result1.answer}")
    # print(f"   Sources: {len(result1.sources)} chunks retrieved")
    
    # Example 2: Query with metadata filters
    print("\n   Example 2: Query with filters")
    query2 = "What are the key risks?"
    print(f"   Query: {query2}")
    print(f"   Filter: Only documents from Finance department")
    # result2 = pd.query(
    #     query2,
    #     filters={"department": "Finance"},
    #     k=5,  # Top 5 most relevant chunks
    # )
    
    # Example 3: Retrieval-only (no answer generation)
    print("\n   Example 3: Retrieval-only mode")
    query3 = "operating expenses"
    print(f"   Query: {query3}")
    # result3 = pd.query(query3, generate_answer=False)
    # for i, source in enumerate(result3.sources[:3], 1):
    #     print(f"\n   Source {i}:")
    #     print(f"   - Document: {source['document_id']}")
    #     print(f"   - Page: {source['page_number']}")
    #     print(f"   - Score: {source['score']:.3f}")
    #     print(f"   - Text: {source['text'][:100]}...")
    
    # Example 4: Query with custom LLM parameters
    print("\n   Example 4: Custom LLM parameters")
    query4 = "Summarize the financial highlights"
    print(f"   Query: {query4}")
    # result4 = pd.query(
    #     query4,
    #     temperature=0.3,  # Lower temperature for more factual
    #     max_tokens=500,   # Longer response
    # )

    # Example 5: Query with automatic output format generation
    print("\n   Example 5: Generate deliverable outputs")
    query5 = "What was the Q3 revenue and expenses?"
    print(f"   Query: {query5}")

    # Generate Excel report
    # result_excel = pd.query(query5, output_format="excel")
    # print(f"   Excel report: {result_excel.output_path}")

    # Generate PDF report
    # result_pdf = pd.query(query5, output_format="pdf")
    # print(f"   PDF report: {result_pdf.output_path}")

    # Generate PowerPoint presentation
    # result_pptx = pd.query(
    #     "Create a summary presentation of Q3 results",
    #     output_format="powerpoint"
    # )
    # print(f"   PowerPoint: {result_pptx.output_path}")

    print("   Available formats: excel, markdown, json, powerpoint, pdf")
    
    # Get system statistics
    print("\n4. System Statistics:")
    stats = pd.get_stats()
    print(f"   Project: {stats['project']}")
    # print(f"   Total documents: {stats['metadata_store']['document_count']}")
    # print(f"   Total chunks: {stats['metadata_store']['chunk_count']}")
    # print(f"   Vector index size: {stats['vector_store']['total_vectors']}")
    
    # Clean up
    print("\n5. Cleaning up...")
    pd.close()
    print("✓ Done")
    
    print("\n" + "=" * 60)
    print("To run this example with real data:")
    print("1. Create directory: ./data/reports/")
    print("2. Add PDF files to that directory")
    print("3. Uncomment the code blocks above")
    print("4. Run: python examples/pdf_ingestion_example.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
