"""Google provider (Gemini models)."""
from typing import AsyncGenerator, Optional

from .base import BaseProvider


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
        return response.text

    async def stream(
        self, text: str, system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        prompt = f"{system_prompt}\n\n{text}" if system_prompt else text
        async for chunk in await self.model.generate_content_async(prompt, stream=True):
            if chunk.text:
                yield chunk.text
