"""
Unit tests for SafetyRouter.

Run with: pytest tests/
"""
import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from safetyrouter import SafetyRouter, SafetyRouterConfig
from safetyrouter.classifier import BiasClassifier
from safetyrouter.models import ModelProvider


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_analysis(bias_overrides=None, mh_overrides=None, note=""):
    """Build a correctly-shaped classifier output dict."""
    bias = {
        "demographic": 0.0, "age": 0.0, "physical_appearance": 0.0,
        "gender": 0.0, "disability": 0.0, "socioeconomic_status": 0.0,
        "religion": 0.0, "sexual_orientation": 0.0, "race": 0.0,
        "nationality": 0.0, "others": 0.0,
    }
    mh = {"emotional_dependency": 0.0, "self_harm": 0.0, "severe_distress": 0.0, "existential_crisis": 0.0}
    if bias_overrides:
        bias.update(bias_overrides)
    if mh_overrides:
        mh.update(mh_overrides)

    # Find highest bias (excluding demographic/others)
    skip = {"demographic", "others"}
    best_cat = max((k for k in bias if k not in skip), key=lambda k: bias[k], default="others")
    best_prob = bias.get(best_cat, 0.0)
    if best_prob == 0.0:
        best_cat = "others"

    # Find highest mental health
    mh_best = max(mh, key=lambda k: mh[k])
    mh_prob = mh[mh_best]

    return {
        "bias": bias,
        "mental_health": mh,
        "highest_probability_category": {"category": best_cat, "probability": best_prob},
        "highest_mental_health_risk": {"category": mh_best if mh_prob > 0 else "none", "probability": mh_prob},
        "rephrased_text": {
            "original": "test",
            "rephrased": "test",
            "changes_made": ["No bias detected; no changes required"],
            "meaning_preserved": True,
            "meaning_change_risk": "low",
        },
        "note": note,
    }


MOCK_GENDER = _make_analysis(bias_overrides={"gender": 0.92})
MOCK_RACE   = _make_analysis(bias_overrides={"race": 0.88})
MOCK_EMERGENCY = _make_analysis(mh_overrides={"self_harm": 0.85})
MOCK_HELPLINE  = _make_analysis(mh_overrides={"severe_distress": 0.65})
MOCK_EMOTIONAL = _make_analysis(mh_overrides={"emotional_dependency": 0.70})


# ── Classifier tests ──────────────────────────────────────────────────────────

class TestBiasClassifier:
    @patch("safetyrouter.classifier.ollama.chat")
    def test_classify_gender_bias(self, mock_chat):
        mock_chat.return_value = {"message": {"content": json.dumps(MOCK_GENDER)}}
        classifier = BiasClassifier(model="gemma3n:e2b")
        result = asyncio.run(classifier.classify("Women shouldn't be engineers."))
        assert result["highest_probability_category"]["category"] == "gender"
        assert result["highest_probability_category"]["probability"] == pytest.approx(0.92)

    @patch("safetyrouter.classifier.ollama.chat")
    def test_normalize_0_to_100_scale(self, mock_chat):
        """Classifier should handle models returning 0-100 instead of 0-1."""
        analysis = _make_analysis()
        analysis["bias"]["gender"] = 92.0   # 0-100 scale
        mock_chat.return_value = {"message": {"content": json.dumps(analysis)}}
        classifier = BiasClassifier(model="gemma3n:e2b")
        result = asyncio.run(classifier.classify("test"))
        assert result["bias"]["gender"] <= 1.0

    @patch("safetyrouter.classifier.ollama.chat")
    def test_strips_markdown_code_fences(self, mock_chat):
        mock_chat.return_value = {
            "message": {"content": f"```json\n{json.dumps(MOCK_GENDER)}\n```"}
        }
        result = asyncio.run(BiasClassifier().classify("test"))
        assert "bias" in result

    @patch("safetyrouter.classifier.ollama.chat")
    def test_strips_uppercase_markdown_fence(self, mock_chat):
        """Issue #9: handle ```JSON (uppercase) code fence."""
        mock_chat.return_value = {
            "message": {"content": f"```JSON\n{json.dumps(MOCK_GENDER)}\n```"}
        }
        result = asyncio.run(BiasClassifier().classify("test"))
        assert "bias" in result

    @patch("safetyrouter.classifier.ollama.chat")
    def test_malformed_json_returns_fallback(self, mock_chat):
        """Issue #2: malformed JSON must return a safe zero-score fallback, not crash."""
        mock_chat.return_value = {"message": {"content": "this is not json { broken"}}
        result = asyncio.run(BiasClassifier().classify("test"))
        # Should return fallback — not raise
        assert result["highest_probability_category"]["category"] == "others"
        assert result["highest_probability_category"]["probability"] == 0.0
        assert "Classifier error" in result["rephrased_text"]["changes_made"][0]

    @patch("safetyrouter.classifier.ollama.chat")
    def test_missing_bias_field_uses_zeros(self, mock_chat):
        """Issue #8: missing 'bias' key in response must not crash."""
        mock_chat.return_value = {
            "message": {"content": json.dumps({"mental_health": MOCK_GENDER["mental_health"], "note": "x"})}
        }
        result = asyncio.run(BiasClassifier().classify("test"))
        assert result["bias"] == {k: 0.0 for k in result["bias"]}

    @patch("safetyrouter.classifier.ollama.chat")
    def test_missing_mental_health_field_uses_zeros(self, mock_chat):
        """Issue #8: missing 'mental_health' key must not crash."""
        mock_chat.return_value = {
            "message": {"content": json.dumps({"bias": MOCK_GENDER["bias"], "note": "x"})}
        }
        result = asyncio.run(BiasClassifier().classify("test"))
        assert result["mental_health"]["self_harm"] == 0.0

    @patch("safetyrouter.classifier.ollama.chat")
    def test_demographic_skipped_in_routing(self, mock_chat):
        """Issue #10: demographic category should not win routing over specific categories."""
        analysis = _make_analysis(bias_overrides={"demographic": 0.9, "race": 0.9})
        mock_chat.return_value = {"message": {"content": json.dumps(analysis)}}
        result = asyncio.run(BiasClassifier().classify("test"))
        # race should win over demographic
        assert result["highest_probability_category"]["category"] == "race"

    @patch("safetyrouter.classifier.ollama.chat")
    def test_meaning_change_risk_annotated(self, mock_chat):
        """Issue #11: meaning_change_risk heuristic should be added to rephrased_text."""
        mock_chat.return_value = {"message": {"content": json.dumps(MOCK_GENDER)}}
        result = asyncio.run(BiasClassifier().classify("test"))
        assert "meaning_change_risk" in result["rephrased_text"]


# ── Router tests ──────────────────────────────────────────────────────────────

class TestSafetyRouter:
    @patch("safetyrouter.classifier.ollama.chat")
    def test_gender_routes_to_gpt4(self, mock_chat):
        mock_chat.return_value = {"message": {"content": json.dumps(MOCK_GENDER)}}
        config = SafetyRouterConfig(openai_api_key="test-key")
        router = SafetyRouter(config=config)

        with patch.object(router, "_get_provider") as mock_get:
            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value="GPT-4 response.")
            mock_get.return_value = mock_provider
            result = asyncio.run(router.route("Women shouldn't be engineers.", execute=True))

        assert result.selected_model == ModelProvider.GPT4.value
        assert result.bias_category == "gender"
        assert result.confidence == pytest.approx(0.92)
        assert result.content == "GPT-4 response."

    @patch("safetyrouter.classifier.ollama.chat")
    def test_race_routes_to_claude(self, mock_chat):
        mock_chat.return_value = {"message": {"content": json.dumps(MOCK_RACE)}}
        config = SafetyRouterConfig(anthropic_api_key="test-key")
        router = SafetyRouter(config=config)

        with patch.object(router, "_get_provider") as mock_get:
            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value="Claude response.")
            mock_get.return_value = mock_provider
            result = asyncio.run(router.route("text with racial bias", execute=True))

        assert result.selected_model == ModelProvider.CLAUDE.value
        assert result.bias_category == "race"

    @patch("safetyrouter.classifier.ollama.chat")
    def test_no_execute_skips_model_call(self, mock_chat):
        mock_chat.return_value = {"message": {"content": json.dumps(MOCK_GENDER)}}
        result = asyncio.run(SafetyRouter().route("test", execute=False))
        assert result.content is None

    def test_inspect_returns_routing_table(self):
        table = SafetyRouter().inspect()
        assert "gender" in table
        assert "race" in table
        assert table["gender"]["provider"] == "gpt4"
        assert table["race"]["provider"] == "claude"

    def test_custom_routing_override(self):
        config = SafetyRouterConfig(custom_routing={"gender": "claude"})
        assert SafetyRouter(config=config).inspect()["gender"]["provider"] == "claude"

    def test_missing_api_key_raises(self):
        config = SafetyRouterConfig(openai_api_key=None)
        router = SafetyRouter(config=config)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            router._get_provider(ModelProvider.GPT4)

    # Issue #1: emergency escalation tests
    @patch("safetyrouter.classifier.ollama.chat")
    def test_emergency_escalation_skips_llm(self, mock_chat):
        """Issue #1: self_harm >= threshold must skip LLM and return crisis info."""
        mock_chat.return_value = {"message": {"content": json.dumps(MOCK_EMERGENCY)}}
        router = SafetyRouter(config=SafetyRouterConfig(self_harm_threshold=0.70))
        result = asyncio.run(router.route("I want to hurt myself", execute=True))

        assert result.escalation_type == "emergency"
        assert result.content is None
        assert result.escalation_number is not None
        assert result.session_transcript_path is not None

    @patch("safetyrouter.classifier.ollama.chat")
    def test_helpline_escalation_includes_llm_response(self, mock_chat):
        """Issue #1: severe_distress >= threshold must return LLM response + helpline."""
        mock_chat.return_value = {"message": {"content": json.dumps(MOCK_HELPLINE)}}
        config = SafetyRouterConfig(helpline_threshold=0.60, openai_api_key="test-key")
        router = SafetyRouter(config=config)

        with patch.object(router, "_get_provider") as mock_get:
            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value="LLM response.")
            mock_get.return_value = mock_provider
            result = asyncio.run(router.route("I feel hopeless.", execute=True))

        assert result.escalation_type == "helpline"
        assert result.content == "LLM response."
        assert result.escalation_number is not None

    @patch("safetyrouter.classifier.ollama.chat")
    def test_emotional_dependency_triggers_helpline(self, mock_chat):
        """Issue #7: emotional_dependency >= helpline_threshold must trigger helpline."""
        mock_chat.return_value = {"message": {"content": json.dumps(MOCK_EMOTIONAL)}}
        config = SafetyRouterConfig(helpline_threshold=0.60, openai_api_key="test-key")
        router = SafetyRouter(config=config)

        with patch.object(router, "_get_provider") as mock_get:
            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value="response")
            mock_get.return_value = mock_provider
            result = asyncio.run(router.route("I can't live without them.", execute=True))

        assert result.escalation_type == "helpline"

    @patch("safetyrouter.classifier.ollama.chat")
    def test_unknown_bias_category_falls_back_to_gpt4(self, mock_chat):
        """Issue #3: unknown category must fall back to GPT-4 (not crash)."""
        analysis = _make_analysis()
        analysis["highest_probability_category"] = {"category": "linguistic_bias", "probability": 0.8}
        mock_chat.return_value = {"message": {"content": json.dumps(analysis)}}
        config = SafetyRouterConfig(openai_api_key="test-key")
        router = SafetyRouter(config=config)

        with patch.object(router, "_get_provider") as mock_get:
            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(return_value="fallback response")
            mock_get.return_value = mock_provider
            result = asyncio.run(router.route("test", execute=True))

        assert result.selected_model == ModelProvider.GPT4.value
        assert result.model_accuracy is None

    @patch("safetyrouter.classifier.ollama.chat")
    def test_provider_exception_surfaces_clearly(self, mock_chat):
        """Issue #4: provider exceptions must raise RuntimeError, not propagate raw."""
        mock_chat.return_value = {"message": {"content": json.dumps(MOCK_GENDER)}}
        config = SafetyRouterConfig(openai_api_key="test-key")
        router = SafetyRouter(config=config)

        with patch.object(router, "_get_provider") as mock_get:
            mock_provider = AsyncMock()
            mock_provider.complete = AsyncMock(side_effect=ConnectionError("timeout"))
            mock_get.return_value = mock_provider

            with pytest.raises(RuntimeError, match="gpt4.*failed"):
                asyncio.run(router.route("test", execute=True))

    def test_input_too_long_raises(self):
        """Issue #16: inputs over MAX_INPUT_LENGTH must raise ValueError."""
        router = SafetyRouter()
        with pytest.raises(ValueError, match="too long"):
            asyncio.run(router.route("x" * 10_001, execute=False))

    # Issue #1: stream() escalation tests
    @patch("safetyrouter.classifier.ollama.chat")
    def test_stream_emergency_yields_crisis_info(self, mock_chat):
        """Issue #1: stream() must yield crisis resources on self_harm, not LLM tokens."""
        mock_chat.return_value = {"message": {"content": json.dumps(MOCK_EMERGENCY)}}
        router = SafetyRouter(config=SafetyRouterConfig(self_harm_threshold=0.70))

        async def collect():
            tokens = []
            async for t in router.stream("I want to hurt myself"):
                tokens.append(t)
            return tokens

        tokens = asyncio.run(collect())
        combined = "".join(tokens)
        assert "CRISIS" in combined or "Emergency" in combined

    # Issue #13: config threshold validation
    def test_invalid_threshold_env_var_uses_default(self, monkeypatch):
        """Issue #13: bad SR_SELF_HARM_THRESHOLD must not crash — falls back to 0.70."""
        monkeypatch.setenv("SR_SELF_HARM_THRESHOLD", "not-a-float")
        config = SafetyRouterConfig.from_env()
        assert config.self_harm_threshold == pytest.approx(0.70)

    # Issue #14: custom routing from env
    def test_custom_routing_from_env(self, monkeypatch):
        """Issue #14: SR_CUSTOM_ROUTING env var must override routing table."""
        monkeypatch.setenv("SR_CUSTOM_ROUTING", '{"gender": "claude"}')
        config = SafetyRouterConfig.from_env()
        assert config.custom_routing == {"gender": "claude"}

    def test_invalid_custom_routing_env_var_uses_empty(self, monkeypatch):
        """Issue #14: malformed SR_CUSTOM_ROUTING must not crash."""
        monkeypatch.setenv("SR_CUSTOM_ROUTING", "not-json")
        config = SafetyRouterConfig.from_env()
        assert config.custom_routing == {}

    # Issue #15: session transcript permissions
    @patch("safetyrouter.classifier.ollama.chat")
    def test_emergency_transcript_is_owner_only(self, mock_chat, tmp_path, monkeypatch):
        """Issue #15: emergency transcript must be chmod 0600."""
        monkeypatch.setattr("safetyrouter.crisis.os.path.expanduser", lambda p: str(tmp_path))
        mock_chat.return_value = {"message": {"content": json.dumps(MOCK_EMERGENCY)}}
        router = SafetyRouter(config=SafetyRouterConfig(self_harm_threshold=0.70))
        result = asyncio.run(router.route("I want to hurt myself", execute=False))

        if result.session_transcript_path and os.path.exists(result.session_transcript_path):
            mode = oct(os.stat(result.session_transcript_path).st_mode)[-3:]
            assert mode == "600", f"Expected 600, got {mode}"
