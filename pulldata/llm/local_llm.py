"""
Local LLM implementation using Hugging Face transformers.

Supports quantization (int8, int4) and GPU acceleration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TextIteratorStreamer,
)
from threading import Thread

from pulldata.core.exceptions import LLMError
from pulldata.llm.base import BaseLLM, LLMResponse


class LocalLLM(BaseLLM):
    """
    Local LLM using Hugging Face transformers.

    Supports quantization and GPU acceleration for efficient inference.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-3B-Instruct",
        device: str = "cuda",
        quantization: str = "int8",
        cache_dir: Optional[str | Path] = None,
        trust_remote_code: bool = True,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        **kwargs,
    ):
        """
        Initialize local LLM.

        Args:
            model_name: Model name or path
            device: Device to use ('cuda' or 'cpu')
            quantization: Quantization type ('none', 'int8', 'int4', 'fp16')
            cache_dir: Directory to cache models
            trust_remote_code: Whether to trust remote code
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            **kwargs: Additional model parameters
        """
        super().__init__(
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs,
        )

        self.device = device
        self.quantization = quantization
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.trust_remote_code = trust_remote_code
        self.top_k = top_k

        # Load model and tokenizer
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """
        Load model and tokenizer with appropriate quantization.

        Raises:
            LLMError: If model loading fails
        """
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=self.trust_remote_code,
            )

            # Set padding token if not set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Configure quantization
            quantization_config = None
            torch_dtype = torch.float32

            if self.quantization == "int8":
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_threshold=6.0,
                )
            elif self.quantization == "int4":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
            elif self.quantization == "fp16":
                torch_dtype = torch.float16
            elif self.quantization != "none":
                raise ValueError(
                    f"Invalid quantization: {self.quantization}. "
                    f"Choose from: none, int8, int4, fp16"
                )

            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                torch_dtype=torch_dtype,
                device_map="auto" if self.device == "cuda" else None,
                cache_dir=self.cache_dir,
                trust_remote_code=self.trust_remote_code,
            )

            # Move to device if not using quantization
            if quantization_config is None and self.device == "cuda":
                if torch.cuda.is_available():
                    self.model = self.model.to(self.device)
                else:
                    self.device = "cpu"
                    self.model = self.model.to("cpu")

            self.model.eval()

        except Exception as e:
            raise LLMError(
                f"Failed to load model '{self.model_name}': {e}",
                details={"model": self.model_name, "error": str(e)},
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
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse object
        """
        # Use defaults if not specified
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature if temperature is not None else self.temperature
        top_p = top_p if top_p is not None else self.top_p

        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
            ).to(self.model.device)

            prompt_tokens = inputs["input_ids"].shape[1]

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=self.top_k,
                    do_sample=temperature > 0,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    **kwargs,
                )

            # Decode output
            generated_text = self.tokenizer.decode(
                outputs[0][prompt_tokens:],
                skip_special_tokens=True,
            )

            completion_tokens = outputs.shape[1] - prompt_tokens

            return LLMResponse(
                text=generated_text,
                prompt=prompt,
                model=self.model_name,
                tokens_used=prompt_tokens + completion_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason="stop",
                metadata={
                    "device": str(self.model.device),
                    "quantization": self.quantization,
                },
            )

        except Exception as e:
            raise LLMError(
                f"Text generation failed: {e}",
                details={"prompt": prompt[:100], "error": str(e)},
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
            **kwargs: Additional generation parameters

        Yields:
            Text chunks as they are generated
        """
        # Use defaults if not specified
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature if temperature is not None else self.temperature
        top_p = top_p if top_p is not None else self.top_p

        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
            ).to(self.model.device)

            # Set up streamer
            streamer = TextIteratorStreamer(
                self.tokenizer,
                skip_prompt=True,
                skip_special_tokens=True,
            )

            # Generation kwargs
            generation_kwargs = {
                **inputs,
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": self.top_k,
                "do_sample": temperature > 0,
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
                "streamer": streamer,
                **kwargs,
            }

            # Start generation in separate thread
            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()

            # Yield text chunks
            for text_chunk in streamer:
                yield text_chunk

            thread.join()

        except Exception as e:
            raise LLMError(
                f"Streaming generation failed: {e}",
                details={"prompt": prompt[:100], "error": str(e)},
            )

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        return len(tokens)

    def unload(self) -> None:
        """
        Unload model from memory.
        """
        if self.model is not None:
            del self.model
            self.model = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
