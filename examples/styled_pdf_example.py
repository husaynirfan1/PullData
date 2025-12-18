"""Example: Creating styled PDF reports with PullData.

Demonstrates three usage patterns:
1. Direct ReportData creation (manual)
2. LLM-powered structuring from RAG text
3. Integration with PullData query workflow
"""

from pathlib import Path

from pulldata import PullData
from pulldata.synthesis import (
    MetricItem,
    Reference,
    ReportData,
    ReportSection,
    StyledPDFFormatter,
    render_styled_pdf,
)


def example_1_manual_report():
    """Example 1: Manually create structured report data."""
    print("=" * 60)
    print("Example 1: Manual ReportData Creation")
    print("=" * 60)

    # Create structured report data
    report = ReportData(
        title="Q3 2024 Financial Analysis",
        subtitle="Revenue Growth and Market Performance",
        summary=(
            "Q3 2024 demonstrated strong financial performance with revenue "
            "reaching $10.5M, representing 15% year-over-year growth. Key drivers "
            "include successful product launches and enterprise segment expansion."
        ),
        metrics=[
            MetricItem(label="Revenue", value="$10.5M", icon="💰"),
            MetricItem(label="Growth", value="+15%", icon="📈"),
            MetricItem(label="Customers", value="1,234", icon="👥"),
            MetricItem(label="Retention", value="94%", icon="🎯"),
        ],
        sections=[
            ReportSection(
                heading="Executive Overview",
                content=(
                    "The third quarter of 2024 marked a significant milestone "
                    "in our company's growth trajectory. Total revenue reached $10.5M, "
                    "exceeding our projections by 8% and demonstrating robust market demand."
                ),
            ),
            ReportSection(
                heading="Key Performance Indicators",
                content=(
                    "Our analysis reveals three primary growth drivers that contributed "
                    "to the quarter's success."
                ),
                subsections=[
                    ReportSection(
                        heading="Enterprise Segment",
                        content=(
                            "Enterprise sales grew 25% quarter-over-quarter, driven by "
                            "successful implementations of our flagship product."
                        ),
                    ),
                    ReportSection(
                        heading="Product Expansion",
                        content=(
                            "New product lines contributed $1.2M in revenue, exceeding "
                            "initial forecasts and validating our product strategy."
                        ),
                    ),
                ],
            ),
            ReportSection(
                heading="Market Outlook",
                content=(
                    "Looking ahead to Q4, we anticipate continued strong performance "
                    "based on pipeline metrics and market conditions."
                ),
            ),
        ],
        references=[
            Reference(
                title="Q3 Financial Statement",
                url="https://example.com/q3-statement.pdf",
                page=5,
                relevance_score=0.95,
            ),
            Reference(
                title="Market Analysis Report",
                url="https://example.com/market-analysis",
                relevance_score=0.88,
            ),
        ],
        metadata={
            "author": "Financial Analysis Team",
            "date": "2024-10-15",
            "version": "1.0",
            "department": "Finance",
        },
    )

    # Generate PDFs in all three styles
    output_dir = Path("./output/styled_pdfs")
    output_dir.mkdir(parents=True, exist_ok=True)

    styles = ["executive", "modernist", "academic"]

    for style in styles:
        print(f"\nGenerating {style} style PDF...")
        pdf_bytes = render_styled_pdf(report, style_name=style)

        output_path = output_dir / f"financial_report_{style}.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        print(f"✓ Saved: {output_path} ({len(pdf_bytes):,} bytes)")

    print("\n✓ All PDFs generated successfully!")


def example_2_llm_structuring():
    """Example 2: Use LLM to structure RAG-retrieved text into a report."""
    print("\n" + "=" * 60)
    print("Example 2: LLM-Powered Data Structuring")
    print("=" * 60)

    # Simulate RAG-retrieved text
    raw_text = """
    Based on the retrieved documents, our Q3 2024 revenue reached $10.5M, which
    represents a 15% increase compared to Q3 2023. This growth was primarily driven
    by enterprise segment expansion and new product launches.

    Key findings:
    - Enterprise segment grew 25% with 345 new enterprise customers
    - Customer retention improved to 94%
    - Average deal size increased to $8,500
    - Product expansion contributed $1.2M in additional revenue

    The market outlook remains positive for Q4, with a strong sales pipeline
    indicating continued momentum. However, we anticipate some headwinds from
    increased competition in the mid-market segment.
    """

    try:
        # Initialize PullData with LLM (using default config)
        pd = PullData(project="styled_pdf_example")

        # Create formatter with LLM
        formatter = StyledPDFFormatter(
            style="executive",
            llm=pd._llm,  # Use PullData's LLM instance
        )

        print("\nStructuring data with LLM...")
        structured_data = formatter.structure_with_llm(
            raw_text=raw_text,
            query="What was our Q3 2024 performance?",
        )

        print(f"✓ Structured report with {len(structured_data.sections)} sections")
        print(f"  - Metrics extracted: {len(structured_data.metrics)}")
        print(f"  - Title: {structured_data.title}")

        # Generate PDF
        pdf_bytes = formatter.render_styled_pdf(structured_data)

        output_path = Path("./output/styled_pdfs/llm_structured_report.pdf")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        print(f"\n✓ Generated: {output_path} ({len(pdf_bytes):,} bytes)")

        pd.close()

    except Exception as e:
        print(f"\n⚠️  LLM structuring requires configured LLM. Error: {e}")
        print("   Tip: Ensure your config has LLM settings configured.")


def example_3_pulldata_integration():
    """Example 3: Full integration with PullData query workflow."""
    print("\n" + "=" * 60)
    print("Example 3: PullData Query Integration")
    print("=" * 60)

    try:
        # Initialize PullData
        pd = PullData(project="financial_docs")

        # Check if we have documents
        stats = pd.get_stats()
        if stats.get("metadata_store", {}).get("document_count", 0) == 0:
            print("⚠️  No documents ingested. Please ingest documents first.")
            print("   Example: pd.ingest('./documents/financial_reports.pdf')")
            pd.close()
            return

        print(f"✓ Found {stats['metadata_store']['document_count']} documents")

        # Perform query
        print("\nQuerying documents...")
        result = pd.query(
            "What were our key financial metrics for Q3?",
            k=5,
            generate_answer=True,
        )

        print(f"✓ Retrieved {len(result.retrieved_chunks)} relevant chunks")

        # Create formatter with LLM
        formatter = StyledPDFFormatter(
            style="modernist",
            llm=pd._llm,
        )

        # Build raw text from query results
        raw_text = f"Query: {result.query}\n\n"
        raw_text += f"Answer: {result.llm_response.text}\n\n"
        raw_text += "Retrieved Information:\n"
        for i, chunk in enumerate(result.retrieved_chunks, 1):
            raw_text += f"\n{i}. {chunk.chunk.text}\n"

        # Structure with LLM
        print("\nStructuring with LLM...")
        structured_data = formatter.structure_with_llm(
            raw_text=raw_text,
            query=result.query,
            sources=[
                {
                    "title": chunk.chunk.document_id,
                    "page": chunk.chunk.start_page,
                    "score": chunk.score,
                }
                for chunk in result.retrieved_chunks
            ],
        )

        # Generate styled PDF
        pdf_bytes = formatter.render_styled_pdf(structured_data)

        output_path = Path("./output/styled_pdfs/pulldata_query_report.pdf")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        print(f"\n✓ Generated: {output_path} ({len(pdf_bytes):,} bytes)")

        pd.close()

    except Exception as e:
        print(f"\n⚠️  Error: {e}")


def example_4_compare_styles():
    """Example 4: Generate same report in all three styles for comparison."""
    print("\n" + "=" * 60)
    print("Example 4: Style Comparison")
    print("=" * 60)

    # Simple report for style comparison
    report = ReportData(
        title="Style Comparison Report",
        subtitle="Demonstrating Visual Design Variants",
        summary=(
            "This report demonstrates the three available visual styles for "
            "PDF generation: Executive (clean and minimal), Modernist (bold and "
            "high-contrast), and Academic (traditional two-column layout)."
        ),
        metrics=[
            MetricItem(label="Styles", value="3", icon="🎨"),
            MetricItem(label="Layouts", value="Varied", icon="📐"),
        ],
        sections=[
            ReportSection(
                heading="Style Overview",
                content=(
                    "Each style is optimized for different use cases and audiences. "
                    "The Executive style prioritizes clarity and whitespace, making it "
                    "ideal for executive summaries and board presentations. The Modernist "
                    "style uses bold typography and high contrast for impact. The Academic "
                    "style follows traditional academic paper conventions with serif fonts "
                    "and two-column layout."
                ),
            ),
        ],
        references=[
            Reference(title="PullData Documentation", url="https://github.com/pulldata"),
        ],
        metadata={"author": "PullData Team", "date": "2024-12-18"},
    )

    output_dir = Path("./output/style_comparison")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\nGenerating comparison PDFs...")

    styles = {
        "executive": "Clean, minimal, blue/grey palette",
        "modernist": "Bold, high-contrast, dark accents",
        "academic": "Traditional, serif, two-column",
    }

    for style_name, description in styles.items():
        print(f"\n  • {style_name.title()}: {description}")

        pdf_bytes = render_styled_pdf(report, style_name=style_name)
        output_path = output_dir / f"comparison_{style_name}.pdf"

        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        print(f"    Saved: {output_path}")

    print("\n✓ All comparison PDFs generated!")
    print(f"\nOpen {output_dir} to view the style comparison.")


if __name__ == "__main__":
    # Run examples
    example_1_manual_report()

    # Uncomment to run LLM examples (requires configured LLM)
    # example_2_llm_structuring()
    # example_3_pulldata_integration()

    example_4_compare_styles()

    print("\n" + "=" * 60)
    print("✓ All examples completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Open ./output/styled_pdfs/ to view generated PDFs")
    print("  2. Compare the three visual styles")
    print("  3. Customize templates in pulldata/synthesis/templates/")
    print("  4. Modify CSS in pulldata/synthesis/templates/styles/")
    print("\nDocumentation: See docs/STYLED_PDF_GUIDE.md")
