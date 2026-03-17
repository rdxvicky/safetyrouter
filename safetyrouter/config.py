"""
Configuration management for SafetyRouter.

Values are loaded from environment variables (or a .env file).
All API keys are optional — only the keys for providers you use are required.
"""
import os
from dataclasses import dataclass, field
from typing import Dict, Optional

from dotenv import load_dotenv

# Load in priority order (later calls don't override earlier ones):
#   1. Actual environment variables   — highest priority
#   2. Local .env file                — project-level overrides
#   3. ~/.safetyrouter.env            — global fallback (written by `safetyrouter setup`)
load_dotenv()
load_dotenv(os.path.expanduser("~/.safetyrouter.env"))


@dataclass
class SafetyRouterConfig:
    # Classifier model (runs locally via Ollama)
    classifier_model: str = "gemma3n:e2b"

    # Provider API keys
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    google_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))
    groq_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GROQ_API_KEY"))

    # Provider model overrides (optional — sensible defaults used if not set)
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    anthropic_model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6"))
    google_model: str = field(default_factory=lambda: os.getenv("GOOGLE_MODEL", "gemini-1.5-pro"))
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "mixtral-8x7b-32768"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2"))

    # Ollama host (for local provider)
    ollama_host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))

    # Custom bias-to-provider routing table (overrides defaults)
    # Format: {"gender": "gpt4", "race": "claude", ...}
    custom_routing: Dict[str, str] = field(default_factory=dict)

    # User profile (for age-aware responses and country-specific crisis resources)
    user_name: Optional[str] = field(default_factory=lambda: os.getenv("SR_USER_NAME"))
    user_age_range: Optional[str] = field(default_factory=lambda: os.getenv("SR_USER_AGE_RANGE"))
    user_country: str = field(default_factory=lambda: os.getenv("SR_USER_COUNTRY", "US"))

    # Mental health escalation thresholds
    self_harm_threshold: float = field(
        default_factory=lambda: float(os.getenv("SR_SELF_HARM_THRESHOLD", "0.70"))
    )
    helpline_threshold: float = field(
        default_factory=lambda: float(os.getenv("SR_HELPLINE_THRESHOLD", "0.60"))
    )

    @classmethod
    def from_env(cls) -> "SafetyRouterConfig":
        return cls()
