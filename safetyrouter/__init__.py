"""
SafetyRouter — Bias-aware LLM routing.

Detects bias type locally with gemma3n (via Ollama), then routes
to the best specialized model for that bias category.

Quick start:
    from safetyrouter import SafetyRouter

    router = SafetyRouter()
    response = await router.route("Should women be paid less?")
    print(response.selected_model)  # "claude"
    print(response.content)         # Claude's response
"""
from .config import SafetyRouterConfig
from .models import BiasCategory, ModelProvider, RouteResponse
from .router import SafetyRouter

__version__ = "0.1.1"
__all__ = [
    "SafetyRouter",
    "SafetyRouterConfig",
    "RouteResponse",
    "BiasCategory",
    "ModelProvider",
]
