"""Styled PDF formatter with LLM-powered data structuring.

Creates professional PDF reports with 3 visual styles:
- Executive: Clean, minimalist, blue/grey
- Modernist: Bold, high contrast, dark accents
- Academic: Serif fonts, two-column layout
"""

import json
import os
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Literal, Optional

# Fix Windows fontconfig warning
if os.name == 'nt':  # Windows only
    os.environ.setdefault('FONTCONFIG_PATH', '')
    os.environ.setdefault('FONTCONFIG_FILE', '')

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pulldata.synthesis.base import FormatConfig, FormatterError, OutputData, OutputFormatter
from pulldata.synthesis.report_models import ReportData, get_structuring_prompt

try:
    from weasyprint import HTML, CSS

    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    from pulldata.llm.api_llm import APILLM
    from pulldata.llm.local_llm import LocalLLM

    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


# Style definitions
AVAILABLE_STYLES = {
    "executive": {
        "name": "The Executive",
        "description": "Clean, minimalist design with generous whitespace",
        "css_file": "executive.css",
    },
    "modernist": {
        "name": "The Modernist",
        "description": "Bold typography with high contrast and dark accents",
        "css_file": "modernist.css",
    },
    "academic": {
        "name": "The Academic",
        "description": "Traditional serif fonts with two-column layout",
        "css_file": "academic.css",
    },
}


class StyledPDFFormatter(OutputFormatter):
    """Advanced PDF formatter with LLM-powered structuring and visual styles.

    This formatter takes raw RAG-retrieved text, uses an LLM to structure it
    into a JSON schema, and renders it as a professionally styled PDF using
    Jinja2 templates and WeasyPrint.

    Features:
    - LLM-powered data structuring
    - 3 professional visual styles
    - Markdown content support
    - Automatic page breaks
    - Source citations
    - Metrics visualization

    Example:
        >>> formatter = StyledPDFFormatter(style="executive")
        >>> data = OutputData(title="Report", content="...", sources=[...])
        >>> pdf_bytes = formatter.format(data)

        Or with LLM structuring:
        >>> formatter = StyledPDFFormatter(style="modernist", llm=my_llm)
        >>> structured_data = formatter.structure_with_llm(raw_text)
        >>> pdf_bytes = formatter.render_styled_pdf(structured_data)
    """

    def __init__(
        self,
        config: Optional[FormatConfig] = None,
        style: Literal["executive", "modernist", "academic"] = "executive",
        llm: Optional[Any] = None,
        enable_markdown: bool = True,
    ):
        """Initialize styled PDF formatter.

        Args:
            config: Formatter configuration
            style: Visual style to use ("executive", "modernist", or "academic")
            llm: Optional LLM instance for data structuring
            enable_markdown: Enable markdown processing in content
        """
        super().__init__(config)

        if not WEASYPRINT_AVAILABLE:
            raise FormatterError(
                "weasyprint not available",
                formatter="StyledPDF",
                details={"install": "pip install weasyprint"},
            )

        if style not in AVAILABLE_STYLES:
            raise FormatterError(
                f"Unknown style: {style}",
                formatter="StyledPDF",
                details={"available_styles": list(AVAILABLE_STYLES.keys())},
            )

        self.style = style
        self.style_info = AVAILABLE_STYLES[style]
        self.llm = llm
        self.enable_markdown = enable_markdown

        # Setup Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Load CSS for the selected style
        css_path = template_dir / "styles" / self.style_info["css_file"]
        if not css_path.exists():
            raise FormatterError(
                f"CSS file not found: {css_path}",
                formatter="StyledPDF",
                details={"style": style, "expected_path": str(css_path)},
            )

        with open(css_path, "r", encoding="utf-8") as f:
            self.style_css = f.read()

    @property
    def file_extension(self) -> str:
        return ".pdf"

    @property
    def format_name(self) -> str:
        return f"StyledPDF ({self.style_info['name']})"

    def format(self, data: OutputData) -> bytes:
        """Format OutputData as styled PDF.

        This converts the standard OutputData to ReportData structure
        and renders it as a PDF.

        Args:
            data: Standard PullData output data

        Returns:
            PDF file as bytes
        """
        # Convert OutputData to ReportData
        report_data = self._convert_to_report_data(data)

        # Render PDF
        return self.render_styled_pdf(report_data)

    def render_styled_pdf(
        self,
        data: ReportData,
        style_name: Optional[str] = None,
    ) -> bytes:
        """Render ReportData to PDF with the specified style.

        Args:
            data: Structured report data
            style_name: Optional style override

        Returns:
            PDF file as bytes

        Raises:
            FormatterError: If rendering fails
        """
        if not WEASYPRINT_AVAILABLE:
            raise FormatterError(
                "weasyprint not available",
                formatter="StyledPDF",
                details={"install": "pip install weasyprint"},
            )

        try:
            # Load template
            template = self.jinja_env.get_template("report_base.html")

            # Process markdown in content if enabled
            if self.enable_markdown:
                data = self._process_markdown(data)

            # Render HTML
            html_content = template.render(
                data=data,
                style_name=style_name or self.style,
                style_css=self.style_css,
            )

            # Generate PDF using WeasyPrint
            html = HTML(string=html_content)
            pdf_bytes = html.write_pdf()

            return pdf_bytes

        except Exception as e:
            raise FormatterError(
                f"Failed to render PDF: {str(e)}",
                formatter="StyledPDF",
                details={"error": str(e), "style": self.style},
            ) from e

    def structure_with_llm(
        self,
        raw_text: str,
        query: Optional[str] = None,
        sources: Optional[list] = None,
    ) -> ReportData:
        """Use LLM to structure raw text into ReportData.

        Args:
            raw_text: Raw text from RAG retrieval
            query: Original user query (optional)
            sources: Source documents (optional)

        Returns:
            Structured ReportData

        Raises:
            FormatterError: If LLM is not available or structuring fails
        """
        if not self.llm:
            raise FormatterError(
                "No LLM provided for data structuring",
                formatter="StyledPDF",
                details={"hint": "Pass an LLM instance to the formatter constructor"},
            )

        if not LLM_AVAILABLE:
            raise FormatterError(
                "LLM modules not available",
                formatter="StyledPDF",
                details={"install": "Ensure pulldata.llm is properly installed"},
            )

        try:
            # Build prompt
            system_prompt = get_structuring_prompt(include_schema=True)

            # Build user message
            user_message = f"**Raw Text:**\n{raw_text}\n\n"
            if query:
                user_message = f"**Query:** {query}\n\n" + user_message
            if sources:
                user_message += f"\n**Sources:** {len(sources)} documents retrieved\n"

            user_message += "\nStructure this into the ReportData JSON format."

            # Generate structured data
            response = self.llm.generate(
                prompt=user_message,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for structured output
                max_tokens=4000,
            )

            # Parse JSON response
            json_str = response.text.strip()

            # Remove markdown code blocks if present
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                json_str = json_str.strip()

            # Parse and validate
            data_dict = json.loads(json_str)
            report_data = ReportData(**data_dict)

            return report_data

        except json.JSONDecodeError as e:
            raise FormatterError(
                f"Failed to parse LLM response as JSON: {str(e)}",
                formatter="StyledPDF",
                details={"error": str(e), "response_preview": response.text[:500]},
            ) from e
        except Exception as e:
            raise FormatterError(
                f"Failed to structure data with LLM: {str(e)}",
                formatter="StyledPDF",
                details={"error": str(e)},
            ) from e

    def _convert_to_report_data(self, data: OutputData) -> ReportData:
        """Convert standard OutputData to ReportData format.

        This is a fallback conversion when LLM structuring is not used.

        Args:
            data: Standard output data

        Returns:
            ReportData instance
        """
        from datetime import datetime

        # Extract metrics from metadata if available
        metrics = []
        if "metrics" in data.metadata and isinstance(data.metadata["metrics"], list):
            metrics = data.metadata["metrics"]

        # Convert sections
        sections = []
        if data.sections:
            for section in data.sections:
                sections.append({
                    "heading": section.get("title", "Section"),
                    "content": section.get("content", ""),
                    "subsections": [],
                })
        elif data.content:
            # If no sections, use content as a single section
            sections.append({
                "heading": "Overview",
                "content": data.content,
                "subsections": [],
            })

        # Convert sources to references
        references = []
        for source in data.sources:
            references.append({
                "title": source.get("document_id", "Unknown"),
                "url": source.get("url"),
                "page": source.get("page_number"),
                "relevance_score": source.get("score"),
            })

        # Build metadata
        metadata = data.metadata.copy() if data.metadata else {}
        if "generated_at" not in metadata:
            metadata["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return ReportData(
            title=data.title,
            subtitle=metadata.get("subtitle"),
            summary=data.content[:500] if data.content else "No summary available.",
            metrics=metrics,
            sections=sections,
            references=references,
            metadata=metadata,
        )

    def _process_markdown(self, data: ReportData) -> ReportData:
        """Process markdown in content fields.

        Args:
            data: Report data with markdown content

        Returns:
            Report data with processed markdown
        """
        try:
            import markdown2

            md = markdown2.Markdown(extras=["fenced-code-blocks", "tables"])

            # Process sections
            for section in data.sections:
                section.content = md.convert(section.content)
                if section.subsections:
                    for subsection in section.subsections:
                        subsection.content = md.convert(subsection.content)

            return data

        except ImportError:
            # If markdown2 not available, return as-is
            return data


def render_styled_pdf(
    data: ReportData,
    style_name: Literal["executive", "modernist", "academic"] = "executive",
) -> bytes:
    """Convenience function to render a styled PDF.

    Args:
        data: Structured report data
        style_name: Visual style to use

    Returns:
        PDF file as bytes

    Example:
        >>> from pulldata.synthesis.report_models import ReportData
        >>> data = ReportData(title="My Report", summary="...", sections=[...])
        >>> pdf_bytes = render_styled_pdf(data, style_name="executive")
        >>> with open("report.pdf", "wb") as f:
        ...     f.write(pdf_bytes)
    """
    formatter = StyledPDFFormatter(style=style_name)
    return formatter.render_styled_pdf(data)
