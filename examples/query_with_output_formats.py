"""End-to-End Example: Query with Output Formats.

This example demonstrates the complete PullData workflow:
1. Initialize PullData with LM Studio API
2. Ingest a document
3. Query with automatic output format generation

Deliverable formats: Excel, Markdown, JSON, PowerPoint, PDF
"""

from pathlib import Path
from pulldata import PullData


def main():
    """End-to-end example with output format generation."""
    print("=" * 70)
    print("PullData - Query with Output Formats Example")
    print("=" * 70)

    # Setup paths
    config_path = Path("configs/lm_studio_api_embeddings.yaml")
    sample_file = Path("testdocs/test.txt")

    # Validate files exist
    if not config_path.exists():
        print(f"[ERROR] Config not found: {config_path}")
        print("Please create the config file first.")
        return

    if not sample_file.exists():
        print(f"[ERROR] Sample file not found: {sample_file}")
        print("Please ensure the test document exists.")
        return

    # Step 1: Initialize PullData
    print("\n[1/5] Initializing PullData...")
    try:
        pd = PullData(
            project="output_demo",
            config_path=str(config_path),
            data_dir="./data/output_demo",
        )
        print(f"      [OK] Project: {pd.project}")
        print(f"      [OK] Embedder: {pd.config.models.embedder.provider}")
        print(f"      [OK] LLM: {pd.config.models.llm.provider}")

    except Exception as e:
        print(f"      [FAILED] {e}")
        return

    # Step 2: Ingest document
    print("\n[2/5] Ingesting document...")
    try:
        stats = pd.ingest(str(sample_file))
        print(f"      [OK] Processed: {stats.get('processed_files', 0)} files")
        print(f"      [OK] New chunks: {stats.get('new_chunks', 0)}")
        print(f"      [OK] Total chunks: {stats.get('total_chunks', 0)}")
    except Exception as e:
        print(f"      [FAILED] {e}")
        pd.close()
        return

    # Step 3: Query WITHOUT output format (standard behavior)
    print("\n[3/5] Standard query (no output format)...")
    try:
        result = pd.query(
            "What are the types of machine learning?",
            generate_answer=True,
        )
        answer = result.llm_response.text if result.llm_response else "No answer"
        print(f"      [OK] Answer: {answer[:100]}...")
        print(f"      [OK] Sources: {len(result.retrieved_chunks)}")
    except Exception as e:
        print(f"      [FAILED] {e}")

    # Step 4: Query WITH output formats (NEW FEATURE!)
    print("\n[4/5] Queries with automatic output format generation...")

    query = "What are the main concepts in machine learning?"

    # Test all supported formats
    formats = ["excel", "markdown", "json", "powerpoint", "pdf"]

    for fmt in formats:
        print(f"\n      [{formats.index(fmt)+1}/{len(formats)}] Generating {fmt.upper()} output...")
        try:
            result = pd.query(
                query,
                generate_answer=True,
                output_format=fmt,
            )

            # Check that file was created
            if result.output_path:
                output_file = Path(result.output_path)
                if output_file.exists():
                    size_kb = output_file.stat().st_size / 1024
                    print(f"            [OK] {output_file.name} ({size_kb:.1f} KB)")
                else:
                    print(f"            [WARNING] File not found: {result.output_path}")
            else:
                print(f"            [WARNING] No output_path returned")

        except Exception as e:
            print(f"            [FAILED] {e}")

    # Step 5: Show all generated files
    print("\n[5/5] Summary of generated outputs...")

    output_dir = Path("./output")
    if output_dir.exists():
        output_files = list(output_dir.glob("output_demo_query_*"))
        if output_files:
            print(f"\n      Generated {len(output_files)} files in {output_dir.absolute()}:")
            for file in sorted(output_files):
                size_kb = file.stat().st_size / 1024
                print(f"      • {file.name:40s} ({size_kb:>7.1f} KB)")
        else:
            print(f"      [WARNING] No files found in {output_dir}")
    else:
        print(f"      [WARNING] Output directory not found: {output_dir}")

    # Cleanup
    pd.close()

    print("\n" + "=" * 70)
    print("[SUCCESS] Example completed!")
    print("\nKey Features Demonstrated:")
    print("  [OK] Document ingestion with chunking")
    print("  [OK] Query with LLM answer generation")
    print("  [OK] Automatic output format generation (Excel, Markdown, JSON, PowerPoint, PDF)")
    print("  [OK] Persistent file storage with timestamps")
    print("\nOpen the files in ./output/ to see the formatted results!")
    print("=" * 70)


if __name__ == "__main__":
    main()
