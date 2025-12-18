"""Pydantic models for structured report generation.

These models define the schema for LLM-generated report content
that will be rendered into styled PDFs.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MetricItem(BaseModel):
    """A single key-value metric for visual highlighting."""

    label: str = Field(..., description="Metric label (e.g., 'Revenue')")
    value: str = Field(..., description="Metric value (e.g., '$5M')")
    icon: Optional[str] = Field(None, description="Optional icon/emoji for the metric")


class ReportSection(BaseModel):
    """A section of the report with heading and content."""

    heading: str = Field(..., description="Section heading")
    content: str = Field(..., description="Section content (supports markdown)")
    subsections: Optional[List['ReportSection']] = Field(default_factory=list, description="Optional nested subsections")


class Reference(BaseModel):
    """A source reference/citation."""

    title: str = Field(..., description="Reference title or document name")
    url: Optional[str] = Field(None, description="URL if available")
    page: Optional[int] = Field(None, description="Page number if applicable")
    relevance_score: Optional[float] = Field(None, description="Relevance score (0-1)")


class ReportData(BaseModel):
    """Complete structured report data for PDF generation.

    This schema is used by the LLM to structure raw RAG-retrieved
    text into a format suitable for styled PDF rendering.
    """

    title: str = Field(..., description="Report title")
    subtitle: Optional[str] = Field(None, description="Optional subtitle or tagline")

    summary: str = Field(..., description="Executive summary (2-3 sentences)")

    metrics: List[MetricItem] = Field(
        default_factory=list,
        description="Key metrics for visual highlighting"
    )

    sections: List[ReportSection] = Field(
        default_factory=list,
        description="Report sections with headings and content"
    )

    references: List[Reference] = Field(
        default_factory=list,
        description="Source references and citations"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (author, date, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Q3 2024 Revenue Analysis",
                "subtitle": "Financial Performance Report",
                "summary": "Q3 revenue reached $10.5M, representing 15% year-over-year growth. Key drivers include strong performance in the enterprise segment and successful product launches.",
                "metrics": [
                    {"label": "Revenue", "value": "$10.5M", "icon": "💰"},
                    {"label": "Growth", "value": "+15%", "icon": "📈"},
                    {"label": "Customers", "value": "1,234", "icon": "👥"}
                ],
                "sections": [
                    {
                        "heading": "Overview",
                        "content": "The third quarter demonstrated strong financial performance..."
                    },
                    {
                        "heading": "Key Findings",
                        "content": "Our analysis reveals three primary trends...",
                        "subsections": [
                            {
                                "heading": "Enterprise Segment",
                                "content": "Enterprise sales grew 25%..."
                            }
                        ]
                    }
                ],
                "references": [
                    {
                        "title": "Q3 Financial Statement",
                        "url": "https://example.com/q3-statement.pdf",
                        "page": 5,
                        "relevance_score": 0.95
                    }
                ],
                "metadata": {
                    "author": "Financial Analysis Team",
                    "date": "2024-10-15",
                    "version": "1.0"
                }
            }
        }


# System prompt for LLM to structure data
REPORT_STRUCTURING_PROMPT = """You are a professional report writer assistant. Your task is to convert raw text from a RAG (Retrieval-Augmented Generation) system into a structured JSON report.

# Your Task
Analyze the provided text and extract/organize it into the following JSON structure:

```json
{
  "title": "Clear, descriptive title",
  "subtitle": "Optional subtitle or tagline",
  "summary": "2-3 sentence executive summary highlighting the most important points",
  "metrics": [
    {"label": "Metric Name", "value": "Value with units", "icon": "relevant emoji"}
  ],
  "sections": [
    {
      "heading": "Section Title",
      "content": "Detailed content for this section. Use clear, professional language.",
      "subsections": []
    }
  ],
  "references": [
    {
      "title": "Source document or reference",
      "url": "URL if available",
      "page": page_number,
      "relevance_score": 0.0-1.0
    }
  ],
  "metadata": {
    "author": "extracted or inferred",
    "date": "YYYY-MM-DD",
    "source": "data source"
  }
}
```

# Guidelines

1. **Title & Subtitle**: Create a clear, descriptive title that captures the main topic. Add a subtitle if it adds value.

2. **Summary**: Write a concise 2-3 sentence executive summary that a busy executive could read to understand the key points.

3. **Metrics**: Extract 3-6 key quantitative metrics that deserve visual highlighting. Format values clearly (e.g., "$5M", "15%", "1,234 users"). Add relevant emojis.

4. **Sections**: Organize content into logical sections:
   - Use clear, descriptive headings
   - Write well-structured paragraphs
   - Group related information together
   - Use subsections for hierarchical information
   - Aim for 3-5 main sections

5. **References**: List all source documents/citations mentioned in the text. Include relevance scores if confidence information is available.

6. **Metadata**: Extract or infer metadata like author, date, version, etc.

# Content Rules
- Be concise but comprehensive
- Use professional, clear language
- Preserve important numbers, dates, and facts
- Remove redundancy
- Maintain logical flow
- Format for readability

# Output Format
Return ONLY valid JSON matching the schema above. No markdown code blocks, no explanations, just the JSON object.
"""


# Alternative prompt for when source documents are provided
REPORT_STRUCTURING_PROMPT_WITH_SOURCES = """You are a professional report writer assistant. Convert the provided RAG-retrieved text and source documents into a structured JSON report.

**Input provided:**
- Query: The user's original question
- Retrieved chunks: Text snippets from source documents with metadata
- (Optional) Generated answer: LLM-generated answer

**Your task:** Structure this information into the ReportData JSON schema.

{schema}

**Instructions:**
1. Use the query as inspiration for the title
2. Synthesize retrieved chunks into the summary and sections
3. Extract key metrics from the text (numbers, percentages, amounts)
4. Preserve source information in the references array
5. Create a well-organized, professional report structure

**Output:** Valid JSON only, no markdown code blocks.
"""


def get_structuring_prompt(include_schema: bool = True) -> str:
    """Get the LLM prompt for structuring report data.

    Args:
        include_schema: Whether to include the full schema in the prompt

    Returns:
        System prompt string
    """
    if include_schema:
        schema = ReportData.model_json_schema()
        return REPORT_STRUCTURING_PROMPT_WITH_SOURCES.format(
            schema=str(schema)
        )
    return REPORT_STRUCTURING_PROMPT
