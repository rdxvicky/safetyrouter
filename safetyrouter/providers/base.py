"""Abstract base class for LLM providers."""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional


class BaseProvider(ABC):
    """
    All providers must implement `complete`. Streaming is optional —
    the default falls back to yielding the full response as one chunk.
    """

    @abstractmethod
    async def complete(self, text: str, system_prompt: Optional[str] = None) -> str:
        """Return the full completion string."""
        ...

    async def stream(
        self, text: str, system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Yield completion tokens. Default: single chunk (not truly streaming)."""
        content = await self.complete(text, system_prompt)
        yield content
