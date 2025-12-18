"""
API-based LLM implementation using OpenAI-compatible APIs.

Supports OpenAI API, local servers (LM Studio, Ollama), and other compatible providers.
"""

from __future__ import annotations

import time
from typing import Iterator, Optional

import requests

from pulldata.core.exceptions import LLMError
from pulldata.llm.base import BaseLLM, LLMResponse


class APILLM(BaseLLM):
    """
    API-based LLM using OpenAI-compatible endpoints.

    Works with:
    - OpenAI API
    - Local servers (LM Studio, Ollama with OpenAI compatibility)
    - Other OpenAI-compatible providers
    """

    def __init__(
        self,
        model_name: str = "qwen3-1.7b",
        base_url: str = "http://100.67.99.40:1234",
        api_key: str = "sk-dummy",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        timeout: int = 60,
        max_retries: int = 3,
        **kwargs,
    ):
        """
        Initialize API-based LLM.

        Args:
            model_name: Model name (e.g., 'gpt-3.5-turbo', 'local-model')
            base_url: API base URL
            api_key: API key (use 'sk-dummy' for local servers)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            **kwargs: Additional API parameters
        """
        super().__init__(
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs,
        )

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

        # Set up session
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

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
            **kwargs: Additional API parameters

        Returns:
            LLMResponse object
        """
        # Use defaults if not specified
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature if temperature is not None else self.temperature
        top_p = top_p if top_p is not None else self.top_p

        # Build request payload
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False,
        }

        if stop:
            payload["stop"] = stop

        # Add custom parameters
        payload.update(kwargs)

        # Make request with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    data = response.json()

                    # Extract response
                    choice = data["choices"][0]
                    generated_text = choice["message"]["content"]
                    finish_reason = choice.get("finish_reason", "stop")

                    # Extract token usage
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens")
                    completion_tokens = usage.get("completion_tokens")
                    total_tokens = usage.get("total_tokens")

                    return LLMResponse(
                        text=generated_text,
                        prompt=prompt,
                        model=self.model_name,
                        tokens_used=total_tokens,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        finish_reason=finish_reason,
                        metadata={
                            "base_url": self.base_url,
                            "attempt": attempt + 1,
                        },
                    )

                else:
                    error_msg = response.text
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", error_msg)
                    except:
                        pass

                    last_error = f"API error (status {response.status_code}): {error_msg}"

            except requests.Timeout:
                last_error = f"Request timeout after {self.timeout}s"
            except requests.RequestException as e:
                last_error = f"Request failed: {e}"
            except Exception as e:
                last_error = f"Unexpected error: {e}"

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)

        # All retries failed
        raise LLMError(
            f"Failed to generate response after {self.max_retries} attempts: {last_error}",
            details={
                "model": self.model_name,
                "base_url": self.base_url,
                "error": last_error,
            },
        )

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
            **kwargs: Additional API parameters

        Yields:
            Text chunks as they are generated
        """
        # Use defaults if not specified
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature if temperature is not None else self.temperature
        top_p = top_p if top_p is not None else self.top_p

        # Build request payload
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": True,
        }

        if stop:
            payload["stop"] = stop

        # Add custom parameters
        payload.update(kwargs)

        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout,
                stream=True,
            )

            if response.status_code != 200:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", error_msg)
                except:
                    pass
                raise LLMError(
                    f"API error (status {response.status_code}): {error_msg}",
                    details={"model": self.model_name, "base_url": self.base_url},
                )

            # Stream response
            for line in response.iter_lines():
                if not line:
                    continue

                line = line.decode("utf-8")

                # Skip non-data lines
                if not line.startswith("data: "):
                    continue

                # Remove 'data: ' prefix
                data_str = line[6:]

                # Check for end of stream
                if data_str.strip() == "[DONE]":
                    break

                try:
                    import json

                    data = json.loads(data_str)
                    delta = data["choices"][0]["delta"]

                    # Extract content
                    if "content" in delta:
                        yield delta["content"]

                except json.JSONDecodeError:
                    continue
                except (KeyError, IndexError):
                    continue

        except requests.RequestException as e:
            raise LLMError(
                f"Streaming request failed: {e}",
                details={"model": self.model_name, "error": str(e)},
            )

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Uses approximate estimation (4 chars ≈ 1 token).
        For accurate counting, use tiktoken library.

        Args:
            text: Input text

        Returns:
            Approximate number of tokens
        """
        # Simple approximation: ~4 characters per token
        # For more accuracy, use tiktoken library
        return len(text) // 4

    def test_connection(self) -> bool:
        """
        Test connection to API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/models",
                timeout=5,
            )
            return response.status_code == 200
        except:
            return False
