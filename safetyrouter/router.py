"""
Core SafetyRouter — the main Python SDK interface.

Usage:
    from safetyrouter import SafetyRouter

    router = SafetyRouter()
    response = await router.route("Should women be paid less?")
    print(response.selected_model)   # "claude"
    print(response.content)          # Claude's response
"""
import logging
import time
from typing import Any, AsyncGenerator, Dict, Optional

from .classifier import BiasClassifier
from .config import SafetyRouterConfig
from .models import BiasCategory, ModelProvider, RouteResponse
from .providers.base import BaseProvider

logger = logging.getLogger(__name__)

# Default routing table: bias category → (ModelProvider, accuracy_pct)
DEFAULT_ROUTING: Dict[str, tuple] = {
    cat.key: (cat.provider, cat.accuracy) for cat in BiasCategory
}


class SafetyRouter:
    """
    Routes prompts to the best LLM based on detected bias category.

    1. Classify bias using gemma3n locally (no API key needed for this step)
    2. Look up the best provider for that bias type
    3. Send the prompt to that provider and return the response

    Args:
        config: SafetyRouterConfig instance. If None, loads from environment.
        providers: Custom provider instances keyed by ModelProvider value.
                   If None, providers are auto-instantiated from config/env keys.

    Example — minimal setup (only OpenAI key needed for gpt4 routing):
        router = SafetyRouter()
        response = await router.route("text here")

    Example — custom providers:
        router = SafetyRouter(providers={"claude": AnthropicProvider(api_key="...")})
    """

    def __init__(
        self,
        config: Optional[SafetyRouterConfig] = None,
        providers: Optional[Dict[str, BaseProvider]] = None,
    ):
        self.config = config or SafetyRouterConfig.from_env()
        self.classifier = BiasClassifier(model=self.config.classifier_model)
        self._providers: Dict[str, BaseProvider] = providers or {}
        self._routing_table = self._build_routing_table()

    def _build_routing_table(self) -> Dict[str, tuple]:
        """Merge default routing with any custom overrides from config."""
        table = dict(DEFAULT_ROUTING)
        for category, provider_key in self.config.custom_routing.items():
            if category in table:
                _, accuracy = table[category]
                table[category] = (ModelProvider(provider_key), accuracy)
            else:
                table[category] = (ModelProvider(provider_key), None)
        return table

    def _get_provider(self, provider: ModelProvider) -> BaseProvider:
        """Lazily instantiate a provider from config if not already created."""
        key = provider.value
        if key in self._providers:
            return self._providers[key]

        cfg = self.config
        if provider == ModelProvider.GPT4:
            if not cfg.openai_api_key:
                raise ValueError("OPENAI_API_KEY not set. Cannot use gpt4 provider.")
            from .providers.openai_provider import OpenAIProvider
            self._providers[key] = OpenAIProvider(cfg.openai_api_key, cfg.openai_model)

        elif provider == ModelProvider.CLAUDE:
            if not cfg.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not set. Cannot use claude provider.")
            from .providers.anthropic_provider import AnthropicProvider
            self._providers[key] = AnthropicProvider(cfg.anthropic_api_key, cfg.anthropic_model)

        elif provider == ModelProvider.GEMINI:
            if not cfg.google_api_key:
                raise ValueError("GOOGLE_API_KEY not set. Cannot use gemini provider.")
            from .providers.google_provider import GoogleProvider
            self._providers[key] = GoogleProvider(cfg.google_api_key, cfg.google_model)

        elif provider == ModelProvider.MIXTRAL:
            if not cfg.groq_api_key:
                raise ValueError("GROQ_API_KEY not set. Cannot use mixtral provider.")
            from .providers.groq_provider import GroqProvider
            self._providers[key] = GroqProvider(cfg.groq_api_key, cfg.groq_model)

        elif provider == ModelProvider.OLLAMA:
            from .providers.ollama_provider import OllamaProvider
            self._providers[key] = OllamaProvider(cfg.ollama_model, cfg.ollama_host)

        else:
            raise ValueError(f"Unknown provider: {provider}")

        return self._providers[key]

    async def route(
        self,
        text: str,
        execute: bool = True,
        system_prompt: Optional[str] = None,
    ) -> RouteResponse:
        """
        Classify bias in text, select the best model, and (optionally) call it.

        Args:
            text: The user prompt to route.
            execute: If True (default), calls the selected model and includes its
                     response in RouteResponse.content. If False, only returns
                     the routing decision — useful for dry-run/inspection.
            system_prompt: Optional system prompt forwarded to the target model.

        Returns:
            RouteResponse with routing metadata and (if execute=True) model content.
        """
        start = time.monotonic()

        # Step 1: classify bias
        bias_analysis = await self.classifier.classify(text)

        # Step 2: routing decision
        highest = bias_analysis.get("highest_probability_category", {})
        category = highest.get("category", "others")
        confidence = float(highest.get("probability", 0.0))

        if category in self._routing_table:
            provider_enum, accuracy = self._routing_table[category]
        else:
            provider_enum, accuracy = ModelProvider.GPT4, None

        reason = (
            f"Routed to {provider_enum.value} for '{category}' bias"
            + (f" (benchmark accuracy: {accuracy}%)" if accuracy else "")
        )
        logger.info(reason)

        # Step 3: call the model (optional)
        content = None
        if execute:
            provider = self._get_provider(provider_enum)
            content = await provider.complete(text, system_prompt)

        return RouteResponse(
            selected_model=provider_enum.value,
            provider=provider_enum.value,
            bias_category=category,
            confidence=confidence,
            model_accuracy=accuracy,
            reason=reason,
            content=content,
            response_time=round(time.monotonic() - start, 3),
            bias_analysis=bias_analysis,
        )

    async def stream(
        self,
        text: str,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Classify bias, select the best model, and stream its response token by token.

        Usage:
            async for token in router.stream("your prompt"):
                print(token, end="", flush=True)
        """
        bias_analysis = await self.classifier.classify(text)
        highest = bias_analysis.get("highest_probability_category", {})
        category = highest.get("category", "others")

        provider_enum = self._routing_table.get(category, (ModelProvider.GPT4, None))[0]
        provider = self._get_provider(provider_enum)

        logger.info(f"Streaming via {provider_enum.value} for '{category}' bias")
        async for token in provider.stream(text, system_prompt):
            yield token

    def inspect(self) -> Dict[str, Any]:
        """Return the current routing table for inspection/debugging."""
        return {
            cat: {"provider": prov.value, "accuracy": acc}
            for cat, (prov, acc) in self._routing_table.items()
        }
