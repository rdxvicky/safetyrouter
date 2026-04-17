"""
Bias + mental health classifier using gemma3n via Ollama.

Runs entirely locally — no API keys required for classification.
gemma3n is chosen for its strong multilingual reasoning and lightweight
footprint (e2b = 5.6 GB), making it ideal for edge/local deployment.
"""
import json
import logging
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

        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            options={"temperature": 0},
        )

        raw = response["message"]["content"].strip()

        # Strip markdown code fences if the model wraps its output
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        analysis = json.loads(raw)
        return self._normalize(analysis)

    def _to_float(self, v: Any) -> float:
        """Convert value to float, scaling 0–100 range to 0–1 if needed."""
        f = float(v)
        return f / 100.0 if f > 1.0 else f

    def _normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all probabilities are in [0, 1] float range."""
        result = {}
        for key, value in raw.items():
            if key == "bias" and isinstance(value, dict):
                result["bias"] = {
                    cat: round(min(max(self._to_float(v), 0.0), 1.0), 4)
                    for cat, v in value.items()
                }
            elif key == "mental_health" and isinstance(value, dict):
                result["mental_health"] = {
                    cat: round(min(max(self._to_float(v), 0.0), 1.0), 4)
                    for cat, v in value.items()
                }
            elif key == "rephrased_text" and isinstance(value, dict):
                result["rephrased_text"] = value
            else:
                result[key] = value

        # Recalculate highest fields to be safe
        result["highest_probability_category"] = self._find_highest(result)
        result["highest_mental_health_risk"] = self._find_highest_mental_health(result)
        return result

    def _find_highest(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Find the bias category with the highest probability score."""
        bias_scores = analysis.get("bias", {})
        skip = {"others"}
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
