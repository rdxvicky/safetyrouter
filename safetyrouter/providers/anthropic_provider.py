"""Anthropic provider (Claude models)."""
from typing import AsyncGenerator, Optional

from .base import BaseProvider


class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "claude-opus-4-6"):
        try:
            import anthropic
            self._anthropic = anthropic
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Run: pip install 'safetyrouter[anthropic]'"
            )
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, text: str, system_prompt: Optional[str] = None) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": text}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    async def stream(
        self, text: str, system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": text}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        async with self.client.messages.stream(**kwargs) as stream:
            async for text_chunk in stream.text_stream:
                yield text_chunk
