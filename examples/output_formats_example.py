"""Standalone Output Formatters Example.

This example shows how to use the output formatters WITHOUT
needing to set up a full PullData pipeline or database.

Perfect for quick testing and demonstrations.
"""

from pathlib import Path
from pulldata.synthesis import (
    ExcelFormatter,
    MarkdownFormatter,
    JSONFormatter,
    PowerPointFormatter,
    PDFFormatter,
    OutputData,
)


def main():
    """Standalone formatters example - no database required!"""
    print("=" * 60)
    print("Standalone Output Formatters Example")
    print("(No database or PullData setup required!)")
    print("=" * 60)
    
    # Create sample data
    print("\n1. Creating sample data...")
    
    sample_data = OutputData(
        title="Q3 2024 Financial Summary",
        content="""
        **Executive Summary**
        
        Q3 2024 demonstrated strong financial performance with revenue 
        growth of 15% year-over-year and improved profit margins.
        
        **Key Metrics:**
        - Total Revenue: $10.5M (+15% YoY)
        - Operating Expenses: $8.2M (-5% QoQ)
        - Net Profit: $2.3M (+35% YoY)
        - Profit Margin: 22%
        
        The company continues to show healthy growth across all segments.
        """,
        sections=[
            {
                "title": "Revenue Analysis",
                "content": "Product sales led growth at $6.5M, followed by services at $4.0M."
            },
            {
                "title": "Cost Analysis",
                "content": "Operational efficiency improvements resulted in 5% cost reduction."
            }
        ],
        tables=[
            {
                "name": "Quarterly Comparison",
                "headers": ["Metric", "Q1", "Q2", "Q3", "Q4 (Projected)"],
                "rows": [
                    ["Revenue ($M)", "8.5", "9.2", "10.5", "11.2"],
                    ["Expenses ($M)", "7.0", "7.5", "8.2", "8.5"],
                    ["Profit ($M)", "1.5", "1.7", "2.3", "2.7"],
                    ["Margin (%)", "18%", "18%", "22%", "24%"],
                ]
            },
            {
                "name": "Regional Performance",
                "headers": ["Region", "Revenue ($M)", "Growth (%)"],
                "rows": [
                    ["North America", "5.2", "12%"],
                    ["Europe", "3.1", "18%"],
                    ["Asia Pacific", "2.2", "20%"],
                ]
            }
        ],
        metadata={
            "company": "Demo Corp",
            "author": "Finance Team",
            "date": "2024-12-18",
            "department": "Finance",
            "classification": "Internal",
        },
        sources=[
            {"document_id": "q3_financial_report.pdf", "page_number": 1, "score": 0.95},
            {"document_id": "q3_financial_report.pdf", "page_number": 5, "score": 0.88},
            {"document_id": "regional_analysis.pdf", "page_number": 3, "score": 0.85},
        ]
    )
    
    print("[OK] Sample data created")
    
    # Create output directory
    output_dir = Path("./examples_output")
    output_dir.mkdir(exist_ok=True)
    print(f"[OK] Output directory: {output_dir.absolute()}")
    
    # Export to all formats
    print("\n2. Exporting to all formats...")
    
    # Excel
    print("\n   [1/5] Excel (.xlsx)...")
    excel = ExcelFormatter()
    excel_file = excel.save(sample_data, output_dir / "financial_summary.xlsx")
    print(f"   [OK] {excel_file.name}")
    
    # Markdown
    print("\n   [2/5] Markdown (.md)...")
    markdown = MarkdownFormatter(include_toc=True)
    md_file = markdown.save(sample_data, output_dir / "financial_summary.md")
    print(f"   [OK] {md_file.name}")
    
    # JSON
    print("\n   [3/5] JSON (.json)...")
    json_fmt = JSONFormatter(indent=2, sort_keys=True)
    json_file = json_fmt.save(sample_data, output_dir / "financial_summary.json")
    print(f"   [OK] {json_file.name}")
    
    # PowerPoint
    print("\n   [4/5] PowerPoint (.pptx)...")
    pptx = PowerPointFormatter()
    pptx_file = pptx.save(sample_data, output_dir / "financial_summary.pptx")
    print(f"   [OK] {pptx_file.name}")
    
    # PDF
    print("\n   [5/5] PDF (.pdf)...")
    pdf = PDFFormatter()
    pdf_file = pdf.save(sample_data, output_dir / "financial_summary.pdf")
    print(f"   [OK] {pdf_file.name}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All files saved to: {}".format(output_dir.absolute()))
    print("\nGenerated files:")
    for file in sorted(output_dir.glob("financial_summary.*")):
        size_kb = file.stat().st_size / 1024
        print(f"  • {file.name:30s} ({size_kb:>6.1f} KB)")
    print("\nOpen these files to see the results!")
    print("=" * 60)


if __name__ == "__main__":
    main()
