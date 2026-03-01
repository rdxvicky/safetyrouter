"""
Bias classifier using gemma3n via Ollama.

Runs entirely locally — no API keys required for classification.
gemma3n is chosen for its strong multilingual reasoning and lightweight
footprint (e2b = 5.6 GB), making it ideal for edge/local deployment.
"""
import json
import logging
from typing import Any, Dict

import ollama

logger = logging.getLogger(__name__)

CLASSIFIER_SYSTEM_PROMPT = """You are a bias detection classifier. Analyze the given text and respond ONLY with a JSON object.

Assign probability scores (0.0 to 1.0) for each bias category based on how likely the text contains or relates to that type of bias.

Return exactly this JSON structure:
{
  "demographic": {"probability": 0.0},
  "age": {"probability": 0.0},
  "physical_appearance": {"probability": 0.0},
  "gender": {"probability": 0.0},
  "disability": {"probability": 0.0},
  "socioeconomic_status": {"probability": 0.0},
  "religion": {"probability": 0.0},
  "sexual_orientation": {"probability": 0.0},
  "race": {"probability": 0.0},
  "nationality": {"probability": 0.0},
  "others": {"probability": 0.0},
  "highest_probability_category": {"category": "<category_name>", "probability": 0.0},
  "note": "<brief explanation under 20 words>"
}

Rules:
- All probability values must be floats between 0.0 and 1.0
- "highest_probability_category" must match the category with the highest score
- If no clear bias is present, set all scores near 0 and use "others"
- Respond with JSON only — no markdown, no extra text"""


class BiasClassifier:
    """
    Local bias classifier powered by gemma3n via Ollama.

    Usage:
        classifier = BiasClassifier(model="gemma3n:e2b")
        result = await classifier.classify("Women shouldn't be engineers.")
    """

    def __init__(self, model: str = "gemma3n:e2b"):
        self.model = model

    async def classify(self, text: str) -> Dict[str, Any]:
        """Classify bias in text. Returns normalized probability scores."""
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

    def _normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all probabilities are in [0, 1] float range."""
        result = {}
        for key, value in raw.items():
            if isinstance(value, dict) and "probability" in value:
                prob = float(value["probability"])
                # Handle cases where the model returns 0–100 instead of 0–1
                if prob > 1.0:
                    prob = prob / 100.0
                result[key] = {"probability": round(min(max(prob, 0.0), 1.0), 4)}
            else:
                result[key] = value

        # Recalculate highest_probability_category to be safe
        result["highest_probability_category"] = self._find_highest(result)
        return result

    def _find_highest(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        skip = {"highest_probability_category", "others", "note"}
        best_cat, best_prob = "others", 0.0
        for cat, val in analysis.items():
            if cat in skip:
                continue
            if isinstance(val, dict) and "probability" in val:
                prob = float(val["probability"])
                if prob > best_prob:
                    best_prob = prob
                    best_cat = cat
        return {"category": best_cat, "probability": round(best_prob, 4)}
