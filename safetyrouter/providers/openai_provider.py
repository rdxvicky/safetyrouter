"""OpenAI provider (GPT-4o, GPT-4, etc.)"""
from typing import AsyncGenerator, Optional

from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "openai package not installed. Run: pip install 'safetyrouter[openai]'"
            )
        self.client = AsyncOpenAI(api_key=api_key)
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

        async with await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        ) as response:
            async for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
