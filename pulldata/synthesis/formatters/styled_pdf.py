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
from typing import Any, Dict, List, Literal, Optional

# Fix Windows fontconfig warning
if os.name == 'nt':  # Windows only
    os.environ.setdefault('FONTCONFIG_PATH', '')
    os.environ.setdefault('FONTCONFIG_FILE', '')

from jinja2 import Environment, FileSystemLoader, select_autoescape

from pulldata.synthesis.base import FormatConfig, FormatterError, OutputData, OutputFormatter
from pulldata.synthesis.report_models import (
    ReportData,
    MetricItem,
    ReportSection,
    SIMPLE_STRUCTURING_PROMPT,
    CHAIN_TITLE_PROMPT,
    CHAIN_SUBTITLE_PROMPT,
    CHAIN_SUMMARY_PROMPT,
    CHAIN_KEY_INSIGHT_PROMPT,
    CHAIN_METRICS_PROMPT,
    CHAIN_SECTION_PROMPT,
    CHAIN_RECOMMENDATIONS_PROMPT,
    get_structuring_prompt,
    get_refinement_prompt,
    get_quick_polish_prompt,
)

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
        executive_mode: bool = True,
        auto_polish: bool = True,
        use_llm_structuring: bool = True,
    ):
        """Initialize styled PDF formatter.

        Args:
            config: Formatter configuration
            style: Visual style to use ("executive", "modernist", or "academic")
            llm: Optional LLM instance for data structuring
            enable_markdown: Enable markdown processing in content
            executive_mode: Use executive-grade prompts for VP-ready output (default True)
            auto_polish: Automatically apply LLM polish pass for maximum quality (default True)
            use_llm_structuring: Use LLM to structure content (set False if LLM has issues with JSON output)
        """
        super().__init__(config)
        self.executive_mode = executive_mode
        self.auto_polish = auto_polish
        self.use_llm_structuring = use_llm_structuring

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
        apply_polish: Optional[bool] = None,
    ) -> ReportData:
        """Use LLM to structure raw text into ReportData.

        This method uses executive-grade prompts to create VP-ready content,
        with an optional second-pass polish for maximum quality.

        Args:
            raw_text: Raw text from RAG retrieval
            query: Original user query (optional)
            sources: Source documents (optional)
            apply_polish: Override auto_polish setting for this call

        Returns:
            Structured and polished ReportData

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
            # Use simple prompt optimized for smaller models (1.7B-7B)
            # This has a concrete JSON example which helps smaller models
            system_prompt = SIMPLE_STRUCTURING_PROMPT

            # Build simplified user message for better JSON compliance
            user_parts = []
            if query:
                user_parts.append(f"Topic: {query}")
            user_parts.append(f"\nContent:\n{raw_text[:4000]}")  # Limit content for smaller models
            user_parts.append("\nReturn ONLY a JSON object with the report. Start with {")
            user_parts.append("\n/no_think")  # Disable thinking for Qwen models

            user_message = "\n".join(user_parts)

            # Generate structured data
            response = self.llm.generate(
                prompt=user_message,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temp for more reliable JSON
                max_tokens=4000,  # Reduced for faster response
            )

            # Parse JSON response - handle thinking blocks
            response_text = response.text if hasattr(response, 'text') else str(response)
            json_str = self._extract_json(response_text)
            data_dict = json.loads(json_str)
            report_data = ReportData(**data_dict)

            # Apply polish pass if enabled
            should_polish = apply_polish if apply_polish is not None else self.auto_polish
            if should_polish:
                report_data = self.polish_report(report_data)

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

    def polish_report(self, report_data: ReportData) -> ReportData:
        """Apply LLM polish pass to elevate report quality.

        This second-pass refinement ensures the report is truly VP-ready
        by improving titles, strengthening language, and enhancing impact.

        Args:
            report_data: The structured report to polish

        Returns:
            Polished ReportData with elevated content

        Raises:
            FormatterError: If LLM is not available or polishing fails
        """
        if not self.llm:
            return report_data  # Return as-is if no LLM

        try:
            # Convert to JSON for the polish prompt
            report_json = report_data.model_dump_json(indent=2)

            # Use quick polish for efficiency - add /no_think for Qwen models
            polish_prompt = get_quick_polish_prompt(report_json) + "\n\n/no_think"

            # Generate polished version
            response = self.llm.generate(
                prompt=polish_prompt,
                system_prompt="Return ONLY valid JSON. No thinking, no markdown. Start with {",
                temperature=0.3,
                max_tokens=4000,
            )
            
            # Parse polished JSON
            json_str = self._extract_json(response.text)
            polished_dict = json.loads(json_str)
            polished_data = ReportData(**polished_dict)

            return polished_data

        except Exception as e:
            # If polish fails, return original data rather than failing entirely
            import logging
            logging.warning(f"Polish pass failed, using original: {e}")
            return report_data

    # =========================================================================
    # CHAIN-BASED STRUCTURING - Multiple simple LLM calls for small models
    # =========================================================================

    def _chain_call(self, prompt: str, max_tokens: int = 500) -> str:
        """Make a single chain LLM call returning plain text.

        Args:
            prompt: The prompt to send (already formatted)
            max_tokens: Maximum tokens for response

        Returns:
            Plain text response, cleaned up
        """
        # Add /no_think for Qwen models
        full_prompt = prompt + "\n/no_think"

        response = self.llm.generate(
            prompt=full_prompt,
            system_prompt="Answer directly and concisely. No explanations.",
            temperature=0.3,
            max_tokens=max_tokens,
        )

        # Clean response
        text = response.text if hasattr(response, 'text') else str(response)

        # Remove think blocks
        import re
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)

        return text.strip()

    def structure_with_chain(
        self,
        raw_text: str,
        query: Optional[str] = None,
        sources: Optional[list] = None,
    ) -> ReportData:
        """Structure content using multiple simple LLM calls.

        This approach works better with small models (1.7B-7B) by:
        1. Making independent calls for each component
        2. Each call returns plain text (not JSON)
        3. Pydantic validates the assembled data

        Args:
            raw_text: Raw text content to structure
            query: Original user query
            sources: Source documents

        Returns:
            Validated ReportData instance
        """
        import logging
        from datetime import datetime

        # Limit content for small models
        content = raw_text[:3000]

        logging.info("Starting chain-based PDF structuring...")

        # Call 1: Get title
        logging.debug("Chain call 1: Getting title...")
        title = self._chain_call(
            CHAIN_TITLE_PROMPT.format(content=content[:1500]),
            max_tokens=100
        )
        # Clean up title
        title = title.replace('"', '').replace("'", "").strip()
        if not title or len(title) < 5:
            title = query or "Analysis Report"

        # Call 2: Get subtitle
        logging.debug("Chain call 2: Getting subtitle...")
        subtitle = self._chain_call(
            CHAIN_SUBTITLE_PROMPT.format(content=content[:1000]),
            max_tokens=80
        )
        subtitle = subtitle.replace('"', '').replace("'", "").strip()

        # Call 3: Get summary
        logging.debug("Chain call 3: Getting summary...")
        summary = self._chain_call(
            CHAIN_SUMMARY_PROMPT.format(content=content),
            max_tokens=300
        )
        if not summary or len(summary) < 20:
            summary = content[:300] + "..."

        # Call 4: Get key insight
        logging.debug("Chain call 4: Getting key insight...")
        key_insight = self._chain_call(
            CHAIN_KEY_INSIGHT_PROMPT.format(content=content[:1500]),
            max_tokens=150
        )

        # Call 5: Get metrics
        logging.debug("Chain call 5: Getting metrics...")
        metrics_text = self._chain_call(
            CHAIN_METRICS_PROMPT.format(content=content),
            max_tokens=400
        )
        metrics = self._parse_metrics(metrics_text)

        # Call 6: Get main section
        logging.debug("Chain call 6: Getting main section...")
        section_text = self._chain_call(
            CHAIN_SECTION_PROMPT.format(
                topic=query or "Key Findings",
                content=content
            ),
            max_tokens=800
        )
        sections = self._parse_sections(section_text, content)

        # Call 7: Get recommendations
        logging.debug("Chain call 7: Getting recommendations...")
        recs_text = self._chain_call(
            CHAIN_RECOMMENDATIONS_PROMPT.format(content=content),
            max_tokens=300
        )
        recommendations = self._parse_recommendations(recs_text)

        # Build references from sources
        references = []
        if sources:
            for src in sources[:5]:
                if isinstance(src, dict):
                    references.append({
                        "title": src.get("document_id", "Source"),
                        "url": src.get("url"),
                        "page": src.get("page_number"),
                        "relevance_score": src.get("score"),
                    })

        # Build metadata
        metadata = {
            "generated_at": datetime.now().strftime("%B %d, %Y"),
            "generation_method": "chain",
        }

        logging.info("Chain structuring complete - assembling ReportData")

        # Assemble and validate with Pydantic
        return ReportData(
            title=title,
            subtitle=subtitle,
            summary=summary,
            key_insight=key_insight,
            metrics=metrics,
            sections=sections,
            recommendations=recommendations,
            references=references,
            metadata=metadata,
        )

    def _parse_metrics(self, text: str) -> List[dict]:
        """Parse metrics from plain text response.

        Expected format:
        Label: Value
        Label2: Value2
        """
        metrics = []
        for line in text.strip().split('\n'):
            line = line.strip()
            if not line or ':' not in line:
                continue
            # Remove bullet points
            line = line.lstrip('•-*').strip()
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    label = parts[0].strip()
                    value = parts[1].strip()
                    if label and value:
                        metrics.append({
                            "label": label,
                            "value": value,
                            "trend": None,
                            "context": None,
                        })
        return metrics[:6]  # Limit to 6 metrics

    def _parse_sections(self, text: str, fallback_content: str) -> List[dict]:
        """Parse sections from plain text response.

        Expected format:
        HEADING: [heading]
        CONTENT:
        [paragraphs]
        """
        sections = []

        # Try to parse HEADING:/CONTENT: format
        if 'HEADING:' in text.upper():
            import re
            heading_match = re.search(r'HEADING:\s*(.+?)(?:\n|CONTENT:)', text, re.IGNORECASE)
            content_match = re.search(r'CONTENT:\s*(.+)', text, re.IGNORECASE | re.DOTALL)

            heading = heading_match.group(1).strip() if heading_match else "Key Findings"
            content = content_match.group(1).strip() if content_match else text

            sections.append({
                "heading": heading,
                "content": content,
                "subsections": [],
            })
        else:
            # Fallback: use the whole response as content
            sections.append({
                "heading": "Key Findings",
                "content": text if text else fallback_content[:1000],
                "subsections": [],
            })

        return sections

    def _parse_recommendations(self, text: str) -> List[str]:
        """Parse recommendations from plain text response."""
        recs = []
        for line in text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            # Remove numbering and bullets
            line = line.lstrip('0123456789.•-*) ').strip()
            if line and len(line) > 10:
                recs.append(line)
        return recs[:5]  # Limit to 5 recommendations

    def _build_structuring_prompt(
        self,
        raw_text: str,
        query: Optional[str] = None,
        sources: Optional[list] = None,
    ) -> str:
        """Build the user message for structuring, optimized for executive output.

        Args:
            raw_text: Raw text content
            query: User's original query
            sources: Source documents

        Returns:
            Formatted user message
        """
        parts = []

        # Include topic/context without polluting title with "Query:"
        if query:
            parts.append(f"**Topic/Focus:** {query}")
            parts.append("(Create a compelling headline-style title, NOT 'Query: {query}')")

        parts.append(f"\n**Content to Structure:**\n{raw_text}")

        if sources:
            source_info = []
            for i, src in enumerate(sources[:5], 1):  # Limit to top 5
                if isinstance(src, dict):
                    title = src.get("document_id", src.get("title", f"Source {i}"))
                    score = src.get("score", src.get("relevance_score"))
                    page = src.get("page_number", src.get("page"))
                    info = f"  {i}. {title}"
                    if score:
                        info += f" (relevance: {score:.0%})"
                    if page:
                        info += f" [page {page}]"
                    source_info.append(info)
            if source_info:
                parts.append(f"\n**Source Documents:**\n" + "\n".join(source_info))

        parts.append("\n**Instructions:** Create a polished, executive-ready report. "
                    "The title must be compelling and professional - NO 'Query:' prefix.")

        return "\n".join(parts)

    def _extract_json(self, text: str) -> str:
        """Extract JSON from LLM response, handling various formats.

        Handles:
        - Markdown code blocks (```json ... ```)
        - LLM thinking blocks (<think>...</think>)
        - Raw JSON with surrounding text
        - Multiple JSON objects (takes the first complete one)

        Args:
            text: Raw LLM response text

        Returns:
            Cleaned JSON string

        Raises:
            ValueError: If no valid JSON object can be found
        """
        import re

        json_str = text.strip()

        # Remove <think>...</think> blocks (some LLMs include reasoning)
        # Handle both complete and incomplete think blocks
        json_str = re.sub(r'<think>.*?</think>', '', json_str, flags=re.DOTALL)
        # Also handle incomplete <think> blocks (no closing tag)
        json_str = re.sub(r'<think>.*', '', json_str, flags=re.DOTALL)
        json_str = json_str.strip()

        # Remove markdown code blocks if present
        if "```" in json_str:
            # Try to extract content from code blocks
            code_block_match = re.search(r'```(?:json|JSON)?\s*([\s\S]*?)```', json_str)
            if code_block_match:
                json_str = code_block_match.group(1).strip()

        # If still not starting with {, find the JSON object
        if not json_str.startswith("{"):
            # Find the first { and matching }
            start = json_str.find("{")
            if start != -1:
                # Count braces to find the matching closing brace
                brace_count = 0
                end = start
                for i, char in enumerate(json_str[start:], start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
                json_str = json_str[start:end]

        # Final cleanup - remove any trailing text after the JSON
        if json_str.startswith("{"):
            brace_count = 0
            for i, char in enumerate(json_str):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_str = json_str[:i+1]
                        break

        if not json_str or not json_str.startswith("{"):
            raise ValueError(f"No valid JSON object found in response. Got: {text[:200]}...")

        return json_str

    def _convert_to_report_data(self, data: OutputData) -> ReportData:
        """Convert standard OutputData to ReportData format.

        If LLM is available, uses it to create executive-grade content.
        Otherwise falls back to basic conversion.

        Args:
            data: Standard output data

        Returns:
            ReportData instance (polished if LLM available)
        """
        from datetime import datetime

        # If LLM is available and enabled, use chain-based structuring
        # Chain method makes multiple simple calls - works better with small models
        if self.llm and data.content and self.use_llm_structuring:
            try:
                # Get the query from metadata if available
                query = data.metadata.get("query") if data.metadata else None

                return self.structure_with_chain(
                    raw_text=data.content,
                    query=query or data.title,
                    sources=data.sources,
                )
            except Exception as e:
                import logging
                logging.warning(f"Chain structuring failed, using fallback: {e}")

        # Fallback: basic conversion without LLM - still creates professional output
        metrics = []
        if data.metadata and "metrics" in data.metadata:
            if isinstance(data.metadata["metrics"], list):
                metrics = data.metadata["metrics"]

        # Convert sections - split content into logical paragraphs if no sections
        sections = []
        if data.sections:
            for section in data.sections:
                sections.append({
                    "heading": section.get("title", "Section"),
                    "content": section.get("content", ""),
                    "subsections": [],
                })
        elif data.content:
            # Try to create a more structured layout from raw content
            content = data.content
            # If content has multiple paragraphs, try to structure them
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            if len(paragraphs) > 2:
                # First paragraph as overview
                sections.append({
                    "heading": "Overview",
                    "content": paragraphs[0],
                    "subsections": [],
                })
                # Middle paragraphs as analysis
                sections.append({
                    "heading": "Analysis",
                    "content": '\n\n'.join(paragraphs[1:-1]) if len(paragraphs) > 2 else paragraphs[1],
                    "subsections": [],
                })
                # Last paragraph as conclusion
                if len(paragraphs) > 2:
                    sections.append({
                        "heading": "Conclusion",
                        "content": paragraphs[-1],
                        "subsections": [],
                    })
            else:
                sections.append({
                    "heading": "Key Findings",
                    "content": content,
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
            metadata["generated_at"] = datetime.now().strftime("%B %d, %Y")

        # Create a professional title from the query
        title = data.title or ""
        # Remove common prefixes and clean up
        for prefix in ["query:", "question:", "what is", "what are", "how to", "explain"]:
            if title.lower().startswith(prefix):
                title = title[len(prefix):].strip()
                break
        # Capitalize properly
        if title:
            title = title.strip('?').strip()
            # Title case but preserve acronyms
            words = title.split()
            title = ' '.join(w if w.isupper() else w.title() for w in words)

        # Create a summary from the first part of content
        summary = ""
        if data.content:
            # Take first 2-3 sentences
            sentences = data.content.replace('\n', ' ').split('. ')
            summary = '. '.join(sentences[:3])
            if len(summary) > 500:
                summary = summary[:497] + "..."
            elif not summary.endswith('.'):
                summary += '.'

        return ReportData(
            title=title or "Strategic Analysis Report",
            subtitle=metadata.get("subtitle", "Comprehensive Analysis & Insights"),
            summary=summary or "Analysis results detailed below.",
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
