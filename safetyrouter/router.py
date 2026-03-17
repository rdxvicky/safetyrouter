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
from .crisis import (
    build_mailto_link,
    build_session_transcript,
    get_crisis_resources,
    get_helpline,
)
from .models import BiasCategory, ModelProvider, RouteResponse
from .providers.base import BaseProvider

logger = logging.getLogger(__name__)

# Default routing table: bias category → (ModelProvider, accuracy_pct)
DEFAULT_ROUTING: Dict[str, tuple] = {
    cat.key: (cat.provider, cat.accuracy) for cat in BiasCategory
}


class SafetyRouter:
    """
    Routes prompts to the best LLM based on detected bias category,
    with two-tier mental health escalation for crisis situations.

    1. Classify bias + mental health risk using gemma3n locally (no API key needed)
    2. If self-harm risk ≥ threshold: emergency escalation — skip LLM
    3. If distress/crisis risk ≥ threshold: run LLM + attach helpline
    4. Otherwise: look up the best provider for the bias type and call it

    Args:
        config: SafetyRouterConfig instance. If None, loads from environment.
        providers: Custom provider instances keyed by ModelProvider value.
                   If None, providers are auto-instantiated from config/env keys.
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

    def _age_aware_system_prompt(
        self, base_prompt: Optional[str], age_range: Optional[str]
    ) -> Optional[str]:
        """Prepend age context to system prompt for youth or elder users."""
        if not age_range:
            return base_prompt

        prefix = None
        if age_range == "Under 18":
            prefix = (
                "The user is a young person (under 18). "
                "Please use age-appropriate language, avoid complex jargon, "
                "and consider youth-specific resources when relevant."
            )
        elif age_range == "60+":
            prefix = (
                "The user is an older adult (60+). "
                "Please use clear, accessible language and consider "
                "elder-specific resources when relevant."
            )

        if not prefix:
            return base_prompt
        return f"{prefix}\n\n{base_prompt}" if base_prompt else prefix

    def _build_emergency_response(
        self, analysis: Dict[str, Any], text: str, start: float
    ) -> RouteResponse:
        """Build an emergency escalation response — skips LLM entirely."""
        mh = analysis.get("mental_health", {})
        country = self.config.user_country
        resources = get_crisis_resources(country)
        helpline_info = get_helpline(country)

        transcript_path = build_session_transcript(
            text=text,
            mental_health_scores=mh,
            user_name=self.config.user_name,
            age_range=self.config.user_age_range,
            country=country,
        )

        emergency_msg = (
            f"Your message suggests you may be in crisis. Please reach out immediately:\n"
            f"Emergency: {resources['emergency']}\n"
            f"Crisis Line: {helpline_info['number']} — {helpline_info['name']}"
        )
        if helpline_info.get("webchat"):
            emergency_msg += f"\nWeb Chat: {helpline_info['webchat']}"

        logger.warning(
            f"EMERGENCY escalation triggered (self_harm={mh.get('self_harm', 0):.2f})"
        )

        return RouteResponse(
            selected_model="escalated",
            provider="human_escalation",
            bias_category="mental_health",
            confidence=float(mh.get("self_harm", 0.0)),
            model_accuracy=None,
            reason="Emergency escalation: high self-harm risk detected. No LLM response generated.",
            content=None,
            response_time=round(time.monotonic() - start, 3),
            bias_analysis=analysis,
            mental_health_scores=mh,
            escalation_type="emergency",
            escalation_number=resources["emergency"],
            escalation_service=helpline_info["name"],
            escalation_webchat=helpline_info.get("webchat"),
            escalation_message=emergency_msg,
            session_transcript_path=transcript_path,
        )

    def _attach_helpline(self, response: RouteResponse) -> RouteResponse:
        """Attach helpline info to a normal RouteResponse."""
        helpline_info = get_helpline(self.config.user_country)

        helpline_msg = f"Support line: {helpline_info['number']} — {helpline_info['name']}"
        if helpline_info.get("webchat"):
            helpline_msg += f" | Chat: {helpline_info['webchat']}"

        response.escalation_type = "helpline"
        response.escalation_number = helpline_info["number"]
        response.escalation_service = helpline_info["name"]
        response.escalation_webchat = helpline_info.get("webchat")
        response.escalation_message = helpline_msg
        return response

    async def route(
        self,
        text: str,
        execute: bool = True,
        system_prompt: Optional[str] = None,
    ) -> RouteResponse:
        """
        Classify bias + mental health risk, escalate if needed, else route to best model.

        Args:
            text: The user prompt to route.
            execute: If True (default), calls the selected model and includes its
                     response in RouteResponse.content. If False, only returns
                     the routing decision — useful for dry-run/inspection.
            system_prompt: Optional system prompt forwarded to the target model.

        Returns:
            RouteResponse with routing metadata and (if execute=True) model content.
            If emergency escalation fires, content is None and escalation_* fields are set.
        """
        start = time.monotonic()

        # Step 1: classify bias + mental health
        analysis = await self.classifier.classify(text)

        # Step 2: two-tier mental health escalation check (runs before LLM routing)
        mh = analysis.get("mental_health", {})
        self_harm_score = float(mh.get("self_harm", 0.0))
        crisis_score = max(
            float(mh.get("existential_crisis", 0.0)),
            float(mh.get("severe_distress", 0.0)),
        )

        if self_harm_score >= self.config.self_harm_threshold:
            return self._build_emergency_response(analysis, text, start)

        # Step 3: routing decision
        highest = analysis.get("highest_probability_category", {})
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

        # Step 4: call the model (optional)
        content = None
        if execute:
            eff_prompt = self._age_aware_system_prompt(system_prompt, self.config.user_age_range)
            provider = self._get_provider(provider_enum)
            content = await provider.complete(text, eff_prompt)

        response = RouteResponse(
            selected_model=provider_enum.value,
            provider=provider_enum.value,
            bias_category=category,
            confidence=confidence,
            model_accuracy=accuracy,
            reason=reason,
            content=content,
            response_time=round(time.monotonic() - start, 3),
            bias_analysis=analysis,
            mental_health_scores=mh,
        )

        # Helpline tier: add helpline info but still return LLM response
        if crisis_score >= self.config.helpline_threshold:
            logger.info(
                f"HELPLINE escalation triggered (crisis_score={crisis_score:.2f})"
            )
            response = self._attach_helpline(response)

        return response

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
        analysis = await self.classifier.classify(text)
        highest = analysis.get("highest_probability_category", {})
        category = highest.get("category", "others")

        provider_enum = self._routing_table.get(category, (ModelProvider.GPT4, None))[0]
        provider = self._get_provider(provider_enum)

        eff_prompt = self._age_aware_system_prompt(system_prompt, self.config.user_age_range)
        logger.info(f"Streaming via {provider_enum.value} for '{category}' bias")
        async for token in provider.stream(text, eff_prompt):
            yield token

    def inspect(self) -> Dict[str, Any]:
        """Return the current routing table for inspection/debugging."""
        return {
            cat: {"provider": prov.value, "accuracy": acc}
            for cat, (prov, acc) in self._routing_table.items()
        }
