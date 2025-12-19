"""Pydantic models for structured report generation.

These models define the schema for LLM-generated report content
that will be rendered into styled PDFs.

Includes executive-grade prompts for VP-ready output.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MetricItem(BaseModel):
    """A single key-value metric for visual highlighting."""

    label: str = Field(..., description="Metric label (e.g., 'Revenue Growth')")
    value: str = Field(..., description="Metric value (e.g., '+23%' or '$5.2M')")
    trend: Optional[str] = Field(None, description="Trend indicator: 'up', 'down', 'stable'")
    context: Optional[str] = Field(None, description="Brief context (e.g., 'vs. Q3 2023')")


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

    title: str = Field(..., description="Compelling report title - NO 'Query:' prefix, professional headline style")
    subtitle: Optional[str] = Field(None, description="Powerful subtitle that adds context or intrigue")

    summary: str = Field(..., description="Executive summary - 2-3 impactful sentences that capture key insights")

    key_insight: Optional[str] = Field(None, description="Single most important takeaway - bold statement")

    metrics: List[MetricItem] = Field(
        default_factory=list,
        description="3-6 key metrics with impactful values and trends"
    )

    sections: List[ReportSection] = Field(
        default_factory=list,
        description="Well-structured report sections with professional content"
    )

    recommendations: Optional[List[str]] = Field(
        default_factory=list,
        description="Actionable recommendations or next steps"
    )

    references: List[Reference] = Field(
        default_factory=list,
        description="Source references and citations"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Professional metadata (author, date, classification, etc.)"
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


# =============================================================================
# EXECUTIVE-GRADE LLM PROMPTS FOR VP-READY OUTPUT
# =============================================================================

# Simplified prompt for smaller models (1.7B, 3B, 7B)
SIMPLE_STRUCTURING_PROMPT = """Convert the content into a JSON report. Return ONLY valid JSON, nothing else.

EXAMPLE OUTPUT FORMAT:
{
  "title": "Compelling Professional Headline",
  "subtitle": "Supporting context",
  "summary": "2-3 sentence executive summary of key findings.",
  "key_insight": "Single most important takeaway.",
  "metrics": [
    {"label": "Key Metric", "value": "+25%", "trend": "up", "context": "vs last year"}
  ],
  "sections": [
    {"heading": "Main Finding", "content": "Detailed content here.", "subsections": []}
  ],
  "recommendations": ["Action item 1", "Action item 2"],
  "references": [],
  "metadata": {}
}

RULES:
1. Title: Professional headline, NOT "Query:" or "Analysis of"
2. Summary: Lead with the most important insight
3. Return ONLY the JSON object - no other text"""

# Full executive prompt for larger models (14B+)
EXECUTIVE_STRUCTURING_PROMPT = """You are an elite executive communications specialist. Transform raw information into polished, boardroom-ready reports.

CRITICAL: Your response must be ONLY a valid JSON object. No markdown, no explanations, no thinking.

# TITLE RULES (MOST IMPORTANT)
- NEVER use "Query:", "Question:", "Analysis of" prefixes
- Create COMPELLING headlines like a top business publication
- Good: "Digital Transformation Drives 40% Efficiency Gains"
- Bad: "Query: What is the company's digital strategy?"

# CONTENT GUIDELINES
- Summary: 2-3 impactful sentences for busy executives
- Key Insight: One powerful, memorable takeaway
- Metrics: 3-6 metrics formatted for impact ("$5.2M", "+23%")
- Sections: Action-oriented headings, scannable content
- Recommendations: Actionable directives

# OUTPUT
Return ONLY the JSON object starting with {{ - no other text.

{schema}
"""


CONTENT_REFINEMENT_PROMPT = """You are a senior executive editor at McKinsey or Harvard Business Review. Your task is to refine and elevate a structured report to be truly VP-ready.

# YOUR MISSION
Take the provided JSON report and ELEVATE every element:

## Title Refinement
- Make it punchy, memorable, boardroom-worthy
- If it starts with "Query", "Analysis", or similar - COMPLETELY REWRITE IT
- Think: What would make a VP stop scrolling and read this?

## Summary Polish
- Should answer "Why should I care?" in the first sentence
- Include the most impressive metric if available
- Every word must earn its place

## Metric Enhancement
- Are the metrics the RIGHT ones? Choose impactful over comprehensive
- Are values formatted for maximum impact?
- Add trend context if missing (e.g., "vs. prior year")

## Section Improvement
- Strengthen weak headings
- Ensure each section has clear value
- Remove redundancy
- Add transition phrases between sections
- Ensure professional paragraph structure

## Language Elevation
- Replace weak verbs with strong ones
- Eliminate filler words
- Ensure consistency in tone
- Fix any grammatical issues

# INPUT
{input_report}

# OUTPUT
CRITICAL: Return ONLY the refined JSON object.
- NO thinking blocks or reasoning
- NO markdown code blocks
- NO explanations
- Start directly with the opening brace
"""


QUICK_POLISH_PROMPT = """You are an executive communications expert. Polish this report JSON for VP presentation.

CRITICAL FIXES REQUIRED:
1. If title contains "Query:", "Question:", "Analysis of" - REWRITE to compelling headline
2. Ensure summary is impactful and leads with key insight
3. Format all metrics for visual impact (use $, %, proper number formatting)
4. Ensure section headings are action-oriented, not generic

Input JSON:
{input_json}

OUTPUT: Return ONLY the polished JSON object. NO thinking, NO explanations, NO code blocks. Start directly with the opening brace.
"""

# =============================================================================
# CHAIN PROMPTS - Simple plain text responses for small models
# Each prompt asks for ONE specific thing, returns plain text (not JSON)
# =============================================================================

CHAIN_TITLE_PROMPT = """Based on this content, write a compelling professional headline title (5-15 words).

Rules:
- NO "Query:", "Analysis of", "Report on" prefixes
- Make it sound like a business publication headline
- Be specific and impactful

Content: {content}

Write ONLY the title, nothing else:"""

CHAIN_SUBTITLE_PROMPT = """Based on this content, write a brief subtitle (5-12 words) that adds context.

Content: {content}

Write ONLY the subtitle, nothing else:"""

CHAIN_SUMMARY_PROMPT = """Summarize the key points in 2-3 sentences for a busy executive.
Lead with the most important finding.

Content: {content}

Write ONLY the summary, nothing else:"""

CHAIN_KEY_INSIGHT_PROMPT = """What is the SINGLE most important takeaway from this content?
Write ONE powerful sentence that captures the key insight.

Content: {content}

Write ONLY the key insight sentence, nothing else:"""

CHAIN_METRICS_PROMPT = """Extract 3-5 key metrics or important facts from this content.
Format each as: Label: Value

Example format:
Growth Rate: +25%
Total Users: 1.5M
Efficiency: 40% improvement

Content: {content}

List the metrics (one per line):"""

CHAIN_SECTION_PROMPT = """Create a report section about this content.
Write a heading and 2-4 paragraphs of professional content.

Topic: {topic}
Content: {content}

Format:
HEADING: [Your heading here]
CONTENT:
[Your paragraphs here]"""

CHAIN_RECOMMENDATIONS_PROMPT = """Based on this content, list 2-4 actionable recommendations.
Write as directives (e.g., "Implement...", "Expand...", "Review...").

Content: {content}

List recommendations (one per line):"""


def get_structuring_prompt(include_schema: bool = True, executive_mode: bool = True) -> str:
    """Get the LLM prompt for structuring report data.

    Args:
        include_schema: Whether to include the full schema in the prompt
        executive_mode: Use executive-grade prompts (default True)

    Returns:
        System prompt string
    """
    schema = ReportData.model_json_schema() if include_schema else ""
    return EXECUTIVE_STRUCTURING_PROMPT.format(schema=schema)


def get_refinement_prompt(report_json: str) -> str:
    """Get the LLM prompt for refining/polishing a report.

    Args:
        report_json: The JSON string of the report to refine

    Returns:
        System prompt for refinement
    """
    return CONTENT_REFINEMENT_PROMPT.format(input_report=report_json)


def get_quick_polish_prompt(report_json: str) -> str:
    """Get a quick polish prompt for fast refinement.

    Args:
        report_json: The JSON string to polish

    Returns:
        Polish prompt string
    """
    return QUICK_POLISH_PROMPT.format(input_json=report_json)
