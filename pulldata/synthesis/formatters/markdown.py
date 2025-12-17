"""Markdown formatter for PullData output.

Converts structured data into clean, readable Markdown with
automatic table of contents, code blocks, and table support.
"""

from io import StringIO
from typing import Any, Dict, List, Optional

from pulldata.synthesis.base import FormatConfig, FormatterError, OutputData, OutputFormatter

try:
    import markdown2

    MARKDOWN2_AVAILABLE = True
except ImportError:
    MARKDOWN2_AVAILABLE = False


class MarkdownFormatter(OutputFormatter):
    """Markdown formatter with auto-generated TOC and clean formatting.
    
    Features:
    - Auto-generated table of contents
    - GFM-style tables
    - Code block highlighting
    - Clean document structure
    - Link and image support
    
    Example:
        >>> formatter = MarkdownFormatter()
        >>> data = OutputData(title="Report", content="Summary", sections=[...])
        >>> formatter.save(data, "output.md")
    """

    def __init__(
        self,
        config: Optional[FormatConfig] = None,
        include_toc: bool = True,
        heading_level: int = 1,
        code_highlighting: bool = True,
    ):
        """Initialize Markdown formatter.
        
        Args:
            config: Formatter configuration
            include_toc: Generate table of contents
            heading_level: Starting heading level for title (1-6)
            code_highlighting: Enable code block syntax highlighting hints
        """
        super().__init__(config)
        self.include_toc = include_toc
        self.heading_level = max(1, min(6, heading_level))
        self.code_highlighting = code_highlighting

    @property
    def file_extension(self) -> str:
        return ".md"

    @property
    def format_name(self) -> str:
        return "Markdown"

    def format(self, data: OutputData) -> bytes:
        """Format data as Markdown.
        
        Args:
            data: Data to format
            
        Returns:
            Markdown content as bytes
        """
        output = StringIO()

        # Title
        output.write(f"{'#' * self.heading_level} {data.title}\n\n")

        # Table of contents
        if self.include_toc and (data.sections or data.tables or data.sources):
            self._write_toc(output, data)

        # Main content
        if data.content:
            output.write(f"{data.content}\n\n")

        # Sections
        if data.sections:
            self._write_sections(output, data.sections)

        # Tables
        if data.tables:
            self._write_tables(output, data.tables)

        # Metadata
        if self.config.include_metadata and data.metadata:
            self._write_metadata(output, data.metadata)

        # Sources
        if self.config.include_sources and data.sources:
            self._write_sources(output, data.sources)

        return output.getvalue().encode("utf-8")

    def _write_toc(self, output: StringIO, data: OutputData) -> None:
        """Write table of contents."""
        output.write(f"{'#' * (self.heading_level + 1)} Table of Contents\n\n")

        # Add main sections
        if data.sections:
            for section in data.sections:
                title = section.get("title", "Untitled Section")
                anchor = self._make_anchor(title)
                output.write(f"- [{title}](#{anchor})\n")

        # Add tables section
        if data.tables:
            output.write(f"- [Tables](#tables)\n")
            for i, table in enumerate(data.tables):
                table_name = table.get("name", f"Table {i+1}")
                anchor = self._make_anchor(f"table-{table_name}")
                output.write(f"  - [{table_name}](#{anchor})\n")

        # Add metadata
        if self.config.include_metadata and data.metadata:
            output.write(f"- [Metadata](#metadata)\n")

        # Add sources
        if self.config.include_sources and data.sources:
            output.write(f"- [Sources](#sources)\n")

        output.write("\n")

    def _write_sections(self, output: StringIO, sections: List[Dict[str, Any]]) -> None:
        """Write document sections."""
        for section in sections:
            title = section.get("title", "Untitled Section")
            content = section.get("content", "")
            level = section.get("level", self.heading_level + 1)

            output.write(f"{'#' * level} {title}\n\n")
            output.write(f"{content}\n\n")

    def _write_tables(self, output: StringIO, tables: List[Dict[str, Any]]) -> None:
        """Write tables in GFM format."""
        output.write(f"{'#' * (self.heading_level + 1)} Tables\n\n")

        for i, table_data in enumerate(tables):
            table_name = table_data.get("name", f"Table {i+1}")
            output.write(f"{'#' * (self.heading_level + 2)} {table_name}\n\n")

            headers = table_data.get("headers", [])
            rows = table_data.get("rows", [])

            if not headers and not rows:
                output.write("*No table data*\n\n")
                continue

            # Write table header
            if headers:
                output.write("| " + " | ".join(str(h) for h in headers) + " |\n")
                output.write("| " + " | ".join("---" for _ in headers) + " |\n")

            # Write table rows
            for row in rows:
                # Ensure row has same length as headers
                padded_row = list(row) + [""] * (len(headers) - len(row))
                output.write("| " + " | ".join(str(v) for v in padded_row[:len(headers)]) + " |\n")

            output.write("\n")

    def _write_metadata(self, output: StringIO, metadata: Dict[str, Any]) -> None:
        """Write metadata section."""
        output.write(f"{'#' * (self.heading_level + 1)} Metadata\n\n")

        for key, value in metadata.items():
            output.write(f"- **{key}**: {value}\n")

        output.write("\n")

    def _write_sources(self, output: StringIO, sources: List[Dict[str, Any]]) -> None:
        """Write sources/citations."""
        output.write(f"{'#' * (self.heading_level + 1)} Sources\n\n")

        for i, source in enumerate(sources, 1):
            doc_id = source.get("document_id", "Unknown")
            page = source.get("page_number", "N/A")
            chunk = source.get("chunk_id", "N/A")
            score = source.get("score", "N/A")

            output.write(
                f"{i}. **Document**: {doc_id}, **Page**: {page}, "
                f"**Chunk**: {chunk}, **Relevance**: {score}\n"
            )

        output.write("\n")

    def _make_anchor(self, text: str) -> str:
        """Convert text to GitHub-style anchor link.
        
        Args:
            text: Text to convert
            
        Returns:
            Anchor-ready string
        """
        # Lowercase and replace spaces with hyphens
        anchor = text.lower().replace(" ", "-")
        # Remove special characters except hyphens
        anchor = "".join(c for c in anchor if c.isalnum() or c == "-")
        return anchor

    def to_html(self, data: OutputData) -> str:
        """Convert formatted Markdown to HTML.
        
        Args:
            data: Data to format
            
        Returns:
            HTML string
            
        Raises:
            FormatterError: If markdown2 is not available
        """
        if not MARKDOWN2_AVAILABLE:
            raise FormatterError(
                "markdown2 not available for HTML conversion",
                formatter=self.format_name,
                details={"install": "pip install markdown2"},
            )

        markdown_content = self.format(data).decode("utf-8")

        # Convert to HTML with extras
        extras = ["tables", "fenced-code-blocks", "header-ids", "toc"]
        if self.code_highlighting:
            extras.append("code-friendly")

        html = markdown2.markdown(markdown_content, extras=extras)
        return html
