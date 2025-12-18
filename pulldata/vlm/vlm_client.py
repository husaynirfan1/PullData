"""Vision Language Model (VLM) client for OCR and image understanding.

Supports OpenAI-compatible VLM APIs (LM Studio, OpenAI GPT-4 Vision, etc.)
"""

from __future__ import annotations

import base64
import time
from io import BytesIO
from pathlib import Path
from typing import Optional

import requests
from PIL import Image

from pulldata.core.exceptions import LLMError


class VLMClient:
    """
    Vision Language Model client for OCR and image analysis.
    
    Compatible with OpenAI-compatible vision APIs including:
    - LM Studio (SmolVLM, LLaVA, etc.)
    - OpenAI GPT-4 Vision
    - Other OpenAI-compatible VLM servers
    """

    def __init__(
        self,
        model_name: str = "smolvlm-500m-instruct",
        base_url: str = "http://localhost:1234/v1",
        api_key: str = "sk-dummy",
        timeout: int = 120,  # VLM inference is slower
        max_retries: int = 3,
        **kwargs,
    ):
        """
        Initialize VLM client.

        Args:
            model_name: Model name (e.g., 'smolvlm-500m-instruct', 'gpt-4-vision-preview')
            base_url: API base URL
            api_key: API key (use 'sk-dummy' for local servers like LM Studio)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            **kwargs: Additional parameters
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.kwargs = kwargs

        # Setup session
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def analyze_image(
        self,
        image: Image.Image | bytes | Path | str,
        prompt: str = "Extract all text from this image. Return only the extracted text, nothing else.",
        max_tokens: Optional[int] = 2048,
        temperature: float = 0.1,  # Lower temperature for OCR
        **kwargs,
    ) -> str:
        """
        Analyze an image and extract text or information.

        Args:
            image: PIL Image, bytes, or path to image file
            prompt: Instruction for the VLM
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional API parameters

        Returns:
            Extracted text or analysis result

        Raises:
            LLMError: If analysis fails
        """
        # Convert image to base64
        image_base64 = self._encode_image(image)

        # Build request payload
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                        },
                    ],
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        # Merge additional parameters
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
                    choice = data["choices"][0]
                    extracted_text = choice["message"]["content"]
                    return extracted_text.strip()

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
            f"Failed to analyze image after {self.max_retries} attempts: {last_error}",
            details={
                "model": self.model_name,
                "base_url": self.base_url,
                "error": last_error,
            },
        )

    def ocr_pdf_page(
        self,
        page_image: Image.Image,
        page_number: int,
    ) -> str:
        """
        Perform OCR on a PDF page image.

        Args:
            page_image: PIL Image of the PDF page
            page_number: Page number for context

        Returns:
            Extracted text from the page
        """
        prompt = f"""Extract all text from this PDF page (page {page_number}).

Instructions:
- Return ONLY the extracted text, exactly as it appears
- Preserve formatting, line breaks, and structure
- Do not add any explanations or comments
- If the page is blank or has no text, return an empty string"""

        return self.analyze_image(
            image=page_image,
            prompt=prompt,
            max_tokens=2048,
            temperature=0.1,
        )

    def _encode_image(self, image: Image.Image | bytes | Path | str) -> str:
        """
        Encode image to base64 string.

        Args:
            image: PIL Image, bytes, or path to image

        Returns:
            Base64 encoded image string
        """
        # Handle different input types
        if isinstance(image, (str, Path)):
            # Load from file
            image = Image.open(image)

        if isinstance(image, Image.Image):
            # Convert PIL Image to bytes
            buffer = BytesIO()
            # Convert to RGB if necessary
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            image.save(buffer, format="JPEG", quality=95)
            image_bytes = buffer.getvalue()
        elif isinstance(image, bytes):
            image_bytes = image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

        # Encode to base64
        return base64.b64encode(image_bytes).decode("utf-8")

    def test_connection(self) -> bool:
        """
        Test connection to VLM API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create a small test image (1x1 pixel)
            test_image = Image.new("RGB", (1, 1), color="white")
            
            # Try a simple request
            result = self.analyze_image(
                test_image,
                prompt="What color is this image?",
                max_tokens=50,
            )
            return len(result) > 0
        except:
            return False
