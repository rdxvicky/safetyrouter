"""
SafetyRouter — Safety-Aware LLM Routing Framework.

Combines Bias Detection + Mental Health Risk Detection + Human Escalation.
Detects bias type and mental health risk locally with gemma3n (via Ollama),
then routes to the best specialized model or escalates to crisis services.

Quick start:
    from safetyrouter import SafetyRouter

    router = SafetyRouter()
    response = await router.route("Should women be paid less?")
    print(response.selected_model)  # "claude"
    print(response.content)         # Claude's response

Crisis escalation:
    response = await router.route("I want to hurt myself")
    if response.escalation_type == "emergency":
        print(response.escalation_message)  # crisis number + webchat
"""
from .config import SafetyRouterConfig
from .models import BiasCategory, ModelProvider, RouteResponse, UserProfile
from .router import SafetyRouter

__version__ = "0.2.0"
__all__ = [
    "SafetyRouter",
    "SafetyRouterConfig",
    "RouteResponse",
    "BiasCategory",
    "ModelProvider",
    "UserProfile",
]
