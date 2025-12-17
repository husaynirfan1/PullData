"""
PullData: Turn Documents into Deliverables

A high-performance, text-based RAG system optimized for extracting structured data
from documents and generating versatile output formats.
"""

__version__ = "0.1.0"
__author__ = "PullData Team"

from pulldata.pipeline.orchestrator import PullData

__all__ = [
    "__version__",
    "__author__",
    "PullData",
]
