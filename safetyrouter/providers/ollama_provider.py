"""Ollama provider — fully local, no API keys needed."""
import asyncio
import logging
from typing import AsyncGenerator, Optional

import ollama

from .base import BaseProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Use any locally running Ollama model as a target provider."""

    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    async def complete(self, text: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": text})

        # Issue #6: wrap sync ollama call in a thread to avoid blocking the event loop
        response = await asyncio.to_thread(
            ollama.chat,
            model=self.model,
            messages=messages,
            options={"temperature": 0.7},
        )
        return response["message"]["content"]

    async def stream(
        self, text: str, system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": text})

        # Issue #6: collect chunks in a thread to avoid blocking the event loop
        # Issue #5: catch stream errors and surface them clearly
        try:
            chunks = await asyncio.to_thread(
                lambda: list(ollama.chat(model=self.model, messages=messages, stream=True))
            )
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            raise

        for chunk in chunks:
            content = chunk["message"]["content"]
            if content:
                yield content
