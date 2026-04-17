"""
Configuration management for SafetyRouter.

Values are loaded from environment variables (or a .env file).
All API keys are optional — only the keys for providers you use are required.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Issue #18: clarified priority order comment.
# python-dotenv only sets variables that are NOT already in os.environ,
# so the FIRST source that provides a value wins.
# Priority (highest → lowest):
#   1. Actual shell environment variables (os.environ)
#   2. Local ./.env file  — project-level overrides
#   3. ~/.safetyrouter.env — global fallback (written by `safetyrouter setup`)
load_dotenv()                                              # sets vars from .env not in os.environ
load_dotenv(os.path.expanduser("~/.safetyrouter.env"))    # sets remaining vars from global config


def _safe_float(env_var: str, default: float) -> float:
    """Issue #13: parse float env vars safely — bad values fall back to default."""
    raw = os.getenv(env_var)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning(f"Invalid value for {env_var}='{raw}' — using default {default}")
        return default


def _parse_custom_routing() -> Dict[str, str]:
    """Issue #14: allow custom routing overrides via SR_CUSTOM_ROUTING env var (JSON dict)."""
    raw = os.getenv("SR_CUSTOM_ROUTING", "{}")
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("must be a JSON object")
        return {str(k): str(v) for k, v in parsed.items()}
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Invalid SR_CUSTOM_ROUTING='{raw}' ({e}) — ignoring custom routing")
        return {}


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
    anthropic_model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-opus-4-5-20251101"))
    google_model: str = field(default_factory=lambda: os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"))
    groq_model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "open-mixtral-8x7b"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.2"))

    # Ollama host (for local provider)
    ollama_host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))

    # Custom bias-to-provider routing table (overrides defaults).
    # Issue #14: can now be set via SR_CUSTOM_ROUTING='{"gender":"claude","race":"gpt4"}'
    # Format: {"gender": "gpt4", "race": "claude", ...}
    custom_routing: Dict[str, str] = field(default_factory=_parse_custom_routing)

    # User profile (for age-aware responses and country-specific crisis resources)
    user_name: Optional[str] = field(default_factory=lambda: os.getenv("SR_USER_NAME"))
    user_age_range: Optional[str] = field(default_factory=lambda: os.getenv("SR_USER_AGE_RANGE"))
    user_country: str = field(default_factory=lambda: os.getenv("SR_USER_COUNTRY", "US"))

    # Mental health escalation thresholds.
    # Issue #19: threshold rationale documented here.
    # self_harm_threshold=0.70 — high bar for emergency (skips LLM entirely).
    #   At 0.70 the classifier has seen clear self-harm language; lower values
    #   risk false-positives on metaphorical phrases ("I could kill for a coffee").
    # helpline_threshold=0.60 — lower bar since a helpline note is low-cost and
    #   the LLM still responds. Catches severe distress, existential crisis, and
    #   extreme emotional dependency even when self-harm language is absent.
    # Both are configurable — tune down if you prefer sensitivity over specificity.
    self_harm_threshold: float = field(
        default_factory=lambda: _safe_float("SR_SELF_HARM_THRESHOLD", 0.70)
    )
    helpline_threshold: float = field(
        default_factory=lambda: _safe_float("SR_HELPLINE_THRESHOLD", 0.60)
    )

    @classmethod
    def from_env(cls) -> "SafetyRouterConfig":
        return cls()
