"""
Base LLM interface for PullData.

Defines the abstract interface for all LLM implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional


@dataclass
class LLMResponse:
    """
    Represents a response from an LLM.
    """

    text: str
    """Generated text"""

    prompt: str
    """Input prompt"""

    model: str
    """Model name used"""

    tokens_used: Optional[int] = None
    """Total tokens used (prompt + completion)"""

    prompt_tokens: Optional[int] = None
    """Tokens in prompt"""

    completion_tokens: Optional[int] = None
    """Tokens in completion"""

    finish_reason: Optional[str] = None
    """Reason for completion (stop, length, etc.)"""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata"""

    def __repr__(self) -> str:
        return f"LLMResponse(text='{self.text[:50]}...', model='{self.model}')"


class BaseLLM(ABC):
    """
    Abstract base class for LLM implementations.

    All LLM providers (local, API-based) must implement this interface.
    """

    def __init__(
        self,
        model_name: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs,
    ):
        """
        Initialize LLM.

        Args:
            model_name: Name/path of the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            top_p: Nucleus sampling parameter (0.0-1.0)
            **kwargs: Additional model-specific parameters
        """
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.kwargs = kwargs

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[list[str]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate text from a prompt.

        Args:
            prompt: Input prompt
            max_tokens: Override default max_tokens
            temperature: Override default temperature
            top_p: Override default top_p
            stop: List of stop sequences
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse object
        """
        pass

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[list[str]] = None,
        **kwargs,
    ) -> Iterator[str]:
        """
        Generate text with streaming.

        Args:
            prompt: Input prompt
            max_tokens: Override default max_tokens
            temperature: Override default temperature
            top_p: Override default top_p
            stop: List of stop sequences
            **kwargs: Additional generation parameters

        Yields:
            Text chunks as they are generated
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        pass

    def update_config(
        self,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        **kwargs,
    ) -> None:
        """
        Update generation configuration.

        Args:
            max_tokens: New max_tokens value
            temperature: New temperature value
            top_p: New top_p value
            **kwargs: Additional parameters to update
        """
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature
        if top_p is not None:
            self.top_p = top_p
        self.kwargs.update(kwargs)

    def get_config(self) -> dict[str, Any]:
        """
        Get current configuration.

        Returns:
            Configuration dictionary
        """
        return {
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            **self.kwargs,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model='{self.model_name}')"
