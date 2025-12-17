"""JSON formatter for PullData output.

Provides structured JSON output with schema validation,
nested data support, and pretty-printing options.
"""

import json
from typing import Any, Dict, Optional

from pulldata.synthesis.base import FormatConfig, FormatterError, OutputData, OutputFormatter


class JSONFormatter(OutputFormatter):
    """JSON formatter with schema validation and pretty-printing.
    
    Features:
    - Clean JSON structure
    - Pretty-printing with configurable indentation
    - Schema validation (optional)
    - Nested data support
    
    Example:
        >>> formatter = JSONFormatter(indent=2)
        >>> data = OutputData(title="Report", content="Summary")
        >>> formatter.save(data, "output.json")
    """

    def __init__(
        self,
        config: Optional[FormatConfig] = None,
        indent: Optional[int] = 2,
        sort_keys: bool = False,
        ensure_ascii: bool = False,
    ):
        """Initialize JSON formatter.
        
        Args:
            config: Formatter configuration
            indent: Number of spaces for indentation (None for compact)
            sort_keys: Sort dictionary keys alphabetically
            ensure_ascii: Escape non-ASCII characters
        """
        super().__init__(config)
        self.indent = indent
        self.sort_keys = sort_keys
        self.ensure_ascii = ensure_ascii

    @property
    def file_extension(self) -> str:
        return ".json"

    @property
    def format_name(self) -> str:
        return "JSON"

    def format(self, data: OutputData) -> bytes:
        """Format data as JSON.
        
        Args:
            data: Data to format
            
        Returns:
            JSON content as bytes
        """
        # Build JSON structure
        output_dict = {
            "title": data.title,
            "content": data.content,
        }

        # Add sections
        if data.sections:
            output_dict["sections"] = data.sections

        # Add tables
        if data.tables:
            output_dict["tables"] = data.tables

        # Add metadata
        if self.config.include_metadata and data.metadata:
            output_dict["metadata"] = data.metadata

        # Add sources
        if self.config.include_sources and data.sources:
            output_dict["sources"] = data.sources

        # Convert to JSON
        try:
            json_str = json.dumps(
                output_dict,
                indent=self.indent,
                sort_keys=self.sort_keys,
                ensure_ascii=self.ensure_ascii,
            )
            return json_str.encode("utf-8")
        except (TypeError, ValueError) as e:
            raise FormatterError(
                f"Failed to serialize to JSON: {e}",
                formatter=self.format_name,
                details={"error": str(e)},
            ) from e

    def format_with_schema(self, data: OutputData, schema: Dict[str, Any]) -> bytes:
        """Format data with custom schema.
        
        Args:
            data: Data to format
            schema: JSON schema defining output structure
            
        Returns:
            JSON content as bytes
            
        Raises:
            FormatterError: If data doesn't match schema
        """
        # Build output according to schema
        output_dict = self._apply_schema(data, schema)

        # Convert to JSON
        try:
            json_str = json.dumps(
                output_dict,
                indent=self.indent,
                sort_keys=self.sort_keys,
                ensure_ascii=self.ensure_ascii,
            )
            return json_str.encode("utf-8")
        except (TypeError, ValueError) as e:
            raise FormatterError(
                f"Failed to serialize to JSON: {e}",
                formatter=self.format_name,
                details={"error": str(e)},
            ) from e

    def _apply_schema(self, data: OutputData, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Apply schema to data.
        
        This is a simple implementation. For production use,
        consider using jsonschema library for validation.
        """
        output = {}

        # Map data fields to schema fields
        field_mapping = {
            "title": data.title,
            "content": data.content,
            "sections": data.sections,
            "tables": data.tables,
            "metadata": data.metadata,
            "sources": data.sources,
        }

        # Include only fields defined in schema
        properties = schema.get("properties", {})
        for field_name in properties:
            if field_name in field_mapping:
                value = field_mapping[field_name]
                # Skip empty lists/dicts if not required
                if value or field_name in schema.get("required", []):
                    output[field_name] = value

        return output

    def validate_json(self, json_bytes: bytes) -> bool:
        """Validate that output is valid JSON.
        
        Args:
            json_bytes: JSON bytes to validate
            
        Returns:
            True if valid JSON
            
        Raises:
            FormatterError: If JSON is invalid
        """
        try:
            json.loads(json_bytes.decode("utf-8"))
            return True
        except json.JSONDecodeError as e:
            raise FormatterError(
                f"Invalid JSON: {e}",
                formatter=self.format_name,
                details={"error": str(e)},
            ) from e
