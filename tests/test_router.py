"""
Unit tests for SafetyRouter.

Run with: pytest tests/
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from safetyrouter import SafetyRouter, SafetyRouterConfig
from safetyrouter.classifier import BiasClassifier
from safetyrouter.models import ModelProvider


# --- Fixtures ---

MOCK_GENDER_ANALYSIS = {
    "demographic": {"probability": 0.1},
    "age": {"probability": 0.0},
    "physical_appearance": {"probability": 0.0},
    "gender": {"probability": 0.92},
    "disability": {"probability": 0.0},
    "socioeconomic_status": {"probability": 0.0},
    "religion": {"probability": 0.0},
    "sexual_orientation": {"probability": 0.05},
    "race": {"probability": 0.0},
    "nationality": {"probability": 0.0},
    "others": {"probability": 0.0},
    "highest_probability_category": {"category": "gender", "probability": 0.92},
    "note": "Text contains gender bias.",
}

MOCK_RACE_ANALYSIS = {
    **{k: {"probability": 0.0} for k in [
        "demographic", "age", "physical_appearance", "gender",
        "disability", "socioeconomic_status", "religion",
        "sexual_orientation", "nationality", "others",
    ]},
    "race": {"probability": 0.88},
    "highest_probability_category": {"category": "race", "probability": 0.88},
    "note": "Text contains racial bias.",
}


# --- Classifier tests ---

class TestBiasClassifier:
    @patch("safetyrouter.classifier.ollama.chat")
    def test_classify_gender_bias(self, mock_chat):
        mock_chat.return_value = {
            "message": {"content": json.dumps(MOCK_GENDER_ANALYSIS)}
        }
        classifier = BiasClassifier(model="gemma3n:e2b")
        result = asyncio.run(classifier.classify("Women shouldn't be engineers."))
        assert result["highest_probability_category"]["category"] == "gender"
        assert result["highest_probability_category"]["probability"] == pytest.approx(0.92)

    @patch("safetyrouter.classifier.ollama.chat")
    def test_normalize_0_to_100_scale(self, mock_chat):
        """Classifier should handle models returning 0-100 instead of 0-1."""
        analysis_100_scale = {**MOCK_GENDER_ANALYSIS}
        analysis_100_scale["gender"] = {"probability": 92.0}  # 0-100 scale
        mock_chat.return_value = {
            "message": {"content": json.dumps(analysis_100_scale)}
        }
        classifier = BiasClassifier(model="gemma3n:e2b")
        result = asyncio.run(classifier.classify("test"))
        assert result["gender"]["probability"] <= 1.0

    @patch("safetyrouter.classifier.ollama.chat")
    def test_strips_markdown_code_fences(self, mock_chat):
        mock_chat.return_value = {
            "message": {"content": f"```json\n{json.dumps(MOCK_GENDER_ANALYSIS)}\n```"}
        }
        classifier = BiasClassifier()
        result = asyncio.run(classifier.classify("test"))
        assert "gender" in result


# --- Router tests ---

class TestSafetyRouter:
    @patch("safetyrouter.classifier.ollama.chat")
    def test_gender_routes_to_gpt4(self, mock_chat):
        mock_chat.return_value = {
            "message": {"content": json.dumps(MOCK_GENDER_ANALYSIS)}
        }
        config = SafetyRouterConfig(openai_api_key="test-key")
        router = SafetyRouter(config=config)

        with patch.object(router, "_get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value="GPT-4 response about gender.")
            mock_get_provider.return_value = mock_provider

            result = asyncio.run(router.route("Women shouldn't be engineers.", execute=True))

        assert result.selected_model == ModelProvider.GPT4.value
        assert result.bias_category == "gender"
        assert result.confidence == pytest.approx(0.92)
        assert result.content == "GPT-4 response about gender."

    @patch("safetyrouter.classifier.ollama.chat")
    def test_race_routes_to_claude(self, mock_chat):
        mock_chat.return_value = {
            "message": {"content": json.dumps(MOCK_RACE_ANALYSIS)}
        }
        config = SafetyRouterConfig(anthropic_api_key="test-key")
        router = SafetyRouter(config=config)

        with patch.object(router, "_get_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value="Claude response.")
            mock_get_provider.return_value = mock_provider

            result = asyncio.run(router.route("text with racial bias", execute=True))

        assert result.selected_model == ModelProvider.CLAUDE.value
        assert result.bias_category == "race"

    @patch("safetyrouter.classifier.ollama.chat")
    def test_no_execute_skips_model_call(self, mock_chat):
        mock_chat.return_value = {
            "message": {"content": json.dumps(MOCK_GENDER_ANALYSIS)}
        }
        router = SafetyRouter()
        result = asyncio.run(router.route("test", execute=False))
        assert result.content is None

    def test_inspect_returns_routing_table(self):
        router = SafetyRouter()
        table = router.inspect()
        assert "gender" in table
        assert "race" in table
        assert table["gender"]["provider"] == "gpt4"
        assert table["race"]["provider"] == "claude"

    def test_custom_routing_override(self):
        config = SafetyRouterConfig(custom_routing={"gender": "claude"})
        router = SafetyRouter(config=config)
        table = router.inspect()
        assert table["gender"]["provider"] == "claude"

    def test_missing_api_key_raises(self):
        config = SafetyRouterConfig(openai_api_key=None)
        router = SafetyRouter(config=config)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            router._get_provider(ModelProvider.GPT4)


import asyncio  # noqa: E402 — import at end to avoid polluting test namespace
