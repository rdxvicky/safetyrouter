"""Google provider (Gemini models)."""
import logging
from typing import AsyncGenerator, Optional

from .base import BaseProvider

logger = logging.getLogger(__name__)


class GoogleProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        try:
            import google.generativeai as genai
            self._genai = genai
        except ImportError:
            raise ImportError(
                "google-generativeai not installed. Run: pip install 'safetyrouter[google]'"
            )
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)

    async def complete(self, text: str, system_prompt: Optional[str] = None) -> str:
        prompt = f"{system_prompt}\n\n{text}" if system_prompt else text
        response = await self.model.generate_content_async(prompt)

        # Issue #5: Gemini returns None for response.text when content is filtered
        if response.text is None:
            raise RuntimeError(
                "Google Gemini returned no text content — response may have been filtered."
            )
        return response.text

    async def stream(
        self, text: str, system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        prompt = f"{system_prompt}\n\n{text}" if system_prompt else text

        # Issue #5: catch mid-stream errors
        try:
            async for chunk in await self.model.generate_content_async(prompt, stream=True):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Google Gemini stream error: {e}")
            raise
