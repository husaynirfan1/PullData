"""Base classes and utilities for output formatters.

This module provides the abstract base class that all formatters must implement,
along with common utilities for file I/O, validation, and configuration.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from pulldata.core.exceptions import  PullDataError



class FormatterError(PullDataError):
    """Exception raised by formatters."""

    def __init__(self, message: str, formatter: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details or {})
        self.formatter = formatter


@dataclass
class FormatConfig:
    """Configuration for output formatters.
    
    Attributes:
        output_path: Path where the output file will be saved
        include_metadata: Whether to include metadata in output
        include_sources: Whether to include source citations
        template_path: Optional path to custom template
        custom_options: Format-specific options
    """

    output_path: Optional[Path] = None
    include_metadata: bool = True
    include_sources: bool = True
    template_path: Optional[Path] = None
    custom_options: Dict[str, Any] = field(default_factory=dict)


class OutputData(BaseModel):
    """Standard data structure for formatter input.
    
    This provides a consistent interface for all formatters.
    """

    title: str = Field(description="Document title")
    content: str = Field(description="Main content/answer")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source citations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted tables")
    sections: List[Dict[str, Any]] = Field(default_factory=list, description="Document sections")


class OutputFormatter(ABC):
    """Abstract base class for all output formatters.
    
    All formatters must implement the format() method and provide
    a file extension property.
    """

    def __init__(self, config: Optional[FormatConfig] = None):
        """Initialize the formatter.
        
        Args:
            config: Optional configuration for the formatter
        """
        self.config = config or FormatConfig()

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for this format (e.g., '.xlsx', '.md')."""
        pass

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Human-readable name of the format (e.g., 'Excel', 'Markdown')."""
        pass

    @abstractmethod
    def format(self, data: OutputData) -> bytes:
        """Format the data and return as bytes.
        
        Args:
            data: The data to format
            
        Returns:
            Formatted output as bytes
            
        Raises:
            FormatterError: If formatting fails
        """
        pass

    def save(self, data: OutputData, output_path: Optional[Union[str, Path]] = None) -> Path:
        """Format and save data to a file.
        
        Args:
            data: The data to format
            output_path: Path to save the file. If None, uses config.output_path
            
        Returns:
            Path to the saved file
            
        Raises:
            FormatterError: If formatting or saving fails
        """
        # Determine output path
        path = output_path or self.config.output_path
        if path is None:
            raise FormatterError(
                "No output path specified",
                formatter=self.format_name,
                details={"hint": "Provide output_path argument or config.output_path"},
            )

        path = Path(path)

        # Ensure it has the correct extension
        if not path.suffix:
            path = path.with_suffix(self.file_extension)
        elif path.suffix != self.file_extension:
            raise FormatterError(
                f"Output path has wrong extension: {path.suffix}",
                formatter=self.format_name,
                details={
                    "expected": self.file_extension,
                    "got": path.suffix,
                    "path": str(path),
                },
            )

        # Create parent directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Format and save
        try:
            formatted_data = self.format(data)
            path.write_bytes(formatted_data)
            return path
        except Exception as e:
            if isinstance(e, FormatterError):
                raise
            raise FormatterError(
                f"Failed to save {self.format_name} file: {e}",
                formatter=self.format_name,
                details={"error": str(e), "path": str(path)},
            ) from e

    def validate_output_path(self, path: Union[str, Path]) -> Path:
        """Validate and normalize output path.
        
        Args:
            path: Path to validate
            
        Returns:
            Normalized Path object
            
        Raises:
            FormatterError: If path is invalid
        """
        path = Path(path)

        # Check if parent directory exists or can be created
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FormatterError(
                f"Cannot create parent directory: {path.parent}",
                formatter=self.format_name,
                details={"error": str(e)},
            ) from e

        return path

    def get_default_filename(self, base_name: str = "output") -> str:
        """Generate a default filename with proper extension.
        
        Args:
            base_name: Base name for the file (without extension)
            
        Returns:
            Filename with extension
        """
        return f"{base_name}{self.file_extension}"
