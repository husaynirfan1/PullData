# Styled PDF Report Generation Guide

Complete guide to creating professional, styled PDF reports with LLM-powered data structuring.

---

## 📚 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Visual Styles](#visual-styles)
- [Data Schema](#data-schema)
- [LLM Structuring](#llm-structuring)
- [Advanced Usage](#advanced-usage)
- [Customization](#customization)
- [API Reference](#api-reference)

---

## Overview

The Styled PDF system provides three professional visual styles for PDF reports, with optional LLM-powered data structuring to convert raw RAG-retrieved text into well-organized reports.

### Features

- **3 Professional Styles**: Executive, Modernist, and Academic
- **LLM Structuring**: Automatically organize raw text into structured reports
- **Markdown Support**: Write content in markdown
- **Source Citations**: Automatic reference management
- **Metrics Dashboard**: Visual highlighting of key metrics
- **Page Break Control**: Intelligent pagination

### Architecture

```
Raw RAG Text
     ↓
  LLM Structuring (optional)
     ↓
  ReportData (structured JSON)
     ↓
  Jinja2 Template + CSS
     ↓
  WeasyPrint PDF Generation
     ↓
  Styled PDF Output
```

---

## Quick Start

### Installation

```bash
# Install required dependencies
pip install weasyprint jinja2 markdown2

# Or install PullData with styled PDF support
pip install pulldata[styled-pdf]
```

### Basic Usage

```python
from pulldata.synthesis import ReportData, MetricItem, ReportSection, render_styled_pdf

# Create structured data
report = ReportData(
    title="Q3 Financial Report",
    summary="Revenue grew 15% to $10.5M with strong enterprise performance.",
    metrics=[
        MetricItem(label="Revenue", value="$10.5M", icon="💰"),
        MetricItem(label="Growth", value="+15%", icon="📈"),
    ],
    sections=[
        ReportSection(
            heading="Overview",
            content="Q3 demonstrated strong growth across all segments..."
        )
    ]
)

# Generate PDF
pdf_bytes = render_styled_pdf(report, style_name="executive")

# Save to file
with open("report.pdf", "wb") as f:
    f.write(pdf_bytes)
```

---

## Visual Styles

### Style A: "The Executive"

**Best for:** Executive summaries, board presentations, client reports

**Characteristics:**
- Clean, minimalist design
- Blue/grey color palette
- Generous whitespace
- Emphasized summary box
- Professional metrics cards

**When to use:** When clarity and readability are paramount. Ideal for busy executives who need to quickly grasp key information.

### Style B: "The Modernist"

**Best for:** Marketing materials, pitch decks, innovation reports

**Characteristics:**
- Bold, expressive typography
- High-contrast dark mode accents
- Orange/red gradient highlights
- Asymmetric layout
- Impact-focused design

**When to use:** When you want to make a strong visual impression. Perfect for showcasing innovation and forward-thinking analysis.

### Style C: "The Academic"

**Best for:** Research reports, white papers, technical documentation

**Characteristics:**
- Traditional serif fonts (Georgia, Crimson Text)
- Two-column layout for body text
- Dense information presentation
- Classic academic footer with page numbers
- Bibliography-style references

**When to use:** For formal documentation where information density and traditional formatting are expected.

---

## Data Schema

### ReportData Model

```python
from pulldata.synthesis import ReportData, MetricItem, ReportSection, Reference

report = ReportData(
    # Required
    title="Report Title",

    # Optional
    subtitle="Optional Subtitle",
    summary="2-3 sentence executive summary",

    # Metrics for visual highlighting
    metrics=[
        MetricItem(
            label="Metric Name",
            value="$5M",
            icon="💰"  # Optional emoji
        )
    ],

    # Content sections
    sections=[
        ReportSection(
            heading="Section Title",
            content="Section content (supports markdown)",
            subsections=[
                ReportSection(
                    heading="Subsection",
                    content="Nested content"
                )
            ]
        )
    ],

    # Source citations
    references=[
        Reference(
            title="Source Document",
            url="https://example.com/doc.pdf",
            page=5,
            relevance_score=0.95
        )
    ],

    # Additional metadata
    metadata={
        "author": "John Doe",
        "date": "2024-12-18",
        "version": "1.0"
    }
)
```

### JSON Schema Example

```json
{
  "title": "Q3 Financial Analysis",
  "subtitle": "Revenue and Growth Report",
  "summary": "Strong quarter with 15% growth and $10.5M revenue.",
  "metrics": [
    {"label": "Revenue", "value": "$10.5M", "icon": "💰"},
    {"label": "Growth", "value": "+15%", "icon": "📈"}
  ],
  "sections": [
    {
      "heading": "Overview",
      "content": "Q3 demonstrated strong performance...",
      "subsections": []
    }
  ],
  "references": [
    {
      "title": "Q3 Financial Statement",
      "url": "https://example.com/q3.pdf",
      "page": 5,
      "relevance_score": 0.95
    }
  ],
  "metadata": {
    "author": "Finance Team",
    "date": "2024-10-15"
  }
}
```

---

## LLM Structuring

### Overview

The LLM structuring feature automatically converts raw RAG-retrieved text into the structured ReportData format.

### How It Works

1. **Input**: Raw text from RAG retrieval
2. **LLM Processing**: Uses system prompt with JSON schema
3. **Output**: Valid ReportData JSON
4. **Rendering**: PDF generation from structured data

### Usage

```python
from pulldata import PullData
from pulldata.synthesis import StyledPDFFormatter

# Initialize PullData
pd = PullData(project="my_project")

# Create formatter with LLM
formatter = StyledPDFFormatter(
    style="executive",
    llm=pd._llm  # Use PullData's LLM instance
)

# Raw text from RAG
raw_text = """
Q3 revenue reached $10.5M, a 15% increase year-over-year.
Key drivers include enterprise growth (25%) and new products ($1.2M).
Customer retention improved to 94%.
"""

# Structure with LLM
structured_data = formatter.structure_with_llm(
    raw_text=raw_text,
    query="What was Q3 performance?",
    sources=[...]  # Optional source metadata
)

# Generate PDF
pdf_bytes = formatter.render_styled_pdf(structured_data)
```

### System Prompt

The LLM receives a system prompt that:
- Defines the ReportData JSON schema
- Provides formatting guidelines
- Specifies content organization rules
- Ensures professional tone

See `pulldata/synthesis/report_models.py` for the full prompt.

### Tips for Better Results

1. **Provide Context**: Include the original query with raw text
2. **Add Sources**: Pass source metadata for better references
3. **Temperature**: Use low temperature (0.2-0.4) for structured output
4. **Validation**: The system validates JSON against Pydantic schema

---

## Advanced Usage

### Custom Metrics Icons

```python
metrics=[
    MetricItem(label="Revenue", value="$10.5M", icon="💰"),
    MetricItem(label="Users", value="50K", icon="👥"),
    MetricItem(label="Growth", value="+25%", icon="📈"),
    MetricItem(label="Rating", value="4.8⭐", icon="⭐"),
]
```

### Nested Sections

```python
sections=[
    ReportSection(
        heading="Market Analysis",
        content="Overall market conditions improved...",
        subsections=[
            ReportSection(
                heading="North America",
                content="NA region grew 20%..."
            ),
            ReportSection(
                heading="Europe",
                content="European markets expanded 15%..."
            ),
        ]
    )
]
```

### Markdown Content

```python
section = ReportSection(
    heading="Technical Details",
    content="""
## Key Points

- **Performance**: 99.9% uptime
- **Scalability**: Handles 10K req/sec
- **Security**: SOC 2 compliant

### Code Example

```python
result = pd.query("What is revenue?")
```
    """
)
```

### Integration with PullData Query

```python
# Perform query
result = pd.query("What were Q3 metrics?", k=5, generate_answer=True)

# Create formatter
formatter = StyledPDFFormatter(style="modernist", llm=pd._llm)

# Build text from results
raw_text = f"Query: {result.query}\n\n"
raw_text += f"Answer: {result.llm_response.text}\n\n"

for chunk in result.retrieved_chunks:
    raw_text += f"{chunk.chunk.text}\n\n"

# Structure and generate
structured = formatter.structure_with_llm(raw_text, query=result.query)
pdf = formatter.render_styled_pdf(structured)
```

---

## Customization

### Modifying CSS Styles

CSS files are located in `pulldata/synthesis/templates/styles/`:

```
styles/
├── executive.css
├── modernist.css
└── academic.css
```

To customize:

1. Copy a CSS file
2. Modify colors, fonts, spacing
3. Load custom CSS:

```python
from pathlib import Path

formatter = StyledPDFFormatter(style="executive")

# Load custom CSS
custom_css = Path("my_custom_style.css").read_text()
formatter.style_css = custom_css

# Or modify existing
formatter.style_css = formatter.style_css.replace("#0ea5e9", "#ff6600")
```

### Custom Templates

Templates are in `pulldata/synthesis/templates/`:

```python
from jinja2 import Environment, FileSystemLoader

# Create custom template environment
env = Environment(loader=FileSystemLoader("./my_templates"))
formatter.jinja_env = env

# Use custom template
template = formatter.jinja_env.get_template("my_report.html")
```

### Adding New Styles

1. Create new CSS file in `styles/` directory
2. Add to `AVAILABLE_STYLES` dict in `styled_pdf.py`:

```python
AVAILABLE_STYLES = {
    # ... existing styles ...
    "corporate": {
        "name": "Corporate",
        "description": "Professional corporate style",
        "css_file": "corporate.css",
    }
}
```

---

## API Reference

### render_styled_pdf()

```python
def render_styled_pdf(
    data: ReportData,
    style_name: Literal["executive", "modernist", "academic"] = "executive"
) -> bytes
```

Convenience function to render a styled PDF.

**Args:**
- `data`: Structured report data
- `style_name`: Visual style to use

**Returns:** PDF file as bytes

### StyledPDFFormatter

```python
class StyledPDFFormatter(OutputFormatter):
    def __init__(
        self,
        config: Optional[FormatConfig] = None,
        style: Literal["executive", "modernist", "academic"] = "executive",
        llm: Optional[Any] = None,
        enable_markdown: bool = True,
    )
```

**Methods:**

#### `format(data: OutputData) -> bytes`
Format standard OutputData as styled PDF.

#### `render_styled_pdf(data: ReportData, style_name: Optional[str] = None) -> bytes`
Render ReportData to PDF with specified style.

#### `structure_with_llm(raw_text: str, query: Optional[str] = None, sources: Optional[list] = None) -> ReportData`
Use LLM to structure raw text into ReportData.

### ReportData

```python
class ReportData(BaseModel):
    title: str
    subtitle: Optional[str] = None
    summary: str
    metrics: List[MetricItem] = []
    sections: List[ReportSection] = []
    references: List[Reference] = []
    metadata: Dict[str, Any] = {}
```

### MetricItem

```python
class MetricItem(BaseModel):
    label: str
    value: str
    icon: Optional[str] = None
```

### ReportSection

```python
class ReportSection(BaseModel):
    heading: str
    content: str
    subsections: Optional[List[ReportSection]] = []
```

### Reference

```python
class Reference(BaseModel):
    title: str
    url: Optional[str] = None
    page: Optional[int] = None
    relevance_score: Optional[float] = None
```

---

## Troubleshooting

### WeasyPrint Installation Issues

**Linux:**
```bash
# Install system dependencies first
sudo apt-get install python3-dev python3-pip python3-cffi libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 shared-mime-info

# Then install WeasyPrint
pip install weasyprint
```

**macOS:**
```bash
brew install cairo pango gdk-pixbuf libffi
pip install weasyprint
```

**Windows:**
Download GTK3 runtime from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

### LLM Not Structuring Correctly

1. **Check temperature**: Use 0.2-0.4 for structured output
2. **Validate JSON**: LLM response must be valid JSON
3. **System prompt**: Ensure LLM receives the structuring prompt
4. **Model capability**: Use capable models (GPT-4, Claude, Llama 3+)

### Fonts Not Rendering

1. **Install fonts**: Ensure system has required fonts
2. **Fallback fonts**: Use web-safe fonts as fallbacks
3. **Font paths**: Check CSS font-family declarations

### PDF Generation Slow

1. **Disable markdown** if not needed
2. **Reduce image count**
3. **Simplify CSS** (remove gradients, shadows)
4. **Use "executive" style** (simplest layout)

---

## Examples

See `examples/styled_pdf_example.py` for complete working examples:

1. **Manual Report Creation**: Build ReportData manually
2. **LLM Structuring**: Convert RAG text with LLM
3. **PullData Integration**: Full workflow integration
4. **Style Comparison**: Generate all 3 styles

Run examples:

```bash
cd /path/to/pulldata
python examples/styled_pdf_example.py
```

---

## Best Practices

### Content Guidelines

1. **Summary**: Keep to 2-3 sentences, highlight key points
2. **Metrics**: Limit to 3-6 most important metrics
3. **Sections**: Aim for 3-5 main sections
4. **References**: Include all source documents

### Style Selection

- **Executive**: For C-level audiences, time-constrained readers
- **Modernist**: For marketing, innovation, creative content
- **Academic**: For research, technical docs, formal reports

### Performance

- Cache LLM responses when possible
- Reuse formatter instances
- Generate PDFs asynchronously for web apps

---

## FAQ

**Q: Can I use this without an LLM?**
A: Yes! Manually create ReportData objects and use `render_styled_pdf()`.

**Q: What LLM models work best?**
A: GPT-4, Claude Sonnet/Opus, Llama 3+ work well. Smaller models may struggle with JSON formatting.

**Q: Can I add my own style?**
A: Yes! Create a new CSS file and add it to AVAILABLE_STYLES.

**Q: Does this work with PDFs in queries?**
A: Yes! Use with any PullData query that returns text.

**Q: Can I customize the template structure?**
A: Yes! Modify `templates/report_base.html` or create your own.

---

## Support

- **Issues**: https://github.com/pulldata/pulldata/issues
- **Documentation**: https://pulldata.readthedocs.io
- **Examples**: `examples/styled_pdf_example.py`

---

**Last Updated:** 2024-12-18
**Version:** 1.0
**Author:** PullData Team
