"""Anthropic provider (Claude models)."""
import logging
from typing import AsyncGenerator, Optional

from .base import BaseProvider

logger = logging.getLogger(__name__)


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

        # Issue #5: guard against empty/filtered responses
        if not response.content:
            raise RuntimeError(
                f"Anthropic returned empty content (stop_reason={response.stop_reason})"
            )
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

        # Issue #5: catch mid-stream errors
        try:
            async with self.client.messages.stream(**kwargs) as stream:
                async for text_chunk in stream.text_stream:
                    yield text_chunk
        except Exception as e:
            logger.error(f"Anthropic stream error: {e}")
            raise
