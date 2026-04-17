"""
Bias + mental health classifier using gemma3n via Ollama.

Runs entirely locally — no API keys required for classification.
gemma3n is chosen for its strong multilingual reasoning and lightweight
footprint (e2b = 5.6 GB), making it ideal for edge/local deployment.
"""
import asyncio
import json
import logging
import re
from typing import Any, Dict

import ollama

logger = logging.getLogger(__name__)

CLASSIFIER_SYSTEM_PROMPT = """You are a bias detection and mitigation assistant. Analyze the given text and respond ONLY with a JSON object.

Assign probability scores (0.0 to 1.0) for bias categories AND mental health risk indicators. Also generate a rephrased version of the input that removes detected bias while preserving meaning.

Return exactly this JSON structure:
{
  "bias": {
    "demographic": 0.0,
    "age": 0.0,
    "physical_appearance": 0.0,
    "gender": 0.0,
    "disability": 0.0,
    "socioeconomic_status": 0.0,
    "religion": 0.0,
    "sexual_orientation": 0.0,
    "race": 0.0,
    "nationality": 0.0,
    "others": 0.0
  },
  "mental_health": {
    "emotional_dependency": 0.0,
    "self_harm": 0.0,
    "severe_distress": 0.0,
    "existential_crisis": 0.0
  },
  "highest_probability_category": {"category": "<bias_category>", "probability": 0.0},
  "highest_mental_health_risk": {"category": "<mental_health_category>", "probability": 0.0},
  "rephrased_text": {
    "original": "<copy input verbatim>",
    "rephrased": "<rewritten sentence with bias removed, meaning preserved>",
    "changes_made": ["<specific edit 1>", "<specific edit 2>"],
    "meaning_preserved": true
  },
  "note": "<brief explanation under 20 words>"
}

Rules:
- All probability values must be floats between 0.0 and 1.0
- "highest_probability_category" must match the bias category with the highest score
- "highest_mental_health_risk" must match the mental health category with the highest score
- self_harm: assign high scores for explicit mentions of self-harm, suicide, or wanting to die
- severe_distress: assign high scores for expressions of hopelessness, despair, or overwhelming pain
- existential_crisis: assign high scores for loss of purpose, meaninglessness, or reasons to live
- emotional_dependency: assign high scores for unhealthy attachment, isolation, or emotional reliance
- If no clear bias is present, set all bias scores near 0
- If no mental health risk is present, set all mental health scores near 0
- rephrased_text.original: copy the input sentence verbatim
- rephrased_text.rephrased: rewrite to remove the highest-probability bias using inclusive, neutral language; do not add information not in the original
- rephrased_text.changes_made: list each specific edit as a short string describing what was changed and why
- rephrased_text.meaning_preserved: true if rewrite retains original intent; false if factual bias makes neutral rephrasing alter meaning (explain in changes_made)
- If the input is already unbiased, set rephrased equal to original, changes_made to ["No bias detected; no changes required"], and meaning_preserved to true
- Respond with JSON only — no markdown, no extra text"""

_BIAS_CATS = [
    "demographic", "age", "physical_appearance", "gender", "disability",
    "socioeconomic_status", "religion", "sexual_orientation", "race",
    "nationality", "others",
]
_MH_CATS = ["emotional_dependency", "self_harm", "severe_distress", "existential_crisis"]


class BiasClassifier:
    """
    Local bias + mental health classifier powered by gemma3n via Ollama.

    Usage:
        classifier = BiasClassifier(model="gemma3n:e2b")
        result = await classifier.classify("Women shouldn't be engineers.")
    """

    def __init__(self, model: str = "gemma3n:e2b"):
        self.model = model

    async def classify(self, text: str) -> Dict[str, Any]:
        """Classify bias and mental health risk in text. Returns normalized scores."""
        logger.info(f"Classifying text with {self.model}: {text[:80]}...")

        # Issue #6: wrap sync ollama call in a thread to avoid blocking the event loop
        response = await asyncio.to_thread(
            ollama.chat,
            model=self.model,
            messages=[
                {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            options={"temperature": 0},
        )

        raw = response["message"]["content"].strip()

        # Issue #9: robust markdown fence stripping (handles ```json, ```JSON, ``` etc.)
        raw = re.sub(r"^```[a-zA-Z0-9]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw).strip()

        # Issue #2: handle malformed JSON gracefully — return safe fallback instead of crashing
        try:
            analysis = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"Classifier returned invalid JSON ({e}). Raw: {raw[:300]}")
            return self._safe_fallback(text)

        return self._normalize(analysis)

    def _safe_fallback(self, text: str = "") -> Dict[str, Any]:
        """Return zero-score fallback when classifier output cannot be parsed."""
        return {
            "bias": {cat: 0.0 for cat in _BIAS_CATS},
            "mental_health": {cat: 0.0 for cat in _MH_CATS},
            "highest_probability_category": {"category": "others", "probability": 0.0},
            "highest_mental_health_risk": {"category": "none", "probability": 0.0},
            "rephrased_text": {
                "original": text,
                "rephrased": text,
                "changes_made": ["Classifier error — response could not be parsed; no changes made"],
                "meaning_preserved": True,
                "meaning_change_risk": "unknown",
            },
            "note": "Classifier returned invalid JSON — all scores defaulted to 0.",
        }

    def _to_float(self, v: Any) -> float:
        """Convert value to float, scaling 0–100 range to 0–1 if needed."""
        f = float(v)
        return f / 100.0 if f > 1.0 else f

    def _normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all probabilities are in [0, 1] float range."""
        result = {}
        for key, value in raw.items():
            if key == "bias":
                # Issue #8: validate that "bias" is actually a dict
                if not isinstance(value, dict):
                    logger.warning(f"Classifier returned non-dict 'bias' field ({type(value)}); using zeros")
                    value = {}
                result["bias"] = {
                    cat: round(min(max(self._to_float(v), 0.0), 1.0), 4)
                    for cat, v in value.items()
                }
            elif key == "mental_health":
                # Issue #8: validate that "mental_health" is actually a dict
                if not isinstance(value, dict):
                    logger.warning(f"Classifier returned non-dict 'mental_health' field ({type(value)}); using zeros")
                    value = {}
                result["mental_health"] = {
                    cat: round(min(max(self._to_float(v), 0.0), 1.0), 4)
                    for cat, v in value.items()
                }
            elif key == "rephrased_text" and isinstance(value, dict):
                result["rephrased_text"] = self._annotate_rephrasing(value)
            else:
                result[key] = value

        # Issue #8: ensure bias and mental_health keys always exist
        if "bias" not in result:
            logger.warning("Classifier response missing 'bias' field; using zeros")
            result["bias"] = {cat: 0.0 for cat in _BIAS_CATS}
        if "mental_health" not in result:
            logger.warning("Classifier response missing 'mental_health' field; using zeros")
            result["mental_health"] = {cat: 0.0 for cat in _MH_CATS}

        # Recalculate highest fields from actual scores (don't trust model's self-reported values)
        result["highest_probability_category"] = self._find_highest(result)
        result["highest_mental_health_risk"] = self._find_highest_mental_health(result)
        return result

    def _annotate_rephrasing(self, rt: Dict[str, Any]) -> Dict[str, Any]:
        """Issue #11: add a heuristic meaning_change_risk flag to rephrased_text."""
        original = rt.get("original", "")
        rephrased = rt.get("rephrased", "")
        if original and rephrased:
            ratio = len(rephrased) / max(len(original), 1)
            # Flag as high-risk if rephrased is less than half or more than double the original length
            rt["meaning_change_risk"] = "high" if (ratio < 0.5 or ratio > 2.0) else "low"
        else:
            rt["meaning_change_risk"] = "unknown"
        return rt

    def _find_highest(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Find the bias category with the highest probability score.

        'demographic' and 'others' are skipped — they are catch-all categories
        with no dedicated routing entry. If only these are present, falls back
        to 'others' (routed to GPT-4).
        """
        bias_scores = analysis.get("bias", {})
        skip = {"others", "demographic"}
        best_cat, best_prob = "others", 0.0
        for cat, prob in bias_scores.items():
            if cat in skip:
                continue
            p = float(prob)
            if p > best_prob:
                best_prob = p
                best_cat = cat
        return {"category": best_cat, "probability": round(best_prob, 4)}

    def _find_highest_mental_health(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Find the mental health category with the highest risk score."""
        mh_scores = analysis.get("mental_health", {})
        best_cat, best_prob = "none", 0.0
        for cat, prob in mh_scores.items():
            p = float(prob)
            if p > best_prob:
                best_prob = p
                best_cat = cat
        return {"category": best_cat, "probability": round(best_prob, 4)}
