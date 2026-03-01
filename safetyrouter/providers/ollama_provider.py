"""Ollama provider — fully local, no API keys needed."""
from typing import AsyncGenerator, Optional

import ollama

from .base import BaseProvider


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

        response = ollama.chat(
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

        for chunk in ollama.chat(
            model=self.model,
            messages=messages,
            stream=True,
        ):
            content = chunk["message"]["content"]
            if content:
                yield content
