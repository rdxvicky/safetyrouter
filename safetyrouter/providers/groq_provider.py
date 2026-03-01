"""Groq provider (Mixtral, LLaMA, etc. — free tier available)."""
from typing import AsyncGenerator, Optional

from .base import BaseProvider


class GroqProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "mixtral-8x7b-32768"):
        try:
            from groq import AsyncGroq
        except ImportError:
            raise ImportError(
                "groq package not installed. Run: pip install 'safetyrouter[groq]'"
            )
        self.client = AsyncGroq(api_key=api_key)
        self.model = model

    async def complete(self, text: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": text})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content

    async def stream(
        self, text: str, system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": text})

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
