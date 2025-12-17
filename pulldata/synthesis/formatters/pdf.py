"""PDF formatter for PullData output.

Creates PDF documents using reportlab with support for
styling, tables, and page layout.
"""

from io import BytesIO
from typing import Any, Dict, List, Optional

from pulldata.synthesis.base import FormatConfig, FormatterError, OutputData, OutputFormatter

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFFormatter(OutputFormatter):
    """PDF formatter using reportlab.
    
    Features:
    - Document layout and styling
    - Paragraph and heading support
    - Table rendering
    - Page numbering and headers/footers
    
    Example:
        >>> formatter = PDFFormatter()
        >>> data = OutputData(title="Report", content="Summary", tables=[...])
        >>> formatter.save(data, "output.pdf")
    """

    def __init__(
        self,
        config: Optional[FormatConfig] = None,
        page_size: Any = None,
        margin: float = 0.75,
    ):
        """Initialize PDF formatter.
        
        Args:
            config: Formatter configuration
            page_size: Page size tuple (width, height). Default is letter size
            margin: Page margin in inches
        """
        super().__init__(config)

        if not REPORTLAB_AVAILABLE:
            raise FormatterError(
                "reportlab not available",
                formatter="PDF",
                details={"install": "pip install reportlab"},
            )

        self.page_size = page_size or letter
        self.margin = margin * inch

    @property
    def file_extension(self) -> str:
        return ".pdf"

    @property
    def format_name(self) -> str:
        return "PDF"

    def format(self, data: OutputData) -> bytes:
        """Format data as PDF document.
        
        Args:
            data: Data to format
            
        Returns:
            PDF file as bytes
        """
        if not REPORTLAB_AVAILABLE:
            raise FormatterError(
                "reportlab not available",
                formatter="PDF",
                details={"install": "pip install reportlab"},
            )

        # Create PDF buffer
        buffer = BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        # Get styles
        styles = getSampleStyleSheet()

        # Build story (document content)
        story = []

        # Title
        story.append(Paragraph(data.title, styles["Title"]))
        story.append(Spacer(1, 12))

        # Main content
        if data.content:
            for paragraph in data.content.split("\n\n"):
                if paragraph.strip():
                    story.append(Paragraph(paragraph, styles["BodyText"]))
                    story.append(Spacer(1, 12))

        # Sections
        if data.sections:
            for section in data.sections:
                story.append(PageBreak())
                story.append(Paragraph(section.get("title", "Section"), styles["Heading1"]))
                story.append(Spacer(1, 12))

                content = section.get("content", "")
                for paragraph in content.split("\n\n"):
                    if paragraph.strip():
                        story.append(Paragraph(paragraph, styles["BodyText"]))
                        story.append(Spacer(1, 12))

        # Tables
        if data.tables:
            story.append(PageBreak())
            story.append(Paragraph("Tables", styles["Heading1"]))
            story.append(Spacer(1, 12))

            for i, table_data in enumerate(data.tables):
                table_name = table_data.get("name", f"Table {i+1}")
                story.append(Paragraph(table_name, styles["Heading2"]))
                story.append(Spacer(1, 12))

                # Create table
                pdf_table = self._create_table(table_data)
                if pdf_table:
                    story.append(pdf_table)
                    story.append(Spacer(1, 12))

        # Metadata
        if self.config.include_metadata and data.metadata:
            story.append(PageBreak())
            story.append(Paragraph("Metadata", styles["Heading1"]))
            story.append(Spacer(1, 12))

            for key, value in data.metadata.items():
                story.append(Paragraph(f"<b>{key}:</b> {value}", styles["BodyText"]))
                story.append(Spacer(1, 6))

        # Sources
        if self.config.include_sources and data.sources:
            story.append(PageBreak())
            story.append(Paragraph("Sources", styles["Heading1"]))
            story.append(Spacer(1, 12))

            for i, source in enumerate(data.sources, 1):
                doc_id = source.get("document_id", "Unknown")
                page = source.get("page_number", "N/A")
                text = f"{i}. <b>Document:</b> {doc_id}, <b>Page:</b> {page}"
                story.append(Paragraph(text, styles["BodyText"]))
                story.append(Spacer(1, 6))

        # Build PDF
        doc.build(story)

        buffer.seek(0)
        return buffer.read()

    def _create_table(self, table_data: Dict[str, Any]) -> Optional[Any]:
        """Create a reportlab Table object.
        
        Args:
            table_data: Table data dictionary
            
        Returns:
            Table object or None if no data
        """
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])

        if not headers and not rows:
            return None

        # Build table data
        table_rows = []
        if headers:
            table_rows.append(headers)
        table_rows.extend(rows)

        # Create table
        table = Table(table_rows)

        # Apply styling
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey) if headers else None,
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke) if headers else None,
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold") if headers else None,
            ("FONTSIZE", (0, 0), (-1, 0), 12) if headers else None,
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12) if headers else None,
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige) if headers else (0, 0),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ROWBACKGROUNDS", (0, 1 if headers else 0), (-1, -1), [colors.white, colors.lightgrey]),
        ]

        # Filter out None commands
        style_commands = [cmd for cmd in style_commands if cmd is not None]

        table.setStyle(TableStyle(style_commands))

        return table
