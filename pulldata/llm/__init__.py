"""
LLM integration for PullData.

Provides interfaces for both local and API-based language models.
"""

from pulldata.llm.base import BaseLLM, LLMResponse
from pulldata.llm.local_llm import LocalLLM
from pulldata.llm.api_llm import APILLM
from pulldata.llm.prompts import PromptTemplate, PromptManager

__all__ = [
    "BaseLLM",
    "LLMResponse",
    "LocalLLM",
    "APILLM",
    "PromptTemplate",
    "PromptManager",
]
